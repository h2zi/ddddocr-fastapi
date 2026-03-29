# 使用官方 Python 运行时作为父镜像
FROM python:3.14-slim

# 设置工作目录
WORKDIR /app

# 先复制依赖文件并安装，利用 Docker 层缓存
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 将当前目录内容复制到容器的 /app 中
COPY . /app

# 暴露端口 8000
EXPOSE 8000

# 运行应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
