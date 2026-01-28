# RAG 系统评估指南

## 概述

本评估工具用于评估 RAG（检索增强生成）系统的检索质量，计算 **Precision（精确率）**、**Recall（召回率）** 和 **F1-Score**，并支持使用 AI 进行辅助评分。

## 评估指标说明

### 1. Precision（精确率）

**定义**：检索到的相关文档数 / 检索到的总文档数

**含义**：表示检索结果中有多少是真正相关的文档

**公式**：
```
Precision = |Retrieved ∩ Relevant| / |Retrieved|
```

**示例**：
- 检索到 10 个文档
- 其中 8 个是相关的
- Precision = 8/10 = 0.8 (80%)

**适用场景**：
- 关注结果质量，希望检索结果尽可能准确
- 不希望出现不相关的结果
- 适用于推荐系统、搜索引擎等

### 2. Recall（召回率）

**定义**：检索到的相关文档数 / 真实相关文档总数

**含义**：表示真实相关的文档中有多少被检索到了

**公式**：
```
Recall = |Retrieved ∩ Relevant| / |Relevant|
```

**示例**：
- 真实相关文档有 20 个
- 检索到了其中的 12 个
- Recall = 12/20 = 0.6 (60%)

**适用场景**：
- 关注覆盖率，希望尽可能找到所有相关文档
- 不遗漏重要信息
- 适用于医学检索、法律检索等领域

### 3. F1-Score

**定义**：Precision 和 Recall 的调和平均数

**含义**：综合评价指标，平衡精确率和召回率

**公式**：
```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**适用场景**：
- 需要同时考虑精确率和召回率
- 寻找最佳平衡点
- 数据集类别不平衡时

## API 使用

### 单次评估

**端点**：`POST /api/v1/evaluation/retrieval`

**请求示例**：
```json
{
  "query": "高血压患者的饮食建议",
  "retrieved_docs": [
    "高血压患者应限制钠盐摄入，每日盐摄入量控制在5g以下",
    "高血压患者应增加钾摄入，多吃香蕉、土豆、菠菜等",
    "糖尿病患者需要注意饮食控制，选择低GI食物",
    "高血压患者应控制脂肪摄入，减少饱和脂肪酸",
    "建议所有成年人每周运动150分钟"
  ],
  "ground_truth_docs": [
    "高血压患者应限制钠盐摄入，每日盐摄入量控制在5g以下",
    "高血压患者应增加钾摄入，多吃香蕉、土豆、菠菜等",
    "高血压患者应控制脂肪摄入，减少饱和脂肪酸",
    "高血压患者应戒烟限酒，保持健康生活方式"
  ],
  "use_ai_rating": false
}
```

**响应示例**：
```json
{
  "query": "高血压患者的饮食建议",
  "retrieved_docs_count": 5,
  "ground_truth_docs_count": 4,
  "relevant_retrieved_count": 3,
  "missed_docs_count": 1,
  "precision": 0.6,
  "recall": 0.75,
  "f1_score": 0.6667,
  "relevant_retrieved_docs": [
    "高血压患者应限制钠盐摄入，每日盐摄入量控制在5g以下",
    "高血压患者应增加钾摄入，多吃香蕉、土豆、菠菜等",
    "高血压患者应控制脂肪摄入，减少饱和脂肪酸"
  ],
  "missed_docs": [
    "高血压患者应戒烟限酒，保持健康生活方式"
  ]
}
```

### 批量评估

**端点**：`POST /api/v1/evaluation/batch`

**请求示例**：
```json
{
  "test_cases": [
    {
      "query": "高血压饮食建议",
      "retrieved_docs": ["文档1", "文档2", "文档3"],
      "ground_truth_docs": ["文档1", "文档2", "文档4"]
    },
    {
      "query": "糖尿病预防",
      "retrieved_docs": ["文档5", "文档6"],
      "ground_truth_docs": ["文档5", "文档6", "文档7"]
    }
  ],
  "use_ai_rating": false
}
```

**响应示例**：
```json
{
  "total_cases": 2,
  "average_precision": 0.75,
  "average_recall": 0.625,
  "average_f1_score": 0.6786,
  "detailed_results": [...]
}
```

### 获取评估报告

**端点**：`GET /api/v1/evaluation/report`

**参数**：
- `query`: 查询问题
- `retrieved_docs`: 检索到的文档（数组，URL 编码）
- `ground_truth_docs`: 真实相关文档（数组，URL 编码）
- `use_ai_rating`: 是否使用 AI 评分

## Python 脚本测试

使用提供的测试脚本：

```bash
python test_evaluation.py
```

该脚本会运行三个测试：
1. 单次检索评估
2. 批量评估
3. 生成评估报告

## Web 界面

访问 `http://localhost:8000/static/evaluation.html` 使用可视化评估界面。

