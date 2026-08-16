"""メール本文・添付ファイル抽出の回帰テスト。"""

from __future__ import annotations

import unittest
from email.message import EmailMessage

from mail_peek.extractor import extract_attachments, extract_body


class ExtractorTests(unittest.TestCase):
    """添付ファイルが本文として扱われないことを確認する。"""

    def test_skips_text_attachment_when_selecting_body(self) -> None:
        message = EmailMessage()
        message.make_mixed()

        attachment = EmailMessage()
        attachment.set_content("attachment-text")
        attachment["Content-Disposition"] = "attachment"
        message.attach(attachment)

        body = EmailMessage()
        body.set_content("real-body")
        message.attach(body)

        self.assertEqual(extract_body(message), "real-body\n")

    def test_detects_attachment_without_filename(self) -> None:
        message = EmailMessage()
        message.make_mixed()

        attachment = EmailMessage()
        attachment.set_content("attachment-text")
        attachment["Content-Disposition"] = "attachment"
        message.attach(attachment)

        self.assertEqual(extract_attachments(message), (True, []))


if __name__ == "__main__":
    unittest.main()
