import secrets
import sqlite3
import string
from urllib.parse import urlparse

from flask import current_app, jsonify, redirect, request

_ALPHABET = string.ascii_letters + string.digits


def health():
    """GET / and GET /health — liveness."""
    return jsonify({"status": "ok"}), 200


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


def redirect_code(code):
    """GET /<code> — redirect to original URL and increment visits (AC2)."""
    db_path = current_app.config["DATABASE"]
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS links ("
            "code TEXT PRIMARY KEY, url TEXT NOT NULL, visits INTEGER NOT NULL DEFAULT 0)"
        )
        row = conn.execute(
            "SELECT url FROM links WHERE code = ?", (code,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "not found"}), 404
        conn.execute(
            "UPDATE links SET visits = visits + 1 WHERE code = ?", (code,)
        )
        conn.commit()
        url = row[0]
    return redirect(url, code=302)


def link_stats(code):
    """GET /links/<code>/stats — visit count without incrementing (AC3/AC4)."""
    db_path = current_app.config["DATABASE"]
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS links ("
            "code TEXT PRIMARY KEY, url TEXT NOT NULL, visits INTEGER NOT NULL DEFAULT 0)"
        )
        row = conn.execute(
            "SELECT code, url, visits FROM links WHERE code = ?", (code,)
        ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"code": row[0], "url": row[1], "visits": row[2]}), 200
