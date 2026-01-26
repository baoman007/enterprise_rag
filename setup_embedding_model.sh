#!/bin/bash
# Embedding 模型快速部署脚本

set -e  # 遇到错误立即退出

MODEL_NAME="BAAI/bge-small-zh-v1.5"
MODELS_DIR="./models"
LOCAL_MODEL_DIR="${MODELS_DIR}/${MODEL_NAME}"

echo "=========================================="
echo "  Embedding 模型私有化部署脚本"
echo "=========================================="
echo ""
echo "模型名称: ${MODEL_NAME}"
echo "本地路径: ${LOCAL_MODEL_DIR}"
echo ""

# 检查是否已下载
if [ -d "${LOCAL_MODEL_DIR}" ]; then
    echo "✅ 模型已存在: ${LOCAL_MODEL_DIR}"
    echo ""
    echo "更新模型? (输入 y 更新，其他跳过)"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "跳过下载，使用现有模型"
    else
        echo "删除旧模型..."
        rm -rf "${LOCAL_MODEL_DIR}"
    fi
fi

# 创建目录
mkdir -p "${MODELS_DIR}"

# 检查 huggingface-cli 是否安装
if ! command -v huggingface-cli &> /dev/null; then
    echo ""
    echo "⚠️  未找到 huggingface-cli"
    echo ""
    echo "安装方法:"
    echo "  pip install huggingface_hub"
    echo ""
    echo "或者使用以下命令安装:"
    echo "  pip3 install huggingface_hub"
    echo ""
    exit 1
fi

# 下载模型
echo ""
echo "=========================================="
echo "开始下载模型..."
echo "=========================================="

# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com

huggingface-cli download \
  "${MODEL_NAME}" \
  --local-dir "${LOCAL_MODEL_DIR}" \
  --local-dir-use-symlinks False

echo ""
echo "=========================================="
echo "✅ 模型下载完成！"
echo "=========================================="

# 检查文件
echo ""
echo "下载的文件:"
ls -lh "${LOCAL_MODEL_DIR}"

# 更新配置文件
echo ""
echo "=========================================="
echo "更新配置文件..."
echo "=========================================="

if [ -f ".env" ]; then
    # 备份原配置
    cp .env .env.backup
    echo "✅ 已备份 .env 到 .env.backup"

    # 更新 EMBEDDING_MODEL 路径
    sed -i.tmp "s|^EMBEDDING_MODEL=.*|EMBEDDING_MODEL=/app/models/${MODEL_NAME}|" .env
    rm -f .env.tmp

    echo "✅ 已更新 .env 中的 EMBEDDING_MODEL"
else
    echo "⚠️  未找到 .env 文件"
fi

# 检查 docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    if ! grep -q "./models:/app/models" docker-compose.yml; then
        echo ""
        echo "=========================================="
        echo "⚠️  需要手动更新 docker-compose.yml"
        echo "=========================================="
        echo ""
        echo "请在 api 服务的 volumes 部分添加:"
        echo "  - ./models:/app/models"
        echo ""
        echo "修改后的示例:"
        echo ""
        cat << 'EOF'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/medical_rag
      - REDIS_URL=redis://redis:6379/0
      - HF_ENDPOINT=https://hf-mirror.com
    volumes:
      - ./static:/app/static
      - ./data:/app/data
      - ./models:/app/models  # <-- 添加这一行
      - model_cache:/root/.cache/huggingface
EOF
        echo ""
    else
        echo "✅ docker-compose.yml 已正确配置"
    fi
fi

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 如果 docker-compose.yml 需要更新，请手动编辑"
echo "2. 重启服务:"
echo "   docker-compose down && docker-compose up -d"
echo "3. 查看日志验证:"
echo "   docker logs enterprise_rag-api-1 | grep embedding"
echo ""
