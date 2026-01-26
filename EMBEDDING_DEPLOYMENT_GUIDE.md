# Embedding 模型私有化部署指南

## 方案概览

### 当前使用的模型
- **模型名称**: `BAAI/bge-small-zh-v1.5`
- **开发者**: 北京智源人工智能研究院 (BAAI)
- **许可证**: MIT（可商用）
- **模型大小**: 约 100MB
- **向量维度**: 512

---

## 方案1：使用 huggingface-cli 下载（推荐）

### 前提条件
```bash
pip install huggingface_hub
```

### 下载步骤

1. 创建模型目录
```bash
cd /Users/baozhen/CodeBuddy/medical-model-training/enterprise_rag
mkdir -p models
```

2. 下载模型
```bash
# 使用国内镜像加速
HF_ENDPOINT=https://hf-mirror.com huggingface-cli download \
  BAAI/bge-small-zh-v1.5 \
  --local-dir ./models/bge-small-zh-v1.5
```

3. 修改配置文件
```bash
# 编辑 .env 文件
EMBEDDING_MODEL=/app/models/bge-small-zh-v1.5
```

4. 更新 docker-compose.yml
```yaml
volumes:
  - ./models:/app/models  # 添加模型卷挂载
```

5. 重启服务
```bash
docker-compose down
docker-compose up -d
```

---

## 方案2：使用 Git LFS 下载

### 前提条件
```bash
# 安装 git-lfs
brew install git-lfs  # macOS
# 或
apt-get install git-lfs  # Ubuntu

git lfs install
```

### 下载步骤

1. 克隆模型仓库
```bash
cd /Users/baozhen/CodeBuddy/medical-model-training/enterprise_rag
mkdir -p models
cd models
git lfs clone https://huggingface.co/BAAI/bge-small-zh-v1.5
```

2. 验证文件
```bash
ls -lh bge-small-zh-v1.5/
# 应该看到: config.json, model.safetensors, tokenizer.json 等
```

3. 更新配置（同方案1）

---

## 方案3：直接使用容器内缓存（当前方案）

### 说明
- 系统会在首次使用时自动下载模型
- 模型缓存在 `/root/.cache/huggingface/` 目录
- 已配置 Docker 卷 `model_cache` 持久化缓存

### 优化配置

在 `docker-compose.yml` 中已配置：
```yaml
volumes:
  - model_cache:/root/.cache/huggingface  # 持久化模型缓存
```

### 离线模式

如果模型已下载，设置离线模式：
```bash
# 在 docker-compose.yml 中添加环境变量
environment:
  - TRANSFORMERS_OFFLINE=1  # 离线模式
```

---

## 验证模型是否加载成功

### 方法1：查看日志
```bash
docker logs enterprise_rag-api-1 | grep -i embedding
```

### 方法2：测试上传文档
```bash
curl -X POST 'http://localhost:8000/api/v1/knowledge/upload?kb_id=test' \
  -F 'file=@test_heart_doc.txt' \
  -F 'category=测试'
```

### 方法3：查看向量数据库
```bash
# 访问向量数据库查看器
open http://localhost:8000/static/index.html
```

---

## 常见问题

### Q1: 下载速度很慢怎么办？
**A**: 使用国内镜像源：
```bash
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download BAAI/bge-small-zh-v1.5 --local-dir ./models
```

### Q2: 如何更换为其他模型？
**A**: 修改配置文件：
```bash
# .env
EMBEDDING_MODEL=shibing624/text2vec-base-chinese  # 其他中文模型
```

推荐的其他中文模型：
- `shibing624/text2vec-base-chinese` (768维)
- `moka-ai/m3e-base` (768维)
- `GanymedeNil/text2vec-large-chinese` (1024维)

### Q3: 模型文件多大？
**A**: 
- `bge-small-zh-v1.5`: 约 100MB
- `bge-large-zh-v1.5`: 约 300MB
- `text2vec-base-chinese`: 约 400MB

### Q4: 如何完全离线部署？
**A**:
1. 在有网络的机器上下载模型
2. 打包模型文件夹
3. 复制到目标服务器
4. 使用本地路径加载模型

---

## 快速开始（推荐流程）

```bash
# 1. 进入项目目录
cd /Users/baozhen/CodeBuddy/medical-model-training/enterprise_rag

# 2. 下载模型（使用镜像）
mkdir -p models
HF_ENDPOINT=https://hf-mirror.com huggingface-cli download \
  BAAI/bge-small-zh-v1.5 \
  --local-dir ./models/bge-small-zh-v1.5

# 3. 更新配置
sed -i '' 's|EMBEDDING_MODEL=.*|EMBEDDING_MODEL=/app/models/bge-small-zh-v1.5|' .env

# 4. 更新 docker-compose.yml（添加卷挂载）
# 手动添加: - ./models:/app/models

# 5. 重启服务
docker-compose down
docker-compose up -d

# 6. 验证
docker logs enterprise_rag-api-1 | grep embedding
```

---

## 性能参考

### 不同模型的性能对比

| 模型 | 维度 | 大小 | 速度 | 准确度 |
|------|------|------|------|--------|
| bge-small-zh-v1.5 | 512 | 100MB | 快 | 中 |
| bge-large-zh-v1.5 | 768 | 300MB | 慢 | 高 |
| text2vec-base-chinese | 768 | 400MB | 中 | 高 |

### 推荐场景
- **快速测试**: `bge-small-zh-v1.5`
- **生产环境**: `bge-large-zh-v1.5` 或 `text2vec-base-chinese`
- **资源受限**: `bge-small-zh-v1.5`

---

## 联系与支持

- 模型仓库: https://huggingface.co/BAAI/bge-small-zh-v1.5
- 文档: https://huggingface.co/docs
- 问题反馈: https://github.com/FlagOpen/FlagEmbedding
