---
title: 📚 大学生选课指南 — RAG 问答系统
emoji: 📚
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.30.0
app_file: app.py
pinned: false
---

# 📚 AI Agent 面试知识库 — RAG 问答系统

基于 **LangChain + ChromaDB + sentence-transformers + DeepSeek** 的本地知识库智能问答系统。支持 PDF/DOCX/TXT 多种文档格式，通过 RAG（检索增强生成）技术实现精准的文档问答。

## ✨ 特性

| 特性 | 说明 |
|------|------|
| 🗂 **多格式支持** | PDF / DOCX / TXT 自动读取入库 |
| 🔍 **语义检索** | 使用 sentence-transformers 本地嵌入模型，无需联网 API |
| 🎯 **MMR 去重** | 最大边际相关性检索，兼顾相关性与多样性 |
| 🤖 **LLM 生成** | 接入 DeepSeek 大模型，基于检索结果生成回答 |
| 📎 **来源追溯** | 每段回答标注信息来源，支持溯源验证 |
| 🖥 **Web 界面** | Streamlit 交互式聊天界面 |
| 🧩 **可扩展** | 预留联网搜索接口，支持知识库+联网双路径 |

## 🏗 系统架构

```
用户提问
    │
    ▼
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│  Streamlit  │───▶│   ChromaDB      │◀───│  docs/       │
│   Web UI    │    │  向量数据库      │    │  PDF/DOCX    │
└─────────────┘    └─────────────────┘    └──────────────┘
    │                      │
    ▼                      ▼
┌─────────────────────────────────────┐
│   LangChain RAG Pipeline            │
│   1. MMR 检索                       │
│   2. 上下文构建                      │
│   3. Prompt 组装                     │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│   DeepSeek LLM                      │
│   基于资料生成回答                    │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│   回答 + 来源引用                     │
└─────────────────────────────────────┘
```

## 📁 项目结构

```
ai-agent-interview/
├── app.py              # Streamlit 主界面
├── build_kb.py         # 知识库构建工具（PDF/DOCX/TXT → Chroma）
├── ask_kb.py           # 命令行问答工具
├── test_api.py         # API 连通性测试
├── test_embedding.py   # Embedding 模型测试
├── docs/               # 知识库源文档
│   └── test.pdf        # 示例文档
├── chroma_db/          # 向量数据库（自动生成）
├── .env                # API Key 配置
├── requirements.txt    # 依赖清单
└── README.md           # 项目说明
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API

在 `.env` 文件中配置 DeepSeek API（已配置可跳过）：

```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

### 3. 构建知识库

将文档放入 `docs/` 目录（支持 .pdf / .docx / .txt），然后运行：

```bash
python build_kb.py
```

### 4. 启动问答

**Web 界面：**

```bash
streamlit run app.py
```

**命令行模式：**

```bash
python ask_kb.py "你的问题"
```

## 🧠 技术要点

### 分块策略

- **chunk_size=400**：每块约 400 字符，适合面试问答场景
- **chunk_overlap=80**：20% 重叠，保持上下文连贯
- **中文标点分隔**：按 `。；，` 等标点切分，避免语义断裂

### 检索优化

- **MMR 检索**：`lambda_mult=0.7`，兼顾相关性与结果多样性
- **Top-K=5**：检索 5 个相关片段，提供充足上下文

### 幻觉缓解

- **低温度 (0.3)**：减少 LLM 自由发挥
- **严格 system prompt**：要求仅根据资料回答
- **来源标注**：每段回答追溯原文
- **诚实机制**：资料不足时明确说明

## 📊 效果展示

```
> 介绍一下这个人的技术栈

根据提供的资料，该候选人的技术栈可以归纳如下：

### AI Agent 方向
- 熟悉主流 AI Agent 框架部署（Claude Code、Codex、OpenClaw）
- 国产大模型 API 接入（DeepSeek、混元）
- Token 中转站搭建（多模型鉴权、流量分发）
- 研究 DeerFlow 2.0 等开源编排框架

### 前端开发
- HTML5 / CSS3 / JavaScript (ES6+)
- Vue.js / React 基础
- 响应式布局

...（来源：test.pdf）
```

## 🗺 后续规划

- [x] 多格式文档支持（PDF/DOCX/TXT）
- [x] Streamlit Web 界面
- [x] MMR 检索优化
- [ ] 🌐 联网搜索扩展（知识库+双路径）
- [ ] 多轮对话记忆
- [ ] 文档在线预览

## 🛠 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.12 | 开发语言 |
| LangChain | RAG 流程编排 |
| ChromaDB | 向量数据库 |
| sentence-transformers | 本地文本嵌入 |
| DeepSeek API | 大语言模型 |
| Streamlit | Web 界面 |
| HuggingFace Hub | 嵌入模型分发 |

## 📝 许可

MIT License
