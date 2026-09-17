import os
import math
from langchain_openai import OpenAIEmbeddings
from  dotenv import load_dotenv
load_dotenv()

embeddings = OpenAIEmbeddings(
    model="embedding-3",          # ← 改回这个
    base_url="https://open.bigmodel.cn/api/paas/v4/",   # ← 也删掉 @url: 和反引号
    api_key=os.getenv("ZHIPUAI_API_KEY"),
)

question_vec = embeddings.embed_query("RAG是什么？")
print(f"问题向量维度：{len(question_vec)}")
print(f"问题向量前5个元素：{question_vec[:5]}")

def cosine_similarity(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x*x for x in a))
    norm_b = math.sqrt(sum(x*x for x in b))

    return dot / (norm_a * norm_b)

# ===== 1. 读文档 + 切分（复用 Layer02 的代码）=====
from langchain_text_splitters import RecursiveCharacterTextSplitter

with open("knowledge.md", "r") as f:
    doc = f.read()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""],
)
chunks = splitter.split_text(doc)

# ===== 2. 把 7 块文本一次性转成向量 =====
chunk_vectors = embeddings.embed_documents(chunks)
print(f"共 {len(chunk_vectors)} 个块向量")

# ===== 3. 算问题向量和每块的相似度 =====
scores = []
for i, chunk_vec in enumerate(chunk_vectors):
    score = cosine_similarity(question_vec, chunk_vec)
    scores.append((score, i))

# ===== 4. 排序，取最相似的 3 块 =====
scores.sort(reverse=True)   # 从高到低排
top3 = scores[:3]

print("\n最相关的 3 块：")
for score, i in top3:
    print(f"  第 {i+1} 块  相似度={score:.4f}  {chunks[i][:30]}...")