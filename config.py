import json

with open("config.json", "r") as f:
    config = json.loads(f.read())

TOKEN = config.get("token")
WORKERS = config.get("workers", 32)
ADMIN_LIST = config.get("admin_list", None)
OPEN_LOBBY = config.get("open_lobby", True)
MIN_PLAYERS = config.get("min_players", 2)  # TODO: set to 3
