"""Molecule testinfra tests for ansible-role-grafana_docker.

These check the files the role renders against the variables in
molecule/default/converge.yml. Grafana is never started in molecule.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from testinfra.host import Host

_COMPOSE = "/opt/grafana/compose.yml"
_ENV = "/opt/grafana/grafana.env"
_DATASOURCES = "/opt/grafana/provisioning/datasources/datasources.yml"
_BARE_COMPOSE = "/opt/grafana-bare/compose.yml"
_BARE_ENV = "/opt/grafana-bare/grafana.env"
_FAKE_SECRET = "molecule-fake-password"  # noqa: S105 - fixture value from converge.yml


def load_yaml(host: Host, path: str) -> Any:
    """Read a file from the host and parse it as YAML."""
    return yaml.safe_load(host.file(path).content_string)


def test_compose_dir_exists(host: Host) -> None:
    assert host.file("/opt/grafana").is_directory


def test_provisioning_datasources_dir_exists(host: Host) -> None:
    assert host.file("/opt/grafana/provisioning/datasources").is_directory


def test_provisioning_dashboards_dir_exists(host: Host) -> None:
    assert host.file("/opt/grafana/provisioning/dashboards").is_directory


def test_provisioning_plugins_dir_exists(host: Host) -> None:
    assert host.file("/opt/grafana/provisioning/plugins").is_directory


def test_provisioning_alerting_dir_exists(host: Host) -> None:
    assert host.file("/opt/grafana/provisioning/alerting").is_directory


def test_compose_file_mode(host: Host) -> None:
    assert host.file(_COMPOSE).mode == 0o644


def test_env_file_mode(host: Host) -> None:
    assert host.file(_ENV).mode == 0o600


def test_datasources_file_mode(host: Host) -> None:
    assert host.file(_DATASOURCES).mode == 0o640


def test_env_file_holds_the_secret(host: Host) -> None:
    assert f"GF_SECURITY_ADMIN_PASSWORD='{_FAKE_SECRET}'" in host.file(_ENV).content_string


def test_compose_never_contains_the_secret(host: Host) -> None:
    assert _FAKE_SECRET not in host.file(_COMPOSE).content_string


def test_compose_uses_the_env_file(host: Host) -> None:
    assert load_yaml(host, _COMPOSE)["services"]["grafana"]["env_file"] == ["./grafana.env"]


def test_compose_project_name_keeps_the_volume_name(host: Host) -> None:
    assert load_yaml(host, _COMPOSE)["name"] == "grafana"


def test_compose_publishes_on_the_configured_address(host: Host) -> None:
    ports = load_yaml(host, _COMPOSE)["services"]["grafana"]["ports"]
    assert ports == ["10.0.0.250:3000:3000"]


def test_compose_mounts_provisioning_read_only(host: Host) -> None:
    volumes = load_yaml(host, _COMPOSE)["services"]["grafana"]["volumes"]
    assert "./provisioning:/etc/grafana/provisioning:ro" in volumes


def test_compose_uses_the_data_volume(host: Host) -> None:
    volumes = load_yaml(host, _COMPOSE)["services"]["grafana"]["volumes"]
    assert "grafana-data:/var/lib/grafana" in volumes


def test_compose_environment_values_are_strings(host: Host) -> None:
    env = load_yaml(host, _COMPOSE)["services"]["grafana"]["environment"]
    assert env["GF_USERS_ALLOW_SIGN_UP"] == "false"


def test_compose_syslog_options(host: Host) -> None:
    logging = load_yaml(host, _COMPOSE)["services"]["grafana"]["logging"]
    assert logging["options"]["syslog-address"] == "udp://10.0.0.5:514"


def test_compose_labels(host: Host) -> None:
    labels = load_yaml(host, _COMPOSE)["services"]["grafana"]["labels"]
    assert "traefik.enable=true" in labels


def test_compose_joins_both_networks(host: Host) -> None:
    networks = load_yaml(host, _COMPOSE)["services"]["grafana"]["networks"]
    assert networks == ["grafana_frontend", "grafana_backend"]


def test_compose_networks_are_external(host: Host) -> None:
    networks = load_yaml(host, _COMPOSE)["networks"]
    assert networks["grafana_backend"] == {"external": True}


def test_datasources_api_version(host: Host) -> None:
    assert load_yaml(host, _DATASOURCES)["apiVersion"] == 1


def test_datasources_names(host: Host) -> None:
    names = [d["name"] for d in load_yaml(host, _DATASOURCES)["datasources"]]
    assert names == ["Prometheus", "Loki"]


def test_datasources_default_is_prometheus(host: Host) -> None:
    prometheus = load_yaml(host, _DATASOURCES)["datasources"][0]
    assert prometheus["isDefault"] is True


def test_datasources_pass_through_nested_keys(host: Host) -> None:
    loki = load_yaml(host, _DATASOURCES)["datasources"][1]
    assert loki["jsonData"]["httpHeaderName1"] == "X-Scope-OrgID"


def test_bare_compose_without_ports(host: Host) -> None:
    assert "ports" not in load_yaml(host, _BARE_COMPOSE)["services"]["grafana"]


def test_bare_compose_without_networks(host: Host) -> None:
    assert "networks" not in load_yaml(host, _BARE_COMPOSE)["services"]["grafana"]


def test_bare_compose_without_env_file(host: Host) -> None:
    assert "env_file" not in load_yaml(host, _BARE_COMPOSE)["services"]["grafana"]


def test_bare_render_writes_no_env_file(host: Host) -> None:
    assert not host.file(_BARE_ENV).exists
