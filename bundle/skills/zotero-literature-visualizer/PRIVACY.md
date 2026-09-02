# Privacy and safe sharing

This repository contains source code, instructions, and synthetic demo metadata only. It must not contain a user's research library or authentication state.

Before publishing a fork or release, confirm that it contains none of the following:

- names, personal email addresses, institutional identifiers, or local usernames;
- API keys, passwords, cookies, access tokens, or browser profiles;
- absolute local filesystem paths;
- `zotero.sqlite`, Zotero storage folders, or database snapshots;
- downloaded PDFs, extracted full text, personal notes, reading status, or generated dashboards;
- run logs, metadata exports, write-back packages, or caches.

Keep user data in a separate run directory outside the skill. The local Zotero workflow reads a temporary snapshot and does not modify the source database. Web API writes require an explicit key supplied at runtime and should be tested with `--dry-run` when supported.

The bundled `scripts/quick_validate.py` performs an offline portability scan and smoke test. Run it before every public release, then inspect the archive manually as a second check.
