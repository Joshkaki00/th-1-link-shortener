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
