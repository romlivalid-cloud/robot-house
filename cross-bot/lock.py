#!/usr/bin/env python3
"""lock.py — lockfile sederhana anti-bentrok antar run.

Ide: Satria (concern) + Gemini (concern), disetujui Bos 2026-10-15.
Masalah: jadwal jembatan tiap 5 menit bisa memicu run baru padahal run
sebelumnya belum selesai (mis. sync_diskusi menarik data sementara
kirim_room mengirim data) → state/log bisa rusak.

Solusi: lockfile berisi PID + timestamp. Skrip berikutnya:
- lewat (skip run) bila lock masih segar, atau
- mengambil alih bila lock basi: lebih tua dari STALE_SECS (default 600 =
  2x interval 5 menit) atau PID-nya sudah tidak ada (lockfile yatim).

Pakai:
    from lock import acquire, release
    if not acquire("bus-write"):
        print("terkunci, lewati run ini")
        return
    try:
        ...kerja...
    finally:
        release("bus-write")
"""
import json
import os
import time

DIR = os.path.dirname(os.path.abspath(__file__))
STALE_SECS = 600  # 2x interval jadwal 5 menit (usul Satria)


def _path(name):
    aman = "".join(c if c.isalnum() or c in "-_" else "-" for c in name)
    return os.path.join(DIR, f".lock-{aman}")


def _pid_hidup(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def acquire(name, stale_secs=STALE_SECS):
    """Coba kunci. True = dapat kunci, False = masih dikunci proses lain."""
    p = _path(name)
    now = time.time()
    if os.path.exists(p):
        try:
            d = json.load(open(p))
            pid, ts = d.get("pid"), d.get("ts", 0)
            if _pid_hidup(pid) and (now - ts) < stale_secs:
                return False  # proses lain masih jalan & lock segar
            # basi/yatim -> ambil alih
        except Exception:
            pass  # lockfile rusak -> tulis ulang
    try:
        json.dump({"pid": os.getpid(), "ts": now}, open(p, "w"))
        return True
    except OSError:
        return False


def release(name):
    try:
        os.remove(_path(name))
    except OSError:
        pass


def tunggu(name, maks_detik=30, stale_secs=STALE_SECS):
    """Coba kunci dengan menunggu hingga maks_detik. Untuk kirim_room:
    pesan lebih baik terkirim telat daripada hilang."""
    tenggat = time.time() + maks_detik
    while time.time() < tenggat:
        if acquire(name, stale_secs):
            return True
        time.sleep(2)
    return False
