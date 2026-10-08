"""
demo-critic (diskusi ide): pengkritik ide.

Membaca task dari demo-creator, lalu mengirim 'concern' (risiko + mitigasi)
+ task ke demo-creator agar menanggapi concern tersebut.
Jalankan dari folder robot-house/:  python3 robots/demo_ide_critic.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bus"))
from bus import send, read_inbox, touch_registry, latest_thread  # noqa: E402

ME = "demo-critic"

CONCERN = (
    "Concern untuk serial ini ada dua. Pertama, tren 'kucing vs timun' sudah "
    "lewat puncak viralnya sekitar 2 bulan lalu — risikonya penonton merasa "
    "bosan karena menganggap ini konten daur ulang. Kedua, dua akun kucing "
    "besar sudah pernah mengulang format serupa bulan lalu, jadi kita terlihat "
    "mengekor. Mitigasi yang saya usulkan: episode 1 jadikan 'umpan nostalgia' "
    "saja (timun, maksimal 30 detik), sedangkan episode 2-3 WAJIB memakai benda "
    "yang benar-benar baru ditambah angle unik 'kucing komentator' — dubbing "
    "seolah-olah kucingnya memberi komentar sinis. Patokan tegas: kalau episode "
    "1 tidak tembus 500 views dalam 24 jam, serial dihentikan dan format diganti."
)


def main():
    # (a) Baca inbox sendiri di awal run
    inbox = read_inbox(ME, clear=True)
    for m in inbox:
        print(f"[{ME}] inbox <- {m['from']} [{m['type']}]: {m['text'][:70]}...")

    tasks = [m for m in inbox if m["type"] == "task"]
    if not tasks:
        print(f"[{ME}] inbox kosong — jalankan demo_ide_creator.py dulu.")
        return

    # (b+c) Tulis concern + tugaskan creator menanggapinya
    tid = tasks[-1].get("thread_id") or latest_thread("demo-scout")
    send(ME, "all", "concern", CONCERN, thread_id=tid)
    send(ME, "demo-creator", "task",
         "Tanggapi concern saya di atas: tulis 'build' revisi yang menjawab "
         "risiko kebosanan tren dengan usulan yang konkret.",
         thread_id=tid)
    print(f"[{ME}] selesai: concern + task ke demo-creator (thread {tid})")

    # (d) Update status di registry
    touch_registry(ME)


if __name__ == "__main__":
    main()
