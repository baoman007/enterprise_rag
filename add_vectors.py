import chromadb
import os

os.makedirs('./data/vector_db', exist_ok=True)
client = chromadb.PersistentClient(path='./data/vector_db')
collection = client.get_or_create_collection(name='medical_documents')

documents = [
    '高血压患者应该控制钠盐摄入,每日不超过5g',
    '多吃富含钾的食物如香蕉、土豆、菠菜有助于降低血压',
    '糖尿病患者需要控制碳水化合物和糖分摄入',
    '选择低升糖指数的食物对糖尿病患者很重要',
    '冠心病的早期症状包括胸痛、胸闷、呼吸困难',
    '预防冠心病需要控制血压、血脂、血糖'
]

metadatas = [
    {'category': '高血压', 'department': '心内科', 'id': 'doc_001'},
    {'category': '高血压', 'department': '心内科', 'id': 'doc_001'},
    {'category': '糖尿病', 'department': '内分泌科', 'id': 'doc_002'},
    {'category': '糖尿病', 'department': '内分泌科', 'id': 'doc_002'},
    {'category': '冠心病', 'department': '心内科', 'id': 'doc_003'},
    {'category': '冠心病', 'department': '心内科', 'id': 'doc_003'},
]

ids = ['vec_001', 'vec_002', 'vec_003', 'vec_004', 'vec_005', 'vec_006']

collection.add(documents=documents, metadatas=metadatas, ids=ids)
print(f'添加向量数据成功, 总量: {collection.count()}')
