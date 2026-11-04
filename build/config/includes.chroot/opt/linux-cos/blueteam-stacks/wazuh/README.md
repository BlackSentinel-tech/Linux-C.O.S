# Wazuh manager stack

`wazuh-agent` ships natively but is **not enrolled and not enabled**: it
needs to know which manager to report to. Point it at one (for example the
stack below, on this machine) and start it:

```bash
sudo sed -i 's|<address>.*</address>|<address>127.0.0.1</address>|' /var/ossec/etc/ossec.conf
sudo systemctl enable --now wazuh-agent
```

The manager+indexer+dashboard (the full SIEM you'd point a fleet of agents
at) needs TLS certs generated *before* first run, so it isn't a plain
`docker-compose.yml` you can drop in blind. `cos-stacks up wazuh` does it
all: it clones the official `wazuh-docker` deployment at the **same version
as the installed wazuh-agent** (a manager must not be older than its
agents; override with `COS_WAZUH_TAG=v4.x.y`) into
`~/.local/share/linux-cos/wazuh-docker`, generates the indexer certificates
once, and starts the single-node stack with `docker-compose.linux-cos.yml`
merged on top.

That override keeps the dashboard (443), the indexer (9200) and the manager
API (55000) on **127.0.0.1**. Only the agent ports 1514/1515 are published
on the network -- remember that Docker-published ports bypass ufw.

The stack starts with Wazuh's **upstream default passwords**
(`cos-stacks creds wazuh` lists them). Change them before you expose
anything, with the procedure in the official documentation:
https://documentation.wazuh.com/current/deployment-options/docker/wazuh-container.html#change-the-password-of-wazuh-users
