# 🤖 Rumah Robot

Fondasi pusat komando untuk asisten-asisten robot. Di sinilah semua robot
terdaftar, berdiskusi, dan dipantau — sebelum robot pekerja sungguhan dibangun.

## Apa isi rumah ini?

| Bagian | Isi | Fungsi |
|--------|-----|--------|
| `bus/` | `log.jsonl`, `inbox/`, `bus.py`, `README.md` | Jalur diskusi: semua pesan antar robot tercatat di sini (dengan validasi substansi, threading, dan heuristik Bahasa Indonesia) |
| `robots/` | `registry.json`, `demo_*.py` | Daftar robot + skrip demo pembuktian |
| `dashboard/` | `index.html` | Dashboard web monitoring (1 file, siap GitHub Pages) |
| `coordinator/` | `PROTOCOL.md` | Aturan main: siklus kerja, diskusi ide, Aturan Bahasa, dan Kontrol User |

## Cara kerja (ringkas)

1. **User memerintah via chat** (WhatsApp) — misalnya *"cari ide konten"*.
2. **Muse (coordinator)** menulis perintah sebagai `task` ke inbox robot yang dituju.
3. **Robot** membaca inbox → mengerjakan → menulis hasil ke bus → memberi tugas ke robot lain bila perlu.
4. **User memantau** lewat dashboard web; **Muse merangkum** diskusi ke chat.

Detail aturan: baca `coordinator/PROTOCOL.md`. Detail format pesan: baca `bus/README.md`.

## Cara menambah robot baru

1. Tambahkan entri di `robots/registry.json`:
   ```json
   {"id":"nama-robot","name":"Nama Robot","role":"tugasnya apa",
    "platform":"instagram","schedule":"harian 07:00 WIB",
    "status":"planned","last_run":null,"notes":"catatan"}
   ```
2. Buat skripnya di `robots/nama_robot.py`, pakai helper `bus/bus.py`:
   `read_inbox()` → kerja → `send()` → `touch_registry()`.
   Bila robot ikut diskusi ide, pakai tipe `idea`/`build`/`alternative`/`concern`
   dengan `thread_id` yang sama, dan patuhi batas 3 ronde (lihat `coordinator/PROTOCOL.md` bagian 5).
3. Ubah `status` jadi `active` setelah disetujui user dan terbukti jalan.

Status yang tersedia: `planned` (rencana), `demo` (contoh), `active` (jalan).

## Aturan penting (ringkas)

- **Diskusi ide**: siklus `usulkan → tanggapi → sintesis → putuskan`; setiap robot
  yang relevan WAJIB menanggapi (`build`/`alternative`/`concern` + alasan konkret);
  persetujuan kosong (`"ok"`, `"setuju"` saja) **ditolak otomatis** oleh bus.
- **Bahasa Indonesia saja** untuk seluruh diskusi robot.
- **Kontrol user penuh**: setiap `decision` robot menunggu persetujuan user;
  keputusan user bersifat final dan mengalahkan keputusan robot mana pun.

## Cara user memerintah via chat

Cukup chat seperti biasa. Contoh perintah yang dimengerti:

- *"Aktifkan robot poster-ig"* → coordinator mengubah status di registry
- *"Minta scout-ig cek komentar terbaru"* → coordinator menulis task ke inbox scout-ig
- *"Laporan hari ini"* → coordinator merangkum `bus/log.jsonl` ke chat

## Cara publish ke GitHub Pages (gratis)

Dashboard adalah 1 file statis (`dashboard/index.html`) tanpa build step.
Dashboard membaca data dari `dashboard/data/` (relatif), sehingga Pages
cukup di-deploy dari folder `/dashboard` saja.

1. Buat repo GitHub baru (mis. `robot-house`), **publik** (Pages gratis).
2. Upload **seluruh isi** folder `robot-house/` ke repo, jaga struktur folder
   tetap sama — termasuk folder tersembunyi `.github/` dan file `.nojekyll`.
3. Di repo: **Settings → Pages → Source: Deploy from a branch → branch `main`,
   folder `/dashboard` → Save.**
4. Tunggu 1–2 menit, buka `https://<username>.github.io/robot-house/` di HP.

**Alur data otomatis:** workflow `.github/workflows/robots.yml` berjalan tiap
30 menit (atau manual via tab Actions → Run workflow): menjalankan robot
berstatus `active` lewat `robots/run_scheduled.py`, lalu menyalin
`bus/log.jsonl` → `dashboard/data/log.jsonl` dan `robots/registry.json` →
`dashboard/data/registry.json`, commit + push bila berubah (pakai
`[skip ci]` agar tidak loop). GitHub Pages rebuild otomatis → dashboard
selalu menampilkan diskusi terbaru. Panduan langkah-demi-langkah untuk
user awam: baca `PANDUAN_PUBLISH.md`.

Catatan: bila dibuka langsung sebagai file lokal (`file://`), browser memblokir
`fetch` — dashboard menampilkan peringatan. Lewat GitHub Pages (https) ia jalan normal.

## Bukti mekanisme diskusi bekerja

### Demo 1 — percakapan dasar (2026-10-07)

```bash
cd ~/workspace/robot-house
python3 robots/demo_scout.py
python3 robots/demo_reporter.py
```

`demo-scout` menulis temuan + memberi tugas ke `demo-reporter`;
`demo-reporter` membaca inbox, merangkum, dan membalas ke `demo-scout`.

### Demo 2 — diskusi ide yang hidup (3 robot, ber-thread)

```bash
cd ~/workspace/robot-house
python3 robots/demo_ide_scout.py     # run 1: kirim 'idea' + task ke demo-creator
python3 robots/demo_ide_creator.py   # run 1: 'build' + task ke demo-critic
python3 robots/demo_ide_critic.py    # 'concern' + task ke demo-creator
python3 robots/demo_ide_creator.py   # run 2: 'build' revisi + task ke demo-scout
python3 robots/demo_ide_scout.py     # run 2: 'synthesis' + 'decision'
python3 robots/demo_ide_user.py      # simulasi 'user_approval' dari user
```

Skenario: scout mengusulkan ide serial konten kucing → creator melengkapi
(`build`) → critic mengajukan `concern` + mitigasi → creator merevisi
(`build` ronde 2) → scout menulis `synthesis` + `decision` → user menyetujui
(`user_approval`). Semua pesan berbagi satu `thread_id`, berbahasa Indonesia,
dan tercatat berurutan di `bus/log.jsonl`.

Validasi bus juga terbukti: pesan kosong (`"ok"`, teks < 20 karakter)
**ditolak** dengan error yang jelas dan tidak tercatat di log.
