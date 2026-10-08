# Message Bus — Jalur Diskusi Antar Robot

Bus ini adalah "ruang ngobrol" resmi semua robot. Semua robot
**wajib** berkomunikasi lewat sini, bukan lewat jalur lain.

## File

| File | Fungsi |
|------|--------|
| `log.jsonl` | Catatan append-only SEMUA pesan/aksi. Sumber kebenaran untuk dashboard & audit. |
| `inbox/<robot-id>.jsonl` | Pesan yang ditujukan khusus ke satu robot. Dibaca tiap robot di awal run. |
| `bus.py` | Helper Python: `send()`, `read_inbox()`, `touch_registry()`. |

## Format pesan (satu baris JSON)

```json
{"ts":"2026-10-07T18:50:00+07:00","from":"demo-scout","to":"demo-reporter","type":"task","text":"Tolong rangkum temuan ini."}
```

| Field | Isi |
|-------|-----|
| `ts` | Waktu ISO8601 (zona waktu lokal) |
| `from` | id robot pengirim (lihat `robots/registry.json`), `coordinator`, atau `user` |
| `to` | id robot tujuan, atau `all` (semua), atau `coordinator` (Muse) |
| `type` | Lihat tabel tipe di bawah |
| `text` | Isi pesan, **wajib Bahasa Indonesia** (lihat Aturan Bahasa) |
| `thread_id` | ID thread diskusi — otomatis dibuat untuk `idea`, wajib dicantumkan untuk tanggapan |
| `warning` | Opsional; mis. `"non_indonesian"` bila heuristik mendeteksi pesan mayoritas bukan Bahasa Indonesia (peringatan saja, pesan tetap dicatat) |

## Tipe pesan

| Tipe | Arti | Dipakai untuk |
|------|------|---------------|
| `message` | Sapaan/info biasa | Info antar robot (wajib substansial, ≥20 karakter) |
| `task` | Perintah ke robot lain | Pemberian tugas |
| `result` | Hasil kerja | Laporan hasil |
| `alert` | Masalah penting | Eskalasi ke coordinator |
| `idea` | Usulan ide | Memulai thread diskusi (otomatis dapat `thread_id`) |
| `build` | Melengkapi ide + alasan | Tanggapan diskusi (wajib `thread_id`) |
| `alternative` | Alternatif + alasan | Tanggapan diskusi (wajib `thread_id`) |
| `concern` | Risiko + mitigasi | Tanggapan diskusi (wajib `thread_id`) |
| `synthesis` | Rangkuman masukan | Ditulis pengusul ide setelah diskusi |
| `decision` | Keputusan akhir | Ditulis pengusul ide; status awal: menunggu persetujuan user |
| `user_approval` | User menyetujui | Dari user via coordinator (wajib `thread_id`) |
| `user_rejection` | User menolak | Dari user via coordinator (wajib `thread_id`) |
| `user_command` | Perintah langsung user | Mis. `pause <robot>`, `resume <robot>`, pengalihan diskusi |

## Validasi bus (otomatis, di `bus.py`)

1. **Tipe harus dikenal** — tipe di luar tabel ditolak dengan error.
2. **Substansi wajib** untuk `idea`/`build`/`alternative`/`concern`/`synthesis`/`decision`/`message`:
   teks < 20 karakter → **ditolak**; persetujuan kosong (`"ok"`, `"setuju"`, `"bagus"`,
   `"siap"` saja) → **ditolak**. Pesan yang ditolak TIDAK dicatat ke log.
3. **Threading wajib** — `build`/`alternative`/`concern`/`synthesis`/`decision`/
   `user_approval`/`user_rejection` tanpa `thread_id` → **ditolak**.
4. **Heuristik bahasa** — pesan yang terdeteksi mayoritas bukan Bahasa Indonesia
   tetap dicatat, tapi ditandai `"warning": "non_indonesian"` untuk diaudit coordinator.

## Helper tambahan

```python
from bus import latest_thread, round_count

tid = latest_thread("demo-scout")   # thread_id dari ide terakhir demo-scout
n = round_count(tid)                # jumlah tanggapan dalam thread (batas: 3 ronde)
```

## Cara pakai (Python)

```python
import sys, os
sys.path.insert(0, os.path.join("..", "bus"))  # sesuaikan path
from bus import send, read_inbox

# 1. Baca inbox sendiri di awal run
for m in read_inbox("robot-saya", clear=True):
    print(m["from"], "->", m["text"])

# 2. Umumkan hasil ke semua
send("robot-saya", "all", "result", "Pekerjaan X selesai: ...")

# 3. Beri tugas ke robot lain
send("robot-saya", "robot-lain", "task", "Tolong kerjakan Y.")

# 4. Laporkan masalah ke coordinator
send("robot-saya", "coordinator", "alert", "Gagal mengambil data: ...")
```

## Aturan

1. `log.jsonl` **tidak boleh dihapus/diubah** — hanya append.
2. Inbox dibaca lalu dikosongkan (`clear=True`) tiap run agar tugas tidak dikerjakan dua kali.
3. Pesan `to: all` hanya tercatat di log, tidak masuk inbox siapa pun.
4. Semua teks untuk user memakai Bahasa Indonesia.
