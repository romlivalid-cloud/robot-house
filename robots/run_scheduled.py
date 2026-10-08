#!/usr/bin/env python3
"""Dispatcher robot terjadwal untuk GitHub Actions.

Membaca robots/registry.json dan menjalankan skrip setiap robot yang
berstatus "active". Robot berstatus "demo"/"planned" dilewati otomatis.
Setiap skrip robot wajib mengikuti protokol di coordinator/PROTOCOL.md:
read_inbox() -> kerja -> send() -> touch_registry().
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "robots", "registry.json")


def main():
    # Ambil perintah user dari Issues dulu agar robot membacanya di siklus ini
    try:
        sys.path.insert(0, os.path.join(ROOT, "robots"))
        import fetch_commands
        fetch_commands.main()
    except Exception as e:
        print(f"[dispatcher] fetch perintah gagal, lanjut: {e}")
    try:
        with open(REG, encoding="utf-8") as f:
            robots = json.load(f).get("robots", [])
    except Exception as e:
        print(f"[dispatcher] gagal membaca registry: {e}")
        return 1

    ran = 0
    for r in robots:
        if r.get("status") != "active":
            continue
        rid = r["id"]
        script = os.path.join(ROOT, "robots", rid.replace("-", "_") + ".py")
        if not os.path.exists(script):
            print(f"[dispatcher] lewati {rid}: skrip tidak ditemukan ({script})")
            continue
        print(f"[dispatcher] menjalankan {rid} ...")
        try:
            subprocess.run([sys.executable, script], cwd=ROOT, timeout=600,
                           check=False)
            ran += 1
        except Exception as e:
            print(f"[dispatcher] {rid} error: {e}")

    print(f"[dispatcher] selesai. {ran} robot dijalankan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
