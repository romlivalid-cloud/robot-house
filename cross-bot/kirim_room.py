"""kirim_room.py — kirim pesan ke kolom chat dashboard Rumah Robot.

Menulis via bus.py ke log lokal, lalu APPEND HANYA PESAN BARU ke file repo
(bus/log.jsonl sebagai sumber + docs/data/log.jsonl untuk tampil instan).

PENTING: jangan pernah push seluruh log lokal ke repo — log lokal adalah
state anti-duplikat yang tidak pernah dibersihkan, sehingga push penuh
memunculkan kembali chat lama di wall (insiden 2026-10-12).

Pakai: python3 kirim_room.py "<teks>" [--dari saras-koordinator] [--tipe message]
"""
import sys
import os
import json
import base64
import subprocess
import importlib.util

sys.path.insert(0, os.path.expanduser("~/workspace/robot-house/bus"))
from bus import send  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lock import tunggu, release  # noqa: E402  (anti-bentrok run, 2026-10-15)

GH_API = os.path.expanduser("~/workspace/skills/github/bin/gh-api.py")
REPO = "romlivalid-cloud/robot-house"
LOG = os.path.expanduser("~/workspace/robot-house/bus/log.jsonl")

_spec = importlib.util.spec_from_file_location("ghapi", GH_API)
_gh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gh)


def repo_append(target, new_line):
    """Append satu baris JSON ke file repo (buat baru jika belum ada)."""
    st, cur = _gh.call("GET", f"/repos/{REPO}/contents/{target}")
    sha = cur.get("sha") if st == 200 and isinstance(cur, dict) else None
    if sha:
        content = base64.b64decode(cur["content"]).decode()
        if content and not content.endswith("\n"):
            content += "\n"
        content += new_line + "\n"
    else:
        content = new_line + "\n"
        sha = None
    payload = {
        "message": f"Pesan room ({target})",
        "content": base64.b64encode(content.encode()).decode(),
    }
    if sha:
        payload["sha"] = sha
    st2, _ = _gh.call("PUT", f"/repos/{REPO}/contents/{target}", payload)
    return st2


def kirim_room(teks, dari="saras-koordinator", tipe="message"):
    # Anti-bentrok dengan sync_diskusi: tunggu lock max 30 dtk; pesan lebih
    # baik terkirim telat daripada hilang, jadi tetap kirim bila gagal kunci.
    dapat_lock = tunggu("bus-write", maks_detik=30)
    try:
        send(dari, "all", tipe, teks)  # tulis ke log lokal
        with open(LOG, encoding="utf-8") as f:
            lines = [ln for ln in f.read().split("\n") if ln.strip()]
        new_line = lines[-1]  # hanya pesan yang baru ditulis
        st1 = repo_append("bus/log.jsonl", new_line)  # sumber (dibaca workflow)
        st2 = repo_append("docs/data/log.jsonl", new_line)  # tampil instan
        print(f"room terkirim (hanya pesan baru): bus/log.jsonl HTTP {st1}, docs/data/log.jsonl HTTP {st2}")
        return st1, st2
    finally:
        if dapat_lock:
            release("bus-write")
        else:
            print("peringatan: kirim tanpa lock (tunggu 30 dtk gagal)")


if __name__ == "__main__":
    args = sys.argv[1:]
    dari = "saras-koordinator"
    tipe = "message"
    teks_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--dari" and i + 1 < len(args):
            dari = args[i + 1]
            i += 2
        elif args[i] == "--tipe" and i + 1 < len(args):
            tipe = args[i + 1]
            i += 2
        else:
            teks_parts.append(args[i])
            i += 1
    teks = " ".join(teks_parts)
    if not teks.strip():
        print('pakai: kirim_room.py "<teks>" [--dari id] [--tipe message]')
        sys.exit(1)
    kirim_room(teks, dari, tipe)
