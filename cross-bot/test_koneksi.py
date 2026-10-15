#!/usr/bin/env python3
"""test_koneksi.py — self-test sekali jalan SEBELUM penjadwalan.

Ide: Gemini (build), disetujui Bos 2026-10-15.
Tujuan: pasang ulang anti-gagal dari human error (salah token, path,
permission, struktur bus belum siap). Jalankan manual setelah menyalin
file paket:

    python3 cross-bot/test_koneksi.py

Keluar 0 = semua lolos, siap dijadwalkan. Keluar 1 = ada yang gagal,
perbaiki dulu (pesan error menunjukkan letak masalahnya).
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CB = os.path.dirname(os.path.abspath(__file__))
REPO = "romlivalid-cloud/robot-house"
GAGAL = []


def cek(nama, fungsi):
    try:
        fungsi()
        print(f"  OK   {nama}")
        return True
    except Exception as e:
        print(f"  GAGAL {nama}: {e}")
        GAGAL.append(nama)
        return False


def _py_version():
    if sys.version_info < (3, 8):
        raise RuntimeError(f"Python {sys.version.split()[0]} < 3.8")


def _config_json():
    for f in ("robots/registry.json", "robots/roles.json",
              "robots/contingency.json"):
        p = os.path.join(ROOT, f)
        if not os.path.isfile(p):
            raise RuntimeError(f"hilang: {f}")
        json.load(open(p, encoding="utf-8"))  # valid JSON?


def _skrip_inti():
    for f in ("bridge.py", "sync_diskusi.py", "fetch_perintah.py",
              "kirim_room.py", "buat_tugas.py", "post_hasil.py",
              "sapu_giliran.py", "cek_partisipasi.py", "lock.py"):
        if not os.path.isfile(os.path.join(CB, f)):
            raise RuntimeError(f"skrip hilang: {f}")


def _bus_writable():
    bus = os.path.join(ROOT, "bus")
    inbox = os.path.join(bus, "inbox")
    os.makedirs(inbox, exist_ok=True)
    uji = os.path.join(bus, ".uji-tulis")
    with open(uji, "w") as f:
        f.write("ok")
    os.remove(uji)


def _lock_ok():
    sys.path.insert(0, CB)
    from lock import acquire, release
    if not acquire("uji-selftest"):
        raise RuntimeError("tidak bisa mengunci (terkunci?)")
    if acquire("uji-selftest"):
        release("uji-selftest")
        raise RuntimeError("kunci ganda lolos — lock rusak")
    release("uji-selftest")
    if not acquire("uji-selftest"):
        raise RuntimeError("tidak bisa mengunci ulang setelah release")
    release("uji-selftest")


def _github_handshake():
    gh = os.path.expanduser("~/workspace/skills/github/bin/gh-api.py")
    if not os.path.isfile(gh):
        gh = os.path.expanduser("~/workspace/custom-connectors/custom.legacy-github/bin/gh-api.py")
    if not os.path.isfile(gh):
        raise RuntimeError("gh-api.py tidak ditemukan")
    r = subprocess.run(["python3", gh, "GET", f"/repos/{REPO}"],
                       capture_output=True, text=True, timeout=30)
    try:
        d = json.loads(r.stdout)
    except Exception:
        raise RuntimeError(f"respons API tak terbaca: {(r.stderr or '')[:100]}")
    if d.get("status") != 200:
        raise RuntimeError(f"handshake HTTP {d.get('status')}")


def main():
    print("Self-test mekanisme diskusi Rumah Robot")
    print(f"ROOT: {ROOT}")
    cek("Python >= 3.8", _py_version)
    cek("config JSON valid (registry/roles/contingency)", _config_json)
    cek("skrip inti lengkap", _skrip_inti)
    cek("bus/ bisa ditulis", _bus_writable)
    cek("mekanisme lockfile", _lock_ok)
    cek("handshake API GitHub", _github_handshake)
    print()
    if GAGAL:
        print(f"GAGAL {len(GAGAL)} cek: {', '.join(GAGAL)} — perbaiki dulu sebelum dijadwalkan.")
        return 1
    print("Semua cek lolos. Siap dijadwalkan (cron jembatan tiap 5 menit).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
