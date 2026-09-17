from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from dotenv import load_dotenv
import os
load_dotenv()

llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

# 1. 定义工具
@tool
def read_file(path: str) -> str:
    """读取指定路径的文件内容"""
    with open(path, "r") as f:
        return f.read()

# 2. 绑定工具
llm_with_tools = llm.bind_tools([read_file])

# 3. LLM 表达意图
messages = [
    SystemMessage(content="你是资深 C++ 工程师，负责审查代码，找出内存泄漏、空指针等问题"),
    HumanMessage(content="请审查 test.cpp 这个文件"),
]

rounds = 0

while True:
    rounds += 1
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    if not response.tool_calls:
        break
# 5. 真正执行工具，把结果喂回
    for tool_call in response.tool_calls:
        if tool_call["name"] == "read_file":
            result = read_file.invoke(tool_call["args"])
            messages.append(ToolMessage(
            content=result,
            tool_call_id=tool_call["id"],)  
            )

print(f"循环了{rounds}次")
print(response.content)