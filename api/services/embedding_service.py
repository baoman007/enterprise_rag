#!/usr/bin/env python3
"""
Embedding 服务 - 使用 SentenceTransformer 生成文本向量
"""

from sentence_transformers import SentenceTransformer
import chromadb
from typing import List, Optional
import logging
import os

from api.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Embedding 服务类"""

    def __init__(self):
        """初始化 embedding 模型"""
        # 设置离线模式
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_DATASETS_OFFLINE'] = '1'

        try:
            # 使用配置的模型
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Embedding 模型加载成功: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"加载配置模型失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding 维度: {self.dimension}")

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        将文本编码为向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,  # 归一化，提高相似度计算准确性
            show_progress_bar=False
        )

        return embeddings.tolist()

    def encode_single(self, text: str) -> List[float]:
        """
        编码单个文本

        Args:
            text: 文本

        Returns:
            向量
        """
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        return embedding.tolist()


class ChromaService:
    """ChromaDB 向量数据库服务"""

    def __init__(self, embedding_service: EmbeddingService):
        """
        初始化 ChromaDB 服务

        Args:
            embedding_service: embedding 服务实例
        """
        self.embedding_service = embedding_service
        self.client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        self.collection_name = "medical_documents"

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "医疗文档向量数据库", "dimension": self.embedding_service.dimension}
        )

        logger.info(f"ChromaDB 集合: {self.collection_name}, 当前文档数: {self.collection.count()}")

    def add_documents(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        """
        添加文档到向量数据库

        Args:
            documents: 文本列表
            metadatas: 元数据列表
            ids: 文档 ID 列表
        """
        if not documents:
            return

        # 使用 embedding 服务生成向量
        embeddings = self.embedding_service.encode(documents)

        # 添加到 ChromaDB
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"成功添加 {len(documents)} 个文档到向量数据库")

    def search(self, query: str, n_results: int = 5, where: Optional[dict] = None):
        """
        搜索相似文档

        Args:
            query: 查询文本
            n_results: 返回结果数量
            where: 过滤条件

        Returns:
            搜索结果
        """
        # 编码查询文本
        query_embedding = self.embedding_service.encode_single(query)

        # 执行搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=['documents', 'metadatas', 'distances']
        )

        return results

    def get_document_count(self) -> int:
        """获取文档总数"""
        return self.collection.count()

    def get_by_doc_id(self, doc_id: str, limit: int = 50):
        """
        根据文档 ID 获取所有段落

        Args:
            doc_id: 文档 ID
            limit: 返回数量限制

        Returns:
            文档段落列表
        """
        results = self.collection.get(
            where={"id": doc_id},
            limit=limit,
            include=['documents', 'metadatas']
        )

        return results


# 全局实例（单例模式）
_embedding_service = None
_chroma_service = None


def get_embedding_service() -> EmbeddingService:
    """获取 embedding 服务实例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_chroma_service() -> ChromaService:
    """获取 ChromaDB 服务实例"""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService(get_embedding_service())
    return _chroma_service
