# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Utilities for code hosting platform URL parsing.

This module provides shared functionality for parsing URLs from code hosting
platforms like GitHub and GitLab.
"""

from typing import Optional
from urllib.parse import urlparse

from openviking_cli.utils.config import get_openviking_config


def parse_code_hosting_url(url: str) -> Optional[str]:
    """Parse code hosting platform URL to get org/repo path.

    Args:
        url: Code hosting URL like https://github.com/volcengine/OpenViking
             or git@github.com:volcengine/OpenViking.git

    Returns:
        org/repo path like "volcengine/OpenViking" or None if not a valid
        code hosting URL
    """
    config = get_openviking_config()

    # Handle git@ SSH URLs
    if url.startswith("git@"):
        try:
            # Expected format: git@host:org/repo.git or git@host:org/repo
            parts = url.split(":", 1)
            if len(parts) != 2:
                return None

            host_part = parts[0]
            path_part = parts[1]

            # Extract host (remove 'git@')
            host = host_part[4:]

            # Check if host is allowed
            all_domains = (
                config.code.github_domains
                + config.code.gitlab_domains
                + config.code.code_hosting_domains
            )
            if host not in all_domains:
                return None

            # Parse path part
            path_segments = [p for p in path_part.split("/") if p]
            if len(path_segments) < 2:
                return None

            # For SSH, we support deep paths (e.g. group/subgroup/project)
            # Remove .git from the last segment if present
            if path_segments and path_segments[-1].endswith(".git"):
                path_segments[-1] = path_segments[-1][:-4]

            # Sanitize all segments
            sanitized_segments = [
                "".join(c if c.isalnum() or c in "-_" else "_" for c in s) for s in path_segments
            ]

            # Join with /
            return "/".join(sanitized_segments)

        except Exception:
            return None

    if not url.startswith(("http://", "https://", "git://", "ssh://")):
        return None

    parsed = urlparse(url)

    path_parts = [p for p in parsed.path.split("/") if p]

    # For GitHub/GitLab URLs with org/repo structure
    if (
        parsed.netloc in config.code.github_domains + config.code.gitlab_domains
        and len(path_parts) >= 2
    ):
        # Take first two parts: org/repo
        org = path_parts[0]
        repo = path_parts[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
        # Sanitize both parts
        org = "".join(c if c.isalnum() or c in "-_" else "_" for c in org)
        repo = "".join(c if c.isalnum() or c in "-_" else "_" for c in repo)
        return f"{org}/{repo}"

    return None


def is_github_url(url: str) -> bool:
    """Check if a URL is a GitHub URL.

    Args:
        url: URL to check

    Returns:
        True if the URL is a GitHub URL
    """
    config = get_openviking_config()
    return urlparse(url).netloc in config.code.github_domains


def is_gitlab_url(url: str) -> bool:
    """Check if a URL is a GitLab URL.

    Args:
        url: URL to check

    Returns:
        True if the URL is a GitLab URL
    """
    config = get_openviking_config()
    return urlparse(url).netloc in config.code.gitlab_domains


def is_code_hosting_url(url: str) -> bool:
    """Check if a URL is a code hosting platform URL.

    Args:
        url: URL to check

    Returns:
        True if the URL is a code hosting platform URL
    """
    config = get_openviking_config()
    all_domains = list(
        set(
            config.code.github_domains
            + config.code.gitlab_domains
            + config.code.code_hosting_domains
        )
    )

    if url.startswith("git@"):
        try:
            parts = url.split(":", 1)
            if len(parts) == 2:
                host_part = parts[0]
                host = host_part[4:]
                return host in all_domains
        except Exception:
            return False

    return urlparse(url).netloc in all_domains


def validate_git_ssh_uri(uri: str) -> None:
    """Validate Git SSH URI format.

    Args:
        uri: The URI to validate.

    Raises:
        ValueError: If the URI is invalid.
    """
    if not uri.startswith("git@"):
        return

    if ":" not in uri:
        raise ValueError(
            f"Invalid Git SSH URI format: '{uri}'. Missing colon separator.\n"
            "Expected format: git@host:group/repo.git"
        )

    parts = uri.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid Git SSH URI format: '{uri}'")

    host_part = parts[0]
    path_part = parts[1]

    if len(host_part) <= 4:  # just "git@"
        raise ValueError(f"Invalid Git SSH URI: '{uri}'. Missing host.")

    if not path_part:
        raise ValueError(f"Invalid Git SSH URI: '{uri}'. Missing path.")

    # Check for empty path segments which might imply malformed path
    # But strictly speaking 'git@host:repo.git' is valid (path 'repo.git')
    pass
