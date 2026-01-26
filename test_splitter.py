#!/usr/bin/env python3
"""
测试文本切分器
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.services.text_splitter import TextSplitter

# 测试文本：模拟PDF提取的格式（包含换行符问题）
test_text = """
心脏是一个拳头大小的肌肉器官，位于胸腔中部偏左。它由四个腔室组成： - 左心房 和 左心
室 ：负责将富含氧气的血液泵送到全身 - 右心房 和 右心室 ：负责将缺氧的血液泵送到肺部进行
氧交换。

心脏通过有节奏的收缩和舒张来泵血，这个过程称为心动周期。正常成年人的心率在 60-100
次/分钟之间。

冠心病的早期症状包括胸痛、胸闷、呼吸困难。

二级预防（防止疾病进展）
阿司匹林  - 作用：防止血栓形成 - 用法：通常 75-100 mg / 天 - 注意事项：注意出血风险

推荐食物：
- 蔬菜：菠菜、西兰花、胡萝卜
- 水果：苹果、橙子、蓝莓
- 全谷物：燕麦、糙米、全麦面包
"""

def main():
    print("=" * 80)
    print("测试智能文本切分器")
    print("=" * 80)

    splitter = TextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_text(test_text)

    print(f"\n原始文本长度: {len(test_text)} 字符")
    print(f"切分后段落数: {len(chunks)}")
    print("\n" + "=" * 80)
    print("切分结果：")
    print("=" * 80)

    for i, chunk in enumerate(chunks, 1):
        print(f"\n【段落 {i}】({len(chunk)} 字符)")
        print("-" * 80)
        print(chunk)
        print("-" * 80)

    # 验证是否包含完整的句子
    print("\n" + "=" * 80)
    print("验证检查：")
    print("=" * 80)

    broken_sentences = 0
    for i, chunk in enumerate(chunks, 1):
        # 检查段落是否以不完整的句子结尾
        last_char = chunk.strip()[-1] if chunk.strip() else ''
        if last_char not in ['。', '！', '？', '；', '，', '、']:
            # 检查是否被截断（例如："左心房 和 左心"）
            if any(keyword in chunk for keyword in ['左心房', '左心室', '右心房', '右心室']):
                print(f"❌ 段落 {i} 可能存在语义断裂")
                print(f"   结尾: ...{chunk[-50:]}")
                broken_sentences += 1

    if broken_sentences == 0:
        print("✅ 所有段落语义完整，无明显断裂！")
    else:
        print(f"⚠️  发现 {broken_sentences} 个可能存在语义断裂的段落")

if __name__ == "__main__":
    main()
