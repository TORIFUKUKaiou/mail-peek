"""mailpeek で扱うデータモデルを定義するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmailSummary:
    """未読メール一覧表示用のサマリーデータ。"""

    uid: str
    date: str
    from_: str
    subject: str


@dataclass(frozen=True)
class EmailDetail:
    """メール詳細表示用のデータ。"""

    uid: str
    date: str
    from_: str
    to: str
    subject: str
    body: str
    has_attachments: bool
    attachment_names: list[str]
