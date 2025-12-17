"""GitHub API client for fetching repository data."""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from .cache import GitHubCache


class GitHubClient:
    """Client for interacting with the GitHub API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None, cache: GitHubCache | None = None):
        """Initialize the GitHub client.

        Args:
            token: Optional GitHub personal access token for authentication
            cache: Optional cache for storing API responses
        """
        self.token = token
        self.cache = cache
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"token {self.token}"})
        self.session.headers.update({"Accept": "application/vnd.github.v3+json"})

    def get_commits(self, owner: str, repo: str, since: datetime) -> list[dict[str, Any]]:
        """Fetch commits from a repository since a given date.

        Uses caching if enabled to reduce API calls. Will fetch incrementally
        by only requesting commits since the last cache update.

        Args:
            owner: Repository owner
            repo: Repository name
            since: Fetch commits after this date

        Returns:
            List of commit data dictionaries
        """
        repo_name = f"{owner}/{repo}"

        # If cache is enabled, try incremental fetch
        if self.cache:
            # Get cached commits first
            cached_commits = self.cache.get_commits(repo_name, since)

            # Check when we last fetched
            last_fetch = self.cache.get_last_fetch_time(repo_name, "commit")

            # If we have a recent fetch, only get new commits
            if last_fetch:
                fetch_since = last_fetch
            else:
                fetch_since = since

            # Fetch new commits from GitHub
            new_commits = self._fetch_commits_from_api(owner, repo, fetch_since)

            # Cache the new commits
            if new_commits:
                self.cache.cache_commits(repo_name, new_commits)

            # Update last fetch time
            self.cache.update_last_fetch_time(repo_name, "commit")

            # Combine cached and new commits, removing duplicates by SHA
            all_commits_dict = {c["sha"]: c for c in cached_commits}
            for commit in new_commits:
                all_commits_dict[commit["sha"]] = commit

            # Return as list, sorted by date (newest first)
            all_commits = list(all_commits_dict.values())
            all_commits.sort(
                key=lambda c: c.get("commit", {}).get("author", {}).get("date", ""),
                reverse=True,
            )

            return all_commits
        else:
            # No cache, fetch directly from API
            return self._fetch_commits_from_api(owner, repo, since)

    def _fetch_commits_from_api(
        self, owner: str, repo: str, since: datetime
    ) -> list[dict[str, Any]]:
        """Internal method to fetch commits from GitHub API.

        Args:
            owner: Repository owner
            repo: Repository name
            since: Fetch commits after this date

        Returns:
            List of commit data dictionaries
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits"
        params = {"since": since.isoformat(), "per_page": 100}

        all_commits = []
        page = 1

        while True:
            params["page"] = page
            response = self.session.get(url, params=params)
            response.raise_for_status()

            commits = response.json()
            if not commits:
                break

            all_commits.extend(commits)
            page += 1

            # Check if we've reached the last page
            if "next" not in response.links:
                break

        return all_commits

    def get_closed_issues(
        self, owner: str, repo: str, since: datetime
    ) -> list[dict[str, Any]]:
        """Fetch issues closed since a given date.

        Uses caching if enabled to reduce API calls. Will fetch incrementally
        by only requesting issues since the last cache update.

        Args:
            owner: Repository owner
            repo: Repository name
            since: Fetch issues closed after this date

        Returns:
            List of closed issue data dictionaries
        """
        repo_name = f"{owner}/{repo}"

        # If cache is enabled, try incremental fetch
        if self.cache:
            # Get cached issues first
            cached_issues = self.cache.get_issues(repo_name, since)

            # Check when we last fetched
            last_fetch = self.cache.get_last_fetch_time(repo_name, "issue")

            # If we have a recent fetch, only get new issues
            if last_fetch:
                fetch_since = last_fetch
            else:
                fetch_since = since

            # Fetch new issues from GitHub
            new_issues = self._fetch_issues_from_api(owner, repo, fetch_since)

            # Cache the new issues
            if new_issues:
                self.cache.cache_issues(repo_name, new_issues)

            # Update last fetch time
            self.cache.update_last_fetch_time(repo_name, "issue")

            # Combine cached and new issues, removing duplicates by number
            all_issues_dict = {i["number"]: i for i in cached_issues}
            for issue in new_issues:
                all_issues_dict[issue["number"]] = issue

            # Return as list, sorted by closed date (newest first)
            all_issues = list(all_issues_dict.values())
            all_issues.sort(
                key=lambda i: i.get("closed_at", ""),
                reverse=True,
            )

            return all_issues
        else:
            # No cache, fetch directly from API
            return self._fetch_issues_from_api(owner, repo, since)

    def _fetch_issues_from_api(
        self, owner: str, repo: str, since: datetime
    ) -> list[dict[str, Any]]:
        """Internal method to fetch issues from GitHub API.

        Args:
            owner: Repository owner
            repo: Repository name
            since: Fetch issues closed after this date

        Returns:
            List of closed issue data dictionaries
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
        params = {
            "state": "closed",
            "since": since.isoformat(),
            "per_page": 100,
        }

        all_issues = []
        page = 1

        while True:
            params["page"] = page
            response = self.session.get(url, params=params)
            response.raise_for_status()

            issues = response.json()
            if not issues:
                break

            # Filter to only include issues (not PRs) closed in our time range
            for issue in issues:
                # GitHub's issue API includes PRs, so filter them out
                if "pull_request" not in issue:
                    closed_at = datetime.fromisoformat(
                        issue["closed_at"].replace("Z", "+00:00")
                    )
                    if closed_at >= since:
                        all_issues.append(issue)

            page += 1

            # Check if we've reached the last page
            if "next" not in response.links:
                break

        return all_issues

    def get_repository_info(self, owner: str, repo: str) -> dict[str, Any]:
        """Fetch basic repository information.

        Uses caching if enabled. Repository metadata is cached indefinitely
        and refreshed on each fetch.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository data dictionary
        """
        repo_name = f"{owner}/{repo}"

        # Try cache first if enabled
        if self.cache:
            cached_info = self.cache.get_repository_info(repo_name)
            if cached_info:
                return cached_info

        # Fetch from API
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        response = self.session.get(url)
        response.raise_for_status()
        repo_data = response.json()

        # Cache the data
        if self.cache:
            self.cache.cache_repository_info(repo_name, repo_data)

        return repo_data

    def search_repositories_by_topic(
        self, topics: list[str], max_results: int = 30
    ) -> list[str]:
        """Search for repositories by topic.

        Args:
            topics: List of GitHub topics to search for
            max_results: Maximum number of repositories to return per topic

        Returns:
            List of repository strings in format "owner/repo"
        """
        all_repos = set()

        for topic in topics:
            # GitHub search API uses topic: prefix for topic searches
            query = f"topic:{topic}"
            url = f"{self.BASE_URL}/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": min(max_results, 100),
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            for repo in data.get("items", []):
                repo_string = repo.get("full_name")
                if repo_string:
                    all_repos.add(repo_string)

        return sorted(all_repos)


def parse_repository(repo_string: str) -> tuple[str, str]:
    """Parse a repository string into owner and repo name.

    Args:
        repo_string: Repository in format "owner/repo"

    Returns:
        Tuple of (owner, repo)

    Raises:
        ValueError: If repository string is not in the correct format
    """
    parts = repo_string.split("/")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid repository format: {repo_string}. Expected 'owner/repo'"
        )
    return parts[0], parts[1]
