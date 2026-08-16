"""mailpeek - CLI to peek at unread IMAP emails."""

from mail_peek.cli import app

def main() -> None:
    """CLI のエントリポイント。"""
    app()
