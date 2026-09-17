import json
import os
from langchain_openai import ChatOpenAI
from fastapi.responses import StreamingResponse
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1", api_key=os.getenv("DEEPSEEK_API_KEY"))

# ===== 三个工具 =====
@tool
def read_file(path: str) -> str:
    """读取指定路径的文件内容"""
    with open(path, "r") as f:
        return f.read()

@tool
def list_files(path: str = ".") -> str:
    """列出目录下的所有文件"""
    return "\n".join(os.listdir(path))

@tool
def run_compiler(command: str) -> str:
    """运行编译命令（如 g++ test.cpp -o test），返回编译输出"""
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
    return f"退出码: {result.returncode}\n标准输出:\n{result.stdout}\n错误输出:\n{result.stderr}"

# 注册表 + 绑定
tools = {"read_file": read_file, "list_files": list_files, "run_compiler": run_compiler}
llm_with_tools = llm.bind_tools([read_file, list_files, run_compiler])

messages = [
    SystemMessage(content="你是资深 C++ 工程师，审查代码找出问题，可以用编译器验证"),
    HumanMessage(content="请审查当前目录下的 C++ 项目，并用编译器验证你的判断"),
]

rounds = 0
while True:
    rounds += 1
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    if not response.tool_calls:
        break
    for tool_call in response.tool_calls:
        tool = tools[tool_call["name"]]
        result = tool.invoke(tool_call["args"])
        messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

print(f"循环转了 {rounds} 轮")
print(response.content)