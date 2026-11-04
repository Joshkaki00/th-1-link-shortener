# Link Shortener API

Flask + SQLite API: shorten a URL, redirect by code (counting visits), and read visit stats.

| Method | Path | Behavior |
|--------|------|----------|
| `GET` | `/` or `/health` | Liveness → `200` + `{"status":"ok"}` |
| `POST` | `/links` | Body `{"url": "https://..."}` → `201` + `code`, `url` |
| `GET` | `/<code>` | `302` to original URL; increments `visits` |
| `GET` | `/links/<code>/stats` | `200` + `code`, `url`, `visits` (no increment) |

Invalid/missing URLs → `4xx`. Unknown codes → `404`.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app run --debug
```

Server: [http://127.0.0.1:5000](http://127.0.0.1:5000)

```bash
pytest
```

## Example requests

```bash
# Health
curl -s http://127.0.0.1:5000/health
# → {"status":"ok"}

# Create
curl -s -X POST http://127.0.0.1:5000/links \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/path"}'
# → {"code":"Ab12Cd34","url":"https://example.com/path"}

# Redirect (follow with -L, or inspect headers)
curl -sI http://127.0.0.1:5000/Ab12Cd34
# → 302 Location: https://example.com/path

# Stats
curl -s http://127.0.0.1:5000/links/Ab12Cd34/stats
# → {"code":"Ab12Cd34","url":"https://example.com/path","visits":1}
```

## Design notes

- **Flask application factory** (`create_app`) so tests pass a temp **file** SQLite DB (not `:memory:` — Flask opens a new connection per request).
- Routes registered on the app: `create_link`, `redirect_code`, `link_stats`.
- Short codes: 8-char `secrets`-based alphabet; HTTP(S) URL validation via `urllib.parse`.
- Visit count lives on the link row; only redirects bump it.

## With more time

- Clearer JSON error bodies and consistent status codes (v1.1)
- Collision retry / uniqueness under concurrent creates
- Optional `last_accessed` timestamp
- Custom aliases, link TTL/expiry, basic rate limiting (v1.2)
- Extract shared DB helpers to trim duplicated schema setup in routes
