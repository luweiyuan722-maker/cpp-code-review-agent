import asyncio
import os, subprocess
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# 用 mcp 库底层 API 创建 Server（不用 fastmcp，避免版本冲突）
server = Server("code-review-tools")

# ===== 列出工具（inputSchema 是 JSON Schema，描述参数）=====
@server.list_tools()
async def handle_list_tools():
    return [
        types.Tool(
            name="read_file",
            description="读取指定路径的文件内容",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        ),
        types.Tool(
            name="list_files",
            description="列出目录下的所有文件",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
            },
        ),
        types.Tool(
            name="run_compiler",
            description="运行编译命令（如 g++ test.cpp -o test），返回编译输出",
            inputSchema={
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        ),
    ]

# ===== 执行工具 =====
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "read_file":
        path = arguments.get("path", "")
        try:
            with open(path, "r") as f:
                return [types.TextContent(type="text", text=f.read())]
        except UnicodeDecodeError:
            return [types.TextContent(type="text", text=f"无法读取 {path}：这是二进制文件，不是文本")]
        except FileNotFoundError:
            return [types.TextContent(type="text", text=f"文件不存在：{path}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"读取失败：{e}")]

    elif name == "list_files":
        path = arguments.get("path", ".")
        try:
            return [types.TextContent(type="text", text="\n".join(os.listdir(path)))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"列出 {path} 失败：{e}")]

    elif name == "run_compiler":
        command = arguments.get("command", "")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            return [types.TextContent(type="text", text="编译超时")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"编译失败：{e}")]
        return [types.TextContent(type="text", text=f"退出码: {result.returncode}\n标准输出:\n{result.stdout}\n错误输出:\n{result.stderr}")]

    else:
        return [types.TextContent(type="text", text=f"未知工具：{name}")]

# ===== 启动（stdio 模式）=====
async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
