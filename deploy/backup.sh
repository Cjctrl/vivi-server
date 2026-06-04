#!/usr/bin/env bash
# V.I.V.I backup — captures the irreplaceable state and prunes old snapshots.
# Invoked by vivi-backup.service (nightly via vivi-backup.timer).
#
# Requires restic and a configured repo. Put these in /etc/vivi/backup.env:
#   RESTIC_REPOSITORY=...            (e.g. b2:bucket:vivi  or  /mnt/nas/vivi-restic)
#   RESTIC_PASSWORD_FILE=/etc/vivi/restic.pass   (chmod 0400 root:vivi)
set -euo pipefail

DATA=/var/lib/vivi

# Back up everything under /var/lib/vivi EXCEPT the regenerable zim archives
# (24+ GB, re-downloadable). The KB vault, Qdrant vectors (incl. episodic
# coding history, which is NOT regenerable), and all SQLite DBs are included.
restic backup \
  --verbose \
  --exclude "${DATA}/zim_kb_data" \
  --exclude "${DATA}/logs" \
  "${DATA}" \
  /etc/vivi/vivi.env

# Retention: keep dense recent history, thin out the tail.
restic forget --prune \
  --keep-daily 14 \
  --keep-weekly 8 \
  --keep-monthly 12

# Cheap integrity spot-check (5% of pack files).
restic check --read-data-subset=5%

echo "vivi backup complete: $(date -Is)"
