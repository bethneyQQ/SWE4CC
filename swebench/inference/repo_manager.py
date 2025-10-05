#!/usr/bin/env python3
"""
Repository management for Claude Code access
Ensures Claude Code can read actual files at the correct commit

Features:
- Shared repo cache to avoid repeated clones
- Instance-specific worktrees for parallel processing
- Automatic cleanup of worktrees
"""
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RepoManager:
    """Manage repository checkouts for Claude Code inference"""

    def __init__(self, base_dir: str = "/tmp/swebench_repos", use_cache: bool = True):
        """
        Initialize RepoManager

        Args:
            base_dir: Base directory for repositories
            use_cache: If True, use shared cache + worktrees (faster, less disk)
                      If False, clone for each instance (slower, more disk)
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.use_cache = use_cache

        # Cache directory for shared bare repos
        self.cache_dir = self.base_dir / ".cache"
        if use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def setup_repo(self, instance_data: Dict) -> str:
        """
        Setup repository at base_commit for an instance

        Args:
            instance_data: SWE-bench instance with repo, base_commit, etc.

        Returns:
            str: Path to the repository
        """
        if self.use_cache:
            return self._setup_repo_with_cache(instance_data)
        else:
            return self._setup_repo_direct_clone(instance_data)

    def _setup_repo_with_cache(self, instance_data: Dict) -> str:
        """
        Setup repo using shared cache + worktree

        Benefits:
        - Only clone once per repo (not per instance)
        - Uses worktrees for instance-specific checkouts
        - Saves disk space and network bandwidth
        - Much faster for multiple instances from same repo
        """
        instance_id = instance_data['instance_id']
        repo_name = instance_data['repo']
        base_commit = instance_data['base_commit']

        # Sanitize repo name for directory
        cache_repo_name = repo_name.replace('/', '__')
        cache_repo_path = self.cache_dir / cache_repo_name

        # Instance-specific worktree
        worktree_path = self.base_dir / instance_id

        # Check if worktree already exists and is correct
        if worktree_path.exists():
            try:
                current_commit = subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=worktree_path,
                    text=True,
                    stderr=subprocess.DEVNULL
                ).strip()

                if current_commit == base_commit:
                    logger.info(f"{instance_id}: Worktree already at {base_commit[:8]}")
                    return str(worktree_path)
            except:
                pass

            # Clean up invalid worktree
            self._cleanup_worktree(cache_repo_path, worktree_path)

        # Ensure cache repo exists
        if not cache_repo_path.exists():
            logger.info(f"{instance_id}: Creating cache for {repo_name}")
            self._create_cache_repo(repo_name, cache_repo_path)
        else:
            logger.info(f"{instance_id}: Using cached {repo_name}")

        # Fetch commit if not present
        self._ensure_commit_available(cache_repo_path, base_commit, instance_id)

        # Create worktree at base_commit
        logger.info(f"{instance_id}: Creating worktree at {base_commit[:8]}")
        try:
            subprocess.run(
                ['git', 'worktree', 'add', '--detach', str(worktree_path), base_commit],
                cwd=cache_repo_path,
                check=True,
                capture_output=True,
                timeout=30
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"{instance_id}: Worktree creation failed: {e.stderr.decode()}")
            raise

        return str(worktree_path)

    def _setup_repo_direct_clone(self, instance_data: Dict) -> str:
        """
        Setup repo by direct cloning (original method)

        Used when use_cache=False
        """
        instance_id = instance_data['instance_id']
        repo_name = instance_data['repo']
        base_commit = instance_data['base_commit']

        # Create instance-specific directory
        repo_path = self.base_dir / instance_id

        # Check if already setup correctly
        if repo_path.exists():
            try:
                current_commit = subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=repo_path,
                    text=True,
                    stderr=subprocess.DEVNULL
                ).strip()

                if current_commit == base_commit:
                    logger.info(f"{instance_id}: Repo already at {base_commit[:8]}")
                    return str(repo_path)
            except:
                pass

            # Clean up if exists but wrong state
            logger.info(f"{instance_id}: Cleaning existing repo")
            shutil.rmtree(repo_path)

        # Clone repository
        logger.info(f"{instance_id}: Cloning {repo_name}")
        github_url = f"https://github.com/{repo_name}.git"

        try:
            # Clone with minimal depth
            subprocess.run(
                ['git', 'clone', '--depth', '1', '--no-single-branch', github_url, str(repo_path)],
                check=True,
                capture_output=True,
                timeout=120
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"{instance_id}: Clone failed: {e.stderr.decode()}")
            raise

        # Fetch the specific commit if needed
        try:
            subprocess.run(
                ['git', 'fetch', 'origin', base_commit],
                cwd=repo_path,
                check=True,
                capture_output=True,
                timeout=60
            )
        except subprocess.CalledProcessError:
            # Commit might already be fetched
            pass

        # Checkout to base_commit
        try:
            subprocess.run(
                ['git', 'checkout', '-f', base_commit],
                cwd=repo_path,
                check=True,
                capture_output=True,
                timeout=30
            )
            logger.info(f"{instance_id}: Checked out {base_commit[:8]}")
        except subprocess.CalledProcessError as e:
            logger.error(f"{instance_id}: Checkout failed: {e.stderr.decode()}")
            raise

        return str(repo_path)

    def _create_cache_repo(self, repo_name: str, cache_path: Path):
        """Create a bare clone in cache directory"""
        github_url = f"https://github.com/{repo_name}.git"

        try:
            subprocess.run(
                ['git', 'clone', '--bare', github_url, str(cache_path)],
                check=True,
                capture_output=True,
                timeout=300
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Cache creation failed for {repo_name}: {e.stderr.decode()}")
            raise

    def _ensure_commit_available(self, cache_path: Path, commit: str, instance_id: str):
        """Ensure specific commit is available in cache repo"""
        try:
            # Check if commit exists
            subprocess.run(
                ['git', 'cat-file', '-e', commit],
                cwd=cache_path,
                check=True,
                capture_output=True,
                timeout=10
            )
        except subprocess.CalledProcessError:
            # Commit not found, fetch it
            logger.info(f"{instance_id}: Fetching {commit[:8]} into cache")
            try:
                subprocess.run(
                    ['git', 'fetch', 'origin', commit],
                    cwd=cache_path,
                    check=True,
                    capture_output=True,
                    timeout=60
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"{instance_id}: Fetch failed: {e.stderr.decode()}")
                raise

    def _cleanup_worktree(self, cache_path: Path, worktree_path: Path):
        """Cleanup a worktree properly"""
        try:
            # Remove from git worktree list
            subprocess.run(
                ['git', 'worktree', 'remove', '--force', str(worktree_path)],
                cwd=cache_path,
                capture_output=True,
                timeout=10
            )
        except:
            pass

        # Remove directory if still exists
        if worktree_path.exists():
            shutil.rmtree(worktree_path)

    def cleanup_repo(self, instance_id: str):
        """Remove repository/worktree for an instance"""
        repo_path = self.base_dir / instance_id

        if self.use_cache and repo_path.exists():
            # Find the cache repo for this instance to clean up worktree
            try:
                # Try to get repo name from worktree
                result = subprocess.run(
                    ['git', 'remote', 'get-url', 'origin'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Extract repo name from URL
                    url = result.stdout.strip()
                    repo_name = url.replace('https://github.com/', '').replace('.git', '')
                    cache_repo_name = repo_name.replace('/', '__')
                    cache_repo_path = self.cache_dir / cache_repo_name

                    if cache_repo_path.exists():
                        self._cleanup_worktree(cache_repo_path, repo_path)
                        logger.info(f"{instance_id}: Cleaned up worktree")
                        return
            except:
                pass

        # Fallback: direct removal
        if repo_path.exists():
            shutil.rmtree(repo_path)
            logger.info(f"{instance_id}: Cleaned up repo")

    def cleanup_all(self):
        """Remove all repositories and cache"""
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
            logger.info("Cleaned up all repos and cache")

    def cleanup_cache(self):
        """Remove only the cache directory (keep worktrees)"""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            logger.info("Cleaned up cache directory")


def get_repo_files_list(repo_path: str, file_pattern: str = "*.py") -> list:
    """Get list of files matching pattern in repo"""
    result = subprocess.run(
        ['find', '.', '-name', file_pattern, '-type', 'f'],
        cwd=repo_path,
        capture_output=True,
        text=True
    )

    files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
    return files
