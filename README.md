# Ansible Role: grafana_docker

Deploys [Grafana](https://grafana.com/oss/grafana/) as a Docker Compose service on a single
host. It creates the Docker networks Grafana joins, renders the datasource provisioning, a secret
environment file and the compose file, brings the project up, and waits for `/api/health`.

It does not install Docker.

## Requirements

* Ansible core >= 2.20
* The `community.docker` collection, declared in `requirements.yml`. Install it with
  `ansible-galaxy collection install -r requirements.yml`.
* Docker Engine and the Compose v2 plugin on the host (for example from `realtime.docker`).

## Supported Platforms

Debian (trixie) and Ubuntu (jammy, noble, resolute).

## Role Variables

All variables are in `defaults/main.yml` and documented in `meta/argument_specs.yml`.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `grafana_docker_image` / `grafana_docker_version` | `grafana/grafana` / `latest` | Image and tag. The role pulls only a missing image, so a host keeps its image until it is pulled again. |
| `grafana_docker_container_name` | `grafana` | Container name. |
| `grafana_docker_project_name` | `grafana` | Compose project. The data volume is `<project>_grafana-data`; changing it on a host that already runs Grafana orphans its dashboards and users. |
| `grafana_docker_compose_dir` | `/opt/grafana` | Holds `compose.yml`, `grafana.env` and `provisioning/`. |
| `grafana_docker_networks` | `[grafana_frontend, grafana_backend]` | Networks the container joins. |
| `grafana_docker_manage_networks` | `true` | Create the networks. When `false` the role only checks that they exist. |
| `grafana_docker_publish_address` / `_port` | `127.0.0.1` / `3000` | Where Grafana's HTTP port is published. `""` publishes nothing. |
| `grafana_docker_env` | `{}` | Container environment, visible in `compose.yml`. |
| `grafana_docker_env_secrets` | `{}` | Secret environment, written to `grafana.env` with mode `0600`. |
| `grafana_docker_datasources` | `[]` | Datasource provisioning entries, rendered as written. |
| `grafana_docker_log_driver` / `_log_options` | `journald` / `{}` | Docker logging driver for the container. |
| `grafana_docker_labels` | `{}` | Extra container labels. |
| `grafana_docker_verify_ready` / `_verify_timeout` | `true` / `120` | Wait for `/api/health` after the service starts. |

### Networks

Other containers on the host (Loki, Prometheus, a Traefik) share these networks, and this role
owns them: it creates each one that is missing, and never removes any. A role that runs before
this one and needs `grafana_backend` will not find it on a fresh host, so run this role first, or
set `grafana_docker_manage_networks: false` and create them elsewhere.

### Secrets

Put credentials such as `GF_SECURITY_ADMIN_PASSWORD` in `grafana_docker_env_secrets`, with the
values coming from a vault. They are written only to `grafana.env` (mode `0600`) and referenced
from `compose.yml` through `env_file`, and the tasks that handle them use `no_log`. A value must
not contain a single quote or a newline, because the env file quotes values to stop compose from
expanding `$`.

### Datasources

Each entry is rendered unchanged under `datasources:`, so anything Grafana provisioning accepts
works, including `jsonData` and `secureJsonData`. Each entry needs `name` and `type`, names must
be unique, and at most one may set `isDefault: true`. The file is mode `0640` because
`secureJsonData` can hold credentials. Grafana reads provisioning at start, so a change restarts
the container.

```yaml
grafana_docker_datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
```

If Loki runs with `auth_enabled: true`, add the tenant header to its entry:

```yaml
    jsonData:
      httpHeaderName1: X-Scope-OrgID
    secureJsonData:
      httpHeaderValue1: <tenant>
```

Dashboards are not managed by this role; the empty `provisioning/dashboards` directory exists so
Grafana does not log an error for it.

## Task Flow

1. **Preflight** validates the variables, and (outside molecule) that Docker works and, when the
   role does not create them, that the networks exist.
2. **Network** creates the Docker networks.
3. **Install** creates `grafana_docker_compose_dir` and the four provisioning subdirectories
   (`datasources`, `dashboards`, `plugins`, `alerting`; Grafana logs an error at start for each one
   that is missing), renders `provisioning/datasources`,
   `grafana.env` (only when secrets are set) and `compose.yml`. A change to the datasources or the
   env file restarts the container through a handler.
4. **Service** runs `docker compose up`.
5. **Verify** polls `/api/health` from the host, and is skipped when nothing is published.

## Behind Traefik

**Traefik on another host**: publish Grafana on an address that host can reach, for example
`grafana_docker_publish_address: 10.0.0.250`, and point a Traefik site at
`http://10.0.0.250:3000`. Restrict that port to the Traefik host upstream.

**Traefik on the same host**: publish nothing and join Traefik's network.

```yaml
grafana_docker_publish_address: ""
grafana_docker_labels:
  traefik.enable: "true"
  traefik.docker.network: grafana_frontend
  traefik.http.routers.grafana.rule: "Host(`grafana.example.com`)"
  traefik.http.routers.grafana.entrypoints: websecure
  traefik.http.routers.grafana.tls: "true"
  traefik.http.services.grafana.loadbalancer.server.port: "3000"
```

With nothing published the host cannot reach Grafana, so the role skips its health check; test
through the proxy.

## Adopting a hand-built Grafana

1. Check the volume name: `docker volume ls | grep grafana`. The role uses project `grafana` and
   volume `grafana-data`, so it expects `grafana_grafana-data`.
2. Stop the old project without removing volumes: `docker compose down` (never `-v`).
3. Run the role. It reuses that volume, so dashboards, users and settings stay.
4. Roll back by running `docker compose down` in `/opt/grafana` and `docker compose up -d` in
   the old directory.

## Testing

CI runs `molecule test` on every supported platform for each push to `ansible-core-2.20`
(`.github/workflows/ci.yml`). Locally, run only the static checks, because the platform images
use too much Docker disk: `pre-commit run --all-files`, `molecule syntax` and
`pytest --collect-only molecule/default/tests`.

The docker tasks need a Docker daemon and are tagged `molecule-notest`; molecule checks the
rendered files and the preflight failures. `molecule/default/pytest.ini` keeps the scenario's
pytest separate from a parent project's configuration and disables two plugins that fail or clash
when installed alongside testinfra (`pytest_molecule` on Python 3.14, and `pytest-ansible`).

## License

MIT
