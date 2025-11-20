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
