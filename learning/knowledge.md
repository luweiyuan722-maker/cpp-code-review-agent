# AI Agent 开发知识库

## RAG（检索增强生成）
RAG（Retrieval-Augmented Generation）是一种将信息检索与大型语言模型结合的技术架构。它的核心思想是：在 LLM 生成回答之前，先从外部知识库中检索相关文档，然后将检索到的内容作为上下文注入到 prompt 中，让 LLM 基于这些内容生成回答。

RAG 的完整管线包括：
1. 文档加载：支持 PDF、HTML、Markdown、TXT 等多种格式
2. 文档切分（Chunk）：使用 RecursiveCharacterTextSplitter，推荐的 chunk_size 为 500-1000 tokens，chunk_overlap 为 10-20%
3. Embedding 向量化：将文本转为向量，常用模型包括 OpenAI text-embedding-3-small（1536维）和 BAAI bge-large-zh-v1.5（1024维）
4. 向量数据库存储：Chroma（学习/原型）、Milvus（生产）、FAISS（中小规模）
5. 检索策略：相似度检索、MMR（最大边际相关性）、混合检索（向量+BM25）
6. 重排序（Reranker）：粗召回后用更强的模型精排

高级 RAG 模式包括 HyDE（先让 LLM 生成假答案再检索）、Small-to-Big（检索小chunk返回大chunk）、Multi-Query（多角度并行检索）、Corrective RAG（检索后评估质量）和 Graph RAG（实体关系图+向量检索）。

## MCP 协议
MCP（Model Context Protocol）是 Anthropic 推出的 Agent 工具集成标准协议，被比喻为 Agent 世界的"USB-C 接口"。

MCP 架构包括 Client（Agent/应用）和 Server（工具提供方）两个角色，通过 JSON-RPC 2.0 通信。

MCP Server 可以暴露三种原语：
- Tools：可执行的操作（如搜索文件、发送邮件）
- Resources：可读取的数据（如文件内容）
- Prompts：预定义的提示词模板

三种传输方式：
- stdio：标准输入/输出，适合本地进程
- SSE：Server-Sent Events，适合远程服务
- Streamable HTTP：HTTP 请求/响应，适合无状态调用

MCP 的核心优势是"一次编写工具，所有 Agent 都能用"，解决了不同模型/框架间 Tool Calling 格式不统一的问题。

## 多 Agent 协作
单 Agent 存在三个致命缺陷：上下文窗口爆炸、能力冲突（系统提示词互相矛盾）、复杂度失控（ReAct 链条越来越长导致迷路）。

多 Agent 协作的核心思想是"分而治之"，三大框架对比：
- LangGraph：图编排模式，自己画状态图，需要精细控制流程时使用
- CrewAI：角色扮演模式，定义角色+任务自动分配，适合内容生产流水线
- AutoGen：对话驱动模式，Agent 之间对话解决问题，适合复杂推理协作

两种多 Agent 模式：
1. Supervisor 模式：一个 Supervisor Agent 决定调用哪个子 Agent
2. Swarm 模式：Agent 之间通过 handoff 工具直接交接

多 Agent 的五大难点：共享记忆、任务分解、错误传播、循环死锁、成本控制。

## Agent 评测体系
Agent 评测分为三层：
1. 运行时监控：延迟（P50/P95/P99）、Token 消耗、错误率、吞吐量
2. 组件评测：检索命中率（目标>85%）、MRR（目标>0.8）、工具调用正确率（目标>90%）、幻觉率（目标<5%）
3. 端到端评测：任务成功率、用户满意度

三种评测方法：人工评测（最准确但慢）、LLM-as-Judge（用更强的 LLM 打分，日常迭代用）、规则评测（正则/关键词匹配，极快）。

可观测性工具：LangSmith（LangChain 用户首选，SaaS）、LangFuse（开源，可自部署）、Phoenix（深入分析 Embedding）。

## Agent 生产部署
从 Demo 到产品的核心差距：
- FastAPI 服务化：将 Agent 封装为 REST API
- SSE 流式输出：Server-Sent Events 逐 token 推送，比 WebSocket 更适合 Agent 场景
- 会话管理：每个用户分配 session_id，对话历史按 session_id 隔离存储（Redis）
- Docker 部署：docker-compose 一键启动全套服务

生产环境 checklist：HTTPS（Nginx+Let's Encrypt）、限流、鉴权（API Key/JWT）、结构化日志、健康检查端点、优雅关闭、环境变量管理。

面试高频题："1000 个用户同时用，架构怎么设计？"——Nginx 反向代理 → 多 FastAPI worker → Redis 会话共享 → LLM API 限流排队 → 异步处理。

## ReAct 模式
ReAct（Reasoning + Acting）是 Agent 执行任务的核心模式，由 Yao et al. 在 2022 年提出。

ReAct 循环：Thought（思考下一步做什么）→ Action（执行工具调用）→ Observation（观察工具返回结果）→ 回到 Thought。

与 CoT（Chain of Thought）的区别：CoT 只有推理没有行动，ReAct 推理和行动交替进行。

与 Plan-Execute 的区别：Plan-Execute 是先做完整计划再执行，ReAct 是边想边做。

## Agent 记忆系统
短期记忆的 8 大策略：
1. 滑动窗口：最近 N 轮对话
2. 摘要记忆：用 LLM 总结历史对话
3. 分层记忆：短期+中期+长期
4. 向量检索记忆：相似度检索历史信息
5. 实体记忆：按实体（人、项目等）组织
6. 对话缓冲：简单存所有对话
7. 摘要缓冲：缓冲+定期摘要
8. 混合策略：组合多种方式

长期记忆的 5 类：用户画像、知识库、经验库、关系图谱、任务记录。

存储选型：结构化数据用 SQL、向量用向量数据库（Chroma/Milvus）、缓存用 Redis、文档用对象存储。
