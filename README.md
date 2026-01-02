# seo-mcp-server

Official MCP server for SEOMCP (https://seomcp.run). Specialized tools for SEO optimization and preparation (including GEO, AEO) of sites and content. Connects your AI agents to professional SEO analytics and data analysis tools.

## Install

```bash
pip install seo-mcp-server
# or
uvx seo-mcp-server
```

## VS Code Configuration

To configure the server globally, edit the `mcp.json` file:

- **Linux**: `~/.config/Code/User/mcp.json`
- **MacOS**: `~/Library/Application Support/Code/User/mcp.json`
- **Windows**: `%APPDATA%\Code\User\mcp.json`

```json
{
	"servers": {
		"seo-mcp-server": {
			"type": "stdio",
			"command": "uvx",
			"args": ["seo-mcp-server"],
			"env": {
				"SEOMCP_API_KEY": "seomcp-...",
				"SEOMCP_API_URL": "https://api.seomcp.run"
			}
		}
	}
}
```

You can also create a project-specific config in `.vscode/mcp.json` with the same content.

## Claude Desktop config

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "seo-mcp-server": {
      "command": "uvx",
      "args": [
        "seo-mcp-server"
      ],
      "env": {
        "SEOMCP_API_KEY": "seomcp-...",
        "SEOMCP_API_URL": "https://api.seomcp.run"
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
- ...

## Get API Key

To use this MCP server, you need an API key.

1. Go to [console.seomcp.run](https://console.seomcp.run).
2. Log in and generate a new key.
3. Use this key as `SEOMCP_API_KEY` in your configuration.
