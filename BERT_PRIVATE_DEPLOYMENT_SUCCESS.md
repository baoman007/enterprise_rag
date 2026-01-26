# ✅ BERT 模型私有化部署成功

## 部署总结

### 已完成的工作

1. **下载模型文件**
   - 模型：`BAAI/bge-small-zh-v1.5`
   - 下载方式：使用国内镜像站直接下载
   - 保存路径：`./models/bge-small-zh-v1.5/`

2. **模型文件清单**
   ```
   config.json              776B   - 模型配置
   model.safetensors      91M     - 模型权重
   tokenizer.json          429K    - 分词器
   tokenizer_config.json   367B    - 分词器配置
   vocab.txt             107K     - 词汇表
   special_tokens_map.json 125B     - 特殊token
   ```

3. **配置文件更新**
   - `.env`：设置 `EMBEDDING_MODEL=/app/models/bge-small-zh-v1.5`
   - `docker-compose.yml`：
     - 添加卷挂载 `./models:/app/models`
     - 设置离线模式 `TRANSFORMERS_OFFLINE=1`

4. **服务验证**
   - ✅ 文档上传成功
   - ✅ 向量数据库正常工作
   - ✅ 模型从本地路径加载
   - ✅ 文档切分并存储为 9 个向量段落

### 验证结果

```bash
# 上传文档
curl -X POST 'http://localhost:8000/api/v1/knowledge/upload?kb_id=test' \
  -F 'file=@test_heart_doc.txt' \
  -F 'category=测试'

# 返回结果
{
  "message": "文档上传成功",
  "document_id": "doc_bbc61b9d",
  "filename": "test_heart_doc.txt",
  "paragraphs_count": 9
}

# 查询向量数据库
curl -s 'http://localhost:8000/api/v1/knowledge/vector/list?limit=10&offset=0'
# 返回：total=9, results=[9条记录]
```

### 模型信息

- **模型名称**：BAAI/bge-small-zh-v1.5
- **向量维度**：512
- **模型大小**：91MB
- **许可证**：MIT（可商用）
- **部署方式**：本地私有化部署

### 架构说明

```
┌─────────────────────────────────────┐
│     Docker 容器                   │
│                                  │
│  ┌────────────────────────────┐   │
│  │  /app/models/          │◄──┼─── 挂载卷 (./models)
│  │  └─ bge-small-zh-v1.5/ │   │
│  │    ├─ config.json       │   │
│  │    ├─ model.safetensors │   │
│  │    └─ ...             │   │
│  └────────────────────────────┘   │
│                                  │
│  ┌────────────────────────────┐   │
│  │  Embedding Service       │   │
│  │  SentenceTransformer()    │   │
│  │  ──> 加载本地模型       │   │
│  └────────────────────────────┘   │
│                                  │
│  ┌────────────────────────────┐   │
│  │  ChromaDB 向量数据库     │   │
│  │  存储文档向量            │   │
│  └────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 访问地址

- **API 服务**：http://localhost:8000
- **向量数据库查看器**：http://localhost:8000/static/index.html
- **RAG 聊天界面**：http://localhost:8000/static/chat.html
- **健康检查**：http://localhost:8000/health

### 后续使用

1. **上传更多文档**
   - 访问 http://localhost:8000/static/index.html
   - 使用上传功能添加文档
   - 文档会自动切分并生成向量

2. **测试 RAG 功能**
   - 访问 http://localhost:8000/static/chat.html
   - 输入问题，系统会检索相关文档片段
   - 使用 LLM 生成回答

3. **查看向量数据**
   ```bash
   # 查看所有向量记录
   curl 'http://localhost:8000/api/v1/knowledge/vector/list'

   # 查看特定文档
   curl 'http://localhost:8000/api/v1/knowledge/vector/search?query=心脏'
   ```

### 常见问题

**Q: 如何更换模型？**
A:
1. 下载新模型到 `./models/new-model/`
2. 更新 `.env` 中的 `EMBEDDING_MODEL=/app/models/new-model`
3. 重启服务：`docker-compose restart`

**Q: 模型加载失败怎么办？**
A:
1. 检查模型文件是否完整：`ls -la ./models/bge-small-zh-v1.5/`
2. 检查容器内卷挂载：`docker exec enterprise_rag-api-1 ls /app/models/`
3. 查看错误日志：`docker logs enterprise_rag-api-1`

**Q: 如何完全离线使用？**
A: 已配置离线模式（`TRANSFORMERS_OFFLINE=1`），系统不会尝试连接外部网络。

### 性能参考

| 操作 | 时间 | 说明 |
|------|------|------|
| 上传文档 (2KB) | ~4秒 | 切分 + embedding |
| 查询向量数据库 | <1秒 | 相似度搜索 |
| 生成回答 | 2-5秒 | 取决于 LLM 响应时间 |

### 注意事项

1. 模型文件已本地化，无需网络连接
2. 向量数据库持久化在 `./data/vector_db/`
3. PostgreSQL 数据存储文档元数据
4. 首次启动时会加载模型到内存 (~100MB)

---

**部署时间**：2026-01-25
**部署状态**：✅ 成功
