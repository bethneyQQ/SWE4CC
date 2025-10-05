#!/usr/bin/env python3
"""
测试repo cache功能
对比有cache和无cache的性能差异
"""
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from swebench.inference.repo_manager import RepoManager
from datasets import load_dataset


def test_cache_performance():
    """测试cache性能提升"""

    print("=" * 80)
    print("Repo Cache 性能测试")
    print("=" * 80)
    print()

    # Load a few instances from same repo
    dataset = load_dataset('princeton-nlp/SWE-bench_Lite', split='test')

    # Find instances from same repo (django)
    django_instances = [
        item for item in dataset
        if item['repo'] == 'django/django'
    ][:3]

    if len(django_instances) < 3:
        print("⚠️  Not enough django instances for test")
        return

    print(f"🎯 Testing with {len(django_instances)} instances from django/django:")
    for inst in django_instances:
        print(f"  - {inst['instance_id']}")
    print()

    # Test 1: Without cache
    print("=" * 80)
    print("Test 1: WITHOUT Cache (每个instance单独clone)")
    print("=" * 80)

    repo_manager_no_cache = RepoManager(
        base_dir="/tmp/test_no_cache",
        use_cache=False
    )

    start_time = time.time()
    for inst in django_instances:
        print(f"\n  Processing {inst['instance_id']}...")
        repo_path = repo_manager_no_cache.setup_repo(inst)
        print(f"    ✓ Setup at: {repo_path}")

    no_cache_time = time.time() - start_time
    print(f"\n⏱️  总耗时: {no_cache_time:.2f} 秒")

    # Cleanup
    repo_manager_no_cache.cleanup_all()

    # Test 2: With cache
    print("\n" + "=" * 80)
    print("Test 2: WITH Cache (共享clone + worktrees)")
    print("=" * 80)

    repo_manager_with_cache = RepoManager(
        base_dir="/tmp/test_with_cache",
        use_cache=True
    )

    start_time = time.time()
    for inst in django_instances:
        print(f"\n  Processing {inst['instance_id']}...")
        repo_path = repo_manager_with_cache.setup_repo(inst)
        print(f"    ✓ Setup at: {repo_path}")

    cache_time = time.time() - start_time
    print(f"\n⏱️  总耗时: {cache_time:.2f} 秒")

    # Results
    print("\n" + "=" * 80)
    print("📊 性能对比结果")
    print("=" * 80)

    print(f"\n方式1 (无cache): {no_cache_time:.2f}秒")
    print(f"方式2 (有cache): {cache_time:.2f}秒")

    if no_cache_time > 0:
        speedup = no_cache_time / cache_time
        time_saved = no_cache_time - cache_time
        percent_saved = (time_saved / no_cache_time) * 100

        print(f"\n🚀 性能提升:")
        print(f"  加速倍数: {speedup:.2f}x")
        print(f"  节省时间: {time_saved:.2f}秒")
        print(f"  节省比例: {percent_saved:.1f}%")

    # Cleanup
    repo_manager_with_cache.cleanup_all()

    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


def test_worktree_isolation():
    """测试worktree隔离性"""

    print("\n" + "=" * 80)
    print("Worktree 隔离性测试")
    print("=" * 80)
    print()

    dataset = load_dataset('princeton-nlp/SWE-bench_Lite', split='test')
    django_instances = [
        item for item in dataset
        if item['repo'] == 'django/django'
    ][:2]

    if len(django_instances) < 2:
        print("⚠️  Not enough django instances")
        return

    repo_manager = RepoManager(
        base_dir="/tmp/test_isolation",
        use_cache=True
    )

    # Setup two worktrees from same repo at different commits
    print("设置两个不同commit的worktree:")
    paths = []
    for inst in django_instances:
        repo_path = repo_manager.setup_repo(inst)
        paths.append(repo_path)
        print(f"  {inst['instance_id']}: {inst['base_commit'][:8]}")

    # Verify isolation
    print("\n验证隔离性:")
    import subprocess

    for path, inst in zip(paths, django_instances):
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=path,
            capture_output=True,
            text=True
        )
        current_commit = result.stdout.strip()
        expected_commit = inst['base_commit']

        is_correct = current_commit == expected_commit
        status = "✅" if is_correct else "❌"

        print(f"  {status} {inst['instance_id']}: {current_commit[:8]} "
              f"(expected: {expected_commit[:8]})")

    # Cleanup
    repo_manager.cleanup_all()

    print("\n✅ 隔离性测试完成")


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("Repo Cache 功能测试套件")
    print("=" * 80)
    print()

    # Test 1: Performance
    test_cache_performance()

    # Test 2: Isolation
    test_worktree_isolation()

    print("\n" + "=" * 80)
    print("🎉 所有测试完成")
    print("=" * 80)
    print()
