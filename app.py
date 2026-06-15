"""
大学选课助手 — RAG 问答系统（知识库 + 联网双路径）
==================================================
基于 LangChain + Chroma + DeepSeek + DuckDuckGo 的智能问答系统
知识库查不到时自动切换为联网搜索。
"""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI
from duckduckgo_search import DDGS

# ── 配置 ──────────────────────────────────────────────
DB_PATH = Path("chroma_db")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RETRIEVAL_K = 5
MMR_LAMBDA = 0.7
MAX_WEB_RESULTS = 3  # 联网搜索返回的网页数

# 缓存加载资源
@st.cache_resource
def load_resources():
    load_dotenv()
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    vectorstore = Chroma(
        persist_directory=str(DB_PATH),
        embedding_function=embeddings,
    )
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    return vectorstore, client


def web_search(query: str, max_results: int = MAX_WEB_RESULTS) -> list[dict]:
    """使用 DuckDuckGo 搜索网页"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        return [{"title": "搜索出错", "body": f"联网搜索失败: {e}"}]


def build_dual_prompt(kb_context: str, web_context: str, question: str) -> list[dict]:
    """构造双路径提示词"""
    has_kb = bool(kb_context.strip())
    has_web = bool(web_context.strip())

    if has_kb and has_web:
        source_note = "知识库资料 + 联网搜索结果"
        system_prompt = """你是一个大学选课指南助手，你的回答要：

1. **综合回答**：同时使用知识库资料和联网搜索结果来回答问题
2. **明确标注来源**：来自知识库的内容标注 📚，来自联网搜索的内容标注 🌐
3. **诚实透明**：资料不足时明确说明
4. **结构化输出**：使用要点、编号等让回答清晰易读"""
    elif has_kb:
        source_note = "知识库资料"
        system_prompt = """你是一个大学选课指南助手，你的回答要：

1. **严格基于资料**：只使用下面给出的知识库资料来回答问题
2. **诚实透明**：资料不足时明确说明
3. **结构化输出**：使用要点、编号等让回答清晰易读"""
    else:
        source_note = "联网搜索结果（知识库中未找到相关信息）"
        system_prompt = """你是一个大学选课指南助手，你的回答要：

1. **基于搜索结果**：使用联网搜索结果来回答问题
2. **诚实告知**：说明这是来自联网搜索的信息，非本地知识库内容
3. **结构化输出**：使用要点、编号等让回答清晰易读"""

    context_parts = []
    if has_kb:
        context_parts.append(f"【📚 知识库资料】\n{kb_context}")
    if has_web:
        context_parts.append(f"【🌐 联网搜索结果】\n{web_context}")

    user_prompt = f"""信息源: {source_note}

{"\n\n".join(context_parts)}

【问题】
{question}

【要求】
请根据上述信息回答问题，并在回答中用 📚 和 🌐 标注每条信息的来源。"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def retrieve_and_answer(question: str, web_enabled: bool = True):
    """双路径检索：知识库 + 联网搜索"""
    vectorstore, client = load_resources()

    # ── 1. 知识库检索 ──
    docs = vectorstore.max_marginal_relevance_search(
        question,
        k=RETRIEVAL_K,
        lambda_mult=MMR_LAMBDA,
    )

    kb_context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知来源")
        page = doc.metadata.get("page", "")
        page_info = f" (第{page}页)" if page != "" else ""
        kb_context_parts.append(f"[片段 {i} — 来自: {source}{page_info}]\n{doc.page_content}")
    kb_context = "\n\n".join(kb_context_parts)

    # ── 2. 联网搜索（可选） ──
    web_context = ""
    web_results = []
    if web_enabled:
        try:
            results = web_search(question)
            web_parts = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                snippet = r.get("body", "")
                href = r.get("href", "")
                web_parts.append(f"[网页 {i}] {title}\n链接: {href}\n摘要: {snippet}")
                web_results.append(r)
            web_context = "\n\n".join(web_parts)
        except Exception as e:
            web_context = f"（联网搜索暂时不可用: {e}）"

    # ── 3. LLM 生成 ──
    messages = build_dual_prompt(kb_context, web_context, question)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.3,
    )

    answer = response.choices[0].message.content
    return answer, docs, web_results


def get_kb_stats():
    """获取知识库统计信息"""
    vectorstore, _ = load_resources()
    try:
        count = vectorstore._collection.count()
    except Exception:
        count = "?"
    docs_dir = Path("docs")
    doc_files = list(docs_dir.glob("*.*")) if docs_dir.exists() else []
    return count, doc_files


