"""IMAP クライアントの安全境界に関する回帰テスト。"""

from __future__ import annotations

import ssl
import unittest
from unittest.mock import patch

from mail_peek.config import Config
from mail_peek.exceptions import InvalidUidError
from mail_peek.imap_client import IMAPClient


class _FakeIMAP:
    """ネットワーク接続を行わない最小の IMAP モック。"""

    instance: _FakeIMAP | None = None

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.uid_calls: list[tuple[object, ...]] = []
        _FakeIMAP.instance = self

    def login(self, username: str, password: str) -> tuple[str, list[bytes]]:
        return "OK", []

    def select(self, mailbox: str) -> tuple[str, list[bytes]]:
        return "OK", []

    def uid(self, *args: object) -> tuple[str, list[object]]:
        self.uid_calls.append(args)
        return "OK", [(b"1 (BODY[] {1}", b"Subject: test\r\n\r\nbody")]

    def close(self) -> tuple[str, list[bytes]]:
        return "OK", []

    def logout(self) -> tuple[str, list[bytes]]:
        return "BYE", []


class IMAPClientTests(unittest.TestCase):
    """UID 検証と TLS コンテキストを確認する。"""

    def setUp(self) -> None:
        self.config = Config("imap.example.com", 993, "user", "password")

    def test_invalid_uids_never_reach_imap_commands(self) -> None:
        client = IMAPClient(self.config)
        fake_client = _FakeIMAP()
        client._client = fake_client

        for uid in ("0", "01", "1:*", "1,2", "-1", "1\r\nSTORE", "１２"):
            with self.subTest(uid=uid):
                with self.assertRaises(InvalidUidError):
                    client.fetch_detail(uid)
                with self.assertRaises(InvalidUidError):
                    client.mark_seen(uid)

        self.assertEqual(fake_client.uid_calls, [])

    def test_valid_uid_is_used_for_one_message(self) -> None:
        client = IMAPClient(self.config)
        fake_client = _FakeIMAP()
        client._client = fake_client

        detail = client.fetch_detail("42")
        client.mark_seen("42")

        self.assertEqual(detail.uid, "42")
        self.assertEqual(
            fake_client.uid_calls,
            [
                ("FETCH", "42", "(BODY.PEEK[])"),
                ("STORE", "42", "+FLAGS", "(\\Seen)"),
            ],
        )

    def test_tls_context_verifies_server_without_legacy_mode(self) -> None:
        with patch("mail_peek.imap_client.imaplib.IMAP4_SSL", _FakeIMAP):
            client = IMAPClient(self.config)
            client.__enter__()
            try:
                fake_client = _FakeIMAP.instance
                assert fake_client is not None
                context = fake_client.kwargs["ssl_context"]
                assert isinstance(context, ssl.SSLContext)
                self.assertTrue(context.check_hostname)
                self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
                self.assertEqual(context.minimum_version, ssl.TLSVersion.TLSv1_2)
                self.assertFalse(context.options & ssl.OP_LEGACY_SERVER_CONNECT)
            finally:
                client.__exit__(None, None, None)

    def test_docomo_tls_context_allows_legacy_renegotiation(self) -> None:
        docomo_config = Config("imap.spmode.ne.jp", 993, "user", "password")

        with patch("mail_peek.imap_client.imaplib.IMAP4_SSL", _FakeIMAP):
            client = IMAPClient(docomo_config)
            client.__enter__()
            try:
                fake_client = _FakeIMAP.instance
                assert fake_client is not None
                context = fake_client.kwargs["ssl_context"]
                assert isinstance(context, ssl.SSLContext)
                self.assertTrue(context.check_hostname)
                self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
                self.assertEqual(context.minimum_version, ssl.TLSVersion.TLSv1_2)
                self.assertTrue(context.options & ssl.OP_LEGACY_SERVER_CONNECT)
            finally:
                client.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()
