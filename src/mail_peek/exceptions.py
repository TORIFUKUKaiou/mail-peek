"""mailpeek 用のカスタム例外を定義するモジュール。"""


class MailPeekError(Exception):
    """mailpeek 全般の基底例外。"""

    pass


class ConfigError(MailPeekError):
    """環境変数の読み込みや検証に失敗した場合の例外。"""

    pass


class ConnectionError(MailPeekError):
    """IMAP サーバーへの接続に失敗した場合の例外。"""

    pass


class AuthenticationError(MailPeekError):
    """IMAP サーバーへの認証に失敗した場合の例外。"""

    pass


class FetchError(MailPeekError):
    """メールの取得に失敗した場合の例外。"""

    pass


class NotFoundError(MailPeekError):
    """指定した ID のメールが存在しない場合の例外。"""

    pass


class InvalidUidError(MailPeekError):
    """指定された IMAP UID が単一メールを指さない場合の例外。"""

    pass
