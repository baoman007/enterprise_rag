#!/usr/bin/env python3
"""
查看 ChromaDB 向量数据库内容
"""

import chromadb
from chromadb.config import Settings

# 连接到向量数据库
client = chromadb.PersistentClient(path="./data/vector_db")

# 列出所有集合
collections = client.list_collections()

print("=" * 60)
print("ChromaDB 向量数据库内容")
print("=" * 60)

if not collections:
    print("当前数据库为空,还没有任何集合")
else:
    print(f"\n共有 {len(collections)} 个集合:\n")

    for i, collection in enumerate(collections, 1):
        print(f"{i}. 集合名称: {collection.name}")
        print(f"   ID: {collection.id}")
        print(f"   文档数量: {collection.count()}")
        print(f"   元数据字段: {collection.metadata or '无'}")

        # 获取前 5 条记录
        try:
            results = collection.get(limit=50, include=['embeddings', 'documents', 'metadatas'])
            print(f"\n   前 5 条记录:")
            for j, (doc_id, doc, metadata) in enumerate(zip(
                results['ids'],
                results.get('documents', []),
                results.get('metadatas', [])
            ), 1):
                print(f"      {j}. ID: {doc_id}")
                print(f"         文档内容: {(doc[:100] + '...') if doc and len(doc) > 100 else doc}")
                print(f"         元数据: {metadata}")
        except Exception as e:
            print(f"   获取记录失败: {e}")

        print()

print("\n" + "=" * 60)
