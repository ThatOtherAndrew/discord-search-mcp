import os
from discord_search_mcp.client import Client


def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("DISCORD_TOKEN environment variable not set")

    client = Client(token)


if __name__ == '__main__':
    main()
