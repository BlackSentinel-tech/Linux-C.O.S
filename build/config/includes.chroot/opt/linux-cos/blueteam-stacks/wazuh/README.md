# Wazuh manager stack

`wazuh-agent` ships natively (native package, already reporting locally --
see `systemctl status wazuh-agent`). The manager+indexer+dashboard (the full
SIEM you'd point a fleet of agents at) needs TLS certs generated *before*
first run, so it isn't a plain `docker-compose.yml` you can drop in blind.

`cos-stacks up wazuh` does all of it for you: it clones the official
`wazuh-docker` deployment (pinned to v4.9.0) into
`~/.local/share/linux-cos/wazuh-docker`, generates the indexer certificates
once, and starts the single-node stack. `cos-stacks down wazuh`,
`cos-stacks logs wazuh` and `cos-stacks status wazuh` work the same way as
for the other stacks.

The manual equivalent, if you want to follow it step by step:

```bash
git clone https://github.com/wazuh/wazuh-docker.git -b v4.9.0 ~/.local/share/linux-cos/wazuh-docker
cd ~/.local/share/linux-cos/wazuh-docker/single-node
docker compose -f generate-indexer-certs.yml run --rm generator
docker compose up -d
```

Dashboard: https://localhost (upstream default admin / SecretPassword --
change it immediately, see the official repo's README for the certs+users
tool). Unlike the other stacks, Wazuh's agent ports (1514, 1515, 55000) are
published on every interface on purpose -- agents on other machines must be
able to reach the manager. Remember that Docker-published ports bypass ufw.
