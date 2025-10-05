#!/usr/bin/env python3
"""
合并多个批次的评估结果为一个完整的报告
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict

def merge_results(input_dir, output_file):
    """合并所有批次的评估结果"""
    input_path = Path(input_dir)

    # 查找所有评估结果文件
    result_files = sorted(input_path.glob("*.*.json"))

    if not result_files:
        print(f"错误: 在 {input_dir} 中没有找到评估结果文件")
        return

    print(f"找到 {len(result_files)} 个批次结果文件")

    # 初始化合并后的结果
    merged = {
        "total_instances": 0,
        "submitted_instances": 0,
        "completed_instances": 0,
        "resolved_instances": 0,
        "unresolved_instances": 0,
        "empty_patch_instances": 0,
        "error_instances": 0,
        "completed_ids": [],
        "incomplete_ids": [],
        "empty_patch_ids": [],
        "resolved_ids": [],
        "unresolved_ids": [],
        "error_ids": [],
        "submitted_ids": [],
        "schema_version": 2
    }

    # 合并所有批次
    for result_file in result_files:
        print(f"处理: {result_file.name}")
        with open(result_file, 'r') as f:
            batch_result = json.load(f)

        # 累加计数
        merged["submitted_instances"] += batch_result.get("submitted_instances", 0)
        merged["completed_instances"] += batch_result.get("completed_instances", 0)
        merged["resolved_instances"] += batch_result.get("resolved_instances", 0)
        merged["unresolved_instances"] += batch_result.get("unresolved_instances", 0)
        merged["empty_patch_instances"] += batch_result.get("empty_patch_instances", 0)
        merged["error_instances"] += batch_result.get("error_instances", 0)

        # 合并 ID 列表
        for key in ["completed_ids", "incomplete_ids", "empty_patch_ids",
                    "resolved_ids", "unresolved_ids", "error_ids", "submitted_ids"]:
            merged[key].extend(batch_result.get(key, []))

    # 设置总实例数
    merged["total_instances"] = merged["submitted_instances"]

    # 保存合并结果
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(merged, f, indent=4)

    print(f"\n合并完成!")
    print(f"总实例数: {merged['total_instances']}")
    print(f"已完成: {merged['completed_instances']}")
    print(f"已解决: {merged['resolved_instances']}")
    print(f"未解决: {merged['unresolved_instances']}")
    print(f"错误: {merged['error_instances']}")
    print(f"\n结果已保存到: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="合并批次评估结果")
    parser.add_argument("--input_dir", required=True, help="包含批次结果的目录")
    parser.add_argument("--output_file", required=True, help="输出的完整结果文件路径")

    args = parser.parse_args()
    merge_results(args.input_dir, args.output_file)
