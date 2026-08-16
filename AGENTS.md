# Repository Guidelines

## Project Structure & Module Organization

`mailpeek` is a Python CLI for safely viewing IMAP mail. Application code lives in `src/mail_peek/`:

- `cli.py` defines the Typer commands and user-facing error handling.
- `config.py` reads IMAP configuration from the environment.
- `imap_client.py` owns IMAP/TLS communication and UID validation.
- `extractor.py`, `formatter.py`, and `models.py` parse mail and render output.

Keep new functionality in the module that owns the concern; avoid putting protocol, parsing, and terminal-rendering logic in CLI commands. Regression tests mirror the relevant behavior in `tests/test_*.py`.

## Build, Test, and Development Commands

- `uv sync` installs the Python 3.14 project environment and dependencies.
- `uv run mailpeek unread` lists up to ten unread messages using `IMAP_*` environment variables.
- `uv run mailpeek read 42` displays UID `42` and marks it seen; use a non-production mailbox when manually testing.
- `uv run python -m unittest discover -s tests` runs the full test suite.
- `uv build` produces distributable artifacts in `dist/`.

Create local credentials in `.envrc` and activate them with `direnv allow`. Never commit `.envrc`, passwords, or message contents.

## Coding Style & Naming Conventions

Use four-space indentation, type annotations, `from __future__ import annotations`, and standard-library-first imports, matching existing modules. Use `snake_case` for functions, variables, and modules; `PascalCase` for classes; keep internal helpers prefixed with `_`. Prefer frozen dataclasses for immutable mail data. Write short docstrings for public classes and non-obvious behavior. No formatter or linter is configured, so preserve the surrounding code style and keep changes focused.

## Testing Guidelines

Tests use `unittest`, with descriptive `test_<behavior>` method names in `tests/test_<module>.py`. Mock IMAP and terminal interfaces: tests must not contact a live mail server or depend on credentials. Add a regression test for each parsing, security, TLS, UID-validation, or terminal-output fix. There is no enforced coverage threshold; maintain or improve coverage around changed code.

## Docomo IMAP TLS Compatibility

Both known Docomo endpoints, `imap.spmode.ne.jp` and `imap2.spmode.ne.jp`, require `ssl.OP_LEGACY_SERVER_CONNECT` for TLS negotiation. Apply this exception only to these exact hostnames; never use a suffix match or enable it for arbitrary IMAP hosts. Retain `ssl.create_default_context()`, hostname verification, and TLS 1.2 as the minimum version. Do not remove or expand this exception without an authorized, authentication-free TLS handshake comparison against the affected endpoint.

## Untrusted Mail Rendering

Treat all mail-derived values—headers, body text, attachment names, and server-provided UIDs—as untrusted terminal input. Normalize ordinary CRLF line endings to LF before sanitization, visibly escape lone CR and C0/C1 control characters, and pass Rich `Text` objects rather than raw strings. Rendering regression tests must cover literal Rich markup and ANSI/OSC control sequences.

## Live Mailbox Verification

Unit tests must remain offline. Perform a live mailbox check only with explicit user authorization, and never print, paste, commit, or otherwise retain message contents. `read` changes the target message by adding `\Seen`; prefer an authentication-free TLS check, authentication plus INBOX selection, or `list_unread(limit=0)` when validating connectivity without retrieving messages.

## Secret-release Checks

Before publishing, audit the complete local Git object history, including all refs, reflogs, and unreachable objects—not only the working tree. Keep `.envrc` and every local credential file untracked, and do not expose credentials or mail contents in terminal captures, commits, pull requests, or issue reports.

## Commit & Pull Request Guidelines

Recent commits use concise imperative subjects, e.g. `Fix Docomo IMAP TLS compatibility` and `Normalize email CRLF line endings`. Keep commits small and scoped. In pull requests, explain the behavioral change, list test commands run, link related issues when applicable, and include terminal output or screenshots for CLI rendering changes. Call out any effect on credentials, TLS, IMAP flags, or message safety.
