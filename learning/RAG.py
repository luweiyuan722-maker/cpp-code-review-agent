from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os, math, re

load_dotenv()
app = FastAPI()

# === 读文档 + 切分（Layer02）===
with open("knowledge.md", "r") as f:
    doc = f.read()
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""],
)
chunks = splitter.split_text(doc)

# === Embedding + LLM ===
embeddings = OpenAIEmbeddings(model="embedding-2", base_url="https://open.bigmodel.cn/api/paas/v4/", api_key=os.getenv("ZHIPUAI_API_KEY"))
llm = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1", api_key=os.getenv("DEEPSEEK_API_KEY"))

# === 启动时 embed 一次（Layer05 持久化）===
chunk_vectors = embeddings.embed_documents(chunks)

# === 余弦相似度 + 关键词 + 混合检索（Layer03 + 混合）===
def cosine_similarity(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    return dot / (na * nb)

def keyword_score(question, chunk):
    return sum(chunk.lower().count(w.lower()) for w in re.findall(r'[A-Za-z]+', question))

def hybrid_search(question, k=3):
    qvec = embeddings.embed_query(question)
    results = []
    for i, cvec in enumerate(chunk_vectors):
        results.append((cosine_similarity(qvec, cvec), keyword_score(question, chunks[i]), i))
    mv = max(r[0] for r in results); mk = max(r[1] for r in results) or 1
    final = sorted(((0.5*(v/mv)+0.5*(kw/mk), i) for v,kw,i in results), reverse=True)
    return [chunks[i] for _, i in final[:k]]

# === 首页：返回前端页面 ===
@app.get("/")
async def index():
    return FileResponse("index.html")

history = []   # 全局对话历史，存 dict 格式

@app.get("/ask")
async def ask(question: str):
    # 1. 检索文档（不变）
    related = hybrid_search(question, k=3)
    context = "\n\n".join(related)

    # 2. 把历史拼成字符串
    history_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in history
    )

    # 3. 拼 prompt：历史 + 文档 + 问题，三块分开
    prompt = f"""根据以下信息回答问题。

## 对话历史
{history_text}

## 相关文档
{context}

## 当前问题
{question}
"""

    # 4. 流式生成，累积完整回答
    async def generate():
        full = ""   # 累积完整回答（generate 的局部变量）
        async for chunk in llm.astream(prompt):
            if chunk.content:
                full += chunk.content                      # 累积
                yield f"data: {chunk.content}\n\n"          # 推送
        # 循环结束 = 生成完，这时才把完整问答写进历史
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": full})
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")