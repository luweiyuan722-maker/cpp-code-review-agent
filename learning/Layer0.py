from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
load_dotenv()

llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

# 读 C++ 代码
with open("test.cpp", "r") as f:
    code = f.read()

# 直接让 LLM 审查
prompt = f"""你是资深 C++ 工程师，请审查以下代码，找出潜在问题：
1. 内存泄漏
2. 空指针 / 野指针
3. 未初始化变量
4. 越界访问
5. 资源管理（RAII / 智能指针）

代码：
{code}
"""
answer = llm.invoke(prompt)
print(answer.content)
