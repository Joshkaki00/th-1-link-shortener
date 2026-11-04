import secrets
import sqlite3
import string
from urllib.parse import urlparse

from flask import current_app, jsonify, request

_ALPHABET = string.ascii_letters + string.digits


def create_link():
    """POST /links — validate URL, store mapping, return short code (AC1)."""
    payload = request.get_json(silent=True) or {}
    url = payload.get("url")
    if not isinstance(url, str) or not url.strip():
        return jsonify({"error": "url is required"}), 400

    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return jsonify({"error": "url must be http or https"}), 400

    code = "".join(secrets.choice(_ALPHABET) for _ in range(8))
    db_path = current_app.config["DATABASE"]
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS links ("
            "code TEXT PRIMARY KEY, url TEXT NOT NULL, visits INTEGER NOT NULL DEFAULT 0)"
        )
        conn.execute(
            "INSERT INTO links (code, url, visits) VALUES (?, ?, 0)",
            (code, url),
        )
        conn.commit()

    return jsonify({"code": code, "url": url}), 201
