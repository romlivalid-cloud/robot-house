# 📖 Panduan Publish Rumah Robot ke GitHub (untuk Pemula)

Panduan ini membawamu dari nol sampai bisa memantau chat robot lewat web
di HP. Tidak perlu bisa coding — cukup ikuti langkahnya satu per satu.

**Yang kamu butuhkan:** file `robot-house.zip`, aplikasi file manager
(bawaan HP biasanya cukup, atau install **ZArchiver** gratis), browser
Chrome, dan akun GitHub (buat gratis di github.com kalau belum punya).

---

## Langkah 1 — Ekstrak file ZIP

1. Buka file manager di HP, cari file `robot-house.zip` (biasanya di folder Download).
2. Tahan file → **Ekstrak di sini**. Akan muncul folder `robot-house/` berisi:
   `bus/`, `robots/`, `dashboard/`, `coordinator/`, `.github/`, `README.md`,
   dan file ini.
3. ⚠️ Pastikan folder **`.github`** ikut terlihat — folder yang namanya diawali
   titik kadang disembunyikan file manager. Di ZArchiver: menu → tampilkan
   file tersembunyi.

## Langkah 2 — Buat repo baru di GitHub

1. Buka **github.com** di Chrome, login.
2. Klik tombol **+** (kanan atas) → **New repository**.
3. Isi:
   - *Repository name:* `robot-house`
   - Pilih **Public** (wajib — GitHub Pages gratis hanya untuk repo publik)
   - Centang **Add a README file** (boleh, nanti tertimpa)
4. Klik **Create repository**.

## Langkah 3 — Upload semua file

1. Di halaman repo barumu, klik tulisan **"uploading an existing file"**
   (atau tombol **Add file → Upload files**).
2. Dari file manager, pilih **SEMUA isi** folder `robot-house/` — semua file
   dan semua folder (`bus`, `robots`, `dashboard`, `coordinator`, `.github`)
   — lalu seret/jatuhkan ke halaman GitHub. Struktur folder harus tetap sama.
3. Tunggu sampai semua file muncul di daftar, lalu klik **Commit changes**.
4. ✅ Cek: di halaman repo harus terlihat folder `.github` (klik untuk
   memastikan ada `workflows/robots.yml` di dalamnya) dan folder `dashboard`.

> 💡 Kalau drag & drop folder susah di HP: upload bisa dilakukan bertahap —
> masuk ke tiap folder di web GitHub (klik folder → Add file → Upload files),
> lalu upload isi folder tersebut.

## Langkah 4 — Aktifkan GitHub Pages

1. Di repo, klik tab **Settings** (ikon gerigi).
2. Di menu kiri, klik **Pages**.
3. Pada *Build and deployment* → *Source*: pilih **Deploy from a branch**.
4. *Branch*: pilih **main**, folder: pilih **/dashboard** → klik **Save**.
5. Tunggu 1–2 menit. GitHub akan menampilkan alamat web-mu, misalnya:
   `https://suburindonesia76-cyber.github.io/robot-house/`

## Langkah 5 — Buka dan pantau! 🎉

1. Buka alamat di atas di Chrome HP-mu.
2. Kamu akan melihat **Ruang Chat Robot**:
   - Tab **💬 Chat** — bubble chat diskusi para robot (mirip WhatsApp),
     lengkap dengan badge tipe pesan dan filter per robot
   - Tab **📋 Robot** — kartu status tiap robot
3. Halaman **otomatis segar tiap 30 detik** — tidak perlu refresh manual.
4. **Simpan sebagai bookmark** atau *Add to Home screen* biar gampang dibuka.

## Langkah 6 — (Opsional) Jalankan robot manual

Robot berjalan otomatis tiap 30 menit via GitHub Actions. Untuk menjalankan
sekarang juga:

1. Di repo, klik tab **Actions**.
2. Klik workflow **"Robot House — Jalankan Robot Terjadwal"**.
3. Klik **Run workflow** → **Run workflow**.

---

## Tanya jawab singkat

**Q: Apakah gratis?**
A: Ya. Repo publik + GitHub Pages + GitHub Actions semuanya gratis
(kuota Actions untuk repo publik tidak dibatasi).

**Q: Datanya update sendiri?**
A: Ya. Tiap 30 menit workflow berjalan, robot yang aktif bekerja, hasilnya
dicatat ke bus, dan dashboard ikut ter-update otomatis.

**Q: Saya mau perintah robot, lewat mana?**
A: Tetap lewat chat WhatsApp ke Muse seperti biasa — Muse yang meneruskan
perintahmu ke robot. Dashboard ini khusus untuk **memantau**.

**Q: Error / halaman kosong?**
A: Pastikan repo berstatus **Public**, folder deploy di Pages adalah
**/dashboard**, dan tunggu 2–3 menit setelah Save. Kalau masih kosong,
buka tab Actions untuk melihat apakah workflow berjalan.
