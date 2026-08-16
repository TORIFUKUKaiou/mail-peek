"""環境変数から設定を読み込むモジュール。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from mail_peek.exceptions import ConfigError


@dataclass(frozen=True)
class Config:
    """IMAP 接続に必要な設定を保持するデータクラス。"""

    host: str
    port: int
    username: str
    password: str

    @classmethod
    def from_env(cls) -> Config:
        """環境変数から設定を読み込む。

        Returns:
            Config: 読み込んだ設定。

        Raises:
            ConfigError: 必須の環境変数が不足している場合。
        """
        required_vars = ["IMAP_HOST", "IMAP_PORT", "IMAP_USERNAME", "IMAP_PASSWORD"]
        missing = [name for name in required_vars if not os.environ.get(name)]
        if missing:
            raise ConfigError(
                "The following environment variables are not set: "
                + ", ".join(missing)
            )

        host = os.environ["IMAP_HOST"]
        username = os.environ["IMAP_USERNAME"]
        password = os.environ["IMAP_PASSWORD"]

        try:
            port = int(os.environ["IMAP_PORT"])
        except ValueError as exc:
            raise ConfigError(
                f"IMAP_PORT must be an integer: {os.environ['IMAP_PORT']}"
            ) from exc

        return cls(
            host=host,
            port=port,
            username=username,
            password=password,
        )
