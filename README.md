# seo-mcp-server

Public stdio client for the private `seomcp-backend`. Exposes SEO article tools via MCP.

## Install

```bash
pip install seo-mcp-server
# or
uvx seo-mcp-server
```

## VS Code mcp.json

```json
{
	"servers": {
		"seo-mcp-server": {
			"type": "stdio",
			"command": "uvx",
			"args": ["seo-mcp-server"],
			"env": {
				"SEOMCP_API_KEY": "sk_...",
					"SEOMCP_BACKEND_URL": "https://api.seomcp.run"
			}
		}
	}
}
```

## Tools
- analyze_serp(keyword)
- research_perplexity(keyword, patterns)
- brainstorm_outline(patterns, facts)
- gather_details(outline)
- generate_article(outline, facts, details)
- embed_links(article, research)

## Firebase Dashboard (app.seomcp.run)
- Google Sign-In
- Generate/list/delete API keys
- Functions: generate_api_key, list_api_keys, delete_api_key

## Structure
```
src/seo_mcp_server/      # stdio client
firebase/functions/      # key mgmt APIs
firebase/public/         # dashboard UI
pyproject.toml
```
