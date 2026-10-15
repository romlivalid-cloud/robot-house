#!/usr/bin/env python3
"""Sinkron komentar diskusi antar-bot ke bus/log.jsonl (wall chat dashboard).

Kenapa: diskusi Saras, Vela & Sultan terjadi di GitHub Issues, sehingga tidak
pernah muncul di wall chat dashboard (yang hanya baca bus/log.jsonl).

Cakupan (perbaikan 2026-10-13): baca issue OPEN berlabel 'diskusi-bot' DAN
'tugas-bot' — diskusi aktif (mis. demo konten di #16) berjalan di issue
tugas-bot, bukan hanya diskusi-bot.

- Identitas bot dibaca dari tag [nama-bot] di awal komentar
- Append yang baru ke bus/log.jsonl lokal (anti-duplikat via github_comment id)
- Ke WALL repo (bus/log.jsonl sumber + docs/data/log.jsonl tampil): hanya
  append pesan bertanggal HARI INI (zona Asia/Jakarta) — aturan Bos 2026-10-12:
  wall bersih kecuali percakapan hari ini. JANGAN pernah PUT seluruh log
  lokal (insiden 2026-10-12: chat lama muncul lagi).
- Dijalankan tiap 5 menit oleh cron jembatan-diskusi-antar-bot (bagian F)
"""
import base64
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lock import acquire, release  # noqa: E402  (anti-bentrok run, 2026-10-15)

REPO = "romlivalid-cloud/robot-house"
SEEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "sync_seen.json")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "bus", "log.jsonl")
GH = "/home/hatch/workspace/skills/github/bin/gh-api.py"
OWNERS = ("romlivalid-cloud", "romlidisduk-beep")
LABELS = ("diskusi-bot", "tugas-bot")
WIB = timezone(timedelta(hours=7))

TAG_RE = re.compile(r"^\s*(?:\*{1,2}|_{1,2})?\[([a-z0-9_-]+)\](?:\*{1,2}|_{1,2})?", re.IGNORECASE)
# 2026-10-14: pengumuman resmi berformat bold `**[pengumuman]` (GitHub markdown)
# sebelumnya tidak cocok `^\s*\[` dan terlewat dari wall → izinkan bold di
# sekeliling tag agar pengumuman ikut tersinkron.


def gh(method, path, data=None):
    # Payload besar (mis. PUT seluruh isi file) dikirim via stdin ("-"),
    # bukan argv — perbaikan 2026-10-13: argv base64 >128KB memicu
    # OSError E2BIG "Argument list too long" dan sync berhenti di tengah.
    cmd = ["python3", GH, method, path]
    inp = None
    if data:
        cmd.append("-")
        inp = json.dumps(data)
    r = subprocess.run(cmd, input=inp, capture_output=True, text=True)
    # Perbaikan 2026-10-13: respons non-JSON (mis. 502/proxy error) tidak boleh
    # crash-kan seluruh sync di tengah loop — kembalikan status 0 agar pemanggil
    # menanganinya dengan aman.
    try:
        d = json.loads(r.stdout)
    except Exception:
        return 0, {"error": (r.stdout or "")[:200] or (r.stderr or "")[:200]}
    return d.get("status"), d.get("body")


def gh_all_comments(num):
    """Ambil SEMUA komentar sebuah issue (paginasi).

    Perbaikan 2026-10-13: sebelumnya `per_page=50` tanpa paginasi memotong
    komentar terbaru saat sebuah issue melewati 50 komentar (insiden: 3 pesan
    terbaru #19 tidak tersinkron ke wall)."""
    out = []
    page = 1
    while True:
        st, comments = gh("GET",
                          f"/repos/{REPO}/issues/{num}/comments?per_page=100&page={page}")
        if st != 200 or not isinstance(comments, list):
            break
        out.extend(comments)
        if len(comments) < 100 or page >= 20:  # halaman terakhir / batas aman
            break
        page += 1
    return out


def repo_put(target, content, sha=None):
    """PUT isi penuh ke file repo. Kembalikan status HTTP."""
    payload = {"message": f"Sinkron diskusi bot ({target})",
               "content": base64.b64encode(content.encode()).decode()}
    if sha:
        payload["sha"] = sha
    st2, _ = gh("PUT", f"/repos/{REPO}/contents/{target}", payload)
    return st2


def repo_append(target, line, cid=None):
    """Append satu baris ke file repo (buat baru bila belum ada).

    Idempoten: bila baris dengan github_comment=cid sudah ada, lewati.
    Kembalikan status HTTP (200/201 = sukses, None = tak terverifikasi).
    """
    st, cur = gh("GET", f"/repos/{REPO}/contents/{target}")
    if st == 200 and isinstance(cur, dict):
        sha = cur.get("sha")
        content = base64.b64decode(cur["content"]).decode()
        if cid is not None and f'"github_comment": {cid}' in content:
            return 200  # sudah ada — anti-duplikat
        if content and not content.endswith("\n"):
            content += "\n"
        content += line + "\n"
    elif st == 404:
        sha = None
        content = line + "\n"
    else:
        return None  # GET gagal — jangan tebak, biarkan heal pass mencoba lagi
    return repo_put(target, content, sha)


def read_local_lines():
    """Baca semua baris mentah log lokal."""
    try:
        with open(LOG, encoding="utf-8") as f:
            return f.readlines()
    except FileNotFoundError:
        return []


