#!/bin/bash
# 改进的 embedding 模型下载脚本

MODEL_NAME="${1:-BAAI/bge-small-zh-v1.5}"
CACHE_DIR="./model_cache"

echo "========================================"
echo "开始下载模型: ${MODEL_NAME}"
echo "模型将保存到: ${CACHE_DIR}"
echo "========================================"

# 确保目录存在
mkdir -p "${CACHE_DIR}"

# 使用已存在的容器环境（避免重复安装依赖）
docker run --rm \
  -v "$(pwd)/${CACHE_DIR}:/model_cache" \
  -e HF_ENDPOINT=https://hf-mirror.com \
  -e TRANSFORMERS_CACHE=/model_cache \
  -e SENTENCE_TRANSFORMERS_HOME=/model_cache \
  python:3.9-slim \
  bash -c "
    echo '安装依赖...'
    pip install --no-cache-dir -q sentence-transformers==2.7.0 torch==2.0.1 transformers==4.37.2

    echo '下载模型: ${MODEL_NAME}'
    python3 << 'PYEOF'
from sentence_transformers import SentenceTransformer
import os

# 设置缓存目录
cache_dir = '/model_cache'
os.environ['TRANSFORMERS_CACHE'] = cache_dir
os.environ['SENTENCE_TRANSFORMERS_HOME'] = cache_dir

print(f'开始从镜像源下载模型: ${MODEL_NAME}')
model = SentenceTransformer('${MODEL_NAME}', cache_folder=cache_dir)
print(f'✅ 模型下载成功！')
print(f'模型维度: {model.get_sentence_embedding_dimension()}')
PYEOF

    echo '检查下载的文件...'
    ls -lh /model_cache/
  "

echo ""
echo "========================================"
echo "✅ 模型下载完成！"
echo "模型缓存位置: $(pwd)/${CACHE_DIR}"
echo "========================================"
