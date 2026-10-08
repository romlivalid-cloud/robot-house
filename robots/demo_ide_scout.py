"""
demo-scout (diskusi ide): pengusul ide.

Run 1: mengirim 'idea' + task ke demo-creator.
Run 2 (setelah ada task dari demo-creator): menulis 'synthesis' + 'decision'.
Jalankan dari folder robot-house/:  python3 robots/demo_ide_scout.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bus"))
from bus import send, read_inbox, touch_registry, latest_thread  # noqa: E402

ME = "demo-scout"

IDEA = (
    "Ide konten: serial 'Kucing Oren vs Benda Dapur' — 3 episode video pendek "
    "(30-45 detik). Episode 1: reaksi kucing oren melihat timun (umpan nostalgia, "
    "format ini pernah viral). Episode 2-3: benda dapur yang belum banyak dipakai "
    "kreator lain (sendok sayur, kardus mie). Alasan: format serial menaikkan "
    "retensi penonton antar-episode, dan bahan syutingnya murah karena memakai "
    "barang yang sudah ada di rumah."
)

SYNTHESIS = (
    "Sintesis thread serial kucing: ide awal saya (serial 3 episode 'Kucing Oren "
    "vs Benda Dapur') dilengkapi creator dengan hook teks 3 detik + dubbing khas "
    "+ jadwal Selasa-Kamis-Sabtu jam 19:00, lalu dikritik critic soal tren timun "
    "yang sudah basi beserta mitigasinya, dan direvisi creator menjadi: episode 1 "
    "sebagai jembatan nostalgia 30 detik, episode 2-3 memakai benda baru dengan "
    "angle 'kucing komentator', plus patokan stop bila episode 1 di bawah 500 "
    "views. Semua masukan sudah terakomodasi dalam struktur revisi."
)

DECISION = (
    "Decision: JALANKAN serial 'Kucing Oren vs Benda Dapur' versi revisi — "
    "3 episode, episode 1 tayang Selasa jam 19:00 WIB. Status keputusan ini: "
    "MENUNGGU PERSETUJUAN USER. Produksi belum boleh dimulai sebelum ada "
    "user_approval di thread ini."
)


def main():
    # (a) Baca inbox sendiri di awal run
    inbox = read_inbox(ME, clear=True)
    for m in inbox:
        print(f"[{ME}] inbox <- {m['from']} [{m['type']}]: {m['text'][:70]}...")

    tasks = [m for m in inbox if m["type"] == "task"]

    if not tasks:
        # (b+c) Run 1: usulkan ide + tugaskan creator melengkapi
        entry = send(ME, "all", "idea", IDEA)
        tid = entry["thread_id"]
        send(ME, "demo-creator", "task",
             "Lengkapi ide serial 'Kucing Oren vs Benda Dapur' di atas: tulis "
             "'build' berisi usulan konkret hook pembuka, jadwal rilis, dan "
             "alasan kenapa usulanmu memperkuat ide ini.",
             thread_id=tid)
        print(f"[{ME}] run 1 selesai: idea dikirim (thread {tid}) + task ke demo-creator")
    else:
        # (b+c) Run 2: sintesis + keputusan
        tid = tasks[-1].get("thread_id") or latest_thread(ME)
        send(ME, "all", "synthesis", SYNTHESIS, thread_id=tid)
        send(ME, "all", "decision", DECISION, thread_id=tid)
        print(f"[{ME}] run 2 selesai: synthesis + decision dikirim (thread {tid})")

    # (d) Update status di registry
    touch_registry(ME)


if __name__ == "__main__":
    main()
