"""
demo-scout: robot contoh #1.

Tugas: menulis temuan ke bus + memberi tugas ke demo-reporter.
Jalankan:  python3 robots/demo_scout.py   (dari folder robot-house/)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bus"))
from bus import send, read_inbox, touch_registry  # noqa: E402

ME = "demo-scout"


def main():
    # (a) Baca inbox sendiri di awal run
    for m in read_inbox(ME, clear=True):
        print(f"[{ME}] inbox <- {m['from']}: {m['text']}")

    # (b) Kerjakan tugas: buat temuan contoh
    temuan = (
        "3 topik kucing terhangat hari ini: "
        "(1) kucing oren vs timun, "
        "(2) kucing tidur dengan posisi aneh, "
        "(3) kucing menirukan suara burung."
    )

    # (c) Tulis hasil ke bus + kirim tugas ke robot lain
    send(ME, "all", "result", f"Temuan scout: {temuan}")
    send(ME, "demo-reporter", "task",
         "Tolong rangkum temuan di atas menjadi 1 paragraf laporan untuk user.")

    # (d) Update status di registry
    touch_registry(ME)
    print(f"[{ME}] selesai: temuan ditulis ke bus + tugas dikirim ke demo-reporter")


if __name__ == "__main__":
    main()
