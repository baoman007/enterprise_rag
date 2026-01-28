#!/usr/bin/env python3
"""
评估服务 - 计算 recall、precision，并使用 AI 进行辅助标注
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import re

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """评估结果"""
    query: str
    retrieved_docs: List[str]
    ground_truth_docs: List[str]
    relevant_retrieved: List[str]  # 检索到的相关文档
    missed_docs: List[str]  # 未检索到的相关文档
    precision: float
    recall: float
    f1_score: float
    ai_rating: Optional[str] = None  # AI 评分
    ai_comment: Optional[str] = None  # AI 评论
    ai_relevance_labels: Optional[Dict[str, bool]] = None  # AI 对每个文档的相关性标注


class EvaluationService:
    """评估服务"""

    def __init__(self, llm_service=None):
        """
        初始化评估服务

        Args:
            llm_service: 可选的 LLM 服务，用于 AI 评分
        """
        self.llm_service = llm_service

    def calculate_metrics(
        self,
        retrieved_docs: List[str],
        ground_truth_docs: List[str]
    ) -> Tuple[float, float, float]:
        """
        计算 Precision、Recall 和 F1-Score

        Args:
            retrieved_docs: 检索到的文档列表
            ground_truth_docs: 真实相关的文档列表（标准答案）

        Returns:
            (precision, recall, f1_score)
        """
        if not retrieved_docs:
            return 0.0, 0.0, 0.0

        if not ground_truth_docs:
            return 0.0, 0.0, 0.0

        # 计算交集（检索到的且是相关的）
        relevant_retrieved = set(retrieved_docs) & set(ground_truth_docs)
        relevant_count = len(relevant_retrieved)

        # Precision = 检索到的相关文档数 / 检索到的总文档数
        precision = relevant_count / len(retrieved_docs) if retrieved_docs else 0.0

        # Recall = 检索到的相关文档数 / 真实相关文档总数
        recall = relevant_count / len(ground_truth_docs) if ground_truth_docs else 0.0

        # F1-Score = 2 * (precision * recall) / (precision + recall)
        if precision + recall == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)

        return precision, recall, f1_score

    def evaluate_retrieval(
        self,
        query: str,
        retrieved_docs: List[str],
        ground_truth_docs: List[str],
        use_ai_rating: bool = False
    ) -> EvaluationResult:
        """
        评估检索结果

        Args:
            query: 查询问题
            retrieved_docs: 检索到的文档列表
            ground_truth_docs: 真实相关的文档列表
            use_ai_rating: 是否使用 AI 进行评分

        Returns:
            EvaluationResult: 评估结果
        """
        # 计算基本指标
        precision, recall, f1_score = self.calculate_metrics(
            retrieved_docs,
            ground_truth_docs
        )

        # 找出相关文档和遗漏文档
        relevant_retrieved = list(set(retrieved_docs) & set(ground_truth_docs))
        missed_docs = list(set(ground_truth_docs) - set(retrieved_docs))

        # 构建 EvaluationResult
        result = EvaluationResult(
            query=query,
            retrieved_docs=retrieved_docs,
            ground_truth_docs=ground_truth_docs,
            relevant_retrieved=relevant_retrieved,
            missed_docs=missed_docs,
            precision=precision,
            recall=recall,
            f1_score=f1_score
        )

        # 如果启用 AI 评分
        if use_ai_rating and self.llm_service:
            result.ai_rating, result.ai_comment, result.ai_relevance_labels = \
                self._ai_evaluate(query, retrieved_docs, ground_truth_docs)

        return result

    def _ai_evaluate(
        self,
        query: str,
        retrieved_docs: List[str],
        ground_truth_docs: List[str]
    ) -> Tuple[str, str, Dict[str, bool]]:
        """
        使用 AI 评估检索质量

        Args:
            query: 查询问题
            retrieved_docs: 检索到的文档
            ground_truth_docs: 真实相关文档

        Returns:
            (rating, comment, relevance_labels)
        """
        try:
            # 构建 AI 评估 prompt
            prompt = self._build_evaluation_prompt(
                query,
                retrieved_docs,
                ground_truth_docs
            )

            # 调用 LLM
            response = self.llm_service._generate_raw_answer(prompt)

            # 解析响应
            return self._parse_ai_response(response)

        except Exception as e:
            logger.error(f"AI 评估失败: {str(e)}")
            return "N/A", f"AI 评估失败: {str(e)}", {}

    def _build_evaluation_prompt(
        self,
        query: str,
        retrieved_docs: List[str],
        ground_truth_docs: List[str]
    ) -> str:
        """构建 AI 评估 prompt"""
        prompt = f"""你是一个专业的信息检索评估专家。请评估以下检索结果的质量。