界面功能：
- 输入查询问题
- 输入检索到的文档（每行一个）
- 输入真实相关文档（标准答案）
- 可选择使用 AI 辅助评分
- 查看评估结果，包括：
  - Precision、Recall、F1-Score
  - 检索统计
  - 相关文档列表
  - 遗漏文档列表
  - AI 评分和评论

## AI 辅助评分

启用 AI 辅助评分后，系统会：

1. **相关性标注**：对每个检索到的文档判断是否相关
2. **总体评分**：给出评分（优秀/良好/中等/较差/很差）
3. **详细评论**：说明评分理由，指出优点和不足

### 使用方法

在请求中设置 `use_ai_rating: true`，或在 Web 界面中勾选"使用 AI 辅助评分"。

### AI 评分输出

```json
{
  "relevance_labels": {
    "文档 1": true,
    "文档 2": false,
    ...
  },
  "rating": "良好",
  "comment": "检索结果整体质量良好。检索到了3个相关文档，覆盖了查询的核心内容。但部分文档与查询相关性较低，可以进一步优化检索算法。"
}
```

## 最佳实践

### 1. 构建 Ground Truth 数据

- 由领域专家标注
- 涵盖多种查询类型（简单、复杂、多意图）
- 平衡正例和负例
- 定期更新和维护

### 2. 评估流程

1. **准备测试集**：收集多样化的查询
2. **标注 Ground Truth**：人工标注相关文档
3. **运行评估**：使用评估工具计算指标
4. **分析结果**：识别问题并优化
5. **迭代改进**：持续优化检索系统

### 3. 指标解释

- **Precision 高，Recall 低**：检索结果很准确，但可能遗漏了相关文档
- **Precision 低，Recall 高**：检索到很多文档，但其中很多不相关
- **两者都高**：检索系统质量好
- **两者都低**：检索系统需要改进

### 4. 优化建议

- **提高 Precision**：
  - 提高相似度阈值
  - 优化嵌入模型
  - 添加重排序机制

- **提高 Recall**：
  - 降低相似度阈值
  - 增加 Top-K 数量
  - 扩充知识库

- **平衡两者**：
  - 调整相似度阈值
  - 使用混合检索策略
  - 实施查询扩展

## 常见问题

### Q1: 如何确定合理的阈值？

A: 根据业务需求调整：
- 医学领域：优先保证 Recall（不遗漏重要信息）
- 推荐系统：优先保证 Precision（提高用户满意度）

### Q2: AI 评分可靠吗？

A: AI 评分提供参考，但不应完全依赖。建议：
- 结合人工评估
- 使用多个 AI 评分器取平均
- 定期校准 AI 评分标准

### Q3: 如何处理文档长度差异？

A: 建议：
- 标准化文档长度
- 使用语义相似度而非字符串匹配
- 考虑文档片段级别评估

### Q4: 评估数据需要多少？

A: 建议：
- 最少 50-100 个查询
- 涵盖不同类型和难度
- 定期更新测试集

## 技术实现

评估服务位于 `api/services/evaluation_service.py`，提供以下功能：

- `EvaluationService`: 评估服务类
- `calculate_metrics()`: 计算 Precision、Recall、F1-Score
- `evaluate_retrieval()`: 评估单次检索
- `batch_evaluate()`: 批量评估
- `_ai_evaluate()`: AI 辅助评分

评估 API 位于 `api/routers/evaluation.py`，提供三个端点：

- `POST /api/v1/evaluation/retrieval`: 单次评估
- `POST /api/v1/evaluation/batch`: 批量评估
- `GET /api/v1/evaluation/report`: 获取报告

## 联系与反馈

如有问题或建议，请联系开发团队。
