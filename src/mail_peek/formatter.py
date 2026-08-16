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
        table.add_row(summary.uid, summary.date, summary.from_, summary.subject)

    console.print(table)


def render_email_detail(detail: EmailDetail) -> None:
    """メール詳細を Rich Panel で表示する。

    Args:
        detail: 表示するメール詳細データ。
    """
    header_lines = [
        f"[bold]Date:[/bold] {detail.date}",
        f"[bold]From:[/bold] {detail.from_}",
        f"[bold]To:[/bold] {detail.to}",
        f"[bold]Subject:[/bold] {detail.subject}",
    ]

    if detail.has_attachments:
        names = ", ".join(detail.attachment_names) or "(filename unknown)"
        header_lines.append(f"[bold]Attachments:[/bold] {names}")
    else:
        header_lines.append("[bold]Attachments:[/bold] None")

    header = "\n".join(header_lines)
    console.print(Panel(header, title=f"Email {detail.uid}"))

    body = detail.body if detail.body.strip() else "[dim](No body)[/dim]"
    console.print(Panel(body, title="Body", expand=False))


def show_error(message: str) -> None:
    """エラーメッセージを Rich Panel で表示する。

    Args:
        message: 表示するエラーメッセージ。
    """
    console.print(Panel(Text(message, style="bold red"), title="Error", border_style="red"))
