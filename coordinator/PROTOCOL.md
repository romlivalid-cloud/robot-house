# Protokol Diskusi & Koordinasi Robot

Semua robot di Rumah Robot wajib mengikuti aturan ini.

## 1. Siklus kerja setiap robot (4 langkah, berurutan)

Setiap kali robot dijalankan, ia harus:

1. **(a) Baca inbox sendiri** — `read_inbox("<id-robot>", clear=True)` dari `bus/inbox/`.
   Tugas yang sudah dibaca dianggap miliknya; jangan dikerjakan dua kali.
2. **(b) Kerjakan tugas** — jalankan pekerjaan sesuai `role` di `robots/registry.json`.
3. **(c) Lapor ke bus** — tulis ke `bus/log.jsonl` via `send()`:
   - hasil kerja → `to: all`, `type: result`
   - butuh bantuan robot lain → `to: <id-robot>`, `type: task`
   - info biasa → `type: message`
   - masalah serius → `to: coordinator`, `type: alert`
4. **(d) Update registry** — `touch_registry("<id-robot>")` agar `last_run` tercatat.
   Dashboard membaca field ini.

## 2. Peran coordinator (Muse)

Coordinator bukan robot biasa. Tugasnya:

- **Meneruskan perintah user**: perintah dari chat (WhatsApp) ditulis sebagai
  `type: task` ke `bus/inbox/<id-robot>.jsonl` robot yang dituju.
- **Merangkum diskusi**: membaca `bus/log.jsonl`, menyampaikan ringkasan
  Bahasa Indonesia ke user via chat — user tidak perlu membaca log mentah.
- **Menyelesaikan konflik**: bila dua robot memberi hasil bertentangan atau
  satu robot mengirim `alert`, coordinator memutuskan dan mencatat
  keputusannya ke bus (`from: coordinator`).
- **Menjaga registry**: menambah/menonaktifkan robot di `robots/registry.json`
  hanya atas persetujuan user.

## 3. Contoh alur diskusi konkret (3 langkah)

Skenario: user memerintah via chat — *"Cari 3 ide konten kucing untuk minggu ini."*

**Langkah 1 — user → coordinator → robot.**
Coordinator menerima perintah di chat, lalu menulis ke bus:
```json
{"from":"coordinator","to":"scout-ig","type":"task",
 "text":"Cari 3 ide konten kucing untuk minggu ini (perintah user via chat)."}
```
Pesan ini otomatis masuk `bus/inbox/scout-ig.jsonl`.

**Langkah 2 — robot kerja & lapor.**
scout-ig berjalan: membaca inbox, mengerjakan pencarian, lalu:
```json
{"from":"scout-ig","to":"all","type":"result",
 "text":"3 ide konten: (1) ... (2) ... (3) ..."}
{"from":"scout-ig","to":"reporter","type":"task",
 "text":"Susun 3 ide di atas jadi laporan rapi untuk user."}
```

**Langkah 3 — robot lain menindaklanjuti, coordinator merangkum.**
reporter membaca inbox, membuat laporan:
```json
{"from":"reporter","to":"all","type":"result",
 "text":"Laporan ide konten minggu ini: ..."}
```
Coordinator membaca bus, lalu menyampaikan ke user via chat:
*"Dapat 3 ide konten minggu ini: (1)... (2)... (3)..."*

User cukup membaca chat; seluruh jejak diskusi tersimpan di `bus/log.jsonl`
dan terlihat di dashboard.

## 4. Aturan tambahan

- Satu tugas = satu pemilik. Robot tidak mengerjakan inbox robot lain.
- `alert` selalu ditujukan ke `coordinator` dan direspons maksimal 1x24 jam.
- Dilarang menghapus/mengubah `bus/log.jsonl` — append-only.
- Semua teks user-facing memakai Bahasa Indonesia.

## 5. Diskusi Ide — agar robot saling melengkapi, bukan sekadar setuju

Diskusi ide memakai tipe pesan khusus dan selalu ber-thread
(`thread_id` dibuat otomatis saat `idea` dikirim).

### 5.1 Siklus hidup ide (4 tahap, berurutan)

1. **Usulkan** — robot mengirim `type: idea` ke `all` (atau robot tertentu).
   Bus otomatis membuat `thread_id` baru untuk ide ini.
2. **Tanggapi** — robot yang relevan **WAJIB** menanggapi pada run
   berikutnya dengan SALAH SATU tipe ini (cantumkan `thread_id`):
   - `build` — melengkapi/memperkuat ide + **alasan konkret** (data, contoh, usulan spesifik)
   - `alternative` — menawarkan alternatif + **alasan** kenapa alternatifnya lebih baik
   - `concern` — menunjukkan risiko/kelemahan + **usulan mitigasi konkret**
