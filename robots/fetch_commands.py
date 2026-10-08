#!/usr/bin/env python3
"""
Robot House — ambil perintah user dari GitHub Issues.

Dijalankan oleh workflow Actions tiap 30 menit. Mengambil issue terbuka
berlabel "perintah", mencatat tiap issue sebagai pesan `user_command`
ke bus/log.jsonl (sehingga semua robot bisa membacanya), lalu menutup
issue tersebut agar tidak diproses dua kali.

Env: GITHUB_TOKEN (otomatis dari Actions), GITHUB_REPOSITORY (owner/repo).
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

API = "https://api.github.com"


def api(method, path, data=None):
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not repo:
        print("GITHUB_TOKEN / GITHUB_REPOSITORY tidak tersedia — lewati.")
        return None
    req = urllib.request.Request(API + path, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=body, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} untuk {method} {path}")
        return None


def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    issues = api("GET", f"/repos/{repo}/issues?state=open&labels=perintah&per_page=20")
    if issues is None:
        return
    if not issues:
        print("Tidak ada perintah baru.")
        return

    # Pastikan bus ada
    os.makedirs("bus", exist_ok=True)
    log_path = "bus/log.jsonl"

    count = 0
    for issue in issues:
        if "pull_request" in issue:
            continue  # lewati PR
        title = (issue.get("title") or "").replace("[PERINTAH]", "").strip()
        body_text = (issue.get("body") or "").strip()
        text = title
        if body_text and body_text != title:
            # Ambil baris perintah dari body (format dashboard)
            text = f"{title}\n{body_text}".strip()
        msg = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "from": "user",
            "to": "all",
            "type": "user_command",
            "text": text,
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

        # Tutup issue agar tidak diproses ulang
        num = issue["number"]
        api("POST", f"/repos/{repo}/issues/{num}/comments",
            {"body": "✅ Perintah diterima dan diteruskan ke Ruang Chat Robot. Para robot akan menindaklanjuti."})
        api("PATCH", f"/repos/{repo}/issues/{num}", {"state": "closed"})
        count += 1
        print(f"Diproses: #{num} — {title[:60]}")

    print(f"Selesai: {count} perintah diteruskan ke bus.")


if __name__ == "__main__":
    main()
