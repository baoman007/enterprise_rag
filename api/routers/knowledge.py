#!/usr/bin/env python3
"""
知识库管理API
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from pydantic import BaseModel
from typing import Optional, List
import logging
import uuid
import os
import chromadb

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.core.database import async_session, get_db
from api.models.database import Document, KnowledgeBase as KnowledgeBaseModel
from api.services import get_chroma_service, get_text_splitter

# 检查是否安装了PDF解析库
try:
    import pypdf
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False
    logging.warning("pypdf未安装，PDF文件上传功能不可用")

router = APIRouter()
logger = logging.getLogger(__name__)


def extract_text_from_pdf(content: bytes) -> str:
    """从PDF文件中提取文本"""
    try:
        import io
        from pypdf import PdfReader

        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)

        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        return text
    except Exception as e:
        logger.error(f"PDF解析失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"PDF解析失败: {str(e)}")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: str
    name: str
    category: str
    document_count: int
    created_at: str
    status: str


class DocumentResponse(BaseModel):
    """文档"""
    id: str
    title: str
    author: str
    department: str
    status: str
    created_at: str


@router.get("/list")
async def list_knowledge_bases():
    """获取所有知识库"""
    return {"knowledge_bases": []}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    kb_id: str = Form(None),
    category: str = Form(None)
):
    """上传文档"""
    try:
        # 检查文件类型
        if file.filename.endswith('.pdf'):
            if not HAS_PDF_SUPPORT:
                raise HTTPException(status_code=400, detail="PDF解析库未安装，请安装pypdf")
            content = await file.read()
            text_content = extract_text_from_pdf(content)
        else:
            # 读取文本文件
            content = await file.read()
            # 尝试多种编码解码
            text_content = None
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if text_content is None:
                raise HTTPException(status_code=400, detail="无法解码文件内容")

        # 生成文档ID
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"

        # 保存到PostgreSQL
        async with async_session() as session:
            # 确认知识库存在
            result = await session.execute(select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id))
            kb = result.scalar_one_or_none()

            # 使用实际的知识库ID
            actual_kb_id = kb_id

            if not kb:
                # 如果知识库不存在，创建一个默认的
                actual_kb_id = kb_id if kb_id else f"kb_{uuid.uuid4().hex[:8]}"
                kb = KnowledgeBaseModel(
                    id=actual_kb_id,
                    name="默认知识库",
                    category=category or "通用",
                    description="自动创建的知识库"
                )
                session.add(kb)
                await session.commit()
                await session.refresh(kb)

            # 创建文档记录
            from datetime import datetime
            document = Document(
                id=doc_id,
                title=file.filename,
                content=text_content,
                author="上传用户",
                department=category or "通用",
                category=category or "通用",
                kb_id=actual_kb_id,
                status="active",
                created_at=datetime.utcnow()
            )
            session.add(document)
            await session.commit()

        # 保存到向量数据库
        paragraphs = []
        try:
            # 使用 embedding 服务
            chroma_service = get_chroma_service()

            # 使用智能文本切分器
            text_splitter = get_text_splitter()
            paragraphs = text_splitter.split_text(text_content)

            if paragraphs:
                # 批量添加到向量数据库
                ids = [f"{doc_id}_{i}" for i in range(len(paragraphs))]
                metadatas = [{"category": category or "通用", "department": category or "通用", "id": doc_id} for _ in range(len(paragraphs))]

                chroma_service.add_documents(
                    documents=paragraphs,
                    metadatas=metadatas,
                    ids=ids
                )

                logger.info(f"成功添加 {len(paragraphs)} 个段落到向量数据库（使用智能切分 + embedding 模型）")
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logger.warning(f"向量数据库保存失败: {str(e)}\n{error_detail}")
            # 即使向量数据库失败，文档也已经保存到PostgreSQL了
            paragraphs = []

        logger.info(f"文档上传成功: {doc_id}, 文件名: {file.filename}, 段落数: {len(paragraphs)}")

        return {
            "message": "文档上传成功",
            "document_id": doc_id,
            "filename": file.filename,
            "paragraphs_count": len(paragraphs)
        }

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"文档上传失败: {str(e)}\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.get("/{kb_id}/documents")
async def list_documents(kb_id: str, status: Optional[str] = None):
    """获取知识库文档列表"""
    async with async_session() as session:
        from sqlalchemy import select

        query = select(Document).where(Document.kb_id == kb_id)
        if status:
            query = query.where(Document.status == status)

        result = await session.execute(query)
        documents = result.scalars().all()

        return {
            "kb_id": kb_id,
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "author": doc.author,
                    "department": doc.department,
                    "status": doc.status,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                }
                for doc in documents
            ]
        }


@router.put("/{kb_id}/documents/{doc_id}")
async def update_document(kb_id: str, doc_id: str, status: str):
    """更新文档状态"""
    async with async_session() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(Document).where(Document.id == doc_id, Document.kb_id == kb_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        document.status = status
        await session.commit()

        return {"message": "文档更新成功"}


@router.get("/vector/search")
async def search_vectors(
    query: str,
    limit: int = 10,
    category: Optional[str] = None,
    doc_id: Optional[str] = None
):
    """搜索向量数据库"""
    try:
        # 使用 embedding 服务进行搜索
        chroma_service = get_chroma_service()

        # 构建过滤条件
        where = {}
        if category:
            where["category"] = category
        if doc_id:
            where["id"] = doc_id

        # 搜索
        results = chroma_service.search(
            query=query,
            n_results=limit,
            where=where if where else None
        )

        # 格式化结果
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                })

        return {
            "query": query,
            "total": len(formatted_results),
            "results": formatted_results
        }
    except Exception as e:
        logger.error(f"向量搜索失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"向量搜索失败: {str(e)}")


@router.get("/vector/list")
async def list_vectors(
    limit: int = 20,
    offset: int = 0,
    category: Optional[str] = None,
    doc_id: Optional[str] = None
):
    """列出向量数据库中的文档"""
    try:
        # 使用统一的 ChromaService
        chroma_service = get_chroma_service()
        collection = chroma_service.collection

        # 获取总数
        total = collection.count()

        # 构建过滤条件 - ChromaDB 需要 $and 操作符来组合多个条件
        where = None
        conditions = []
        if category:
            conditions.append({"category": category})
        if doc_id:
            conditions.append({"id": doc_id})

        if len(conditions) == 1:
            where = conditions[0]
        elif len(conditions) > 1:
            where = {"$and": conditions}

        # 获取数据
        if where:
            results = collection.get(
                where=where,
                limit=limit,
                offset=offset,
                include=['documents', 'metadatas']
            )
        else:
            results = collection.get(
                limit=limit,
                offset=offset,
                include=['documents', 'metadatas']
            )

        # 格式化结果
        formatted_results = []
        for i in range(len(results['ids'])):
            formatted_results.append({
                "id": results['ids'][i],
                "document": results['documents'][i],
                "metadata": results['metadatas'][i]
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": formatted_results
        }
    except Exception as e:
        logger.error(f"获取向量数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取向量数据失败: {str(e)}")


@router.get("/vector/stats")
async def vector_stats():
    """向量数据库统计信息"""
    try:
        # 使用统一的 ChromaService
        chroma_service = get_chroma_service()
        client = chroma_service.client

        collections = client.list_collections()
        stats = []

        for collection in collections:
            stats.append({
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata
            })

        return {
            "total_collections": len(collections),
            "collections": stats
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