**查询问题：**
{query}

**检索到的文档（{len(retrieved_docs)} 个）：**
"""
        for i, doc in enumerate(retrieved_docs, 1):
            prompt += f"\n[文档 {i}] {doc}\n"

        prompt += f"\n**真实相关文档（{len(ground_truth_docs)} 个）：**\n"
        for i, doc in enumerate(ground_truth_docs, 1):
            prompt += f"\n[文档 {i}] {doc}\n"

        prompt += """
请从以下几个维度进行评估：

1. **相关性标注**：对于每个检索到的文档，判断它是否与查询相关（true/false）
2. **总体评分**：根据检索质量给出评分（优秀/良好/中等/较差/很差）
3. **详细评论**：说明评分理由，指出优点和不足

请按以下 JSON 格式输出（只返回 JSON，不要其他内容）：
{
  "relevance_labels": {
    "文档 1": true,
    "文档 2": false,
    ...
  },
  "rating": "优秀",
  "comment": "详细评论内容..."
}
"""

        return prompt

    def _parse_ai_response(self, response: str) -> Tuple[str, str, Dict[str, bool]]:
        """解析 AI 响应"""
        try:
            # 尝试提取 JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return "N/A", "AI 返回格式错误", {}

            data = json.loads(json_match.group())

            rating = data.get("rating", "N/A")
            comment = data.get("comment", "")
            relevance_labels = data.get("relevance_labels", {})

            return rating, comment, relevance_labels

        except Exception as e:
            logger.error(f"解析 AI 响应失败: {str(e)}")
            return "N/A", f"解析失败: {str(e)}", {}

    def batch_evaluate(
        self,
        test_cases: List[Dict],
        use_ai_rating: bool = False
    ) -> Dict:
        """
        批量评估

        Args:
            test_cases: 测试用例列表，每个用例包含：
                - query: 查询问题
                - retrieved_docs: 检索到的文档
                - ground_truth_docs: 真实相关文档
            use_ai_rating: 是否使用 AI 评分

        Returns:
            汇总统计结果
        """
        results = []
        total_precision = 0.0
        total_recall = 0.0
        total_f1 = 0.0

        for case in test_cases:
            result = self.evaluate_retrieval(
                query=case['query'],
                retrieved_docs=case['retrieved_docs'],
                ground_truth_docs=case['ground_truth_docs'],
                use_ai_rating=use_ai_rating
            )
            results.append(result)

            total_precision += result.precision
            total_recall += result.recall
            total_f1 += result.f1_score

        count = len(test_cases)
        if count > 0:
            avg_precision = total_precision / count
            avg_recall = total_recall / count
            avg_f1 = total_f1 / count
        else:
            avg_precision = avg_recall = avg_f1 = 0.0

        return {
            "total_cases": count,
            "average_precision": round(avg_precision, 4),
            "average_recall": round(avg_recall, 4),
            "average_f1_score": round(avg_f1, 4),
            "detailed_results": [
                {
                    "query": r.query,
                    "precision": round(r.precision, 4),
                    "recall": round(r.recall, 4),
                    "f1_score": round(r.f1_score, 4),
                    "ai_rating": r.ai_rating,
                    "ai_comment": r.ai_comment,
                    "relevant_count": len(r.relevant_retrieved),
                    "missed_count": len(r.missed_docs)
                }
                for r in results
            ]
        }

    def format_evaluation_report(self, result: EvaluationResult) -> str:
        """格式化评估报告"""
        report = f"""
{'='*60}
检索结果评估报告
{'='*60}

查询问题：{result.query}

检索统计：
- 检索到文档数：{len(result.retrieved_docs)}
- 真实相关文档数：{len(result.ground_truth_docs)}
- 检索到且相关：{len(result.relevant_retrieved)}
- 未检索到的相关文档：{len(result.missed_docs)}

评估指标：
- Precision（精确率）：{result.precision:.4f} ({result.precision*100:.2f}%)
- Recall（召回率）：{result.recall:.4f} ({result.recall*100:.2f}%)
- F1-Score：{result.f1_score:.4f} ({result.f1_score*100:.2f}%)
"""

        if result.ai_rating:
            report += f"""
AI 评估：
- AI 评分：{result.ai_rating}
- AI 评论：{result.ai_comment}
"""

            if result.ai_relevance_labels:
                report += f"\nAI 相关性标注：\n"
                for doc, is_relevant in result.ai_relevance_labels.items():
                    status = "✓ 相关" if is_relevant else "✗ 不相关"
                    report += f"  {status}\n"

        report += f"\n{'='*60}\n"

        return report
