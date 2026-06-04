# V.I.V.I Server Runbook (Ubuntu)

Reproducible deployment for the **headless** V.I.V.I stack — Ollama, Qdrant, the
NEXUS memory server, the KB file-watcher, the zim_kb offline knowledge base, and
the mobile gateway. The desktop overlay / computer-use (`vividesk-client`) runs on
a separate **desktop** machine, not here.

These systemd units + env template + scripts *are* the infrastructure-as-code:
the server can be rebuilt from this directory alone.

---

## 1. Topology

```
UBUNTU SERVER (GPU, always-on)                         elsewhere
  ollama.service     :11434  (loopback)
  vivi-qdrant        :6333   (loopback)  shared vector store
  vivi-nexus         :7200   (loopback)  memory API + KB vectors
  vivi-filewatcher           re-embeds KB files on change
  vivi-zimkb                 offline knowledge base (oneshot/health)
  vivi-gateway       :7400   (Tailscale) ◀───── phone PWA (vivi-mobile)
                                          ◀───── desktop overlay :7300 (vividesk-client)
```

Two decisions baked into this config:

1. **One NEXUS, from `vivi-server`.** `vivi-brain` and `vivi-server` ship
   near-identical NEXUS servers; only one can bind `:7200`. We run the
   `vivi-server` copy because it carries `zim_kb` and the reembed path-traversal
   fix. The gateway (a `vivi-brain` component) reaches it over HTTP via
   `NEXUS_HOST`/`NEXUS_PORT`.
2. **Standalone Qdrant, not embedded.** `core/vector_store.py` opens an embedded
   Qdrant (`QdrantClient(path=...)`) only when `QDRANT_URL` is unset — and an
   embedded store can be held by exactly **one** process. The NEXUS server *and*
   the gateway both use the vector store, so they would deadlock on the lock.
   Setting `QDRANT_URL=http://127.0.0.1:6333` makes them share one server.

---

## 2. One-time prerequisites

```bash
# Clone both repos to /opt/vivi (gateway needs vivi-brain; NEXUS/zim_kb need vivi-server)
sudo mkdir -p /opt/vivi && sudo chown "$USER" /opt/vivi
git clone <vivi-brain>  /opt/vivi/vivi-brain
git clone <vivi-server> /opt/vivi/vivi-server

# GPU (RTX 5080 = Blackwell → needs a recent driver, 570+)
sudo ubuntu-drivers autoinstall && sudo reboot   # verify after reboot: nvidia-smi

# Ollama + models
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:8b-q4 && ollama pull qwen2.5-coder:14b-q4 && ollama pull deepseek-r1:14b-q4 \
  && ollama pull phi4:14b-q4 && ollama pull nomic-embed-text && ollama pull qwen2.5vl:7b-q4 \
  && ollama pull llava:13b

# Python venv (3.12 — NOT 3.14; some binary deps lack 3.14 wheels)
sudo apt install -y python3.12-venv nodejs npm restic curl docker.io
python3.12 -m venv /opt/vivi/venv
/opt/vivi/venv/bin/pip install -r /opt/vivi/vivi-server/requirements.txt
/opt/vivi/venv/bin/pip install -r /opt/vivi/vivi-brain/requirements.txt

# file_watcher node deps
cd /opt/vivi/vivi-server/memory/nexus && npm install   # chokidar etc.

# Tailscale
curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up
tailscale ip -4    # → put this in TAILSCALE_BIND_IP
```

---

## 3. Install

```bash
cd /opt/vivi/vivi-server/deploy
sudo ./install.sh
sudo nano /etc/vivi/vivi.env       # set WS_SECRET, NEXUS_SECRET, TAILSCALE_BIND_IP
sudo systemctl enable --now vivi-qdrant vivi-nexus vivi-filewatcher vivi-zimkb vivi-gateway
```

