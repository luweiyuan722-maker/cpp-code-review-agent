from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # 读取 .env 文件里的 API Key

app = FastAPI()

# ── 读文档 ──
with open("knowledge.md", "r") as f:
    doc = f.read()

# ── 搭 LLM ──
llm = ChatOpenAI(
    model=os.getenv("CHAT_MODEL", "deepseek-chat"),
    base_url=os.getenv("CHAT_BASE_URL", "https://api.deepseek.com/v1"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

# ── 步骤2+3：网址 → 函数 ──
@app.get("/ask")
def ask(question: str):
    prompt = f"请仅根据以下文档内容回答问题：\n{doc}\n\n问题：{question}"
    answer = llm.invoke(prompt)
    return {"answer": answer.content}