def heal_wall():
    """Self-healing (perbaikan 2026-10-13): pastikan semua baris lokal bertanggal
    HARI INI (yang punya github_comment) benar-benar ada di kedua file wall repo.
    Menutup celah bila run sebelumnya gagal di tengah PUT (crash JSONDecodeError)
    — barisnya sudah di log lokal sehingga loop utama tidak akan mengulanginya.
    Batch: 1 GET + 1 PUT per file, bukan per baris."""
    today = []
    for raw in read_local_lines():
        raw = raw.rstrip("\n")
        if not raw:
            continue
        try:
            m = json.loads(raw)
        except Exception:
            continue
        if "github_comment" in m and is_today(m.get("ts")):
            today.append((m["github_comment"], raw))
    if not today:
        return
    for target in ("bus/log.jsonl", "docs/data/log.jsonl"):
        st, cur = gh("GET", f"/repos/{REPO}/contents/{target}")
        if st != 200 or not isinstance(cur, dict):
            print(f"heal: tidak bisa baca {target} (HTTP {st}), lewati")
            continue
        content = base64.b64decode(cur["content"]).decode()
        missing = [line for cid, line in today
                   if f'"github_comment": {cid}' not in content]
        if not missing:
            continue
        if content and not content.endswith("\n"):
            content += "\n"
        content += "".join(l + "\n" for l in missing)
        st2 = repo_put(target, content, cur.get("sha"))
        print(f"heal: {len(missing)} baris ditambahkan ke {target} (HTTP {st2})")


def is_today(ts):
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.astimezone(WIB).date() == datetime.now(WIB).date()
    except Exception:
        return False


def processed_comment_ids():
    done = set()
    try:
        with open(LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    m = json.loads(line)
                except Exception:
                    continue
                if "github_comment" in m:
                    done.add(m["github_comment"])
    except FileNotFoundError:
        pass
    return done


def load_seen():
    """Muat daftar id komentar yang pernah terlihat (termasuk yang dilewati
    jendela run-pertama). File ini yang membuat state redeploy tetap aman."""
    try:
        with open(SEEN_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(done):
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(done), f)
    except OSError as e:
        print(f"peringatan: gagal simpan {SEEN_FILE}: {e}")


def dalam_24jam(ts):
    """True bila komentar berumur <=24 jam (jendela aman run pertama)."""
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt) <= timedelta(hours=24)
    except Exception:
        return True  # tanggal tak terbaca -> proses normal saja


def detect_type(body):
    b = body.lower()
    if "[perbandingan]" in b:
        return "synthesis"
    if "[lomba]" in b:
        return "idea"
    if "alternative" in b or "alternatif" in b:
        return "alternative"
    if "concern" in b:
        return "concern"
    if "build" in b:
        return "build"
    return "message"


def main():
    # Anti-bentrok: jangan jalan berbarengan dengan kirim_room / run lain.
    if not acquire("bus-write"):
        print("sync_diskusi: terkunci proses lain, lewati run ini")
        return
    try:
        _main()
    finally:
        release("bus-write")


def _main():
    issues = {}
    for label in LABELS:
        st, lst = gh("GET", f"/repos/{REPO}/issues?state=open&labels={label}&per_page=20")
        if st != 200 or not isinstance(lst, list):
            print(f"gagal baca issues {label}: HTTP {st}")
            continue
        for iss in lst:
            if "pull_request" not in iss:
                issues[iss["number"]] = iss
    done = processed_comment_ids() | load_seen()
    # Run pertama (state kosong, mis. fresh redeploy): batasi jendela 24 jam
    # agar komentar lama tidak membanjiri wall/log (concern 2026-10-15).
    # Id lama tetap ditandai terlihat supaya tidak diproses di run berikut.
    first_run = not done
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    heal_wall()  # tutup celah wall bila run sebelumnya gagal di tengah jalan
    new_local = 0
    new_wall = 0
    for num, issue in sorted(issues.items()):
        comments = gh_all_comments(num)
        for c in comments:
            cid = c.get("id")
            if cid in done:
                continue
            if (c.get("user") or {}).get("login") not in OWNERS:
                done.add(cid)  # komentar orang asing → abaikan (anti-impersonasi)
                continue
            if first_run and not dalam_24jam(c.get("created_at")):
                done.add(cid)  # terlalu lama untuk run pertama -> tandai saja
                continue
            body = (c.get("body") or "").strip()
            if not body:
                continue
            m = TAG_RE.match(body)
            if not m:
                continue  # bukan pesan bot (tanpa tag identitas) → lewati
            bot_id = m.group(1).lower()
            text = TAG_RE.sub("", body, count=1).strip()
            # buang baris [lanjut: ...] dari tampilan chat (info giliran saja)
            text = re.sub(r"(?m)^\[lanjut:[^\]]+\]\s*$", "", text).strip()
            label = next((lb for lb in LABELS
                          if lb in [l["name"] for l in issue.get("labels", [])]), "diskusi-bot")
            msg = {
                "ts": c.get("created_at"),
                "from": bot_id,
                "to": "all",
                "type": detect_type(body),
                "text": text,
                "thread_id": f"{label}-{num}",
                "github_comment": cid,
            }
            line = json.dumps(msg, ensure_ascii=False)
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            done.add(cid)
            new_local += 1
            if is_today(c.get("created_at")):
                # Idempoten + aman: kegagalan PUT tidak crash dan ditutup heal_wall()
                # pada run berikutnya.
                s1 = repo_append("bus/log.jsonl", line, cid)       # sumber (dibaca workflow)
                s2 = repo_append("docs/data/log.jsonl", line, cid)  # tampil instan
                if s1 in (200, 201) and s2 in (200, 201):
                    new_wall += 1
                else:
                    print(f"peringatan: wall gagal untuk komentar {cid} "
                          f"(bus={s1}, docs={s2}) — heal_wall menanganinya")
    save_seen(done)
    print(f"selesai: {new_local} komentar baru ke log lokal, {new_wall} diteruskan ke wall (hari ini).")


if __name__ == "__main__":
    main()
