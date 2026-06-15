"""
大学选课助手 — 知识库 + 联网双路径
====================================
用法:
  python ask_kb.py "你的问题"              # 启用联网搜索
  python ask_kb.py --no-web "你的问题"     # 仅知识库

特性:
  - MMR 检索（去重 + 多样性）
  - 联网搜索扩展（知识库不足时自动补充）
  - 双路径来源展示
"""

import os
import sys
import argparse

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI
from duckduckgo_search import DDGS


DB_PATH = "chroma_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RETRIEVAL_K = 5
MMR_LAMBDA = 0.7
MAX_WEB_RESULTS = 3


def web_search(query: str, max_results: int = MAX_WEB_RESULTS) -> list[dict]:
    """DuckDuckGo 联网搜索"""
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        print(f"   ⚠️ 联网搜索失败: {e}")
        return []


def build_dual_prompt(kb_context: str, web_context: str, question: str) -> list[dict]:
    """构造双路径提示词"""
    has_kb = bool(kb_context.strip())
    has_web = bool(web_context.strip())

    if has_kb and has_web:
        source_note = "知识库资料 + 联网搜索结果"
        system_prompt = """你是一个大学选课指南助手，你的回答要：

1. **综合回答**：同时使用知识库资料和联网搜索结果
2. **明确标注来源**：📚 知识库 / 🌐 联网搜索
3. **诚实透明**：资料不足时明确说明
4. **结构化输出**：使用要点、编号等让回答清晰易读"""
    elif has_kb:
        source_note = "知识库资料"
        system_prompt = """你是一个大学选课指南助手，你的回答要：

1. **严格基于资料**：只使用知识库资料回答问题
2. **诚实透明**：资料不足时明确说明
3. **结构化输出**：使用要点、编号等让回答清晰易读"""
    else:
        source_note = "联网搜索结果（知识库中未找到）"
        system_prompt = """你是一个大学选课指南助手，你的回答要：

1. **基于搜索结果**：使用联网搜索信息回答问题
2. **诚实告知**：说明这是联网搜索的结果
3. **结构化输出**：使用要点、编号等让回答清晰易读"""

    parts = [f"信息源: {source_note}"]
    if has_kb:
        parts.append(f"【📚 知识库资料】\n{kb_context}")
    if has_web:
        parts.append(f"【🌐 联网搜索结果】\n{web_context}")
    parts.append(f"【问题】\n{question}")
    parts.append("请根据上述信息回答问题，用 📚 和 🌐 标注来源。")

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="大学生选课指南问答")
    parser.add_argument("question", nargs="*", help="问题")
    parser.add_argument("--no-web", action="store_true", help="禁用联网搜索")
    args = parser.parse_args()

    question = " ".join(args.question).strip()
    if not question:
        question = input("🔍 请输入问题: ").strip()
    if not question:
        raise ValueError("问题不能为空")

    web_enabled = not args.no_web

    print(f"\n🔍 问题: {question}")
    print(f"{'='*50}")

    # 1. 知识库检索
    print("\n📡 检索知识库中...")
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    vectorstore = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embeddings,
    )

    docs = vectorstore.max_marginal_relevance_search(
        question,
        k=RETRIEVAL_K,
        lambda_mult=MMR_LAMBDA,
    )
    print(f"   ✅ 知识库命中 {len(docs)} 个片段")

    kb_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知来源")
        page = doc.metadata.get("page", "")
        page_info = f" (第{page}页)" if page != "" else ""
        kb_parts.append(f"[片段 {i} — 来自: {source}{page_info}]\n{doc.page_content}")
    kb_context = "\n\n".join(kb_parts)

    # 2. 联网搜索
    web_context = ""
    web_results = []
    if web_enabled:
        print("\n🌐 联网搜索中...")
        web_results = web_search(question)
        if web_results:
            print(f"   ✅ 找到 {len(web_results)} 条网页结果")
            web_parts = []
            for i, r in enumerate(web_results, 1):
                title = r.get("title", "")
                snippet = r.get("body", "")
                href = r.get("href", "")
                web_parts.append(f"[网页 {i}] {title}\n链接: {href}\n摘要: {snippet}")
            web_context = "\n\n".join(web_parts)
        else:
            print("   ℹ️ 无联网搜索结果")
    else:
        print("\n🌐 联网搜索已禁用（--no-web）")

    # 3. LLM 生成
    print("\n🤖 正在生成回答...")
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )

    messages = build_dual_prompt(kb_context, web_context, question)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.3,
    )

    answer = response.choices[0].message.content

    # 4. 输出
    print(f"\n{'='*50}")
    print("📝 回答:")
    print(f"{'='*50}")
    print(answer)

    print(f"\n{'='*50}")
    print("📎 参考来源:")
    print(f"{'='*50}")

    if kb_parts:
        print("\n📚 知识库来源:")
        seen = set()
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "未知")
            page = doc.metadata.get("page", "")
            page_info = f" p.{page}" if page != "" else ""
            preview = doc.page_content.replace("\n", " ")[:100]
            key = f"{source}{page}"
            if key not in seen:
                seen.add(key)
                print(f"  [{i}] {source}{page_info}")
                print(f"       {preview}...")

    if web_results:
        print("\n🌐 联网搜索来源:")
        for i, r in enumerate(web_results, 1):
            title = r.get("title", "无标题")
            href = r.get("href", "")
            snippet = r.get("body", "")[:100]
            print(f"  [{i}] {title}")
            print(f"       {snippet}...")
            if href:
                print(f"       🔗 {href}")


if __name__ == "__main__":
    main()

    # 4. 输出结果
    print(f"\n{'='*50}")
    print("📝 回答:")
    print(f"{'='*50}")
    print(answer)

    print(f"\n{'='*50}")
    print("📎 参考来源:")
    print(f"{'='*50}")
    seen_sources = set()
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知来源")
        page = doc.metadata.get("page", "")
        page_info = f" p.{page}" if page != "" else ""
        preview = doc.page_content.replace("\n", " ")[:100]
        source_key = f"{source}{page_info}"
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            print(f"\n  [{i}] {source}{page_info}")
            print(f"      {preview}...")


if __name__ == "__main__":
    main()
