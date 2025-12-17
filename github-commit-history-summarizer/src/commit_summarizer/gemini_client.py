"""Gemini API client for generating commit summaries."""

from typing import Any

import google.generativeai as genai


class GeminiClient:
    """Client for interacting with Google's Gemini API."""

    def __init__(self, api_key: str, model_name: str = "gemini-3-pro-preview"):
        """Initialize the Gemini client.

        Args:
            api_key: Gemini API key
            model_name: Name of the Gemini model to use (e.g., 'gemini-3-pro-preview', 'gemini-2.5-pro')
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_summary(
        self,
        commits: list[dict[str, Any]],
        issues: list[dict[str, Any]],
        repo_name: str,
    ) -> str:
        """Generate a narrative summary of commits and issues.

        Args:
            commits: List of commit data
            issues: List of closed issue data
            repo_name: Name of the repository

        Returns:
            Markdown-formatted narrative summary
        """
        # Prepare commit data for the prompt
        commit_info = []
        for commit in commits:
            commit_data = commit.get("commit", {})
            message = commit_data.get("message", "")
            author = commit_data.get("author", {}).get("name", "Unknown")
            date = commit_data.get("author", {}).get("date", "")
            commit_info.append(f"- {message[:100]} (by {author} on {date})")

        # Prepare issue data for the prompt
        issue_info = []
        for issue in issues:
            title = issue.get("title", "")
            number = issue.get("number", "")
            issue_info.append(f"- #{number}: {title}")

        # Build the prompt
        prompt = f"""You are analyzing the commit history and closed issues for the GitHub repository: {repo_name}

Here are the commits made during this period:

{chr(10).join(commit_info[:500])}  # Limit to avoid token limits

Here are the issues closed during this period:

{chr(10).join(issue_info[:200])}  # Limit to avoid token limits

Please generate a narrative summary of the development activity during this period. The summary should:

1. Highlight major themes and areas of development
2. Identify key features or improvements that were added
3. Note any significant bug fixes or issues resolved
4. Describe patterns in the type of work being done
5. Be written in a clear, professional tone suitable for a development report
6. Be structured with appropriate markdown headings and formatting
7. Be approximately 3-5 paragraphs in length

Focus on the "why" and "what" of the changes, not just listing commits. Provide insights into the development direction and priorities.
"""

        response = self.model.generate_content(prompt)
        return response.text


def prepare_commit_summary_text(commits: list[dict[str, Any]]) -> str:
    """Prepare a text summary of commits for analysis.

    Args:
        commits: List of commit data

    Returns:
        Formatted text of commit messages
    """
    lines = []
    for commit in commits:
        commit_data = commit.get("commit", {})
        message = commit_data.get("message", "")
        author = commit_data.get("author", {}).get("name", "Unknown")
        lines.append(f"{author}: {message}")
    return "\n".join(lines)
