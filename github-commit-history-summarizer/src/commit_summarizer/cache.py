"""SQLite cache for GitHub API data."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class GitHubCache:
    """SQLite-based cache for GitHub API responses."""

    def __init__(self, db_path: Path | str = ".github_cache.db"):
        """Initialize the cache.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._initialize_database()

    def _initialize_database(self):
        """Create the database schema if it doesn't exist."""
        cursor = self.conn.cursor()

        # Repositories table - tracks last fetch times
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                repo_name TEXT PRIMARY KEY,
                last_commit_fetch TEXT,
                last_issue_fetch TEXT,
                repo_data TEXT
            )
        """)

        # Commits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commits (
                repo_name TEXT,
                commit_sha TEXT,
                commit_data TEXT,
                committed_at TEXT,
                fetched_at TEXT,
                PRIMARY KEY (repo_name, commit_sha)
            )
        """)

        # Issues table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                repo_name TEXT,
                issue_number INTEGER,
                issue_data TEXT,
                closed_at TEXT,
                fetched_at TEXT,
                PRIMARY KEY (repo_name, issue_number)
            )
        """)

        # Create indexes for efficient queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_commits_time
            ON commits(repo_name, committed_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_issues_time
            ON issues(repo_name, closed_at)
        """)

        self.conn.commit()

    def get_last_fetch_time(
        self, repo_name: str, data_type: str = "commit"
    ) -> datetime | None:
        """Get the last time data was fetched for a repository.

        Args:
            repo_name: Repository in format "owner/repo"
            data_type: Either "commit" or "issue"

        Returns:
            Datetime of last fetch, or None if never fetched
        """
        cursor = self.conn.cursor()
        column = "last_commit_fetch" if data_type == "commit" else "last_issue_fetch"

        cursor.execute(
            f"SELECT {column} FROM repositories WHERE repo_name = ?", (repo_name,)
        )

        row = cursor.fetchone()
        if row and row[0]:
            return datetime.fromisoformat(row[0])
        return None

    def update_last_fetch_time(
        self, repo_name: str, data_type: str = "commit", timestamp: datetime | None = None
    ):
        """Update the last fetch time for a repository.

        Args:
            repo_name: Repository in format "owner/repo"
            data_type: Either "commit" or "issue"
            timestamp: Timestamp to set (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        cursor = self.conn.cursor()
        column = "last_commit_fetch" if data_type == "commit" else "last_issue_fetch"

        # Insert or update
        cursor.execute(
            f"""
            INSERT INTO repositories (repo_name, {column})
            VALUES (?, ?)
            ON CONFLICT(repo_name) DO UPDATE SET {column} = ?
            """,
            (repo_name, timestamp.isoformat(), timestamp.isoformat()),
        )

        self.conn.commit()

    def cache_commits(self, repo_name: str, commits: list[dict[str, Any]]):
        """Cache commits for a repository.

        Args:
            repo_name: Repository in format "owner/repo"
            commits: List of commit data from GitHub API
        """
        cursor = self.conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        for commit in commits:
            commit_sha = commit.get("sha")
            if not commit_sha:
                continue

            committed_at = commit.get("commit", {}).get("author", {}).get("date")

            cursor.execute(
                """
                INSERT OR REPLACE INTO commits
                (repo_name, commit_sha, commit_data, committed_at, fetched_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    repo_name,
                    commit_sha,
                    json.dumps(commit),
                    committed_at,
                    now,
                ),
            )

        self.conn.commit()

    def cache_issues(self, repo_name: str, issues: list[dict[str, Any]]):
        """Cache issues for a repository.

        Args:
            repo_name: Repository in format "owner/repo"
            issues: List of issue data from GitHub API
        """
        cursor = self.conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        for issue in issues:
            issue_number = issue.get("number")
            if not issue_number:
                continue

            closed_at = issue.get("closed_at")

            cursor.execute(
                """
                INSERT OR REPLACE INTO issues
                (repo_name, issue_number, issue_data, closed_at, fetched_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    repo_name,
                    issue_number,
                    json.dumps(issue),
                    closed_at,
                    now,
                ),
            )

        self.conn.commit()

    def get_commits(
        self, repo_name: str, since: datetime
    ) -> list[dict[str, Any]]:
        """Retrieve cached commits for a repository since a given date.

        Args:
            repo_name: Repository in format "owner/repo"
            since: Get commits after this date

        Returns:
            List of commit data
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT commit_data FROM commits
            WHERE repo_name = ? AND committed_at >= ?
            ORDER BY committed_at DESC
            """,
            (repo_name, since.isoformat()),
        )

        rows = cursor.fetchall()
        return [json.loads(row[0]) for row in rows]

    def get_issues(
        self, repo_name: str, since: datetime
    ) -> list[dict[str, Any]]:
        """Retrieve cached issues for a repository since a given date.

        Args:
            repo_name: Repository in format "owner/repo"
            since: Get issues closed after this date

        Returns:
            List of issue data
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT issue_data FROM issues
            WHERE repo_name = ? AND closed_at >= ?
            ORDER BY closed_at DESC
            """,
            (repo_name, since.isoformat()),
        )

        rows = cursor.fetchall()
        return [json.loads(row[0]) for row in rows]

    def cache_repository_info(self, repo_name: str, repo_data: dict[str, Any]):
        """Cache repository metadata.

        Args:
            repo_name: Repository in format "owner/repo"
            repo_data: Repository data from GitHub API
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO repositories (repo_name, repo_data)
            VALUES (?, ?)
            ON CONFLICT(repo_name) DO UPDATE SET repo_data = ?
            """,
            (repo_name, json.dumps(repo_data), json.dumps(repo_data)),
        )

        self.conn.commit()

    def get_repository_info(self, repo_name: str) -> dict[str, Any] | None:
        """Get cached repository metadata.

        Args:
            repo_name: Repository in format "owner/repo"

        Returns:
            Repository data or None if not cached
        """
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT repo_data FROM repositories WHERE repo_name = ?",
            (repo_name,),
        )

        row = cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return None

    def clear_cache(self, repo_name: str | None = None):
        """Clear the cache.

        Args:
            repo_name: If provided, clear only this repo. Otherwise clear all.
        """
        cursor = self.conn.cursor()

        if repo_name:
            cursor.execute("DELETE FROM commits WHERE repo_name = ?", (repo_name,))
            cursor.execute("DELETE FROM issues WHERE repo_name = ?", (repo_name,))
            cursor.execute("DELETE FROM repositories WHERE repo_name = ?", (repo_name,))
        else:
            cursor.execute("DELETE FROM commits")
            cursor.execute("DELETE FROM issues")
            cursor.execute("DELETE FROM repositories")

        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
