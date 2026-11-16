# Design: realtime.grafana_docker

## Goal

Replace the hand-built `grafana/compose.yml` with a role, without losing the data in the
`grafana-data` volume. Second of several roles for the same host, after `realtime.loki_docker`.

## What the role manages

* The Docker networks Grafana joins
* `{{ grafana_docker_compose_dir }}/provisioning/datasources/datasources.yml`
* `{{ grafana_docker_compose_dir }}/provisioning/dashboards/` (provider and files, only when a dashboards version is set)
* `{{ grafana_docker_compose_dir }}/grafana.env` (only when secrets are set)
* `{{ grafana_docker_compose_dir }}/compose.yml`
* The compose project, through `community.docker.docker_compose_v2`

## What it does not manage

* Docker itself (`realtime.docker`).
* Alerting provisioning. Dashboards are provisioned only when `grafana_docker_dashboards_version` is set; otherwise they live in Grafana's volume.
* A reverse proxy. Traefik labels, if wanted, go in `grafana_docker_labels`.
* A firewall. Docker-published ports bypass ufw, so restrict the published port on the host or
  the network.
* Backups of the data volume.

## Decisions

1. **Compose, not `docker_container`.** The source is a compose file, and the other container
   roles here use compose.
2. **This role owns the shared networks.** `grafana_frontend` and `grafana_backend` are joined by
   Loki, Prometheus and Traefik as external networks. Creating them with `state: present` is a
   no-op when they exist, and the role never removes one.
3. **Project name `grafana`.** Compose names volumes `<project>_<volume>`; keeping the project
   and the volume name from the hand-built file reuses the existing data.
4. **Secrets in an env file, not compose.yml.** `grafana.env` is mode `0600`, values are quoted
   so `$` is not expanded, and the tasks use `no_log`.
5. **Datasources are a pass-through list.** The role renders the list unchanged, so it needs no
   change for a new datasource type or option.
6. **Image tag `latest`.** It matches the hand-built compose file. With `pull: missing` an
   existing host keeps its image until it is pulled again, so upgrades are explicit.
7. **Published on `127.0.0.1` by default.** The hand-built file published `3000` on every
   interface; a host that needs that sets `0.0.0.0`.
8. **Verify from the host.** `/api/health` is polled on the published address and skipped when
   nothing is published.
9. **Restart on provisioning or secret change.** Grafana reads both at start only.

10. **Dashboards: pull a pinned release, checksum-verified.** The dashboards repository is private
    and generates the JSON. The role clones the tag on the controller over SSH, so no secret is
    added, and compares each file with a sha256 kept in host vars, so a moved tag cannot change what
    is deployed. Verification precedes any copy. Dashboards are not a restart trigger (the file
    provider polls); the provider file is, because Grafana reads providers at start.

## Dropped from the original compose

* The commented-out Prometheus-style `command:` block.
* `LOG_HOST` from `.env`; the logging driver is a variable now.
* The `env: HOSTNAME` logging option, which referenced a container variable that is not set.
