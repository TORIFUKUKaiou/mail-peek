"""Rich を使った出力整形モジュール。"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from rich.table import Table
from rich.text import Text

from mail_peek.models import EmailDetail, EmailSummary


console = Console()


def _sanitize_terminal_text(value: str) -> str:
    """通常の改行を保ちつつ、端末制御文字を可視化する。"""
    value = value.replace("\r\n", "\n")
    sanitized: list[str] = []
    for char in value:
        codepoint = ord(char)
        if char == "\n":
            sanitized.append(char)
        elif codepoint < 0x20 or 0x7F <= codepoint <= 0x9F:
            sanitized.append(f"\\x{codepoint:02x}")
        else:
            sanitized.append(char)
    return "".join(sanitized)


def _mail_text(value: str) -> Text:
    """Rich マークアップを解釈しないメール表示用テキストを作る。"""
    return Text(_sanitize_terminal_text(value))


def _append_header_field(header: Text, label: str, value: str) -> None:
    """安全に整形したメールヘッダ項目を追加する。"""
    if header.plain:
        header.append("\n")
    header.append(f"{label}:", style="bold")
    header.append(" ")
    header.append_text(_mail_text(value))


@contextmanager
def show_status(message: str) -> Generator[Status, None, None]:
    """処理中のステータス表示を提供するコンテキストマネージャ。

    Args:
        message: 表示するメッセージ。

    Yields:
        Status: Rich のステータスインスタンス。
    """
    with console.status(message) as status:
        yield status


def render_unread_table(summaries: list[EmailSummary]) -> None:
    """未読メール一覧を Rich Table で表示する。

    Args:
        summaries: 表示する未読メールのリスト。
    """
    if not summaries:
        console.print("[dim]No unread emails.[/dim]")
        return

    table = Table(title="Unread Emails", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Date", style="magenta")
    table.add_column("From", style="green")
    table.add_column("Subject", style="white")

    for summary in summaries:
        table.add_row(
            _mail_text(summary.uid),
            _mail_text(summary.date),
            _mail_text(summary.from_),
            _mail_text(summary.subject),
        )

    console.print(table)


def render_email_detail(detail: EmailDetail) -> None:
    """メール詳細を Rich Panel で表示する。

    Args:
        detail: 表示するメール詳細データ。
    """
    header = Text()
    _append_header_field(header, "Date", detail.date)
    _append_header_field(header, "From", detail.from_)
    _append_header_field(header, "To", detail.to)
    _append_header_field(header, "Subject", detail.subject)

    if detail.has_attachments:
        names = ", ".join(detail.attachment_names) or "(filename unknown)"
        _append_header_field(header, "Attachments", names)
    else:
        _append_header_field(header, "Attachments", "None")

    title = Text("Email ")
    title.append_text(_mail_text(detail.uid))
    console.print(Panel(header, title=title))

    body = _mail_text(detail.body) if detail.body.strip() else Text("(No body)", style="dim")
    console.print(Panel(body, title="Body", expand=False))


def show_error(message: str) -> None:
    """エラーメッセージを Rich Panel で表示する。

    Args:
        message: 表示するエラーメッセージ。
    """
    error_text = _mail_text(message)
    error_text.stylize("bold red")
    console.print(Panel(error_text, title="Error", border_style="red"))
