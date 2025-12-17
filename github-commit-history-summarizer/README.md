# GitHub Commit History Summarizer

Generate AI-powered narrative summaries of GitHub repository commit history using Google's Gemini AI.

## Features

- Fetch commits and closed issues from GitHub repositories
- Generate intelligent narrative summaries using Gemini AI
- Track statistics: commit count, contributors, closed issues, and more
- Support for multiple repositories in batch
- Configurable time periods (default: 30 days)
- Markdown-formatted output reports

## Installation

This project uses `uv` for Python package management. First, install `uv` if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the package:

```bash
uv pip install -e .
```

## Configuration

### 1. Set up environment variables

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add:

- `GEMINI_API_KEY` (required): Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- `GITHUB_TOKEN` (optional but recommended): Get from [GitHub Settings](https://github.com/settings/tokens)

### 2. Create a configuration file

**Option A: Generate from GitHub topics (recommended)**

```bash
commit-summarizer generate-config bioinformatics genomics --max-repos 20
```

**Option B: Manually create**

Copy the example config and customize it:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to specify:

```yaml
repositories:
  - owner/repo1
  - owner/repo2

output_dir: ./summaries
```

## Usage

### Generate Config from GitHub Topics

Create a configuration file by searching GitHub for repositories with specific topics:

```bash
commit-summarizer generate-config python machine-learning
```

With options:

```bash
# Limit results and specify output file
commit-summarizer generate-config data-science --max-repos 50 --output my-config.yaml

# Multiple topics
commit-summarizer generate-config bioinformatics genomics proteomics --max-repos 20
```

### Generate Summaries

Once you have a config file, generate summaries:

```bash
commit-summarizer summarize --config config.yaml
```

Specify a custom time period (in days):

```bash
commit-summarizer summarize --config config.yaml --days 60
```

Choose a different AI model:

```bash
commit-summarizer summarize --config config.yaml --model gemini-2.5-pro
```

Use a custom environment file:

```bash
commit-summarizer summarize --config config.yaml --env-file .env.production
```

## Output

The tool generates one markdown file per repository in the specified output directory. Each file contains:

- Repository metadata and description
- Statistics (commits, contributors, closed issues, lines changed)
- List of top contributors
- AI-generated narrative summary of the development activity

Example output filename: `owner_repo_2024-01-01.md`

## Development

### Project Structure

```
github-commit-history-summarizer/
├── pyproject.toml              # Package configuration
├── .env.example                # Example environment variables
├── config.example.yaml         # Example repository configuration
├── README.md                   # This file
└── src/
    └── commit_summarizer/
        ├── __init__.py         # Package initialization
        ├── cli.py              # Command-line interface
        ├── config.py           # Configuration handling
        ├── github_client.py    # GitHub API client
        ├── gemini_client.py    # Gemini AI client
        └── summarizer.py       # Main summarization logic
```

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
