Goal: markdown-formated narrative summary of github commits for a repository.

Given a list of repositories, grab the github commits for the last month (but configurable). Then, use gemini-3-pro to create summaries per repo. Finally, present the data (number of commits, contributors, etc) along with the narrative summary of the commits produced by gemini. 

## tooling

- Use `uv` for python package management
- Use click for any command-line interactions
- If you need environment variables, make a .env.example file specifying what you need

