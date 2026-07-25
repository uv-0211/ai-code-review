# AI Code Review

An AI-powered code reviewer for GitHub pull requests, built on Claude. It fetches a PR's diff, asks Claude to find real issues (bugs, security problems, correctness concerns), and can post the results back to the PR as a comment.

It can be used two ways:
- **As a GitHub Action** — reviews run automatically in CI whenever a PR is opened or updated, on the repository owner's own tokens.
- **As an HTTP API** — for interactive use (e.g. from a frontend), with a preview mode that returns issues without posting anything.

## How it works

```
app/
├── api.py          — FastAPI app, POST /review endpoint
├── cli.py           — standalone entrypoint used by the GitHub Action
├── github/          — GitHub API client + comment poster
├── reviewer/          — Claude integration (prompt, response parsing)
├── services/           — orchestration: fetch PR → get diff → review → post
└── models/             — Pydantic request/response schemas
```

Both entrypoints (`api.py` and `cli.py`) call the same `ReviewService` — the core logic has no idea whether it was triggered by an HTTP request or a CI job.

Pipeline for a single review:
1. Fetch the pull request.
2. Check whether it's already been reviewed the maximum allowed number of times — if so, stop.
3. Fetch the diff.
4. Send the diff to Claude with a prompt asking for structured, JSON-formatted issues.
5. Validate the response (Pydantic) and cap it at the configured issue limit.
6. Optionally post the results back to the PR.

## Using it as a GitHub Action

Add a workflow to your repository, e.g. `.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  pull-requests: write   # required so the bot can post comments

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: uv-0211/ai-code-review@v1
        with:
          pr-url: ${{ github.event.pull_request.html_url }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          max-issues: '5'          # optional, defaults to 10
          max-iterations: '2'      # optional, defaults to 1
```

Before this works, add your own `ANTHROPIC_API_KEY` under **Settings → Secrets and variables → Actions → New repository secret**. `GITHUB_TOKEN` is provided automatically by GitHub Actions on every run — you don't create it yourself, but the workflow does need `permissions: pull-requests: write` for it to be allowed to post comments.

> **Trigger note:** use `pull_request`, not `pull_request_target`. This action never checks out or executes anything from the PR itself, but `pull_request_target` runs with the base repo's secrets even for PRs from forks, which is generally unsafe unless you understand the implications for your own workflow.

### Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `pr-url` | yes | — | URL of the pull request to review |
| `github-token` | yes | — | Token used to read the PR and post comments |
| `anthropic-api-key` | yes | — | Your own Anthropic API key |
| `max-issues` | no | `10` | Maximum number of issues to report |
| `max-iterations` | no | `1` | Maximum number of times the bot will re-review the same PR |

## Using it as an HTTP API

```bash
uv run uvicorn app.api:app --reload
```

```bash
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{
        "pr_url": "https://github.com/owner/repo/pull/1",
        "max_issues": 10,
        "max_iterations": 1,
        "should_post_to_pr": false
      }'
```

Set `should_post_to_pr: false` to get the issues back in the response without posting anything to the PR — useful for a preview UI.

Requires `GITHUB_TOKEN` and `ANTHROPIC_API_KEY` in the environment (or a `.env` file).

## Development

```bash
uv sync
uv run pytest tests/ -v
```
