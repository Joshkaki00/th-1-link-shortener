"""TH-1 acceptance tests — one failing def at a time (TDD)."""

EXAMPLE_URL = "https://example.com/path"


def test_ac1_create_short_link(tmp_path):
    """AC1: POST /links with valid URL → 2xx + non-empty code ≠ full URL."""
    from app import create_app

    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    client = app.test_client()

    response = client.post("/links", json={"url": EXAMPLE_URL})

    assert 200 <= response.status_code < 300
    data = response.get_json()
    assert data is not None
    assert "code" in data
    code = data["code"]
    assert isinstance(code, str)
    assert code
    assert code != EXAMPLE_URL


def test_ac2_redirect(tmp_path):
    """AC2: GET /{code} → 301/302 with Location = original URL."""
    from app import create_app

    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    client = app.test_client()

    create = client.post("/links", json={"url": EXAMPLE_URL})
    assert 200 <= create.status_code < 300
    code = create.get_json()["code"]

    response = client.get(f"/{code}")

    assert response.status_code in (301, 302)
    assert response.headers["Location"] == EXAMPLE_URL


def test_ac3_visit_tracking(tmp_path):
    """AC3: two redirects → visits==2; stats GET must not increment."""
    from app import create_app

    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    client = app.test_client()

    create = client.post("/links", json={"url": EXAMPLE_URL})
    assert 200 <= create.status_code < 300
    code = create.get_json()["code"]

    assert client.get(f"/{code}").status_code in (301, 302)
    assert client.get(f"/{code}").status_code in (301, 302)

    stats = client.get(f"/links/{code}/stats")
    assert stats.status_code == 200
    assert stats.get_json()["visits"] == 2

    stats_again = client.get(f"/links/{code}/stats")
    assert stats_again.status_code == 200
    assert stats_again.get_json()["visits"] == 2


def test_ac4_stats_for_known_code(tmp_path):
    """AC4: GET /links/{code}/stats → 200 with url/code + numeric visits."""
    from app import create_app

    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    client = app.test_client()

    create = client.post("/links", json={"url": EXAMPLE_URL})
    assert 200 <= create.status_code < 300
    code = create.get_json()["code"]

    response = client.get(f"/links/{code}/stats")

    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data.get("code") == code or data.get("url") == EXAMPLE_URL
    assert "visits" in data
    assert isinstance(data["visits"], int)
    assert data["visits"] == 0


def test_ac5_unknown_redirect_404(tmp_path):
    """AC5: GET /nope with no mapping → 404."""
    from app import create_app

    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    client = app.test_client()

    response = client.get("/nope")
    assert response.status_code == 404


def test_ac6_unknown_stats_404(tmp_path):
    """AC6: GET /links/nope/stats with no mapping → 404."""
    from app import create_app

    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    client = app.test_client()

    response = client.get("/links/nope/stats")
    assert response.status_code == 404


def test_ac7_reject_bad_input(tmp_path):
    """AC7: empty/missing/not-a-url → 4xx and no mapping stored."""
    import sqlite3

    from app import create_app

    db_path = tmp_path / "test.sqlite"
    app = create_app({"TESTING": True, "DATABASE": str(db_path)})
    client = app.test_client()

    for body in ({}, {"url": ""}, {"url": "not-a-url"}):
        response = client.post("/links", json=body)
        assert 400 <= response.status_code < 500

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS links ("
            "code TEXT PRIMARY KEY, url TEXT NOT NULL, visits INTEGER NOT NULL DEFAULT 0)"
        )
        count = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    assert count == 0


def test_ac8_persist_across_restart(tmp_path):
    """AC8: same DB file + new create_app → redirect + prior visits survive."""
    from app import create_app

    db_path = str(tmp_path / "test.sqlite")
    app = create_app({"TESTING": True, "DATABASE": db_path})
    client = app.test_client()

    create = client.post("/links", json={"url": EXAMPLE_URL})
    assert 200 <= create.status_code < 300
    code = create.get_json()["code"]
    assert client.get(f"/{code}").status_code in (301, 302)

    restarted = create_app({"TESTING": True, "DATABASE": db_path})
    client2 = restarted.test_client()

    stats = client2.get(f"/links/{code}/stats")
    assert stats.status_code == 200
    assert stats.get_json()["visits"] == 1

    response = client2.get(f"/{code}")
    assert response.status_code in (301, 302)
    assert response.headers["Location"] == EXAMPLE_URL


def test_ac9_unique_codes(tmp_path):
    """AC9: two creates → distinct codes."""
    from app import create_app

    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    client = app.test_client()

    first = client.post("/links", json={"url": "https://example.com/one"})
    second = client.post("/links", json={"url": "https://example.com/two"})

    assert 200 <= first.status_code < 300
    assert 200 <= second.status_code < 300
    assert first.get_json()["code"] != second.get_json()["code"]
