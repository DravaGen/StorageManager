from config import Config

if not Config.BASE_DIRECTORY.exists():
    Config.BASE_DIRECTORY.mkdir(parents=True, exist_ok=True)
