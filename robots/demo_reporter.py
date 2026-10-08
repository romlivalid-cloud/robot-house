"""
demo-reporter: robot contoh #2.

Tugas: membaca inbox-nya, merangkum temuan scout, membalas ke demo-scout.
Jalankan:  python3 robots/demo_reporter.py   (dari folder robot-house/)
           (jalankan SETELAH demo_scout.py agar ada tugas di inbox)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bus"))
from bus import send, read_inbox, touch_registry  # noqa: E402

ME = "demo-reporter"


def main():
    # (a) Baca inbox sendiri di awal run
    inbox = read_inbox(ME, clear=True)
    tugas = [m for m in inbox if m["type"] == "task"]
    if not tugas:
        print(f"[{ME}] inbox kosong, tidak ada tugas. Jalankan demo_scout.py dulu.")
        return
    for m in tugas:
        print(f"[{ME}] inbox <- {m['from']}: {m['text']}")

    # (b) Kerjakan tugas: buat ringkasan
    ringkasan = (
        "Laporan demo: Scout menemukan 3 topik kucing terhangat hari ini — "
        "kucing oren vs timun, posisi tidur aneh, dan kucing menirukan suara burung. "
        "Siap dijadikan bahan konten."
    )

    # (c) Tulis hasil ke bus + balas ke demo-scout (percakapan 2 arah!)
    send(ME, "all", "result", ringkasan)
    send(ME, "demo-scout", "message",
         "Ringkasan selesai dan sudah diumumkan ke bus. Terima kasih atas temuannya!")

    # (d) Update status di registry
    touch_registry(ME)
    print(f"[{ME}] selesai: ringkasan ditulis + balasan dikirim ke demo-scout")


if __name__ == "__main__":
    main()
