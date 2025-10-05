#!/bin/bash

# 配置参数
PREDICTIONS_PATH="/home/shared/zqq/SWE4CC/results/claude-3.5-sonnet__SWE-bench_Lite_oracle__test.jsonl"
REPORT_DIR="/home/shared/zqq/SWE4CC/reports"
RUN_ID="claude-3.5-sonnet-batch"
BATCH_SIZE=2  # 每批处理2个实例（小批次）
MAX_WORKERS=2  # 降低并发
TEMP_DIR="/home/shared/zqq/SWE4CC/temp_batches"
MIN_DISK_GB=5  # 最小磁盘空间阈值（GB）

# 创建目录
mkdir -p "$TEMP_DIR"
mkdir -p "$REPORT_DIR"

# 磁盘检查函数
check_disk_space() {
    local available_gb=$(df /home | awk 'NR==2 {print int($4/1024/1024)}')
    echo "当前可用磁盘空间: ${available_gb}GB"

    if [ "$available_gb" -lt "$MIN_DISK_GB" ]; then
        echo "⚠️  警告: 可用磁盘空间不足 ${MIN_DISK_GB}GB，触发紧急清理..."
        cleanup_docker

        available_gb=$(df /home | awk 'NR==2 {print int($4/1024/1024)}')
        if [ "$available_gb" -lt "$MIN_DISK_GB" ]; then
            echo "❌ 错误: 清理后磁盘空间仍不足，脚本暂停"
            exit 1
        fi
    fi
}

# Docker 清理函数
cleanup_docker() {
    echo "开始清理 Docker 资源..."

    # 停止并删除所有相关容器
    echo "  - 停止并删除容器..."
    docker ps -aq | xargs -r docker stop 2>/dev/null
    docker ps -aq | xargs -r docker rm -f 2>/dev/null

    # 删除 dangling 镜像
    echo "  - 删除 dangling 镜像..."
    docker images -f "dangling=true" -q | xargs -r docker rmi -f 2>/dev/null

    # 清理构建缓存
    echo "  - 清理构建缓存..."
    docker builder prune -af 2>/dev/null

    # 清理未使用的网络
    echo "  - 清理未使用的网络..."
    docker network prune -f 2>/dev/null

    # 清理未使用的卷
    echo "  - 清理未使用的卷..."
    docker volume prune -f 2>/dev/null

    echo "✓ Docker 清理完成"
}

# 批次专用清理函数（删除本批次构建的镜像，但保留基础镜像）
cleanup_batch_images() {
    local instance_ids="$1"
    echo "清理本批次镜像（保留基础镜像）..."

    for instance_id in $instance_ids; do
        # 查找并删除与该 instance_id 相关的镜像（排除 sweb.base 基础镜像）
        local images=$(docker images | grep "$instance_id" | grep -v "sweb.base" | awk '{print $3}')
        if [ -n "$images" ]; then
            echo "  - 删除 $instance_id 相关镜像"
            echo "$images" | xargs -r docker rmi -f 2>/dev/null
        fi
    done

    # 停止并删除容器
    docker ps -aq | xargs -r docker rm -f 2>/dev/null

    # 仅清理 dangling 镜像（不清理基础镜像）
    docker images -f "dangling=true" -q | xargs -r docker rmi -f 2>/dev/null

    # 轻度清理构建缓存（不使用 -a，避免删除可复用的层）
    docker builder prune -f 2>/dev/null

    echo "✓ 批次镜像清理完成"
}

# 初始清理，确保干净环境
echo "========================================="
echo "初始化: 清理旧的 Docker 资源"
echo "========================================="
cleanup_docker

# 获取总行数
TOTAL_LINES=$(wc -l < "$PREDICTIONS_PATH")
echo "总共 $TOTAL_LINES 个实例需要评估"
echo "每批处理 $BATCH_SIZE 个实例"

# 分批处理
CURRENT_LINE=1
BATCH_NUM=1

while [ $CURRENT_LINE -le $TOTAL_LINES ]; do
    echo ""
    echo "========================================="
    echo "处理第 $BATCH_NUM 批 (实例 $CURRENT_LINE - $((CURRENT_LINE + BATCH_SIZE - 1)))"
    echo "========================================="

    # 批次开始前检查磁盘
    check_disk_space

    # 提取当前批次
    BATCH_FILE="$TEMP_DIR/batch_${BATCH_NUM}.jsonl"
    sed -n "${CURRENT_LINE},$((CURRENT_LINE + BATCH_SIZE - 1))p" "$PREDICTIONS_PATH" > "$BATCH_FILE"

    # 提取 instance_ids
    INSTANCE_IDS=$(jq -r '.instance_id' "$BATCH_FILE" | tr '\n' ' ')
    echo "本批次实例: $INSTANCE_IDS"

    # 构建镜像
    echo "步骤 1/3: 构建 Docker 镜像..."
    python swebench/harness/prepare_images.py \
        --instance_ids $INSTANCE_IDS \
        --max_workers "$MAX_WORKERS" \
        --env_image_tag 1776 \
        --tag latest

    if [ $? -ne 0 ]; then
        echo "❌ 镜像构建失败，清理后继续下一批..."
        cleanup_batch_images "$INSTANCE_IDS"
        CURRENT_LINE=$((CURRENT_LINE + BATCH_SIZE))
        BATCH_NUM=$((BATCH_NUM + 1))
        continue
    fi

    # 运行评估
    echo "步骤 2/3: 运行评估..."
    python swebench/harness/run_evaluation.py \
        --predictions_path "$BATCH_FILE" \
        --max_workers "$MAX_WORKERS" \
        --run_id "${RUN_ID}_${BATCH_NUM}" \
        --report_dir "$TEMP_DIR"

    # 步骤 3: 立即清理本批次镜像和资源
    echo "步骤 3/3: 清理本批次 Docker 资源..."
    cleanup_batch_images "$INSTANCE_IDS"

    # 删除临时批次文件
    rm -f "$BATCH_FILE"

    echo "✓ 批次 $BATCH_NUM 完成并清理"

    # 更新计数器
    CURRENT_LINE=$((CURRENT_LINE + BATCH_SIZE))
    BATCH_NUM=$((BATCH_NUM + 1))

    # 批次间短暂休息，避免系统过载
    sleep 2
done

echo ""
echo "========================================="
echo "所有批次评估完成，开始合并结果..."
echo "========================================="

# 合并结果
python /home/shared/zqq/SWE4CC/analysis/merge_evaluation_results.py \
    --input_dir "$TEMP_DIR" \
    --output_file "$REPORT_DIR/claude-3.5-sonnet.complete-evaluation.json"

echo "完整评估报告已生成: $REPORT_DIR/claude-3.5-sonnet.complete-evaluation.json"

# 最终清理
echo ""
echo "========================================="
echo "执行最终 Docker 清理"
echo "========================================="
cleanup_docker

echo ""
echo "✓ 所有任务完成！"
check_disk_space
