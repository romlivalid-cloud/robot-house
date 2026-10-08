#!/usr/bin/env python3
"""
Robot House — ambil perintah user dari GitHub Issues.

Dijalankan di awal robots/run_scheduled.py setiap siklus Actions.
Mengambil issue terbuka berlabel "perintah" (bisa tanpa auth karena
repo publik), mencatat tiap issue baru sebagai pesan `user_command`
ke bus/log.jsonl sehingga semua robot bisa membacanya.

Anti-duplikat: nomor issue yang sudah diproses ditandai dengan field
"issue" pada pesan di log — tidak perlu file state terpisah.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

API = "https://api.github.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "bus", "log.jsonl")
OWNER_REPO = os.environ.get("GITHUB_REPOSITORY", "romlivalid-cloud/robot-house")


def api_get(path):
    req = urllib.request.Request(API + path, method="GET")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "robot-house-bot")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def processed_issues():
    """Kumpulkan nomor issue yang sudah masuk ke bus."""
    done = set()
    try:
        with open(LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    m = json.loads(line)
                except Exception:
                    continue
                if m.get("type") == "user_command" and "issue" in m:
                    done.add(m["issue"])
    except FileNotFoundError:
        pass
    return done


def main():
    try:
        issues = api_get(
            f"/repos/{OWNER_REPO}/issues?state=open&labels=perintah&per_page=20"
        )
    except Exception as e:
        print(f"[fetch] gagal mengambil issues (lanjut tanpa perintah): {e}")
        return

    done = processed_issues()
    os.makedirs(os.path.join(ROOT, "bus"), exist_ok=True)
    new = 0
    for issue in issues:
        if "pull_request" in issue:
            continue
        num = issue["number"]
        if num in done:
            continue
        title = (issue.get("title") or "").replace("[PERINTAH]", "").strip()
        body_text = (issue.get("body") or "").strip()
        text = title if (not body_text or body_text == title) else f"{title}\n{body_text}"
        msg = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "from": "user",
            "to": "all",
            "type": "user_command",
            "text": text,
            "issue": num,
        }
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        new += 1
        print(f"[fetch] perintah #{num} diteruskan ke bus.")
    print(f"[fetch] selesai: {new} perintah baru.")


if __name__ == "__main__":
    main()
