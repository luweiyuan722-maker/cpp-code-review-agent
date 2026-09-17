import os
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1", api_key=os.getenv("DEEPSEEK_API_KEY"))

# ===== 两个工具 =====
@tool
def read_file(path: str) -> str:
    """读取指定路径的文件内容"""
    with open(path, "r") as f:
        return f.read()

@tool
def list_files(path: str = ".") -> str:
    """列出目录下的所有文件"""
    return "\n".join(os.listdir(path))

# 注册表
tools = {"read_file": read_file, "list_files": list_files}

# 绑定（把两个工具都告诉 LLM）
llm_with_tools = llm.bind_tools([read_file, list_files])

messages = [
    SystemMessage(content="你是资深 C++ 工程师，审查代码找出内存泄漏、空指针等问题"),
    HumanMessage(content="请审查当前目录下的 C++ 项目"),
]

rounds = 0
while True:
    rounds += 1
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    if not response.tool_calls:
        break
    for tool_call in response.tool_calls:
        tool = tools[tool_call["name"]]           # 分发
        result = tool.invoke(tool_call["args"])   # 执行
        messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

print(f"循环转了 {rounds} 轮")
print(response.content)