"""Main summarizer logic for generating repository summaries."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .gemini_client import GeminiClient
from .github_client import GitHubClient, parse_repository


class RepositorySummarizer:
    """Orchestrates the creation of repository commit summaries."""

    def __init__(
        self,
        github_client: GitHubClient,
        gemini_client: GeminiClient,
        output_dir: Path,
    ):
        """Initialize the summarizer.

        Args:
            github_client: GitHub API client
            gemini_client: Gemini API client
            output_dir: Directory to write summary files
        """
        self.github_client = github_client
        self.gemini_client = gemini_client
        self.output_dir = output_dir

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def summarize_repository(self, repo_string: str, days: int = 30) -> Path:
        """Generate a summary for a single repository.

        Args:
            repo_string: Repository in format "owner/repo"
            days: Number of days of history to summarize

        Returns:
            Path to the generated summary file
        """
        owner, repo = parse_repository(repo_string)
        since = datetime.now(timezone.utc) - timedelta(days=days)

        print(f"Fetching data for {owner}/{repo}...")

        # Fetch repository data
        repo_info = self.github_client.get_repository_info(owner, repo)
        commits = self.github_client.get_commits(owner, repo, since)
        issues = self.github_client.get_closed_issues(owner, repo, since)

        print(f"Found {len(commits)} commits and {len(issues)} closed issues")

        # Collect statistics
        stats = self._calculate_statistics(commits, issues)

        # Check if there's any activity to summarize
        if len(commits) == 0 and len(issues) == 0:
            print("No activity found, skipping AI summary...")
            narrative = "No commits or issues were found during this period. The repository had no activity in the specified timeframe."
        else:
            print("Generating AI summary...")
            # Generate AI summary
            narrative = self.gemini_client.generate_summary(commits, issues, repo_string)

        # Write summary to file
        output_path = self._write_summary(
            owner, repo, since, stats, narrative, repo_info
        )

        print(f"Summary written to {output_path}")
        return output_path

    def _calculate_statistics(
        self, commits: list[dict[str, Any]], issues: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate statistics about the commits and issues.

        Args:
            commits: List of commit data
            issues: List of closed issue data

        Returns:
            Dictionary of statistics
        """
        # Count unique contributors
        contributors = set()
        for commit in commits:
            author = commit.get("commit", {}).get("author", {}).get("name")
            if author:
                contributors.add(author)

        # Count files changed (approximate from commit stats)
        total_additions = 0
        total_deletions = 0
        files_changed = set()

        for commit in commits:
            stats = commit.get("stats", {})
            total_additions += stats.get("additions", 0)
            total_deletions += stats.get("deletions", 0)

            # Note: Getting detailed file info would require additional API calls
            # For efficiency, we'll skip detailed file tracking

        return {
            "commit_count": len(commits),
            "contributor_count": len(contributors),
            "contributors": sorted(contributors),
            "issue_count": len(issues),
            "total_additions": total_additions,
            "total_deletions": total_deletions,
        }

    def _write_summary(
        self,
        owner: str,
        repo: str,
        since: datetime,
        stats: dict[str, Any],
        narrative: str,
        repo_info: dict[str, Any],
    ) -> Path:
        """Write the summary to a markdown file.

        Args:
            owner: Repository owner
            repo: Repository name
            since: Start date of the summary period
            stats: Statistics dictionary
            narrative: AI-generated narrative summary
            repo_info: Repository information from GitHub

        Returns:
            Path to the written file
        """
        filename = f"{owner}_{repo}_{since.strftime('%Y-%m-%d')}.md"
        output_path = self.output_dir / filename

        with open(output_path, "w") as f:
            # Header
            f.write(f"# {owner}/{repo}\n\n")
            f.write(f"**Repository Summary**\n\n")

            # Repository info
            description = repo_info.get("description", "No description")
            f.write(f"*{description}*\n\n")

            # Time period
            end_date = datetime.now(timezone.utc)
            f.write(
                f"**Period:** {since.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n\n"
            )

            # Statistics
            f.write("## 📊 Statistics\n\n")
            f.write(f"- **Commits:** {stats['commit_count']}\n")
            f.write(f"- **Contributors:** {stats['contributor_count']}\n")
            f.write(f"- **Closed Issues:** {stats['issue_count']}\n")

            if stats["total_additions"] > 0 or stats["total_deletions"] > 0:
                f.write(
                    f"- **Lines Changed:** +{stats['total_additions']} / -{stats['total_deletions']}\n"
                )

            # Top contributors
            if stats["contributors"]:
                f.write(f"\n**Top Contributors:**\n")
                for contributor in stats["contributors"][:10]:
                    f.write(f"- {contributor}\n")

            # AI-generated narrative
            f.write("\n## 📝 Activity Summary\n\n")
            f.write(narrative)
            f.write("\n\n")

            # Footer
            f.write("---\n")
            f.write("*Generated with GitHub Commit Summarizer*\n")

        return output_path

    def create_combined_summary(
        self, summary_paths: list[Path], days: int = 30
    ) -> Path:
        """Create a combined markdown file from all individual summaries.

        Args:
            summary_paths: List of paths to individual summary files
            days: Number of days covered by the summaries

        Returns:
            Path to the combined summary file
        """
        if not summary_paths:
            raise ValueError("No summary paths provided")

        # Create combined filename
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        combined_filename = f"combined_summary_{timestamp}.md"
        combined_path = self.output_dir / combined_filename

        with open(combined_path, "w") as outfile:
            # Write header
            outfile.write("# GitHub Repository Activity Summary\n\n")
            outfile.write(
                f"**Period:** Last {days} days (as of {timestamp})\n\n"
            )
            outfile.write(f"**Repositories Analyzed:** {len(summary_paths)}\n\n")

            # Write table of contents
            outfile.write("## Table of Contents\n\n")
            for i, path in enumerate(summary_paths, 1):
                # Extract repo name from filename (format: owner_repo_date.md)
                repo_name = path.stem.rsplit('_', 1)[0].replace('_', '/')
                outfile.write(f"{i}. [{repo_name}](#{repo_name.replace('/', '').lower()})\n")
            outfile.write("\n---\n\n")

            # Concatenate all individual summaries
            for i, path in enumerate(summary_paths):
                if i > 0:
                    outfile.write("\n\n---\n\n")

                # Read and write the content
                with open(path, "r") as infile:
                    content = infile.read()
                    # Remove the footer from individual files to avoid repetition
                    content = content.replace(
                        "---\n*Generated with GitHub Commit Summarizer*\n", ""
                    ).rstrip()
                    outfile.write(content)

            # Write combined footer
            outfile.write("\n\n---\n\n")
            outfile.write(
                f"*Combined summary generated with GitHub Commit Summarizer on {timestamp}*\n"
            )

        return combined_path
