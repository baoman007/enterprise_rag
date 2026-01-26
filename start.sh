#!/bin/bash
# 启动 RAG 系统脚本

cd "$(dirname "$0")"

# 检查容器是否运行
if docker ps | grep -q "enterprise_rag-api-1"; then
    echo "容器已在运行"
    docker stop enterprise_rag-api-1
    docker rm enterprise_rag-api-1
fi

# 启动容器
echo "启动 RAG API 容器..."
docker run -d \
    --name enterprise_rag-api-1 \
    --network enterprise_rag_default \
    -p 8000:8000 \
    -v "$(pwd)/static:/app/static" \
    -v "$(pwd)/data:/app/data" \
    -e TRANSFORMERS_OFFLINE=1 \
    enterprise_rag-api

echo "等待服务启动..."
sleep 10

# 检查健康状态
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 服务启动成功！"
    echo "🌐 访问地址: http://localhost:8000"
    echo "📊 向量数据库浏览: http://localhost:8000/static/index.html"
    echo "💬 RAG 聊天页面: http://localhost:8000/static/chat.html"
else
    echo "❌ 服务启动失败，查看日志:"
    docker logs enterprise_rag-api-1 --tail 30
fi
