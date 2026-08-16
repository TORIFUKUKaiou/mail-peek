"""email.message から本文や添付ファイル情報を抽出するモジュール。"""

from __future__ import annotations

from email.header import decode_header, make_header
from email.message import EmailMessage
from html.parser import HTMLParser

from mail_peek.models import EmailDetail


class _HTMLTextExtractor(HTMLParser):
    """HTML からテキストを抽出するためのパーサー。"""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """開始タグを処理する。"""
        if tag in ("script", "style"):
            self._skip_tag = tag
        if tag in ("br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        """終了タグを処理する。"""
        if tag == self._skip_tag:
            self._skip_tag = None
        if tag in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        """タグ内のテキストデータを処理する。"""
        if self._skip_tag is None:
            self._chunks.append(data)

    def get_text(self) -> str:
        """抽出したテキストを返す。"""
        text = "".join(self._chunks)
        # 連続する改行や空白を整える
        lines = [line.strip() for line in text.splitlines()]
        # 連続する空行を 1 つにまとめる
        cleaned: list[str] = []
        prev_empty = False
        for line in lines:
            is_empty = line == ""
            if is_empty and prev_empty:
                continue
            cleaned.append(line)
            prev_empty = is_empty
        return "\n".join(cleaned).strip()


def _decode_payload(part: EmailMessage) -> str:
    """パートのペイロードをデコードして文字列で返す。

    Args:
        part: デコード対象のメールパート。

    Returns:
        str: デコードした文字列。失敗した場合は可能な範囲で文字化けを防ぐ。
    """
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""

    charset = part.get_content_charset()
    if charset:
        try:
            return payload.decode(charset)
        except (LookupError, UnicodeDecodeError):
            pass

    for fallback in ("utf-8", "iso-2022-jp", "shift_jis", "euc-jp", "ascii"):
        try:
            return payload.decode(fallback)
        except UnicodeDecodeError:
            continue

    return payload.decode("utf-8", errors="replace")


def decode_header_value(value: str) -> str:
    """メールヘッダのエンコード済み文字列をデコードする。

    Args:
        value: デコード対象のヘッダ値。

    Returns:
        str: デコードした文字列。
    """
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def extract_body(message: EmailMessage) -> str:
    """メール本文を抽出する。

    text/plain が存在する場合はそれを優先し、存在しない場合のみ
    text/html をテキスト化して返す。

    Args:
        message: 解析対象のメールメッセージ。

    Returns:
        str: 抽出した本文。
    """
    html_part: EmailMessage | None = None

    for part in message.walk():
        if part.is_multipart():
            continue

        if part.get_content_disposition() == "attachment" or part.get_filename():
            continue

        content_type = part.get_content_type()
        if content_type == "text/plain":
            return _decode_payload(part)
        if content_type == "text/html" and html_part is None:
            html_part = part

    if html_part is not None:
        html = _decode_payload(html_part)
        extractor = _HTMLTextExtractor()
        extractor.feed(html)
        return _collapse_blank_lines(extractor.get_text())

    return ""


def _collapse_blank_lines(text: str, max_consecutive: int = 2) -> str:
    """連続する空行を指定した数までに制限する。

    Args:
        text: 処理対象のテキスト。
        max_consecutive: 許容する連続空行の最大数。

    Returns:
        str: 空行を制限したテキスト。
    """
    lines = text.splitlines()
    result: list[str] = []
    blank_count = 0

    for line in lines:
        is_blank = line.strip() == ""
        if is_blank:
            blank_count += 1
            if blank_count <= max_consecutive:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)

    return "\n".join(result).strip()


def extract_attachments(message: EmailMessage) -> tuple[bool, list[str]]:
    """添付ファイルの有無とファイル名一覧を取得する。

    Args:
        message: 解析対象のメールメッセージ。

    Returns:
        tuple[bool, list[str]]: 添付ファイルの有無とファイル名のリスト。
    """
    has_attachments = False
    names: list[str] = []

    for part in message.walk():
        if part.is_multipart():
            continue

        content_disposition = part.get_content_disposition()
        filename = part.get_filename()

        if content_disposition == "attachment" or filename:
            has_attachments = True
            if filename:
                names.append(filename)

    return has_attachments, names


def build_email_detail(uid: str, message: EmailMessage) -> EmailDetail:
    """EmailMessage から EmailDetail を構築する。

    Args:
        uid: メールの UID。
        message: 解析対象のメールメッセージ。

    Returns:
        EmailDetail: 詳細表示用のデータ。
    """
    has_attachments, attachment_names = extract_attachments(message)
    return EmailDetail(
        uid=uid,
        date=decode_header_value(message.get("Date", "")),
        from_=decode_header_value(message.get("From", "")),
        to=decode_header_value(message.get("To", "")),
        subject=decode_header_value(message.get("Subject", "")),
        body=extract_body(message),
        has_attachments=has_attachments,
        attachment_names=attachment_names,
    )
