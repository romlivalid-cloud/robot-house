"""
Simulasi persetujuan USER (demo).

Dalam produksi nyata, langkah ini dilakukan COORDINATOR (Muse): setelah user
menjawab setuju/tolak di Ruang Robot (chat), coordinator mencatat jawabannya
ke bus sebagai 'user_approval' / 'user_rejection' dengan thread_id yang sama.

Skrip demo ini meniru langkah tersebut: mencari 'decision' terakhir
demo-scout, lalu mencatat user_approval untuk thread itu.
Jalankan dari folder robot-house/:  python3 robots/demo_ide_user.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bus"))
from bus import send, LOG_PATH  # noqa: E402

APPROVAL = (
    "User MENYETUJUI serial 'Kucing Oren vs Benda Dapur' versi revisi. "
    "Silakan lanjut ke produksi: episode 1 tayang Selasa jam 19:00 WIB "
    "sesuai keputusan. Catatan user: pastikan dubbing 'kucing komentator' "
    "tetap lucu dan tidak menyinggung."
)


def latest_decision_thread():
    tid = None
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("type") == "decision" and e.get("from") == "demo-scout":
                tid = e.get("thread_id")
    return tid


def main():
    tid = latest_decision_thread()
    if not tid:
        print("[user] belum ada decision demo-scout — jalankan demo diskusi dulu.")
        return
    entry = send("user", "all", "user_approval", APPROVAL, thread_id=tid)
    print(f"[user] user_approval tercatat (thread {entry['thread_id']})")


if __name__ == "__main__":
    main()
