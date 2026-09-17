import json
import asyncio
import os, subprocess
import re
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1", api_key=os.getenv("DEEPSEEK_API_KEY"))

# ===== 知识库（本地）=====
with open("standards.md", "r") as f:
    standards_text = f.read()
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_text(standards_text)
embeddings = OpenAIEmbeddings(model="embedding-2", base_url="https://open.bigmodel.cn/api/paas/v4/", api_key=os.getenv("ZHIPUAI_API_KEY"))
CHUNK_VECTORS = embeddings.embed_documents(chunks)

# ===== 本地工具（Agent 特有）=====
@tool
def search_knowledge_base(query: str) -> str:
    """检索本地知识库（C++ 编码规范），返回相关规范"""
    qv = embeddings.embed_query(query)
    scores = []
    for v in CHUNK_VECTORS:
        dot = sum(a*b for a, b in zip(qv, v))
        norm_q = sum(a*a for a in qv) ** 0.5
        norm_v = sum(b*b for b in v) ** 0.5
        scores.append(dot / (norm_q * norm_v))
    top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
    return "\n\n".join(chunks[i] for i in top_idx)

@tool
def web_search(query: str, max_results: int = 5) -> str:
    """联网搜索，返回搜索结果摘要"""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "没有搜到结果"
        return "\n\n".join(f"标题: {r['title']}\n内容: {r['body']}" for r in results)
    except Exception as e:
        return f"搜索失败：{e}"

# ===== SKILLS（从 SKILL.md 文件加载，可扩展）=====
def load_skills():
    """从 skills/*/SKILL.md 加载所有技能，返回 {name: 检查清单正文}"""
    skills = {}
    skills_dir = Path("skills")
    if not skills_dir.exists():
        return skills
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        content = skill_md.read_text(encoding="utf-8")
        # 解析 frontmatter（--- ... ---）和正文
        m = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
        if not m:
            continue
        frontmatter, body = m.group(1), m.group(2).strip()
        name_m = re.search(r'name:\s*(\S+)', frontmatter)
        if name_m:
            skills[name_m.group(1)] = body
    return skills

SKILLS = load_skills()

# ===== MCP 客户端（连接 mcp_server.py）=====
mcp_client = MultiServerMCPClient({
    "code-review": {
        "command": ".venv/bin/python",
        "args": ["mcp_server.py"],
        "transport": "stdio",
    }
})

# ===== 全局工具表（启动时才填充）=====
ALL_TOOLS = {}
llm_with_tools = None
llm_for_experts = None

@asynccontextmanager# 异步上下文管理器，用于启动时异步拉取 MCP 工具
async def lifespan(app):
    global llm_with_tools, llm_for_experts
    # 启动时：异步拉取 MCP 工具
    mcp_tools = await mcp_client.get_tools()
    for t in mcp_tools:
        ALL_TOOLS[t.name] = t
    # 合并本地工具
    ALL_TOOLS["search_knowledge_base"] = search_knowledge_base
    ALL_TOOLS["web_search"] = web_search
    ALL_TOOLS["multi_expert_review"] = multi_expert_review   # 多专家协作工具
    # 主 Agent 工具：所有工具（含 multi_expert_review）
    llm_with_tools = llm.bind_tools(list(ALL_TOOLS.values()))
    # 子 Agent 工具：不含 multi_expert_review（防递归——专家不能启动多专家）
    expert_tools = {k: v for k, v in ALL_TOOLS.items() if k != "multi_expert_review"}
    llm_for_experts = llm.bind_tools(list(expert_tools.values()))
    yield

app = FastAPI(lifespan=lifespan)

class ReviewRequest(BaseModel):
    question: str
    skill: str = ""

def to_text(result) -> str:
    """把工具返回结果转成字符串（MCP 工具返回 list of TextContent，本地工具返回 str）"""
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        parts = []
        for item in result:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif hasattr(item, "text"):
                parts.append(str(item.text))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(result)

# 1. 定义三个专家（不同 system prompt = 不同专长）
EXPERTS = {
    "memory": "你是内存安全专家，专门审查：内存泄漏、空指针、悬垂指针、数组越界、Rule of Three/Five",
    "performance": "你是性能专家，专门审查：多余拷贝、循环优化、移动语义、缓存友好",
    "concurrency": "你是并发专家，专门审查：线程安全、死锁、竞态条件、锁的使用",
}

# 2. 一个专家 = 一个带专门 prompt 的 Agent 循环
async def run_expert(name, system_prompt, question):
    # 如果有对应的 skill 检查清单，注入（skill 从 SKILL.md 文件加载）
    if name in SKILLS:
        system_prompt += f"\n\n按以下检查清单系统审查：\n{SKILLS[name]}"
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=question)]
    while True:
        response = await llm_for_experts.ainvoke(messages)   # 专家用子 Agent 工具（不含 multi_expert_review）
        messages.append(response)
        if not response.tool_calls:
            return f"【{name}专家报告】\n{response.content}"
        for tool_call in response.tool_calls:
            tool = ALL_TOOLS[tool_call["name"]]
            result = await tool.ainvoke(tool_call["args"])
            messages.append(ToolMessage(content=to_text(result), tool_call_id=tool_call["id"]))

# 3. 主管汇总（不用工具，直接调 llm）
async def summarize(reports):
    prompt = "你是主管，把以下几位专家的报告整合成一份统一的审查报告（去重、按严重程度排序）：\n\n" + "\n\n".join(reports)
    response = await llm.ainvoke(prompt)
    return response.content

# 4. 把多专家协作封装成工具（主 Agent 按需调用）
@tool
async def multi_expert_review(question: str) -> str:
    """启动多专家协作深度审查：内存/性能/并发三位专家并发分析 + 主管汇总。
    用于需要深度分析的复杂问题，简单问题不要调用。"""
    reports = await asyncio.gather(
        run_expert("memory", EXPERTS["memory"], question),
        run_expert("performance", EXPERTS["performance"], question),
        run_expert("concurrency", EXPERTS["concurrency"], question),
    )
    final = await summarize(reports)
    return final

@app.post("/review")
async def review(req: ReviewRequest):
    async def generate():
        system_prompt = "你是资深 C++ 工程师，审查代码找问题。可以用 search_knowledge_base 查规范，web_search 联网。对于需要深度分析的复杂问题，调用 multi_expert_review 启动多专家协作审查。"
        if req.skill and req.skill in SKILLS:
            system_prompt += f"\n\n你当前使用【{req.skill}】skill，按以下清单审查：\n{SKILLS[req.skill]}"
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=req.question)]
        while True:
            response = await llm_with_tools.ainvoke(messages)
            messages.append(response)
            if not response.tool_calls:
                event = {"type": "answer", "content": response.content}
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                break
            for tool_call in response.tool_calls:
                event = {"type": "tool", "name": tool_call["name"], "args": tool_call["args"]}
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                tool = ALL_TOOLS[tool_call["name"]]
                result = await tool.ainvoke(tool_call["args"])
                result_text = to_text(result)
                messages.append(ToolMessage(content=result_text, tool_call_id=tool_call["id"]))
                event = {"type": "observation", "result": result_text[:200]}
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/")
async def index():
    return FileResponse("index.html")