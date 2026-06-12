Go to [prometheus-grafana-monitoring](https://github.com/reef-technologies/prometheus-grafana-monitoring) and generate a cert-key pair for this project (see prometheus-grafana-monitoring's README to find out how to do that).
Copy the generated cert-key pair along with `ca.crt` and place there, named `cert.crt`, `cert.key` and `ca.crt`, respectively.

For **AWS** deployments the certificates live elsewhere and use different names: fill the
placeholder files in `devops/tf/main/files/nginx/monitoring_certs/` (`monitoring.crt.txt`,
`monitoring.key.txt`, `monitoring-ca.crt.txt`) with the same PEM material. See
[README_AWS.md > Monitoring certificates](../../README_AWS.md#monitoring-certificates).