# ── 页面配置 ──────────────────────────────────────────
st.set_page_config(
    page_title="大学生选课指南",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 侧边栏 ────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 📚 大学生选课指南")
    st.markdown("---")

    kb_count, doc_files = get_kb_stats()
    st.markdown("### 📊 知识库状态")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("向量数", kb_count)
    with col2:
        st.metric("文档数", len(doc_files))

    if doc_files:
        st.markdown("### 📄 文档列表")
        for f in doc_files:
            st.markdown(f"- {f.name}")

    st.markdown("---")
    st.markdown("### ⚙️ 检索参数")
    st.markdown(f"- 检索数量: `{RETRIEVAL_K}`")
    st.markdown(f"- MMR 多样性: `{MMR_LAMBDA}`")
    st.markdown(f"- Embedding: `{MODEL_NAME}`")

    st.markdown("---")
    st.markdown("### 🌐 联网搜索")
    web_enabled = st.checkbox("启用联网搜索", value=True,
                               help="知识库查不到时自动搜索网页补充答案")
    st.markdown(f"- 最大结果: `{MAX_WEB_RESULTS}` 条")
    st.markdown(f"- 搜索引擎: DuckDuckGo（免费）")

    st.markdown("---")
    st.markdown("### 🛠 技术栈")
    st.markdown("""
- LangChain
- ChromaDB
- sentence-transformers
- DeepSeek API
- DuckDuckGo Search
- Streamlit
""")

# ── 主界面 ────────────────────────────────────────────
st.title("📚 大学生选课指南")
st.caption("基于 RAG 架构的本地知识库智能问答系统 — 快速查询选课信息")

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好！我是大学选课知识库助手 📚\n\n我可以帮你查询选课相关的信息，例如：\n- *通识选修课有哪些类别？*\n- *选课系统什么时候开放？*\n- *学分上限是多少？*\n- *怎么退课？*\n- *跨专业选课有什么限制？*\n\n请直接在下方输入问题开始查询！"}
    ]

# 显示聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # 如果有来源信息，显示在 expander 中
        has_sources = "sources" in msg and len(msg["sources"]) > 0
        has_web = "web_sources" in msg and len(msg["web_sources"]) > 0
        if has_sources or has_web:
            with st.expander("📎 查看参考来源", expanded=False):
                if has_sources:
                    st.markdown("**📚 知识库来源**")
                    seen = set()
                    for i, src in enumerate(msg["sources"], 1):
                        source = src.metadata.get("source", "未知")
                        page = src.metadata.get("page", "")
                        page_info = f" (p.{page})" if page != "" else ""
                        preview = src.page_content.replace("\n", " ")[:150]
                        key = f"{source}{page}"
                        if key not in seen:
                            seen.add(key)
                            st.markdown(f"**[{i}] {source}{page_info}**")
                            st.markdown(f"> {preview}...")
                if has_web:
                    st.markdown("**🌐 联网搜索来源**")
                    for i, r in enumerate(msg["web_sources"], 1):
                        title = r.get("title", "无标题")
                        href = r.get("href", "")
                        snippet = r.get("body", "")[:150]
                        st.markdown(f"**[{i}] {title}**")
                        st.markdown(f"> {snippet}...")
                        if href:
                            st.markdown(f"  🔗 [{href}]({href})")

# 输入框
if prompt := st.chat_input("请输入你的问题..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 生成回答
    with st.chat_message("assistant"):
        with st.spinner("📡 检索知识库中..."):
            try:
                answer, docs, web_results = retrieve_and_answer(prompt, web_enabled)
                st.markdown(answer)

                # 显示来源
                has_kb = len(docs) > 0 and any(doc.page_content.strip() for doc in docs)
                has_web = len(web_results) > 0

                if has_kb or has_web:
                    with st.expander("📎 查看参考来源", expanded=False):
                        # 知识库来源
                        if has_kb:
                            st.markdown("**📚 知识库来源**")
                            seen = set()
                            for i, doc in enumerate(docs, 1):
                                source = doc.metadata.get("source", "未知")
                                page = doc.metadata.get("page", "")
                                page_info = f" (p.{page})" if page != "" else ""
                                preview = doc.page_content.replace("\n", " ")[:150]
                                key = f"{source}{page}"
                                if key not in seen:
                                    seen.add(key)
                                    st.markdown(f"**[{i}] {source}{page_info}**")
                                    st.markdown(f"> {preview}...")

                        # 联网搜索来源
                        if has_web:
                            st.markdown("**🌐 联网搜索来源**")
                            for i, r in enumerate(web_results, 1):
                                title = r.get("title", "无标题")
                                href = r.get("href", "")
                                snippet = r.get("body", "")[:150]
                                st.markdown(f"**[{i}] {title}**")
                                st.markdown(f"> {snippet}...")
                                if href:
                                    st.markdown(f"  🔗 [{href}]({href})")

                # 保存到聊天记录
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": docs,
                    "web_sources": web_results,
                })

            except Exception as e:
                st.error(f"❌ 回答生成失败: {e}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"抱歉，回答生成失败了：{e}",
                })

# ── 底部信息 ──────────────────────────────────────────
st.markdown("---")
st.caption("Powered by LangChain + ChromaDB + DeepSeek | 大学生选课指南 RAG 问答系统")
