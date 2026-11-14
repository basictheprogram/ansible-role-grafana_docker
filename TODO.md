# TODO

* Create the GitHub repository `basictheprogram/ansible-role-grafana_docker` and the CI workflow.
* Add `playbooks/grafana_docker.yml`, an inventory group and the first host's host_vars.
* Check the live volume name on the first host (expected `grafana_grafana-data`).
* Decide whether to pin `grafana_docker_version` instead of `latest`.
* Dashboards are not managed; add a provider and files if they should be.
* Molecule does not start Grafana; a real container has not been tested yet.
* The scenario's `pytest.ini` works around `pytest_molecule` (Python 3.14) and `pytest-ansible`
  clashing with testinfra in the devcontainer; the same fix is needed in the other roles.
* Molecule runs in CI only (disk use; never locally), but this role has no GitHub repository or
  workflow yet, so the scenario has never run. `README.md` ("Testing") and `CLAUDE.md` ("Testing
  locally") still say `molecule test`; align them once CI exists, as in `realtime.logrotate` and
  `realtime.rustfs`. Add `.github/dependabot.yml` with the workflow.
* Ubuntu 22.04 (jammy) standard support ends 2027-04-30. Decide then whether to drop it from the
  `meta/main.yml` description, the README and the molecule platforms.
* The tests keep their constants in `test_default.py` rather than a shared `_data.py`, and use no
  `conftest.py`, `test_packages.py` or `test_config.py` skeleton: the role installs no packages and
  writes to fixed paths. Revisit only if a second test file is added.
