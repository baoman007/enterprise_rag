#!/usr/bin/env python3
"""
智能文本切分服务 - 用于将长文档切分成语义完整的段落
"""

import re
from typing import List
import logging

logger = logging.getLogger(__name__)


class TextSplitter:
    """智能文本切分器"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = "\n\n"
    ):
        """
        初始化文本切分器

        Args:
            chunk_size: 每个段落的最大字符数
            chunk_overlap: 段落之间的重叠字符数
            separator: 段落分隔符
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def split_text(self, text: str) -> List[str]:
        """
        切分文本为语义完整的段落

        Args:
            text: 原始文本

        Returns:
            切分后的段落列表
        """
        if not text:
            return []

        # 1. 预处理：清理文本
        cleaned_text = self._preprocess_text(text)

        # 2. 按段落切分（多个连续换行符）
        paragraphs = re.split(r'\n{2,}', cleaned_text)

        # 3. 合并过短的段落
        merged_paragraphs = self._merge_short_paragraphs(paragraphs)

        # 4. 处理过长的段落
        final_chunks = []
        for paragraph in merged_paragraphs:
            if len(paragraph) <= self.chunk_size:
                final_chunks.append(paragraph.strip())
            else:
                # 对过长的段落进一步切分
                sub_chunks = self._split_long_paragraph(paragraph)
                final_chunks.extend(sub_chunks)

        # 5. 过滤空段落和过短的段落
        result = [
            chunk for chunk in final_chunks
            if chunk and len(chunk.strip()) > 20
        ]

        logger.info(f"文本切分完成: 原始文本 {len(text)} 字符 -> {len(result)} 个段落")
        return result

    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本：清理多余的空白字符

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 替换多个空格为单个空格
        text = re.sub(r'[ \t]+', ' ', text)

        # 替换多个换行符为单个换行符
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 移除特殊字符
        text = text.replace('\r', '')

        # 移除页码等干扰信息（简单的正则匹配）
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

        return text.strip()

    def _merge_short_paragraphs(self, paragraphs: List[str], min_length: int = 50) -> List[str]:
        """
        合并过短的段落

        Args:
            paragraphs: 段落列表
            min_length: 最小段落长度

        Returns:
            合并后的段落列表
        """
        if not paragraphs:
            return []

        merged = []
        current_paragraph = paragraphs[0].strip()

        for i in range(1, len(paragraphs)):
            next_paragraph = paragraphs[i].strip()

            # 如果当前段落太短，且下一段不是新的标题/列表，则合并
            if (
                len(current_paragraph) < min_length
                and not self._is_heading(next_paragraph)
                and not self._is_list_item(next_paragraph)
            ):
                current_paragraph += ' ' + next_paragraph
            else:
                if current_paragraph:
                    merged.append(current_paragraph)
                current_paragraph = next_paragraph

        # 添加最后一个段落
        if current_paragraph:
            merged.append(current_paragraph)

        return merged

    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """
        切分过长的段落，尽量保持语义完整

        Args:
            paragraph: 过长的段落

        Returns:
            切分后的子段落列表
        """
        chunks = []

        # 尝试按句子切分（中文句子）
        sentences = re.split(r'([。！？\n])', paragraph)

        # 重新组合句子和标点
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
                combined_sentences.append(sentence.strip())
            else:
                combined_sentences.append(sentences[i].strip())

        # 按句子组合成段落
        current_chunk = ""
        for sentence in combined_sentences:
            if not sentence:
                continue

            # 如果添加当前句子后不超过大小限制，则添加
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence
            else:
                # 否则保存当前段落，开始新段落
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # 如果单个句子就超过限制，需要强制切分
                if len(sentence) > self.chunk_size:
                    sub_chunks = self._force_split(sentence, self.chunk_size)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = sentence

        # 添加最后一个段落
        if current_chunk:
            chunks.append(current_chunk.strip())

        # 添加重叠内容
        if self.chunk_overlap > 0:
            chunks = self._add_overlap(chunks, self.chunk_overlap)

        return chunks

    def _force_split(self, text: str, max_length: int) -> List[str]:
        """
        强制切分文本（当单个句子过长时）

        Args:
            text: 文本
            max_length: 最大长度

        Returns:
            切分后的文本列表
        """
        chunks = []
        for i in range(0, len(text), max_length):
            chunk = text[i:i + max_length]
            if chunk:
                chunks.append(chunk)
        return chunks

    def _add_overlap(self, chunks: List[str], overlap: int) -> List[str]:
        """
        在段落之间添加重叠内容

        Args:
            chunks: 段落列表
            overlap: 重叠字符数

        Returns:
            带重叠的段落列表
        """
        if overlap <= 0 or len(chunks) <= 1:
            return chunks

        result = [chunks[0]]
        for i in range(1, len(chunks)):
            # 获取上一个段落的末尾部分
            prev_chunk_end = chunks[i - 1][-overlap:] if len(chunks[i - 1]) > overlap else chunks[i - 1]

            # 添加到当前段落开头
            new_chunk = prev_chunk_end + ' ' + chunks[i]
            result.append(new_chunk)

        return result

    def _is_heading(self, text: str) -> bool:
        """
        判断是否为标题

        Args:
            text: 文本

        Returns:
            是否为标题
        """
        # 简单的标题判断规则
        patterns = [
            r'^第[一二三四五六七八九十\d]+[章节篇]',
            r'^[一二三四五六七八九十]+、',
            r'^\d+[\.\.]',
            r'^[A-Z][A-Z\s]+$',
            r'^【.+】$'
        ]

        for pattern in patterns:
            if re.match(pattern, text.strip()):
                return True

        return False

    def _is_list_item(self, text: str) -> bool:
        """
        判断是否为列表项

        Args:
            text: 文本

        Returns:
            是否为列表项
        """
        patterns = [
            r'^\s*[•·\-]\s+',
            r'^\s*\d+[\.\)]\s+',
            r'^\s*[a-z][\.\)]\s+',
        ]

        for pattern in patterns:
            if re.match(pattern, text.strip()):
                return True

        return False


# 全局实例
_text_splitter = None


def get_text_splitter() -> TextSplitter:
    """获取文本切分器实例"""
    global _text_splitter
    if _text_splitter is None:
        _text_splitter = TextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
    return _text_splitter
