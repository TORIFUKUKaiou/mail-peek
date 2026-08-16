"""IMAP サーバーとの通信を担当するモジュール。"""

from __future__ import annotations

import imaplib
import ssl
from email import message_from_bytes
from email.message import EmailMessage
from typing import cast

from mail_peek.config import Config
from mail_peek.exceptions import (
    AuthenticationError,
    ConnectionError,
    FetchError,
    InvalidUidError,
    NotFoundError,
)
from mail_peek.extractor import build_email_detail, decode_header_value
from mail_peek.models import EmailDetail, EmailSummary


_DOCOMO_LEGACY_RENEGOTIATION_HOSTS = frozenset(
    {"imap.spmode.ne.jp", "imap2.spmode.ne.jp"}
)


class IMAPClient:
    """IMAP4_SSL をラップしたクライアント。

    コンテキストマネージャとして使用し、確実に接続を解放する。
    """

    def __init__(self, config: Config) -> None:
        """クライアントを初期化する。

        Args:
            config: IMAP 接続設定。
        """
        self._config = config
        self._client: imaplib.IMAP4_SSL | None = None

    def __enter__(self) -> IMAPClient:
        """IMAP サーバーに接続・ログインする。

        Returns:
            IMAPClient: 自身のインスタンス。

        Raises:
            ConnectionError: 接続に失敗した場合。
            AuthenticationError: 認証に失敗した場合。
        """
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            if self._config.host.rstrip(".").lower() in _DOCOMO_LEGACY_RENEGOTIATION_HOSTS:
                # ドコモの IMAP サーバーが legacy renegotiation を要求するため。
                # 既知のドコモホストに限定し、証明書検証と TLS 1.2 以上は維持する。
                ssl_context.options |= ssl.OP_LEGACY_SERVER_CONNECT
            self._client = imaplib.IMAP4_SSL(
                host=self._config.host,
                port=self._config.port,
                timeout=30,
                ssl_context=ssl_context,
            )
        except (OSError, imaplib.IMAP4.error) as exc:
            raise ConnectionError(
                f"Could not connect to IMAP server "
                f"({self._config.host}:{self._config.port})."
            ) from exc

        try:
            self._client.login(self._config.username, self._config.password)
        except imaplib.IMAP4.error as exc:
            raise AuthenticationError(
                "Authentication failed. Please check IMAP_USERNAME and IMAP_PASSWORD."
            ) from exc

        try:
            status, _ = self._client.select("INBOX")
            if status != "OK":
                raise ConnectionError("Could not select INBOX.")
        except imaplib.IMAP4.error as exc:
            raise ConnectionError("Could not select INBOX.") from exc

        return self

    def __exit__(self, *exc_info: object) -> None:
        """接続をクローズする。"""
        if self._client is not None:
            try:
                self._client.close()
                self._client.logout()
            except (OSError, imaplib.IMAP4.error):
                pass
            finally:
                self._client = None

    def list_unread(self, limit: int = 10) -> list[EmailSummary]:
        """未読メールを新しい順で最大 limit 件取得する。

        Args:
            limit: 取得する最大件数。デフォルトは 10。

        Returns:
            list[EmailSummary]: 未読メールのサマリーリスト。

        Raises:
            FetchError: メール一覧の取得に失敗した場合。
        """
        client = self._require_client()

        try:
            status, data = client.uid("SEARCH", "UNSEEN")
            if status != "OK" or data is None:
                raise FetchError("Failed to search unread emails.")

            raw_uids = data[0].split() if data[0] else []
            # 新しい順にソートするため数値として降順に並べる
            sorted_uids = sorted(
                (uid.decode() if isinstance(uid, bytes) else uid for uid in raw_uids),
                key=lambda uid: int(uid),
                reverse=True,
            )
            target_uids = sorted_uids[:limit]
        except (ValueError, imaplib.IMAP4.error) as exc:
            raise FetchError("Failed to search unread emails.") from exc

        summaries: list[EmailSummary] = []
        for uid in target_uids:
            detail = self._fetch_summary(uid)
            if detail is not None:
                summaries.append(detail)

        return summaries

    def fetch_detail(self, uid: str) -> EmailDetail:
        """指定した UID のメール詳細を取得する。

        Args:
            uid: メールの UID。

        Returns:
            EmailDetail: メール詳細データ。

        Raises:
            InvalidUidError: UID が単一の正の十進数でない場合。
            NotFoundError: メールが存在しない場合。
            FetchError: 取得に失敗した場合。
        """
        uid = self.validate_uid(uid)
        client = self._require_client()

        try:
            status, data = client.uid("FETCH", uid, "(BODY.PEEK[])")
            if status != "OK" or data is None or data[0] is None:
                raise NotFoundError(f"Email with ID \"{uid}\" was not found.")

            raw_message = data[0][1]
            message = cast(EmailMessage, message_from_bytes(raw_message))
            return build_email_detail(uid, message)
        except (NotFoundError, FetchError):
            raise
        except imaplib.IMAP4.error as exc:
            raise FetchError(f"Failed to fetch email with ID \"{uid}\".") from exc

    def mark_seen(self, uid: str) -> None:
        """指定した UID のメールに \\Seen フラグを付与する。

        Args:
            uid: メールの UID。

        Raises:
            InvalidUidError: UID が単一の正の十進数でない場合。
            FetchError: フラグの更新に失敗した場合。
        """
        uid = self.validate_uid(uid)
        client = self._require_client()

        try:
            status, _ = client.uid("STORE", uid, "+FLAGS", "(\\Seen)")
            if status != "OK":
                raise FetchError(f"Failed to mark email {uid} as seen.")
        except imaplib.IMAP4.error as exc:
            raise FetchError(f"Failed to mark email {uid} as seen.") from exc

    @staticmethod
    def validate_uid(uid: str) -> str:
        """単一メールを指す IMAP UID か検証する。

        IMAP の UID コマンドは ``1:*`` のような集合指定も受け付ける。
        この CLI では単一メールのみを対象とするため、RFC で定義される
        32 ビットの正の十進数 UID に限定する。

        Args:
            uid: 検証対象の UID。

        Returns:
            検証済みの UID。

        Raises:
            InvalidUidError: UID が単一の正の十進数でない場合。
        """
        if (
            not isinstance(uid, str)
            or not uid.isascii()
            or not uid.isdecimal()
            or uid.startswith("0")
            or len(uid) > 10
            or int(uid) > 0xFFFFFFFF
        ):
            raise InvalidUidError("Email ID must be a positive decimal IMAP UID.")
        return uid

    def _require_client(self) -> imaplib.IMAP4_SSL:
        """クライアントが接続済みか確認して返す。

        Returns:
            imaplib.IMAP4_SSL: 接続済みの IMAP クライアント。

        Raises:
            ConnectionError: 未接続の場合。
        """
        if self._client is None:
            raise ConnectionError("IMAP client is not connected.")
        return self._client

    def _fetch_summary(self, uid: str) -> EmailSummary | None:
        """単一メールのヘッダ情報から EmailSummary を作成する。

        Args:
            uid: メールの UID。

        Returns:
            EmailSummary | None: 取得成功時はサマリー、失敗時は None。
        """
        client = self._require_client()

        try:
            status, data = client.uid("FETCH", uid, "(BODY.PEEK[HEADER])")
            if status != "OK" or data is None or data[0] is None:
                return None

            raw_header = data[0][1]
            message = cast(EmailMessage, message_from_bytes(raw_header))
            return EmailSummary(
                uid=uid,
                date=decode_header_value(message.get("Date", "")),
                from_=decode_header_value(message.get("From", "")),
                subject=decode_header_value(message.get("Subject", "")),
            )
        except (imaplib.IMAP4.error, ValueError):
            return None
