#!/usr/bin/env python3
"""
医疗问答API - RAG 实现
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from api.services import get_chroma_service, get_llm_service
from api.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class PatientProfile(BaseModel):
    """患者基本信息"""
    age: int = Field(..., ge=0, le=150, description="年龄")
    gender: str = Field(..., description="性别：male/female")
    medical_history: Optional[List[str]] = Field(None, description="既往病史")
    current_medications: Optional[List[str]] = Field(None, description="当前用药")


class ChatOptions(BaseModel):
    """问答选项"""
    max_results: int = Field(5, ge=1, le=20, description="返回结果数量")
    include_references: bool = Field(True, description="是否包含参考来源")
    evidence_level: Optional[str] = Field(None, description="证据等级：A/B/C")
    department: Optional[str] = Field(None, description="科室过滤")


class ChatRequest(BaseModel):
    """问答请求"""
    query: str = Field(..., min_length=1, description="用户问题")
    patient_profile: Optional[PatientProfile] = Field(None, description="患者信息")
    options: Optional[ChatOptions] = Field(default_factory=ChatOptions)


class Reference(BaseModel):
    """参考来源"""
    title: str
    author: str
    department: str
    evidence_level: str
    url: Optional[str] = None


class ChatResponse(BaseModel):
    """问答响应"""
    answer: str
    references: List[Reference]
    confidence: float
    similar_queries: List[str]
    _rag_details: Optional[dict] = None  # RAG 详细过程数据


class RAGProcessResponse(BaseModel):
    """RAG 检索过程响应"""
    query: str
    embedding_model: str
    embedding_dim: int
    normalized: bool
    query_embedding: List[float]
    top_k: int
    similarity_threshold: float
    retrieved_docs: List[dict]
    final_prompt: str


@router.post("/chat", response_model=ChatResponse)
async def medical_chat(request: ChatRequest):
    """
    医疗问答 - RAG 实现

    - **query**: 用户问题，例如"高血压患者的饮食建议"
    - **patient_profile**: 可选的患者信息
    - **options**: 答案选项
    
    RAG 流程：
    1. 向量检索：从 ChromaDB 查找相关文档
    2. 答案生成：基于检索到的上下文生成答案
    3. 参考来源：返回相关文档信息
    """
    try:
        logger.info(f"收到查询: {request.query}")
        
        # 获取服务实例
        chroma_service = get_chroma_service()
        llm_service = get_llm_service()
        
        # 构建 where 条件
        where = None
        if request.options and request.options.department:
            where = {"department": request.options.department}
        
        # 执行向量检索
        results = chroma_service.search(
            query=request.query,
            n_results=request.options.max_results if request.options else 5,
            where=where
        )
        
        # 提取检索结果
        if not results or not results['documents'] or not results['documents'][0]:
            return ChatResponse(
                answer="抱歉，在当前知识库中没有找到相关的医疗建议。建议您咨询专业医生或提供更具体的问题。",
                references=[],
                confidence=0.0,
                similar_queries=[]
            )
        
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]

        # 过滤低相关结果（相似度阈值）
        filtered_docs = []
        filtered_metas = []
        filtered_dists = []

        for doc, meta, dist in zip(documents, metadatas, distances):
            similarity = 1.0 - dist  # 余弦距离转换为相似度（范围 0-1）
            if similarity >= settings.SIMILARITY_THRESHOLD:
                filtered_docs.append(doc)
                filtered_metas.append(meta)
                filtered_dists.append(dist)

        if not filtered_docs:
            return ChatResponse(
                answer="抱歉，没有找到足够相关的医疗建议。建议您尝试其他关键词或咨询专业医生。",
                references=[],
                confidence=0.0,
                similar_queries=[]
            )

        # 保存 RAG 详细信息（用于调试展示）
        rag_details = {
            'embedding_model': settings.EMBEDDING_MODEL,
            'embedding_dim': chroma_service.embedding_service.dimension,
            'normalized': True,
            'query_embedding': chroma_service.embedding_service.encode_single(request.query),
            'top_k': request.options.max_results if request.options else 5,
            'similarity_threshold': settings.SIMILARITY_THRESHOLD,
            'retrieved_docs': [
                {
                    'id': results['ids'][0][i],
                    'content': documents[i],
                    'similarity': 1.0 - distances[i],
                    'distance': distances[i],
                    'category': metadatas[i].get('category'),
                    'department': metadatas[i].get('department')
                }
                for i in range(len(documents))
            ]
        }

        # 提取患者信息
        patient_info = None
        if request.patient_profile:
            patient_info = {
                "age": request.patient_profile.age,
                "gender": request.patient_profile.gender,
                "medical_history": request.patient_profile.medical_history,
                "current_medications": request.patient_profile.current_medications
            }

        # 构建最终 Prompt（用于展示）
        context = "\n\n".join([f"[文档 {i+1}]\n{doc}" for i, doc in enumerate(filtered_docs)])

        if patient_info:
            patient_str = f"\n\n患者信息：年龄{patient_info['age']}岁，{patient_info['gender']}"
            context += patient_str

        from api.services.llm_service import LLMService
        temp_llm = LLMService()
        final_prompt = temp_llm.prompt_template.format(
            context=context,
            query=request.query
        )
        rag_details['final_prompt'] = final_prompt

        # 生成答案
        answer = llm_service.generate_answer(
            query=request.query,
            context_docs=filtered_docs,
            patient_profile=patient_info
        )
        
        # 构建参考来源
        references = []
        unique_docs = set()
        
        for meta in filtered_metas:
            doc_id = meta.get('id', '')
            if doc_id and doc_id not in unique_docs:
                unique_docs.add(doc_id)
                references.append(Reference(
                    title=f"文档 {doc_id}",
                    author="医疗知识库",
                    department=meta.get('department', '未知'),
                    evidence_level="A",  # 默认为 A 级
                    url=None
                ))
        
        # 计算置信度
        confidence = llm_service.calculate_confidence(
            query=request.query,
            context_docs=filtered_docs,
            distances=filtered_dists
        )
        
        # 生成相似问题建议（简单的关键词提取）
        similar_queries = _generate_similar_queries(request.query, filtered_docs)

        logger.info(f"RAG 检索完成: 检索到 {len(filtered_docs)} 个相关文档, 置信度: {confidence}")

        return ChatResponse(
            answer=answer,
            references=references[:request.options.max_results] if request.options else references[:5],
            confidence=confidence,
            similar_queries=similar_queries,
            _rag_details=rag_details  # 包含 RAG 详细信息
        )

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"问答失败: {str(e)}\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")


@router.post("/rag-process", response_model=RAGProcessResponse)
async def rag_process_detail(request: ChatRequest):
    """
    RAG 检索过程详解

    返回完整的 RAG 处理细节，包括：
    1. Query Embedding 信息
    2. 检索到的文档列表（包含 ID、内容、相似度）
    3. 最终构建的 Prompt
    """
    try:
        logger.info(f"RAG 过程请求: {request.query}")

        chroma_service = get_chroma_service()

        # 构建 where 条件
        where = None
        if request.options and request.options.department:
            where = {"department": request.options.department}

        # 执行向量检索
        results = chroma_service.search(
            query=request.query,
            n_results=request.options.max_results if request.options else 5,
            where=where
        )

        # 提取检索结果
        if not results or not results['documents'] or not results['documents'][0]:
            return RAGProcessResponse(
                query=request.query,
                embedding_model=settings.EMBEDDING_MODEL,
                embedding_dim=chroma_service.embedding_service.dimension,
                normalized=True,
                query_embedding=chroma_service.embedding_service.encode_single(request.query),
                top_k=request.options.max_results if request.options else 5,
                similarity_threshold=settings.SIMILARITY_THRESHOLD,
                retrieved_docs=[],
                final_prompt="未检索到相关文档"
            )

        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]

        # 构建 RAG 详细信息
        rag_details = {
            'embedding_model': settings.EMBEDDING_MODEL,
            'embedding_dim': chroma_service.embedding_service.dimension,
            'normalized': True,
            'query_embedding': chroma_service.embedding_service.encode_single(request.query),
            'top_k': request.options.max_results if request.options else 5,
            'similarity_threshold': settings.SIMILARITY_THRESHOLD,
            'retrieved_docs': [
                {
                    'id': results['ids'][0][i],
                    'content': documents[i],
                    'similarity': max(0.0, 1.0 - distances[i]),
                    'distance': distances[i],
                    'category': metadatas[i].get('category'),
                    'department': metadatas[i].get('department')
                }
                for i in range(len(documents))
            ]
        }

        # 构建最终 Prompt
        context = "\n\n".join([f"[文档 {i+1}]\n{doc}" for i, doc in enumerate(documents)])
        from api.services.llm_service import LLMService
        temp_llm = LLMService()
        final_prompt = temp_llm.prompt_template.format(
            context=context,
            query=request.query
        )

        logger.info(f"RAG 过程响应: 检索到 {len(documents)} 个文档")

        return RAGProcessResponse(
            query=request.query,
            embedding_model=rag_details['embedding_model'],
            embedding_dim=rag_details['embedding_dim'],
            normalized=rag_details['normalized'],
            query_embedding=rag_details['query_embedding'],
            top_k=rag_details['top_k'],
            similarity_threshold=rag_details['similarity_threshold'],
            retrieved_docs=rag_details['retrieved_docs'],
            final_prompt=final_prompt
        )

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"RAG 过程查询失败: {str(e)}\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/search")
async def medical_search(
    query: str = Query(..., description="检索关键词"),
    category: Optional[str] = Query(None, description="科室分类"),
    top_k: int = Query(5, ge=1, le=20, description="返回数量")
):
    """
    文档检索 - RAG 向量检索
    
    使用向量相似度搜索相关医疗文档
    """
    try:
        chroma_service = get_chroma_service()
        
        # 构建过滤条件
        where = {"category": category} if category else None
        
        # 执行搜索
        results = chroma_service.search(
            query=query,
            n_results=top_k,
            where=where
        )
        
        # 格式化结果
        formatted_results = []
        if results and results['documents'] and results['documents'][0]:
            for i, (doc, meta, dist) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                similarity = round(1.0 - dist, 4)
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "content": doc,
                    "metadata": meta,
                    "similarity": similarity
                })
        
        return {
            "query": query,
            "total": len(formatted_results),
            "results": formatted_results
        }
        
    except Exception as e:
        logger.error(f"检索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.get("/emergency")
async def check_emergency(symptoms: str):
    """紧急情况检查"""
    emergency_keywords = ["胸痛", "呼吸困难", "意识模糊", "严重出血"]
    is_emergency = any(keyword in symptoms for keyword in emergency_keywords)
    return {"is_emergency": is_emergency, "message": "建议立即就医！" if is_emergency else "非紧急情况"}


def _generate_similar_queries(query: str, context_docs: List[str]) -> List[str]:
    """
    生成相似问题建议
    
    Args:
        query: 原始问题
        context_docs: 相关文档
        
    Returns:
        相似问题列表
    """
    similar_queries = []
    
    # 简单的关键词扩展
    if "饮食" in query:
        if "高血压" in query:
            similar_queries.extend(["高血压吃什么", "高血压饮食禁忌", "高血压日常饮食"])
        elif "糖尿病" in query:
            similar_queries.extend(["糖尿病吃什么", "糖尿病饮食指南", "糖尿病饮食禁忌"])
    elif "症状" in query or "预防" in query:
        if "冠心病" in query:
            similar_queries.extend(["冠心病早期表现", "冠心病怎么预防", "冠心病注意事项"])
        elif "高血压" in query:
            similar_queries.extend(["高血压早期症状", "高血压并发症", "高血压日常护理"])
    
    return similar_queries[:5]  # 最多返回 5 个
