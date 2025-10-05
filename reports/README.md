# SWE-bench Enhanced Analysis Reports

本目录包含Claude Sonnet 4.5增强版在SWE-bench_Lite_oracle数据集上的完整评估报告。

## 📁 文件清单

### 核心报告
- **comprehensive_analysis_report.md** - 人类可读的综合分析报告（推荐阅读）
- **comprehensive_analysis_report.json** - 机器可读的完整分析数据
- **claude-sonnet-4-5.claude-sonnet-4-5-test.json** - SWE-bench官方评估结果

### 日志文件
- **evaluation_claude-sonnet-4-5-test.log** - 评估执行日志

## 🎯 快速查看

### Executive Summary
```
Model: claude-sonnet-4-5
Success Rate: 100.0%
Average Cost: $0.0890
Average Latency: 22.3s
Cache Efficiency: 100.0%
```

### 关键指标
- ✅ **解决率**: 1/1 (100%)
- 💰 **成本**: $0.089/instance
- ⏱️ **延迟**: 22.3秒/instance
- 🔄 **重试率**: 0% (首次成功)
- 📦 **缓存命中**: 100%

## 📊 报告内容

### comprehensive_analysis_report.md 包含:

1. **字段清单** - prediction文件中的所有可用字段
   - 13个唯一字段
   - 标准schema映射
   - 增强metadata结构

2. **评估结果** - SWE-bench测试结果
   - 已解决/未解决实例
   - 错误分析
   - 空补丁统计

3. **派生指标** - 从原始数据计算
   - 成本分析（总计/平均/中位数/P95）
   - 延迟分析
   - 补丁大小统计

4. **Agent专属指标** - 多步交互分析
   - 重试分析
   - 验证错误
   - 交互轮次
   - 增强功能使用

5. **质量指标** - Token使用与缓存
   - Cache creation tokens
   - Cache read tokens
   - 缓存命中率
   - Token节省量

6. **资源效率** - 成本与时间
   - 每补丁成本
   - 每轮次成本
   - 每轮次延迟

7. **实例详情** - 每个instance的具体数据
   - Cost, latency, patch size
   - Attempts, turns, errors

8. **快速命令** - jq命令示例
   - 字段抽取
   - 统计计算
   - 错误查询

9. **建议** - 基于分析的推荐

## 🔍 使用方式

### 查看人类可读报告
```bash
cat reports/comprehensive_analysis_report.md
```

### 查询JSON数据
```bash
# 查看总览
jq '.summary' reports/comprehensive_analysis_report.json

# 查看成本分析
jq '.prediction_analysis.derived_metrics.cost_analysis' reports/comprehensive_analysis_report.json

# 查看agent指标
jq '.prediction_analysis.agent_metrics' reports/comprehensive_analysis_report.json

# 查看实例详情
jq '.prediction_analysis.per_instance_details[]' reports/comprehensive_analysis_report.json
```

### 查看官方评估结果
```bash
jq '.' reports/claude-sonnet-4-5.claude-sonnet-4-5-test.json
```

## 📈 数据结构

### comprehensive_analysis_report.json 结构:
```
{
  "summary": {           // 执行总览
    "model": "...",
    "success_rate": "...",
    "avg_cost": "...",
    ...
  },
  "prediction_analysis": {
    "basic_info": {...},           // 基本信息
    "field_inventory": {...},      // 字段清单
    "original_fields": {...},      // 标准映射
    "derived_metrics": {...},      // 派生指标
    "agent_metrics": {...},        // Agent指标
    "quality_metrics": {...},      // 质量指标
    "resource_metrics": {...},     // 资源指标
    "per_instance_details": [...]  // 实例详情
  },
  "evaluation_results": {...},     // 评估结果
  "combined_metrics": {...}        // 综合指标
}
```

## 🔗 相关文档

- [SWE-bench官方文档](https://github.com/princeton-nlp/SWE-bench)
- [Claude Code集成指南](../docs/guides/claude_code_integration.md)
- [增强功能说明](../ENHANCED_RUN_API_GUIDE.md)

## 📝 字段参考

### 原始字段（predictions.jsonl）
- `instance_id` - 实例标识
- `model_name_or_path` - 模型名称
- `model_patch` - 生成的补丁
- `full_output` - 完整输出
- `latency_ms` - 延迟（毫秒）
- `cost` - 成本（美元）
- `claude_code_meta` - 增强metadata
  - `enhanced` - 是否启用增强模式
  - `tools_available` - 工具可用性
  - `repo_path` - 仓库路径
  - `attempts` - 尝试次数
  - `validation_errors` - 验证错误列表
  - `response_data` - 响应详情
    - `num_turns` - 交互轮次
    - `usage` - Token使用
      - `cache_creation_input_tokens`
      - `cache_read_input_tokens`
      - `input_tokens`
      - `output_tokens`

### 派生指标
- `success_rate` - 成功率
- `cache_hit_rate` - 缓存命中率
- `cost_per_patch` - 每补丁成本
- `cost_per_turn` - 每轮次成本
- `first_attempt_success_rate` - 首次成功率

## 🔄 重新生成报告

```bash
python3 scripts/comprehensive_analysis.py
```

脚本会自动：
1. 读取predictions.jsonl
2. 读取evaluation JSON
3. 分析所有字段和指标
4. 生成markdown和JSON报告
5. 保存到reports目录

---

**生成时间**: 2025-10-04  
**分析工具**: scripts/comprehensive_analysis.py  
**数据版本**: claude-sonnet-4-5 test run
