from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.core.config import Settings, is_loopback_host
from backend.core.paths import PROJECT_ROOT


def make(**kwargs: object) -> Settings:
    return Settings(_env_file=None, **kwargs)  # type: ignore[call-arg]


def test_defaults_match_phase_2_contract() -> None:
    s = make()
    assert s.app_name == "Local AI Task Automation System"
    assert s.app_env == "development"
    assert s.app_host == "127.0.0.1"  # AC-021: localhost by default
    assert s.app_port == 8000
    assert s.log_level == "INFO"
    assert s.sqlite_journal_mode == "WAL"
    assert s.local_only is True


def test_relative_paths_resolve_against_project_root() -> None:
    s = make()
    assert s.database_path == PROJECT_ROOT / "database" / "automation.db"
    assert s.logs_dir == PROJECT_ROOT / "logs"
    assert s.database_path.is_absolute()


def test_absolute_paths_are_kept(tmp_path: Path) -> None:
    assert make(database_path=tmp_path / "x.db").database_path == (tmp_path / "x.db").resolve()


def test_environment_variables_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_PORT", "9123")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    s = make()
    assert s.app_port == 9123
    assert s.log_level == "DEBUG"


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.20", "example.com"])
def test_non_loopback_host_is_rejected(host: str) -> None:
    with pytest.raises(ValidationError):
        make(app_host=host)


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1", "127.0.0.2"])
def test_loopback_hosts_are_accepted(host: str) -> None:
    assert make(app_host=host).local_only is True


def test_non_loopback_requires_explicit_override() -> None:
    assert make(app_host="0.0.0.0", allow_non_local_bind=True).local_only is False


def test_invalid_port_rejected() -> None:
    with pytest.raises(ValidationError):
        make(app_port=70000)


def test_is_loopback_host() -> None:
    assert is_loopback_host("localhost")
    assert not is_loopback_host("0.0.0.0")
