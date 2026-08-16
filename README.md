# mailpeek

IMAP サーバーに接続して、未読メールを「ちょっと覗く」ための CLI ツールです。

> "peek" は "ちょっと覗く" という意味です。
> 作者は『進撃の巨人』のピーク・フィンガー（Pieck Finger）も連想しています。

## 必要条件

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- [direnv](https://direnv.net/)

## セットアップ

```bash
# リポジトリをクローンして移動
git clone <repository-url>
cd mail-peek

# 依存関係をインストール
uv sync

# 下記を参考に .envrc を作成する
```

## 環境変数

`.envrc` に以下の環境変数を設定してください。

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `IMAP_HOST` | IMAP サーバーのホスト | `imap.example.com` |
| `IMAP_PORT` | IMAP サーバーのポート | `993` |
| `IMAP_USERNAME` | ログインユーザー名 | `user@example.com` |
| `IMAP_PASSWORD` | ログインパスワード（ドコモメールでは IMAP 専用パスワード） | `password` |

`.envrc` の例:

```bash
export IMAP_HOST="imap.example.com"
export IMAP_PORT="993"
export IMAP_USERNAME="user@example.com"
export IMAP_PASSWORD="password"
```

設定後に `.envrc` を有効化します。

```bash
direnv allow
```

### ドコモメールの場合

パソコンから利用する場合は、以下を設定します。

- `IMAP_HOST`: `imap.spmode.ne.jp`
- `IMAP_PORT`: `993`
- `IMAP_USERNAME`: dアカウント ID
- `IMAP_PASSWORD`: IMAP 専用パスワード

dアカウントの利用設定を有効にしたうえで、IMAP 専用パスワードを使用してください。詳細は[ドコモ公式の設定項目](https://www.docomo.ne.jp/service/docomo_mail/other/)を参照してください。

ドコモの既知の IMAP ホストでは、接続互換性のため legacy TLS renegotiation を有効にします。この例外はドコモホストにのみ限定し、証明書検証と TLS 1.2 以上は維持します。

## コマンド例

### 未読メール一覧

```bash
uv run mailpeek unread
```

未読メールを新しい順で最大 10 件表示します。

### メール詳細表示

```bash
uv run mailpeek read 1
```

`unread` に表示された正の十進数の ID（IMAP UID）を指定します。表示が成功すると、自動的に既読フラグが付きます。

## 注意事項

- メールの送信や削除は行いません。ただし、`read` は対象メールに既読（`\Seen`）フラグを付けます。
- 添付ファイルは検出・ファイル名表示のみ行い、保存はしません。
