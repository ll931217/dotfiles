#!/usr/bin/env bash
# Install the optional privileged network helper; never change live networking.
set -Eeuo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
if (( EUID != 0 )); then
    printf '%s\n' 'Run with sudo to install the reviewed helper and Polkit policy.' >&2
    exit 1
fi
/usr/bin/python3 -I - <<'CHECK'
import pathlib
import stat
for text in ('/usr/local/libexec/eww-network-preference', '/usr/share/polkit-1/actions/org.local.eww.network-preference.policy'):
    path = pathlib.Path(text)
    for item in (path, *path.parents):
        if item.exists() or item.is_symlink():
            info = item.lstat()
            if info.st_uid != 0 or info.st_mode & 0o022 or stat.S_ISLNK(info.st_mode):
                raise SystemExit('Refusing untrusted installation target')
CHECK
install -d -o root -g root -m 0755 /usr/local/libexec
install -o root -g root -m 0755 "$repo_root/system/eww-network-preference.py" /usr/local/libexec/eww-network-preference
install -o root -g root -m 0644 "$repo_root/system/org.local.eww.network-preference.policy" /usr/share/polkit-1/actions/org.local.eww.network-preference.policy
printf '%s\n' 'Network helper installed. Connections and routes were not changed.'
