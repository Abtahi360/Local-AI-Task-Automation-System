from fastapi.testclient import TestClient

from backend import __version__


def test_application_imports() -> None:
    import backend.main

    assert backend.main.app.title


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
    assert body["environment"] == "test"
    assert response.headers["x-request-id"]


def test_database_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health/database")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok" and body["connected"] is True
    assert body["foreign_keys_enabled"] is True
    assert body["journal_mode"] == "WAL"
    assert body["database_file"] == "test.db"
    assert "/" not in body["database_file"] and "\\" not in body["database_file"]  # no path leak


def test_environment_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health/environment")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["configuration_loaded"] is True
    assert body["playwright"]["importable"] is True
    assert {p["name"] for p in body["packages"]} >= {"fastapi", "SQLAlchemy", "playwright"}


def test_system_info_endpoint(client: TestClient) -> None:
    body = client.get("/api/v1/system/info").json()
    assert body["host"] == "127.0.0.1"
    assert body["local_only"] is True
    assert body["api_prefix"] == "/api/v1"
    assert body["phase"].startswith("2")


def test_root_serves_frontend(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Local AI Task Automation System" in response.text
    assert client.get("/styles/main.css").status_code == 200
    assert client.get("/assets/app.js").status_code == 200


def test_not_found_uses_consistent_error_shape(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"error_code", "message", "field", "request_id"}
    assert body["request_id"] == response.headers["x-request-id"]


def test_only_phase_2_routes_exist(client: TestClient) -> None:
    paths = set(client.get("/openapi.json").json()["paths"])
    assert paths == {
        "/api/v1/health",
        "/api/v1/health/database",
        "/api/v1/health/environment",
        "/api/v1/system/info",
    }  # no task/queue/scheduler endpoints yet (Phase 3+)


def test_database_failure_is_reported_not_fatal(settings, tmp_path) -> None:
    from backend.main import create_app

    broken = settings.model_copy(update={"database_path": tmp_path})  # a directory, not a file
    with TestClient(create_app(broken)) as test_client:
        assert test_client.get("/api/v1/health").status_code == 200
        response = test_client.get("/api/v1/health/database")
        assert response.status_code == 503
        assert response.json()["connected"] is False
        assert response.json()["error"]
