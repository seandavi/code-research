"""Command-line interface for the GitHub Commit Summarizer."""

import os
import sys
from pathlib import Path

import click
import yaml
from dotenv import load_dotenv

from .cache import GitHubCache
from .config import Config
from .gemini_client import GeminiClient
from .github_client import GitHubClient
from .summarizer import RepositorySummarizer


@click.group()
def cli():
    """GitHub Commit Summarizer - Generate AI-powered summaries of repository activity."""
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the YAML configuration file",
)
@click.option(
    "--days",
    "-d",
    type=int,
    default=30,
    help="Number of days of history to summarize (default: 30)",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True, path_type=Path),
    help="Path to .env file (optional, defaults to .env in current directory)",
)
@click.option(
    "--model",
    "-m",
    type=str,
    default="gemini-3-pro-preview",
    help="Gemini model to use (default: gemini-3-pro-preview)",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable caching and fetch all data from GitHub API",
)
@click.option(
    "--cache-db",
    type=click.Path(path_type=Path),
    default=".github_cache.db",
    help="Path to SQLite cache database (default: .github_cache.db)",
)
def summarize(
    config: Path,
    days: int,
    env_file: Path | None,
    model: str,
    no_cache: bool,
    cache_db: Path,
):
    """Generate AI-powered summaries of GitHub repository commit history.

    This command fetches commits and closed issues from GitHub repositories,
    analyzes them using Google's Gemini AI, and generates comprehensive
    markdown summaries for each repository.

    Example usage:

        commit-summarizer summarize --config config.yaml

        commit-summarizer summarize --config config.yaml --days 60

        commit-summarizer summarize --config config.yaml --model gemini-2.5-pro
    """
    # Load environment variables
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    # Get API keys from environment
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not gemini_api_key:
        click.echo(
            "Error: GEMINI_API_KEY not found in environment variables", err=True
        )
        click.echo("Please set it in your .env file or environment", err=True)
        sys.exit(1)

    # Load configuration
    try:
        cfg = Config(config)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)

    # Initialize cache if enabled
    cache = None
    if not no_cache:
        cache = GitHubCache(db_path=cache_db)
        click.echo(f"Cache enabled: {cache_db}")
    else:
        click.echo("Cache disabled")

    # Initialize clients
    click.echo(f"Initializing clients with model: {model}...")
    github_client = GitHubClient(token=github_token, cache=cache)
    gemini_client = GeminiClient(api_key=gemini_api_key, model_name=model)

    # Initialize summarizer
    summarizer = RepositorySummarizer(
        github_client=github_client,
        gemini_client=gemini_client,
        output_dir=cfg.output_dir,
    )

    # Process each repository
    repositories = cfg.repositories
    click.echo(f"\nProcessing {len(repositories)} repositories...\n")

    summary_paths = []
    for i, repo in enumerate(repositories, 1):
        click.echo(f"[{i}/{len(repositories)}] Processing {repo}...")
        try:
            output_path = summarizer.summarize_repository(repo, days=days)
            summary_paths.append(output_path)
            click.echo(f"✓ Summary saved to {output_path}\n")
        except Exception as e:
            click.echo(f"✗ Error processing {repo}: {e}\n", err=True)
            continue

    # Create combined summary if we have at least one successful repository
    if summary_paths:
        click.echo("\nCreating combined summary...")
        try:
            combined_path = summarizer.create_combined_summary(summary_paths, days=days)
            click.echo(f"✓ Combined summary saved to {combined_path}\n")
        except Exception as e:
            click.echo(f"✗ Error creating combined summary: {e}\n", err=True)

    # Close cache connection if it was opened
    if cache:
        cache.close()

    click.echo("Done!")


@cli.command()
@click.argument("topics", nargs=-1, required=True)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="config.yaml",
    help="Output path for the generated config file (default: config.yaml)",
)
@click.option(
    "--max-repos",
    type=int,
    default=30,
    help="Maximum number of repositories per topic (default: 30)",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True, path_type=Path),
    help="Path to .env file (optional, defaults to .env in current directory)",
)
def generate_config(
    topics: tuple[str, ...],
    output: Path,
    max_repos: int,
    env_file: Path | None,
):
    """Generate a config file from GitHub topics.

    Searches GitHub for repositories matching the specified topics and creates
    a configuration file with the found repositories.

    TOPICS: One or more GitHub topics to search for

    Example usage:

        commit-summarizer generate-config python machine-learning

        commit-summarizer generate-config data-science --max-repos 50

        commit-summarizer generate-config kubernetes --output k8s-config.yaml
    """
    # Load environment variables
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    # Get GitHub token (optional but helps avoid rate limits)
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        click.echo(
            "Warning: GITHUB_TOKEN not found. You may hit API rate limits.",
            err=True,
        )
        click.echo(
            "Consider setting it in your .env file for better performance.\n", err=True
        )

    # Initialize GitHub client
    click.echo(f"Searching GitHub for topics: {', '.join(topics)}...")
    github_client = GitHubClient(token=github_token)

    # Search for repositories
    try:
        repositories = github_client.search_repositories_by_topic(
            list(topics), max_results=max_repos
        )
    except Exception as e:
        click.echo(f"Error searching GitHub: {e}", err=True)
        sys.exit(1)

    if not repositories:
        click.echo("No repositories found for the specified topics.", err=True)
        sys.exit(1)

    click.echo(f"Found {len(repositories)} repositories\n")

    # Create config data
    config_data = {
        "repositories": repositories,
        "output_dir": "./summaries",
    }

    # Write config file
    try:
        with open(output, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        click.echo(f"✓ Config file generated: {output}")
        click.echo(f"\nRepositories included:")
        for i, repo in enumerate(repositories[:10], 1):
            click.echo(f"  {i}. {repo}")
        if len(repositories) > 10:
            click.echo(f"  ... and {len(repositories) - 10} more")
    except Exception as e:
        click.echo(f"Error writing config file: {e}", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
