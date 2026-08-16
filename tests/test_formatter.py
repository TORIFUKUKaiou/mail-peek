"""メール由来文字列の端末表示に関する回帰テスト。"""

from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from rich.console import Console

from mail_peek import formatter
from mail_peek.models import EmailDetail, EmailSummary


class FormatterTests(unittest.TestCase):
    """Rich にメール由来の文字列を安全に渡すことを確認する。"""

    def _console_and_output(self) -> tuple[Console, io.StringIO]:
        output = io.StringIO()
        return Console(file=output, color_system=None, width=120), output

    def test_unread_table_preserves_markup_as_literal_and_removes_controls(self) -> None:
        console, output = self._console_and_output()
        payload = "[red]fake[/red]\x1b]8;;https://example.invalid\x1b\\link\x1b]8;;\x1b\\"
        summary = EmailSummary(uid="1", date="today", from_=payload, subject=payload)

        with patch.object(formatter, "console", console):
            formatter.render_unread_table([summary])

        rendered = output.getvalue()
        self.assertIn("[red]fake[/red]", rendered)
        self.assertIn(r"\x1b", rendered)
        self.assertNotIn("\x1b", rendered)

    def test_email_detail_safely_renders_all_mail_fields(self) -> None:
        console, output = self._console_and_output()
        payload = "[link=https://example.invalid]fake[/link]\x1b]8;;https://example.invalid\x1b\\"
        detail = EmailDetail(
            uid="1",
            date=payload,
            from_=payload,
            to=payload,
            subject=payload,
            body=payload,
            has_attachments=True,
            attachment_names=[payload],
        )

        with patch.object(formatter, "console", console):
            formatter.render_email_detail(detail)

        rendered = output.getvalue()
        self.assertIn("[link=https://example.invalid]fake[/link]", rendered)
        self.assertIn(r"\x1b", rendered)
        self.assertNotIn("\x1b", rendered)

    def test_normalizes_normal_crlf_line_endings(self) -> None:
        self.assertEqual(
            formatter._sanitize_terminal_text("first\r\nsecond\r\n"),
            "first\nsecond\n",
        )
        self.assertEqual(
            formatter._sanitize_terminal_text("first\rsecond"),
            r"first\x0dsecond",
        )


if __name__ == "__main__":
    unittest.main()
