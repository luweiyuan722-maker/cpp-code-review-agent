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

# 3. 第一次调用：LLM 表达意图
messages = [
    SystemMessage(content="你是资深 C++ 工程师，负责审查代码，找出内存泄漏、空指针等问题"),
    HumanMessage(content="请审查 test.cpp 这个文件"),
]
response = llm_with_tools.invoke(messages)

# ===== 下面是新增的后半段 =====

# 4. 把 LLM 的"意图"加进对话历史（LLM 第二次要知道自己说过什么）
messages.append(response)

# 5. 真正执行工具，把结果喂回
for tool_call in response.tool_calls:
    if tool_call["name"] == "read_file":
        result = read_file.invoke(tool_call["args"])   # ← 真正读文件！
        messages.append(ToolMessage(
            content=result,                              # 读到的内容
            tool_call_id=tool_call["id"],               # 用 id 对账
        ))

# 6. 第二次调用：LLM 现在有工具结果了，输出审查
final = llm_with_tools.invoke(messages)
print(final.content)