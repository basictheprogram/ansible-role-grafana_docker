# TODO

* Create the GitHub repository `basictheprogram/ansible-role-grafana_docker` and the CI workflow.
* Add `playbooks/grafana_docker.yml`, an inventory group and the first host's host_vars.
* Check the live volume name on the first host (expected `grafana_grafana-data`).
* Decide whether to pin `grafana_docker_version` instead of `latest`.
* Dashboards are not managed; add a provider and files if they should be.
* Molecule does not start Grafana; a real container has not been tested yet.
* The scenario's `pytest.ini` works around `pytest_molecule` (Python 3.14) and `pytest-ansible`
  clashing with testinfra in the devcontainer; the same fix is needed in the other roles.