3. **Sintesis** — pengusul ide menulis `type: synthesis`: merangkum semua
   masukan yang masuk dalam thread.
4. **Putuskan** — pengusul menulis `type: decision`: keputusan akhir +
   langkah berikutnya. Statusnya otomatis **"menunggu persetujuan user"**
   (lihat bagian 7).

### 5.2 Larangan persetujuan kosong

Pesan seperti *"setuju"*, *"ok"*, *"bagus"*, *"siap"* tanpa substansi
**DITOLAK otomatis oleh bus** dan tidak dicatat ke log. Setiap tanggapan
wajib memuat isi: alasan, data, contoh, risiko, atau usulan konkret
(minimal 20 karakter).

### 5.3 Batas ronde

Maksimal **3 ronde** tanggapan (`build`/`alternative`/`concern`) per ide.
Cek dengan `round_count(thread_id)` dari `bus.py`. Setelah 3 ronde,
pengusul **WAJIB** menulis `synthesis` + `decision`. Bila diskusi buntu
(tidak ada kesepakatan), eskalasi ke coordinator via `type: alert`.

### 5.4 Contoh format pesan diskusi

```json
{"from":"demo-scout","to":"all","type":"idea",
 "thread_id":"th-20261007190000-a1b2c3",
 "text":"Ide konten: serial 3 episode ... (substansial, >=20 karakter)"}
{"from":"demo-creator","to":"all","type":"build",
 "thread_id":"th-20261007190000-a1b2c3",
 "text":"Melengkapi ide scout: tambahkan hook 3 detik ... karena ..."}
{"from":"demo-critic","to":"all","type":"concern",
 "thread_id":"th-20261007190000-a1b2c3",
 "text":"Risiko: tren ini sudah lewat puncaknya. Mitigasi: ..."}
```

## 6. Aturan Bahasa — Bahasa Indonesia saja

**Seluruh diskusi robot** (ide, tanggapan, sintesis, keputusan, log)
**HARUS dalam Bahasa Indonesia.** Ini aturan keras, bukan anjuran.

- Bus menjalankan heuristik ringan: bila sebuah pesan terdeteksi mayoritas
  bukan Bahasa Indonesia, pesan tetap dicatat tetapi diberi tanda
  `"warning": "non_indonesian"` di log. Bus **tidak menolak** pesan
  tersebut karena heuristik bisa salah (false positive).
- Penegakan utama lewat protokol ini + audit coordinator: coordinator
  memeriksa pesan ber-`warning` secara berkala; pelanggaran berulang
  mendapat teguran tercatat di bus (`from: coordinator`).
- Pengecualian: nama teknis/produk (mis. "Instagram", "API") dan kode
  boleh tetap dalam bentuk aslinya.

## 7. Kontrol User — user memegang kendali penuh

Diskusi robot juga dicerminkan ke **Ruang Robot** (ruang chat khusus)
di mana user memegang kontrol penuh. Aturan:

1. **Menyetujui / menolak** — user bisa menyetujui atau menolak ide
   maupun keputusan robot mana pun.
2. **Pause / resume** — user bisa menghentikan sementara (`pause`)
   robot tertentu; robot yang di-pause tidak dijalankan sampai ada
   perintah `resume`.
3. **Mengarahkan ulang** — user bisa membelokkan diskusi kapan saja;
   robot wajib mengikuti arahan terbaru user.
4. **Meminta ringkasan** — user bisa meminta ringkasan diskusi kapan saja;
   coordinator wajib menyediakannya via chat.

**Keputusan user = final** dan mengalahkan keputusan robot mana pun.

### 7.1 Alur persetujuan keputusan

Setiap `decision` robot otomatis berstatus **"menunggu persetujuan user"**,
KECUALI user sudah memberi wewenang penuh sebelumnya untuk jenis
keputusan itu (dicatat coordinator di bus).

Alurnya:

1. Robot menulis `type: decision` ke bus (dengan `thread_id`).
2. Coordinator meneruskan isi keputusan ke Ruang Robot (chat) untuk
   dimintakan persetujuan.
3. User menjawab **setuju** → coordinator mencatat ke bus:
   `{"from":"user","to":"all","type":"user_approval","thread_id":"...",
   "text":"..."}`
   User menjawab **tolak** (+ alasan bila ada) → tercatat sebagai
   `type: user_rejection`.
4. Perintah langsung user ke robot dicatat sebagai `type: user_command`
   (mis. `"pause demo-critic"`, `"lanjutkan diskusi ide X ke arah Y"`).

Tanpa `user_approval`, robot **dilarang** mengeksekusi keputusan yang
berdampak ke dunia luar (posting, membalas, mengubah data).
