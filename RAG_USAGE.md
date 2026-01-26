# RAG 系统完整实现说明

## 已实现的功能

### 1. 数据增加流程
**接口**: `/api/v1/knowledge/upload`

流程：
1. 文件解析（PDF/文本文件）
2. 保存完整内容到 PostgreSQL
3. 文本分片（按段落）
4. 使用 SentenceTransformer 生成向量嵌入
5. 保存到 ChromaDB 向量数据库

### 2. 检索流程
**接口**: `/api/v1/medical/chat`

RAG 流程：
1. 用户问题 → SentenceTransformer 生成查询向量
2. ChromaDB 向量检索（Top-K 相似文档）
3. 过滤低相似度结果（阈值 0.7）
4. 基于检索上下文生成答案
5. 返回答案 + 参考来源 + 置信度

## 测试命令

### 1. 上传文档
```bash
curl -X 'POST' 'http://localhost:8000/api/v1/knowledge/upload?kb_id=kb_new&category=测试' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@test.txt;type=text/plain'
```

### 2. RAG 问答
```bash
curl -X POST http://localhost:8000/api/v1/medical/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "高血压患者的饮食建议",
    "options": {"max_results": 5}
  }'
```

### 3. 向量检索
```bash
curl -G http://localhost:8000/api/v1/medical/search \
  --data-urlencode "query=心脏" \
  --data-urlencode "top_k=5"
```

## 组件说明

### EmbeddingService
- 模型: BAAI/bge-large-zh-v1.5
- 向量维度: 1024
- 归一化: 启用

### ChromaService
- 集合名: medical_documents
- 检索方式: 余弦相似度

### LLMService
- 答案生成: 基于规则（可替换为 LLM API）
- 置信度计算: 基于向量相似度

## 查看向量数据

访问：http://localhost:8000/static/index.html
