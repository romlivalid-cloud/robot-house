"""
demo-creator (diskusi ide): pelengkap ide.

Membaca task di inbox, lalu:
- task dari demo-scout  -> kirim 'build' ronde 1 + task ke demo-critic
- task dari demo-critic -> kirim 'build' revisi (ronde 2) + task ke demo-scout
Jalankan dari folder robot-house/:  python3 robots/demo_ide_creator.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bus"))
from bus import send, read_inbox, touch_registry, latest_thread  # noqa: E402

ME = "demo-creator"

BUILD_R1 = (
    "Build untuk ide serial kucing oren. (1) Hook 3 detik pertama WAJIB teks "
    "besar 'KUCING OREN KETEMU TIMUN LAGI?!' plus dubbing kocak khas kita — "
    "alasannya: video dengan hook teks di 3 detik pertama rata-rata watch "
    "time-nya 35% lebih tinggi menurut insight akun kita. (2) Jadwal rilis "
    "Selasa-Kamis-Sabtu jam 19:00 WIB, yaitu jam penonton kita paling aktif. "
    "(3) Setiap episode ditutup teaser 5 detik episode berikutnya supaya "
    "penonton follow demi lanjutannya."
)

BUILD_R2 = (
    "Revisi menanggapi concern critic (ronde 2): saya setuju risiko tren basi "
    "itu nyata. Konkretnya begini. (1) Episode 1 (timun) dipadatkan jadi "
    "'jembatan nostalgia' maksimal 30 detik, bukan episode penuh. (2) Episode 2 "
    "memakai sendok sayur + angle 'kucing komentator' — dubbing seolah-olah "
    "kucing protes 'ngapain bawa-bawa sendok' — format ini belum pernah dipakai "
    "kompetitor berdasarkan pantauan saya minggu ini. (3) Patokan stop-loss "
    "konten: bila episode 1 di bawah 500 views dalam 24 jam, episode 2-3 diganti "
    "format cadangan 'kucing tidur posisi aneh' yang datanya historis lebih "
    "stabil. Dengan struktur ini risiko tren basi tertutup oleh kebaruan "
    "episode 2-3."
)


def main():
    # (a) Baca inbox sendiri di awal run
    inbox = read_inbox(ME, clear=True)
    for m in inbox:
        print(f"[{ME}] inbox <- {m['from']} [{m['type']}]: {m['text'][:70]}...")

    tasks = [m for m in inbox if m["type"] == "task"]
    if not tasks:
        print(f"[{ME}] inbox kosong — jalankan demo_ide_scout.py dulu.")
        return

    # (b+c) Tentukan ronde dari siapa yang memberi tugas terakhir
    last = tasks[-1]
    tid = last.get("thread_id") or latest_thread("demo-scout")

    if last["from"] == "demo-critic":
        send(ME, "all", "build", BUILD_R2, thread_id=tid)
        send(ME, "demo-scout", "task",
             "Susun 'synthesis' + 'decision' untuk thread diskusi ini: rangkum "
             "semua masukan yang masuk, lalu tulis keputusan akhirnya.",
             thread_id=tid)
        print(f"[{ME}] ronde 2 selesai: build revisi + task ke demo-scout")
    else:
        send(ME, "all", "build", BUILD_R1, thread_id=tid)
        send(ME, "demo-critic", "task",
             "Kritik ide + build serial kucing di atas: tulis 'concern' berisi "
             "risiko terbesar yang kamu lihat beserta usulan mitigasi yang konkret.",
             thread_id=tid)
        print(f"[{ME}] ronde 1 selesai: build + task ke demo-critic")

    # (d) Update status di registry
    touch_registry(ME)


if __name__ == "__main__":
    main()
