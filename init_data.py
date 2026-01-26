#!/usr/bin/env python3
"""
初始化数据库和添加示例数据
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import chromadb
import os

# 初始化数据库
from api.core.database import Base, engine, get_db
from api.models.database import Document, KnowledgeBase


async def init_database():
    """创建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def add_sample_data():
    """添加示例数据"""
    from api.core.database import async_session

    async with async_session() as session:
        # 创建知识库
        kb = KnowledgeBase(
            id="kb_001",
            name="心血管疾病知识库",
            category="心内科",
            description="包含高血压、冠心病、心律失常等疾病的治疗指南"
        )
        session.add(kb)

        # 添加文档
        doc = Document(
            id="doc_001",
            title="高血压患者饮食指南",
            content="""高血压患者应该如何控制饮食?

1. 控制钠盐摄入:每日盐摄入量应控制在5g以下
2. 增加钾摄入:多吃香蕉、土豆、菠菜等富含钾的食物
3. 控制脂肪:减少饱和脂肪酸,选择橄榄油等不饱和脂肪
4. 适量蛋白质:优选鱼类、禽肉、豆制品
5. 限制酒精:男性不超过2标准杯/日,女性不超过1标准杯/日
6. 保持健康体重:避免肥胖
7. 定期运动:每周150分钟中等强度有氧运动
8. 戒烟
9. 管理压力:保持良好心态""",
            author="中华医学会心血管病学分会",
            department="心内科",
            category="高血压",
            kb_id="kb_001",
            status="active"
        )
        session.add(doc)

        doc2 = Document(
            id="doc_002",
            title="糖尿病患者的饮食注意事项",
            content="""糖尿病患者饮食需要注意:

1. 控制碳水化合物摄入
2. 选择低升糖指数(GI)食物
3. 增加膳食纤维摄入
4. 规律饮食,定时定量
5. 避免高糖食物和饮料
6. 控制总热量摄入
7. 合理分配三餐营养""",
            author="中国医师协会",
            department="内分泌科",
            category="糖尿病",
            kb_id="kb_001",
            status="active"
        )
        session.add(doc2)

        doc3 = Document(
            id="doc_003",
            title="冠心病的早期症状和预防",
            content="""冠心病的早期症状包括:

1. 胸痛或胸闷
2. 呼吸困难
3. 乏力、头晕
4. 心悸

预防措施:
1. 控制血压、血脂、血糖
2. 戒烟限酒
3. 健康饮食
4. 规律运动
5. 控制体重
6. 保持心理健康""",
            author="心血管疾病防治指南",
            department="心内科",
            category="冠心病",
            kb_id="kb_001",
            status="active"
        )
        session.add(doc3)

        await session.commit()
        print("✅ 成功添加3篇示例文档")


async def add_vector_data():
    """添加向量数据到ChromaDB"""
    # 创建目录
    os.makedirs("./data/vector_db", exist_ok=True)

    # 连接ChromaDB
    client = chromadb.PersistentClient(path="./data/vector_db")

    # 创建集合
    collection = client.get_or_create_collection(
        name="medical_documents",
        metadata={"description": "医疗文档向量数据库"}
    )

    # 示例文档和向量
    documents = [
        "高血压患者应该控制钠盐摄入,每日不超过5g",
        "多吃富含钾的食物如香蕉、土豆、菠菜有助于降低血压",
        "糖尿病患者需要控制碳水化合物和糖分摄入",
        "选择低升糖指数(GI)的食物对糖尿病患者很重要",
        "冠心病的早期症状包括胸痛、胸闷、呼吸困难",
        "预防冠心病需要控制血压、血脂、血糖"
    ]

    metadatas = [
        {"category": "高血压", "department": "心内科", "id": "doc_001"},
        {"category": "高血压", "department": "心内科", "id": "doc_001"},
        {"category": "糖尿病", "department": "内分泌科", "id": "doc_002"},
        {"category": "糖尿病", "department": "内分泌科", "id": "doc_002"},
        {"category": "冠心病", "department": "心内科", "id": "doc_003"},
        {"category": "冠心病", "department": "心内科", "id": "doc_003"},
    ]

    ids = ["vec_001", "vec_002", "vec_003", "vec_004", "vec_005", "vec_006"]

    # 添加数据(实际应用中需要用embedding模型生成向量)
    try:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✅ 成功添加 {len(documents)} 条向量数据")
        print(f"   当前向量数据库总量: {collection.count()}")
    except Exception as e:
        print(f"❌ 添加向量数据失败: {e}")


async def main():
    """主函数"""
    print("开始初始化数据库...")

    # 初始化数据库
    await init_database()
    print("✅ 数据库表创建成功")

    # 添加示例数据
    await add_sample_data()

    # 添加向量数据
    await add_vector_data()

    print("\n✅ 初始化完成!")


if __name__ == "__main__":
    asyncio.run(main())
