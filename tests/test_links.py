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
