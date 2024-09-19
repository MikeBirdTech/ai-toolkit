# TODO Issue Creator

A GitHub Action that scans your codebase for `TODO` comments and creates GitHub issues for them using an LLM for detailed descriptions.

## Inputs

- `groq_api_key` (required): Your API key for Groq.
- `github_token` (required): GitHub token with permissions to create issues.

## Usage

Create a workflow file in your repository's `.github/workflows` directory:

```yaml
name: "TODO Issue Creator Workflow"
on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  issues: write
  contents: read

jobs:
  create_todo_issues:
    runs-on: ubuntu-latest
    steps:
      - name: Run TODO Issue Creator action
        uses: ./.github/todo-issue-creator
        with:
          groq_api_key: \${{ secrets.GROQ_API_KEY }}
          github_token: \${{ secrets.GITHUB_TOKEN }}
```

<!-- TODO: Add better instructions for set up -->
