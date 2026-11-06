import argparse
import secrets
from pathlib import Path

from cryptography.fernet import Fernet


def initialise() -> None:
    env_path = Path(".env")
    if env_path.exists():
        raise SystemExit(".env already exists; refusing to overwrite it.")
    admin_token = secrets.token_urlsafe(36)
    encryption_key = Fernet.generate_key().decode("ascii")
    env_path.write_text(
        "# Generated locally. Never commit this file.\n"
        f"MERGEMIND_ADMIN_TOKEN={admin_token}\n"
        f"MERGEMIND_ENCRYPTION_KEY={encryption_key}\n"
        "MERGEMIND_DATABASE_PATH=data/mergemind.sqlite3\n"
        "MERGEMIND_LLM_BASE_URL=http://127.0.0.1:11434/v1\n"
        "MERGEMIND_LLM_API_KEY=ollama\n"
        "MERGEMIND_LLM_MODEL=qwen2.5-coder:3b\n",
        encoding="utf-8",
    )
    print("Created .env with a random admin token and encryption key.")
    print("Keep .env private. Start the app with: uvicorn backend.app.main:app --host 127.0.0.1 --port 8000")


def main() -> None:
    parser = argparse.ArgumentParser(prog="mergemind")
    parser.add_argument("command", choices=["init"])
    args = parser.parse_args()
    if args.command == "init":
        initialise()


if __name__ == "__main__":
    main()
