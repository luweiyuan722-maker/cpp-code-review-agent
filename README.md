# C++ 代码审查 Agent（多智能体系统）

基于 LangChain + FastAPI 从零构建的智能代码审查系统，采用 **Supervisor 多智能体架构**，支持工具调用、知识检索、联网搜索与 MCP 标准化工具，形成"知识检索 → 工具调用 → 编译验证 → 多专家审查 → 结果聚合"的闭环。

## ✨ 核心特性

- **ReAct Agent 运行时**：从零实现的「思考 → 行动 → 观察」循环，集成文件读取、目录探索、编译验证、联网搜索、知识库检索 5 类工具；工具注册表模式实现插件化接入（加工具不改循环，符合开闭原则）
- **RAG 知识库**：文档切分 → Embedding 向量化 → 余弦相似度检索，构建 C++ 编码规范知识库，审查报告可引用具体规范条目
- **MCP 协议**：将文件操作、编译验证等通用能力封装为独立 Server，实现工具与 Agent 解耦（解决 fastmcp 与 mcp 库的版本兼容冲突）
- **Skill 机制**：内存安全 / 并发安全 / 性能审查清单封装为 SKILL.md 文件，按需动态加载，降低 Prompt 耦合
- **Supervisor 多智能体**：内存 / 性能 / 并发三位专家通过 `asyncio.gather` 并发审查，Supervisor 负责去重、严重程度排序与最终报告
- **递归防护**：主 Agent 与子 Agent 工具分离（专家不持有"启动多专家"工具），从根源切断递归
- **SSE 流式输出**：前端实时可视化 Agent 的完整推理轨迹
- **编译验证闭环**：g++ 静态分析 + 动态验证

## 🛠 技术栈

Python · FastAPI · LangChain · MCP · asyncio · DeepSeek · 智谱 Embedding · SSE · Docker

## 🚀 快速开始

### 1. 环境准备

```bash
git clone https://github.com/luweiyuan722-maker/cpp-code-review-agent.git
cd cpp-code-review-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置密钥

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek 和智谱 API Key
```

### 3. 启动

```bash
unset PYTHONPATH   # 重要：避免环境污染导致 MCP 子进程崩溃
uvicorn Cagent:app --reload
```

浏览器打开 `http://127.0.0.1:8000`，或：

```bash
curl -N -X POST http://127.0.0.1:8000/review \
  -H "Content-Type: application/json" \
  -d '{"question":"审查 test.cpp 找问题"}'
```

## 🏗 架构

```
用户提问 → FastAPI /review 端点
   ↓
ReAct 主循环（主 Agent）
   ├─ read_file / list_files / run_compiler（MCP 工具）
   ├─ search_knowledge_base（RAG 检索规范）
   ├─ web_search（联网查证）
   └─ multi_expert_review（多专家深度审查）
          ↓
    内存专家 + 性能专家 + 并发专家（asyncio.gather 并发）
          ↓
    Supervisor 汇总去重、严重程度排序
          ↓
    SSE 流式输出最终报告
```

## 📁 目录结构

```
├── Cagent.py            # 主程序（ReAct + RAG + MCP + 多 Agent）
├── mcp_server.py        # MCP Server（文件操作、编译验证）
├── skills/              # SKILL.md 检查清单（memory/concurrency/performance）
├── standards.md         # C++ 编码规范知识库
├── test.cpp / student.h # 审查测试用例
├── index.html           # 前端（SSE 渲染）
├── learning/            # 分层学习脚本（Layer 0-6）
└── requirements.txt     # 依赖清单
```

## 📄 License

MIT
