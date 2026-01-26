import chromadb

# 连接
client = chromadb.PersistentClient(path="./data/vector_db")

# 列出集合
for coll in client.list_collections():
    print(f"集合: {coll.name}, 数量: {coll.count()}")
    
    # 查询数据
    results = coll.get(include=['documents', 'metadatas', 'embeddings'])
