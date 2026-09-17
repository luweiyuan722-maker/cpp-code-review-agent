import os
import math
import re # 正则表达式
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
    model="embedding-3",
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

print("正在把 7 块文本转成向量（可能需要几秒钟）...")
chunk_vectors = embeddings.embed_documents(chunks)   # 7块转向量
print("向量转换完成")

# ===== 5. 检索函数：问题 → Top-K 相关块 =====
def retrieve(question, k=3):
    question_vec = embeddings.embed_query(question)      # 问题转向量
    scores = []
    for i, chunk_vec in enumerate(chunk_vectors):
        score = cosine_similarity(question_vec, chunk_vec)
        scores.append((score, i))

    scores.sort(reverse=True)
    return [chunks[i] for _, i in scores[:k]]   # 返回最相关的 k 块文本

# ===== 6. 问答函数：检索 + 生成 =====
def ask(question):
    related = retrieve(question, k=3)
    context = "\n\n".join(related)
    prompt = f"请仅根据以下文档内容回答问题：\n{context}\n\n问题：{question}"
    print("回答：", end="", flush=True)
    for chunk in llm.stream(prompt):
        print(chunk.content, end="", flush=True)
    print()

# ===== 8. 关键词匹配函数：问题 → 块的关键词匹配度 =====
def keyword_score(question, chunk):
    """统计问题里的英文单词在 chunk 里出现了几次"""
    # 1. 提取问题里的英文单词（MCP、RAG、ReAct...）
    words = re.findall(r'[A-Za-z]+', question)

    # 2. 统计每个单词在 chunk 里出现的次数
    score = 0
    for word in words:
        score += chunk.lower().count(word.lower())

    return score

# ===== 9. 混合检索函数：问题 → Top-K 相关块（向量 + 关键词） =====
def hybrid_search(question, k=3):
    question_vec = embeddings.embed_query(question)

    # 1. 算向量分数和关键词分数
    results = []
    for i, chunk_vec in enumerate(chunk_vectors):
        vec_score = cosine_similarity(question_vec, chunk_vec)
        kw_score = keyword_score(question, chunks[i])
        results.append((vec_score, kw_score, i))

    # 2. 归一化（都缩放到 0~1）
    max_vec = max(r[0] for r in results)
    max_kw = max(r[1] for r in results) or 1   # 防止除以 0

    # 3. 加权融合（各占一半，你可以调权重）
    final = []
    for vec_score, kw_score, i in results:
        combined = 0.5 * (vec_score / max_vec) + 0.5 * (kw_score / max_kw)
        final.append((combined, i))

    final.sort(reverse=True)
    return [chunks[i] for _, i in final[:k]]
# ===== 测试：混合检索 =====
ask("MCP 是什么？")