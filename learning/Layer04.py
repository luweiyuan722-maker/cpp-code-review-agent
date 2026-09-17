import os
import math
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ===== 1. 读文档 + 切分（来自 Layer 2）=====
with open("knowledge.md", "r") as f:
    doc = f.read()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""],
)
chunks = splitter.split_text(doc)

# ===== 2. Embedding（来自 Layer 3，注意用 embedding-2）=====
embeddings = OpenAIEmbeddings(
    model="embedding-2",
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.getenv("ZHIPUAI_API_KEY"),
)

# ===== 3. LLM（来自 Layer 1）=====
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

# ===== 4. 余弦相似度函数（来自 Layer 3）=====
def cosine_similarity(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    norm_a = math.sqrt(sum(x*x for x in a))
    norm_b = math.sqrt(sum(x*x for x in b))
    return dot / (norm_a * norm_b)
    

# ===== 5. 检索函数：问题 → Top-K 相关块 =====
def retrieve(question, k=3):
    question_vec = embeddings.embed_query(question)      # 问题转向量
    chunk_vectors = embeddings.embed_documents(chunks)   # 7块转向量

    scores = []
    for i, chunk_vec in enumerate(chunk_vectors):
        score = cosine_similarity(question_vec, chunk_vec)
        scores.append((score, i))

    scores.sort(reverse=True)
    return [chunks[i] for _, i in scores[:k]]   # 返回最相关的 k 块文本

# ===== 6. 问答函数：检索 + 生成 =====
def ask(question):
    related = retrieve(question, k=3)          # ← 检索
    context = "\n\n".join(related)             # ← 拼接成 context
    prompt = f"请仅根据以下文档内容回答问题：\n{context}\n\n问题：{question}"
    answer = llm.invoke(prompt)                # ← 生成
    return answer.content

# ===== 7. 测试 =====
question = "RAG 是什么？"
print(ask(question))