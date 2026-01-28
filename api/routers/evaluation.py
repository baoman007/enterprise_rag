#!/usr/bin/env python3
"""
评估 API - 提供 RAG 系统评估接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging
import json
from datetime import datetime

from api.services import get_llm_service
from api.services.evaluation_service import EvaluationService, EvaluationResult

router = APIRouter()
logger = logging.getLogger(__name__)


class RetrievalEvaluationRequest(BaseModel):
    """检索评估请求"""
    query: str = Field(..., min_length=1, description="查询问题")
    retrieved_docs: List[str] = Field(..., min_length=1, description="检索到的文档内容列表")
    ground_truth_docs: List[str] = Field(..., min_length=1, description="真实相关的文档列表（标准答案）")
    use_ai_rating: bool = Field(False, description="是否使用 AI 进行辅助评分")


class RetrievalEvaluationResponse(BaseModel):
    """检索评估响应"""
    query: str
    retrieved_docs_count: int
    ground_truth_docs_count: int
    relevant_retrieved_count: int
    missed_docs_count: int
    precision: float
    recall: float
    f1_score: float
    ai_rating: Optional[str] = None
    ai_comment: Optional[str] = None
    ai_relevance_labels: Optional[Dict[str, bool]] = None
    relevant_retrieved_docs: List[str]
    missed_docs: List[str]


class BatchEvaluationRequest(BaseModel):
    """批量评估请求"""
    test_cases: List[Dict] = Field(..., min_length=1, description="测试用例列表")
    use_ai_rating: bool = Field(False, description="是否使用 AI 评分")


class BatchEvaluationResponse(BaseModel):
    """批量评估响应"""
    total_cases: int
    average_precision: float
    average_recall: float
    average_f1_score: float
    detailed_results: List[Dict]


@router.post("/retrieval", response_model=RetrievalEvaluationResponse)
async def evaluate_retrieval(request: RetrievalEvaluationRequest):
    """
    评估单次检索结果

    计算 Precision、Recall、F1-Score，可选使用 AI 辅助评分

    **评估指标说明：**
    - **Precision（精确率）** = 检索到的相关文档数 / 检索到的总文档数
      表示检索结果中有多少是真正相关的

    - **Recall（召回率）** = 检索到的相关文档数 / 真实相关文档总数
      表示真实相关的文档中有多少被检索到了

    - **F1-Score** = 2 * (Precision * Recall) / (Precision + Recall)
      Precision 和 Recall 的调和平均数，综合评价检索质量
    """
    try:
        logger.info(f"评估检索: query='{request.query}', docs={len(request.retrieved_docs)}")

        # 获取 LLM 服务（如果需要 AI 评分）
        llm_service = get_llm_service() if request.use_ai_rating else None

        # 创建评估服务
        evaluation_service = EvaluationService(llm_service=llm_service)

        # 执行评估
        result = evaluation_service.evaluate_retrieval(
            query=request.query,
            retrieved_docs=request.retrieved_docs,
            ground_truth_docs=request.ground_truth_docs,
            use_ai_rating=request.use_ai_rating
        )

        logger.info(f"评估完成: precision={result.precision:.4f}, recall={result.recall:.4f}")

        return RetrievalEvaluationResponse(
            query=result.query,
            retrieved_docs_count=len(result.retrieved_docs),
            ground_truth_docs_count=len(result.ground_truth_docs),
            relevant_retrieved_count=len(result.relevant_retrieved),
            missed_docs_count=len(result.missed_docs),
            precision=result.precision,
            recall=result.recall,
            f1_score=result.f1_score,
            ai_rating=result.ai_rating,
            ai_comment=result.ai_comment,
            ai_relevance_labels=result.ai_relevance_labels,
            relevant_retrieved_docs=result.relevant_retrieved,
            missed_docs=result.missed_docs
        )

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"评估失败: {str(e)}\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")


@router.post("/batch", response_model=BatchEvaluationResponse)
async def batch_evaluate(request: BatchEvaluationRequest):
    """
    批量评估多个检索结果

    对多个测试用例进行评估，并计算平均指标
    """
    try:
        logger.info(f"批量评估: test_cases={len(request.test_cases)}")

        # 获取 LLM 服务
        llm_service = get_llm_service() if request.use_ai_rating else None

        # 创建评估服务
        evaluation_service = EvaluationService(llm_service=llm_service)

        # 执行批量评估
        results = evaluation_service.batch_evaluate(
            test_cases=request.test_cases,
            use_ai_rating=request.use_ai_rating
        )

        logger.info(
            f"批量评估完成: avg_precision={results['average_precision']:.4f}, "
            f"avg_recall={results['average_recall']:.4f}, "
            f"avg_f1={results['average_f1_score']:.4f}"
        )

        return BatchEvaluationResponse(**results)

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"批量评估失败: {str(e)}\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"批量评估失败: {str(e)}")


@router.get("/report")
async def get_evaluation_report(
    query: str,
    retrieved_docs: List[str],
    ground_truth_docs: List[str],
    use_ai_rating: bool = False
):
    """
    获取格式化的评估报告（纯文本格式）
    """
    try:
        # 获取 LLM 服务
        llm_service = get_llm_service() if use_ai_rating else None

        # 创建评估服务
        evaluation_service = EvaluationService(llm_service=llm_service)

        # 执行评估
        result = evaluation_service.evaluate_retrieval(
            query=query,
            retrieved_docs=retrieved_docs,
            ground_truth_docs=ground_truth_docs,
            use_ai_rating=use_ai_rating
        )

        # 生成报告
        report = evaluation_service.format_evaluation_report(result)

        return {
            "report": report,
            "metrics": {
                "precision": result.precision,
                "recall": result.recall,
                "f1_score": result.f1_score
            }
        }

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"生成报告失败: {str(e)}\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")
