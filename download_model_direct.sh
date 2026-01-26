#!/bin/bash
# 直接下载模型文件（绕过 huggingface-cli）

set -e

MODEL_DIR="./models/bge-small-zh-v1.5"
MIRROR_URL="https://hf-mirror.com/BAAI/bge-small-zh-v1.5/resolve/main"

echo "=========================================="
echo "  直接下载 embedding 模型文件"
echo "=========================================="
echo ""

# 创建目录
mkdir -p "${MODEL_DIR}"

echo "模型目录: ${MODEL_DIR}"
echo "镜像地址: ${MIRROR_URL}"
echo ""

# 模型文件列表
FILES=(
    "config.json"
    "model.safetensors"
    "tokenizer.json"
    "tokenizer_config.json"
    "vocab.txt"
    "special_tokens_map.json"
)

echo "开始下载模型文件..."
echo ""

for file in "${FILES[@]}"; do
    echo "下载: ${file}"
    url="${MIRROR_URL}/${file}"

    # 使用 curl 下载
    if curl -L --connect-timeout 30 --max-time 600 -f -o "${MODEL_DIR}/${file}" "${url}"; then
        size=$(ls -lh "${MODEL_DIR}/${file}" | awk '{print $5}')
        echo "  ✅ ${file} (${size})"
    else
        echo "  ❌ 下载失败: ${file}"
        echo "  URL: ${url}"
    fi
    echo ""
done

echo "=========================================="
echo "验证下载的文件..."
echo "=========================================="

missing_files=0
for file in "${FILES[@]}"; do
    if [ -f "${MODEL_DIR}/${file}" ]; then
        size=$(ls -lh "${MODEL_DIR}/${file}" | awk '{print $5}')
        echo "  ✅ ${file} (${size})"
    else
        echo "  ❌ 缺少: ${file}"
        missing_files=$((missing_files + 1))
    fi
done

echo ""
if [ $missing_files -eq 0 ]; then
    echo "=========================================="
    echo "✅ 所有文件下载完成！"
    echo "=========================================="
    echo ""
    echo "下一步: 更新配置文件"
    echo ""
    echo "1. 编辑 .env 文件:"
    echo "   EMBEDDING_MODEL=/app/models/bge-small-zh-v1.5"
    echo ""
    echo "2. 更新 docker-compose.yml，添加卷挂载:"
    echo "   - ./models:/app/models"
    echo ""
    echo "3. 重启服务:"
    echo "   docker-compose down && docker-compose up -d"
else
    echo "=========================================="
    echo "❌ 下载不完整，缺少 ${missing_files} 个文件"
    echo "=========================================="
    exit 1
fi
