#!/bin/bash
# 下载 embedding 模型脚本

MODEL_NAME="${1:-BAAI/bge-small-zh-v1.5}"
CACHE_DIR="./model_cache"

echo "开始下载模型: ${MODEL_NAME}"
echo "模型将保存到: ${CACHE_DIR}"

# 使用国内镜像源
export HF_ENDPOINT=https://hf-mirror.com

docker run --rm \
  -v "$(pwd)/${CACHE_DIR}:/root/.cache/huggingface" \
  -e HF_ENDPOINT=https://hf-mirror.com \
  python:3.9-slim \
  bash -c "
    pip install --no-cache-dir sentence-transformers==2.7.0 torch==2.0.1
    python3 -c \"from sentence_transformers import SentenceTransformer; model = SentenceTransformer('${MODEL_NAME}'); print(f'✅ 模型下载成功！'); print(f'模型维度: {model.get_sentence_embedding_dimension()')\"
  "

echo "✅ 模型下载完成！"
echo "模型缓存位置: $(pwd)/${CACHE_DIR}"
