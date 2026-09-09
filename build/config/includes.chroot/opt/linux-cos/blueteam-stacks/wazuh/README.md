# Wazuh manager stack

`wazuh-agent` ships natively (native package, already reporting locally --
see `systemctl status wazuh-agent`). The manager+indexer+dashboard (the full
SIEM you'd point a fleet of agents at) needs TLS certs generated *before*
first run, so it isn't a plain `docker-compose.yml` you can drop in blind.

Bring it up:

```bash
cd /opt/linux-cos/blueteam-stacks/wazuh
git clone https://github.com/wazuh/wazuh-docker.git -b v4.9.0 official
cd official/single-node
docker compose -f generate-indexer-certs.yml run --rm generator
docker compose up -d
```

Dashboard: https://localhost:443 (default admin / SecretPassword -- change
it immediately, see the official repo's README for the certs+users tool).
