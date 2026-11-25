# Adapter: windshift

Maps the two operations of `../OPERATIONS.md` to GlobalDev's Windshift (`https://windshift.globaldev.asia`), through the plugin's MCP connector `windshift` (OAuth).

## Loading the tools

The tools are deferred: load them with ToolSearch, query `windshift get_item add_comment`. Their names carry a server prefix that differs by install (`mcp__windshift__get_item`, `mcp__plugin_gdv-ai-kit_windshift__get_item`, `mcp__<uuid>__get_item` for an organisation connector): match on the suffix `get_item` / `add_comment` of a Windshift server. No tool found → the connector is not signed in: tell the person to sign in to `windshift` with `/mcp` (result `failed`). Do not use the Plane tools, even when a Plane plugin is installed.

## Operations

| Operation | Call | Notes |
|---|---|---|
| `get-item` | `get_item(item_key=<KEY>, full_description=true)`; a URL → take the key or numeric id (`item_id`) from it | Without `full_description=true` the description is cut at 500 characters. Acceptance criteria live in the description (look for a heading or list named Acceptance / AC / Tiêu chí). Status name is `status` |
| `add-comment` | `add_comment(item_key=<KEY>, content=<text>)` | Plain text; put one fact per line |

## Result codes

- `not-found`: `get_item` says the item does not exist.
- `failed`: tools missing (not signed in), permission denied, network error.

## Credentials

OAuth only: the person signs in with `/mcp`. Nothing goes into chat.
