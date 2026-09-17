# 1. 基础镜像：Python 3.13 精简版
FROM python:3.13-slim

# 2. 工作目录（容器里所有操作都在这）
WORKDIR /app

# 3. 先复制依赖清单，装依赖（利用缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 再复制代码（不含 .env，密钥通过 docker run -e 注入）
COPY Cagent.py mcp_server.py standards.md test.cpp student.h ./
COPY skills/ ./skills/

# 5. 暴露端口
EXPOSE 8000

# 6. 启动命令
CMD ["uvicorn", "Cagent:app", "--host", "0.0.0.0", "--port", "8000"]
