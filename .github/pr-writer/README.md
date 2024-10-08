# PR Summary Generator

A GitHub Action that automatically generates concise and informative summaries for Pull Requests based on commit messages. Leveraging AI, it enhances the clarity and professionalism of your PR descriptions.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Automated Summaries**: Generates PR titles and descriptions from commit messages.
- **AI-Powered**: Utilizes advanced language models to ensure clarity and relevance.
- **Easy Integration**: Simple setup within your GitHub workflows.
- **Customizable**: Configure API keys and tokens as needed.

## Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/your-repo/.github/pr-writer.git
    ```
2. **Navigate to the Directory**:
    ```bash
    cd .github/pr-writer
    ```
3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Ensure you have the following secrets set in your repository settings:

- `GROQ_API_KEY`: Your API key for Groq.
- `GITHUB_TOKEN`: GitHub token with permissions to create and edit issues.

## Usage

Add the following workflow file to your repository's `.github/workflows` directory:

```yaml
name: "PR Summary Generator"
on:
  pull_request:
    types: [opened, synchronize]
permissions:
  issues: write
  contents: read

jobs:
  generate_pr_summary:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/pr-writer
        with:
          groq_api_key: ${{ secrets.GROQ_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

This workflow triggers on pull request events and generates a summary based on commit messages.

## Troubleshooting

- **Missing Environment Variables**: Ensure that `GROQ_API_KEY` and `GITHUB_TOKEN` are correctly set in your repository secrets.
- **API Errors**: Verify that your `GROQ_API_KEY` is valid and has the necessary permissions.
- **Action Fails to Run**: Check the workflow logs for detailed error messages and ensure all dependencies are installed.

## Contributing

Contributions are welcome! Please open issues or submit pull requests for any enhancements or bug fixes.

## License

This project is licensed under the [MIT License](../LICENSE).
