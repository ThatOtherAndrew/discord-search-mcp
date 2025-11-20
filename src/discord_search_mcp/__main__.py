import os
import sys
from discord_search_mcp.mcp import main

def run_module():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print('Error: DISCORD_TOKEN environment variable not set', file=sys.stderr)
        sys.exit(1)

    main()

if __name__ == '__main__':
    run_module()