Generate the two secrets:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"   # ×2 → WS_SECRET, NEXUS_SECRET
```

Startup order is enforced by the units
(`ollama → vivi-qdrant → vivi-nexus → {filewatcher, zimkb, gateway}`), and the
gateway/filewatcher `ExecStartPre` blocks until `GET /health` on `:7200` answers,
so "ordering ≠ readiness" races are handled.

---

## 4. Smoke test

```bash
systemctl --failed                              # expect: 0 loaded units failed
curl -s localhost:11434/api/tags   | head       # Ollama: models present
curl -s 127.0.0.1:6333/healthz                  # Qdrant up
curl -s 127.0.0.1:7200/health                   # NEXUS up        (server.py:900)
curl -s 127.0.0.1:7400/health                   # gateway up
curl -s 127.0.0.1:7200/api/graph | head -c 200  # graph API (feeds the HUD widget)
# From the phone on Tailscale: open the PWA → connect → send a trivial task.
```

---

## 5. Day-to-day ops

| Task | Command |
|---|---|
| Tail a service | `journalctl -u vivi-gateway -f` |
| Restart one service | `sudo systemctl restart vivi-nexus` |
| Restart the whole stack | `sudo systemctl restart vivi-qdrant vivi-nexus vivi-filewatcher vivi-zimkb vivi-gateway` |
| Status overview | `systemctl status 'vivi-*'` |
| What failed | `systemctl --failed` |
| Edit config then apply | edit `/etc/vivi/vivi.env` → `sudo systemctl restart vivi-*` |

Logs go to **journald** (rotation handled automatically). Cap disk use if needed:
`journalctl --vacuum-size=2G`.

---

## 6. Backups & restore

Configure the restic repo once in `/etc/vivi/backup.env` (owner `root:vivi`, `0640`):
```ini
RESTIC_REPOSITORY=b2:my-bucket:vivi        # or  /mnt/nas/vivi-restic
RESTIC_PASSWORD_FILE=/etc/vivi/restic.pass # chmod 0400 root:vivi
```
Then enable the nightly timer and verify a restore:
```bash
restic -r "$RESTIC_REPOSITORY" init           # first time only
sudo systemctl enable --now vivi-backup.timer
sudo systemctl start vivi-backup.service       # run once now
restic snapshots                               # confirm it landed
# RESTORE drill (to a scratch dir) — do this at least once:
restic restore latest --target /tmp/vivi-restore-test
```
What's backed up: all of `/var/lib/vivi` **except** `zim_kb_data` (regenerable) and
`logs`, plus `/etc/vivi/vivi.env`. This includes the KB vault, the Qdrant vectors
(incl. non-regenerable episodic coding history), and every SQLite DB.

---

## 7. Rollback

Code is a git checkout under `/opt/vivi`, so rollback is a checkout + restart:
```bash
cd /opt/vivi/vivi-server && git fetch && git checkout <previous-tag-or-sha>
cd /opt/vivi/vivi-brain  && git checkout <previous-tag-or-sha>
sudo systemctl restart vivi-nexus vivi-filewatcher vivi-zimkb vivi-gateway
```
Pin a known-good release by tagging it (`git tag deploy-YYYYMMDD`) before each update.
No DB migrations to reverse — NEXUS is file-based and SQLite schemas are created
in-code.

---

## 8. Security notes

- **Bind discipline:** only `:7400` is reachable off-box, and only on the Tailscale
  interface. Lock it down with ufw:
  ```bash
  sudo ufw default deny incoming && sudo ufw default allow outgoing
  sudo ufw allow in on tailscale0 to any port 7400 proto tcp
  sudo ufw allow in on tailscale0 to any port 22
  sudo ufw enable
  ```
  Enable **MFA** on the Tailscale account and an ACL restricting which devices may
  reach `:7400`.
- **Secrets** live in `/etc/vivi/vivi.env` (`root:vivi`, `0640`) — never in the repo.
  `WS_SECRET`/`NEXUS_SECRET` are `_required()`, so a missing secret fails the unit
  loudly rather than starting insecure.
- **Hardening:** every app unit runs as the unprivileged `vivi` user with
  `ProtectSystem=strict` (so `/opt` code is read-only), `ProtectHome`, `PrivateTmp`,
  and `NoNewPrivileges`. All writes are confined to `/var/lib/vivi`.
- **Code execution off:** `CODING_AGENT_EXECUTION_ENABLED=false` in the env keeps the
  coding agent from running generated code on this remotely-reachable box.
- **`NEXUS_REQUIRE_READ_AUTH=true`** so reads (not just writes) require the token —
  important because the desktop overlay reaches NEXUS over Tailscale.

---

## 9. Qdrant without Docker (alternative)

If you'd rather not run Docker, use the native binary and drop the
`Requires=docker.service` line from `vivi-qdrant.service`, replacing its
`ExecStart`:
```ini
[Service]
User=vivi
Environment=QDRANT__SERVICE__HOST=127.0.0.1
Environment=QDRANT__STORAGE__STORAGE_PATH=/var/lib/vivi/qdrant
ExecStart=/opt/vivi/qdrant/qdrant
Restart=always
```
Download the binary for your arch from <https://github.com/qdrant/qdrant/releases>
into `/opt/vivi/qdrant/`. (The Docker unit is the default because it needs no
manual binary management; it runs as root only because the Docker socket requires
it — qdrant itself is non-root inside the container.)

---

## 10. File map

```
deploy/
├── install.sh                     # creates user/dirs/env, installs units
├── backup.sh                      # restic wrapper (run by vivi-backup.service)
├── vivi.env.example               # → /etc/vivi/vivi.env
├── RUNBOOK.md                     # this file
└── systemd/
    ├── ollama.service.d/override.conf   # OLLAMA_KEEP_ALIVE=-1
    ├── vivi-qdrant.service
    ├── vivi-nexus.service
    ├── vivi-filewatcher.service
    ├── vivi-zimkb.service
    ├── vivi-gateway.service
    ├── vivi-backup.service
    └── vivi-backup.timer
```
