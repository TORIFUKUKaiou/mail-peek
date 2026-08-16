"""Typer ベースの CLI エントリ。"""

from __future__ import annotations

import typer

from mail_peek.config import Config
from mail_peek.exceptions import MailPeekError
from mail_peek.formatter import render_email_detail, render_unread_table, show_error, show_status
from mail_peek.imap_client import IMAPClient

app = typer.Typer(help="Peek at unread IMAP emails.")


@app.command()
def unread() -> None:
    """未読メールを新しい順で最大 10 件表示する。"""
    try:
        config = Config.from_env()
        with show_status("Connecting to IMAP server..."):
            with IMAPClient(config) as client:
                summaries = client.list_unread(limit=10)
        render_unread_table(summaries)
    except MailPeekError as exc:
        show_error(str(exc))
        raise typer.Exit(1) from exc


@app.command()
def read(uid: str = typer.Argument(..., help="メールの ID（IMAP UID）")) -> None:
    """指定した ID のメールを表示し、既読にする。"""
    try:
        config = Config.from_env()
        with show_status("Connecting to IMAP server..."):
            with IMAPClient(config) as client:
                detail = client.fetch_detail(uid)
                render_email_detail(detail)
                client.mark_seen(uid)
    except MailPeekError as exc:
        show_error(str(exc))
        raise typer.Exit(1) from exc
