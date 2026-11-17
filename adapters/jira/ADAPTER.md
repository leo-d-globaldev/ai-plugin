# Adapter: jira

Maps the two operations of `../OPERATIONS.md` to Jira (Cloud or Data Center). Most outsourcing customers use Jira; the project's Jira belongs to the customer, so read only what the work needs and comment only when the person asks.

## Which connection

In this order, use the first that answers:

1. **Atlassian MCP connector** (claude.ai connector or the `atlassian` plugin; tools such as `getJiraIssue`, `addCommentToJiraIssue`). Load with ToolSearch, query `jira issue comment`. Not signed in → tell the person to sign in with `/mcp`.
2. **REST API** with the person's own token, only when the connector is not available and the customer allows API access: env vars `JIRA_BASE_URL`, `JIRA_EMAIL` and `JIRA_API_TOKEN` (Cloud) or `JIRA_PAT` (Data Center). Check with `[ -n "$JIRA_API_TOKEN" ]`; never print a token, write it to a file or ask for it in chat. Use it only in the `curl` header.

Neither → result `failed`: say which one to set up, and go on from the repo.

## Operations

| Operation | MCP | REST |
|---|---|---|
| `get-item` | `getJiraIssue(issueIdOrKey=<KEY>)` (pass the cloud id when the tool asks for it) | `GET $JIRA_BASE_URL/rest/api/3/issue/<KEY>?fields=*navigable&expand=names` (Data Center: `/rest/api/2/`); `names` maps `customfield_NNNNN` to field names, so the acceptance field is found by its name |
| `add-comment` | `addCommentToJiraIssue(issueIdOrKey=<KEY>, commentBody=<text>)` | `POST .../issue/<KEY>/comment` with body `{"body": ...}` (Cloud v3 wants Atlassian Document Format: one paragraph per line) |

Acceptance criteria: often a custom field (the name contains "Acceptance"); else a heading or list in the description. Jira Cloud returns the description as Atlassian Document Format: read the text of its paragraphs and list items.

## Result codes

- `not-found`: 404.
- `failed`: 401/403 (credential or permission), connector missing, network error.
