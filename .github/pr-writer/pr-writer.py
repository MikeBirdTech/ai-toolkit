import os
import sys
from github import Github
from groq import Groq

# Initialize clients
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
g = Github(os.environ["GITHUB_TOKEN"])


def get_commit_messages(repo_name, pr_number):
    repo = g.get_repo(repo_name)
    pull_request = repo.get_pull(pr_number)
    commits = pull_request.get_commits()
    return [commit.commit.message for commit in commits]


def generate_summary(commit_messages):
    if not commit_messages:
        return "No commit messages available to generate a summary."

    prompt = f"""
You are an AI assistant helping to create a pull request summary.

Based on the following commit messages, generate a concise and informative PR title and description.

**Commit Messages:**
{commit_messages}

**Instructions:**

1. **PR Title** (max 50 characters): A brief, clear summary of the changes.
2. **PR Description**:
   - **Overview**: A short paragraph explaining the purpose of the PR.
   - **Key Changes**: A bullet-point list of significant changes.
   - **Notes**: Any important considerations or follow-up actions.

Maintain a professional and clear tone appropriate for a developer audience.

Do not write "PR Title" or "PR Description" in the fields. No preamble 
"""

    response = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistant that generates PR summaries based on commit messages.",
            },
            {"role": "user", "content": prompt},
        ],
        model="llama-3.1-70b-versatile",
        temperature=0.5,
        max_tokens=500,
    )

    return response.choices[0].message.content


def update_pr(repo_name, pr_number, title, description):
    repo = g.get_repo(repo_name)
    pull_request = repo.get_pull(pr_number)
    pull_request.edit(title=title, body=description)


def main():
    try:
        repo_name = os.environ["GITHUB_REPOSITORY"]
        pr_number = int(os.environ["GITHUB_PR_NUMBER"])

        commit_messages = get_commit_messages(repo_name, pr_number)
        summary = generate_summary(commit_messages)

        # Parse the summary to extract title and description
        lines = summary.split("\n")
        title = lines[0].strip()
        description = "\n".join(lines[1:]).strip()

        update_pr(repo_name, pr_number, title, description)
    except KeyError as e:
        print(f"Missing environment variable: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
