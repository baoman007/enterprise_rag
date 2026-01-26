#!/usr/bin/env python3
"""
LLM 服务 - 根据检索到的内容生成答案
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """大语言模型服务（基于规则的答案生成）"""
    
    def __init__(self):
        """初始化 LLM 服务"""
        self.prompt_template = """你是一个专业的医疗助手。请基于以下参考文档回答用户的问题。

参考文档：
{context}

用户问题：{query}

请根据参考文档提供准确、专业的医疗建议。如果文档中没有相关信息，请诚实告知用户。
答案应该：
1. 结构清晰，易于理解
2. 基于提供的参考文档
3. 适当使用分级列表或要点
4. 包含具体的数值或建议
"""
    
    def generate_answer(
        self,
        query: str,
        context_docs: List[str],
        patient_profile: Dict = None
    ) -> str:
        """
        根据检索到的文档生成答案
        
        Args:
            query: 用户问题
            context_docs: 检索到的相关文档列表
            patient_profile: 患者信息（可选）
            
        Returns:
            生成的答案
        """
        # 构建上下文
        context = "\n\n".join([f"[文档 {i+1}]\n{doc}" for i, doc in enumerate(context_docs)])
        
        # 添加患者信息到提示
        if patient_profile:
            patient_info = f"\n\n患者信息：年龄{patient_profile.get('age')}岁，{patient_profile.get('gender', '')}"
            if patient_profile.get('medical_history'):
                patient_info += f"，既往史：{', '.join(patient_profile['medical_history'])}"
            if patient_profile.get('current_medications'):
                patient_info += f"，当前用药：{', '.join(patient_profile['current_medications'])}"
            context += patient_info
        
        # 构建完整提示
        prompt = self.prompt_template.format(
            context=context,
            query=query
        )
        
        # 基于规则生成答案（简化版本，实际应调用 LLM API）
        answer = self._generate_rule_based_answer(query, context_docs)
        
        logger.info(f"生成答案: {query[:50]}...")
        
        return answer
    
    def _generate_rule_based_answer(self, query: str, context_docs: List[str]) -> str:
        """
        基于规则生成答案（模拟 LLM 输出）
        
        Args:
            query: 用户问题
            context_docs: 相关文档
            
        Returns:
            答案文本
        """
        # 合并所有相关文档
        all_context = " ".join(context_docs)
        
        # 简单的关键词匹配和答案生成
        answer_parts = []
        
        # 提取关键信息
        if "高血压" in query and "饮食" in query:
            if "盐" in all_context:
                answer_parts.append("1. **限制钠盐摄入**：每日盐摄入量应控制在5g以下")
            if "钾" in all_context:
                answer_parts.append("2. **增加钾摄入**：多吃香蕉、土豆、菠菜等富含钾的食物")
            if "脂肪" in all_context or "油" in all_context:
                answer_parts.append("3. **控制脂肪**：减少饱和脂肪酸，选择橄榄油等不饱和脂肪")
        
        elif "糖尿病" in query and "饮食" in query:
            if "糖" in all_context or "碳水化合物" in all_context:
                answer_parts.append("1. **控制碳水化合物摄入**：选择低升糖指数(GI)食物")
            if "纤维" in all_context:
                answer_parts.append("2. **增加膳食纤维**：多吃蔬菜、全谷物")
        
        elif "冠心病" in query or "心脏" in query:
            # 检查是否询问心脏结构
            if "结构" in query or "腔室" in query or "心房" in query or "心室" in query:
                answer_parts.append("**心脏结构**：")
                for doc in context_docs:
                    if "心脏" in doc and ("腔室" in doc or "心房" in doc or "心室" in doc):
                        answer_parts.append(f"- {doc}")
            # 检查是否询问心脏功能
            elif "功能" in query or "泵血" in query or "心动周期" in query:
                answer_parts.append("**心脏功能**：")
                for doc in context_docs:
                    if "心脏" in doc and ("功能" in doc or "泵" in doc or "收缩" in doc or "舒张" in doc or "心动周期" in doc):
                        answer_parts.append(f"- {doc}")
            # 症状相关
            elif "症状" in all_context or "胸痛" in all_context:
                answer_parts.append("**早期症状**：胸痛、胸闷、呼吸困难、心悸")
            # 预防相关
            if "预防" in all_context and ("预防" not in query or "症状" not in query):
                answer_parts.append("**预防措施**：控制血压、血脂、血糖，戒烟限酒")
        
        # 如果没有匹配到特定模式，返回摘要
        if not answer_parts and context_docs:
            # 提取前几段作为答案，智能合并相关内容
            answer_parts.append("根据相关文档：")
            # 合并相似的文档段落
            merged_content = []
            for i, doc in enumerate(context_docs[:5], 1):
                doc = doc.strip()
                if doc and doc not in merged_content:
                    merged_content.append(doc)
                    # 限制每段长度
                    if len(doc) > 200:
                        doc = doc[:200] + "..."
                    answer_parts.append(f"{i}. {doc}")
        
        if not answer_parts:
            answer_parts.append("抱歉，在当前知识库中没有找到相关的医疗建议。建议您咨询专业医生。")
        
        # 添加免责声明
        answer_parts.append("\n\n**温馨提示**：以上内容仅供参考，具体治疗方案请以医生面诊为准。")
        
        return "\n\n".join(answer_parts)
    
    def calculate_confidence(self, query: str, context_docs: List[str], distances: List[float]) -> float:
        """
        计算答案置信度
        
        Args:
            query: 用户问题
            context_docs: 相关文档
            distances: 向量距离
            
        Returns:
            置信度 (0-1)
        """
        if not distances:
            return 0.0
        
        # 基于最小距离计算置信度
        min_distance = min(distances)
        
        # 距离越小，相似度越高
        # ChromaDB 默认使用余弦距离，范围是 [0, 2]
        # 转换为相似度：1 - distance / 2
        similarity = max(0.0, 1.0 - min_distance / 2.0)
        
        # 如果有多个高质量匹配，提高置信度
        high_quality_matches = sum(1 for d in distances if d < 0.5)
        if high_quality_matches >= 2:
            similarity = min(1.0, similarity + 0.1)
        
        return round(similarity, 2)


# 全局实例
_llm_service = None


def get_llm_service() -> LLMService:
    """获取 LLM 服务实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
