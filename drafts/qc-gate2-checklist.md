# Checklist QC Gate 2 — @romligresik (slot malam 19:30)

> **Status:** DISETUJUI v1.1 — 2026-10-17 (keputusan Bos via [saras-koordinator], komentar 6232275592 di #37)
> Berlaku mulai: QC slot 19:30 malam ini.
> Berlaku untuk: slot tayang malam 19:30, QC pra-tayang selesai s.d. 18:30, go/no-go oleh Saras.

---

## Butir 1a — Verifikasi fakta tilawah (audit fakta: Sultan)

- [ ] Teks yang dibaca terverifikasi benar ayat/hadis (redaksi kata-per-kata sesuai sumber).
- [ ] Identitas qari dan riwayat yang tertera di overlay/caption sesuai sumber.
- [ ] Bila nama qari atau sumber riwayat diklaim dalam caption, perlu verifikasi faktual.

## Butir 1b — Kualitas teknis tilawah & aset final (QC teknis: Vela)

- [ ] Overlay selaras dengan audio (sinkronisasi disertai timestamp).
- [ ] Level audio dalam ambang — tilawah tidak tertutup backsound/musik; audio tidak pecah/berbunyi aneh.
- [ ] Durasi & resolusi sesuai spesifikasi slot (9:16).
- [ ] Status klaim frekuensi "kesalahan QC tilawah yang paling sering lolos": **menunggu bukti** — ditulis sebagai risiko yang perlu diperiksa, BUKAN sebagai statistik, sampai ada log insiden (aturan Bos, 2026-10-14).
- [ ] Setiap temuan teknis dicatat dengan timestamp + file/commit agar bisa diaudit silang.

## Butir 2 — Lisensi rekaman & aset visual (verifikasi fakta: Sultan; QC: Vela)

- [ ] Bila lisensi rekaman belum jelas → gunakan **fallback teks-visual**.
- [ ] Fallback teks-visual BUKAN klaim "bebas lisensi penuh" — sumber/izin tetap dicatat.
- [ ] Sumber/izin dicatat **per aset** visual.
- [ ] **Ayat:** terjemahan Kemenag. **Hadis:** cantumkan koleksi/sumber + nomor hadis + penerjemah/edisi terjemah yang dipakai.

---

## Riwayat status

| Tanggal (WIB) | Status | Keterangan |
|---|---|---|
| 2026-10-17 | diusulkan | Usulan Vela di issue #37; dikomit oleh saras-koordinator sebagai DRAFT v1.0. Menunggu review Sultan (artefak audit) — per aturan Bos 2026-10-16, perubahan checklist hanya "diusulkan/dicatat" sampai ada commit ini; kolom status dua nilai ("menunggu bukti"/"terverifikasi") berlaku per butir klaim. |
| 2026-10-17 | diusulkan | Amandemen Vela (komentar 6231925243): Butir 1 dipecah jadi 1a (fakta — Sultan) dan 1b (teknis — Vela); Butir 2 diperjelas (Kemenag hanya untuk ayat; hadis wajib koleksi + nomor + penerjemah/edisi). Status tetap **diusulkan** — keberadaan commit BUKAN bukti disetujui/dijalankan; checklist baru menjadi dasar QC slot malam HANYA setelah Bos menyetujui atau pemakaian nyata tercatat. |
