# Discord Search MCP

An MCP server for intelligently retrieving data from Discord servers via a bot account.

## MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_guild_info` | Get a list of all Discord guilds (servers) accessible to the bot | `include_members`, `include_channels` |
| `get_message` | Fetch a specific message by channel and message ID with full details | `channel_id`, `message_id` |
| `get_message_from_url` | Fetch a Discord message directly from its URL | `url` |
| `get_channel_messages` | Get multiple messages from a channel with token-optimised output | `channel_id`, `message_id`, `direction`, `limit` |
| `search_guild` | Search for messages in a guild by content | `guild_id`, `content`, `limit` |
| `get_active_threads` | Get currently active threads in a guild | `guild_id`, `limit` |
| `get_archived_threads` | Get archived threads from a channel | `channel_id`, `public`, `limit` |
| `get_attachment` | Get a fresh URL for a Discord attachment (URLs expire after 24 hours) | `channel_id`, `message_id`, `filename` |

## Setup Instructions

### Running the MCP server

Make sure you have [created a Discord bot](https://discord.com/developers/docs/quick-start/getting-started#step-1-creating-an-app), and set the `DISCORD_TOKEN` environment variable to your bot's token.

If you have [`uv`](https://docs.astral.sh/uv/) installed, you can run the MCP server directly with `uvx`:

```bash
DISCORD_TOKEN="xxxxx" uvx git+https://github.com/ThatOtherAndrew/discord-search-mcp
```

To install `discord-search-mcp` locally instead, use one of the following commands:

```bash
# Using pip
pip install git+https://github.com/ThatOtherAndrew/discord-search-mcp

# Using uv
uv tool install git+https://github.com/ThatOtherAndrew/discord-search-mcp
```

Then, run the MCP server with:

```bash
# Remember to set the DISCORD_TOKEN environment variable!
discord-search-mcp
```

The default port number is `8000`. You can override this by passing the `PORT` environment variable:

```bash
PORT=1234 discord-search-mcp
# or
DISCORD_TOKEN="xxxxx" PORT=1234 uvx git+https://github.com/ThatOtherAndrew/discord-search-mcp
```

### Configuring your MCP client

#### Claude Code

Use the following command to add the MCP server to your Claude Code user configuration:

```bash
claude mcp add -s user -t http discord-search http://{DOMAIN}:{PORT}/mcp
```

For instance, if you are running the MCP server locally, and using the default port `8000`, the command would be:

```bash
claude mcp add -s user -t http discord-search http://127.0.0.1:8000/mcp
```

## Development

Note that [`uv`](https://docs.astral.sh/uv/) is required for development.

Use the following commands for setup:

```bash
# Clone the repository
git clone https://github.com/ThatOtherAndrew/discord-search-mcp
cd discord-search-mcp

# Install project and dependencies
uv sync
```

To run the MCP server locally for development:

```bash
# Remember to set the DISCORD_TOKEN environment variable!
uv run discord-search-mcp
```

To run the MCP inspector:

```bash
# Remember to set the DISCORD_TOKEN environment variable!
uv run mcp dev src/discord_search_mcp/mcp.py
```
