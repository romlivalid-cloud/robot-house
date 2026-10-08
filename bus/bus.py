"""
Helper message bus Rumah Robot.

Fungsi:
- send(from_id, to, msg_type, text, thread_id=None) : tulis pesan ke
  bus/log.jsonl, sekaligus ke bus/inbox/<to>.jsonl bila 'to' adalah
  robot spesifik. Melakukan VALIDASI sebelum mencatat:
    * tipe pesan harus dikenal (lihat MESSAGE_TYPES)
    * tipe diskusi (idea/build/alternative/concern/synthesis/decision)
      dan 'message' wajib substansial: teks >= 20 karakter dan BUKAN
      persetujuan kosong ("ok", "setuju", "bagus", ... saja)
    * tanggapan diskusi (build/alternative/concern/synthesis/decision)
      dan user_approval/user_rejection WAJIB mencantumkan thread_id
    * pesan 'idea' selalu dibuatkan thread_id baru otomatis
  Pesan yang gagal validasi DITOLAK via ValueError dan TIDAK dicatat.
- read_inbox(robot_id, clear=False) : baca pesan untuk robot tertentu.
- touch_registry(robot_id)          : update last_run robot di registry.
- latest_thread(from_id=None)      : thread_id dari 'idea' terakhir.
- round_count(thread_id)           : jumlah tanggapan (build/alternative/
  concern) dalam satu thread — untuk menegakkan batas 3 ronde.

Heuristik bahasa: bila pesan terdeteksi mayoritas BUKAN Bahasa Indonesia
(rasio kata umum Indonesia rendah), pesan tetap dicatat tapi diberi
field "warning": "non_indonesian". Penegakan utama lewat protokol
(PROTOCOL.md bagian "Aturan Bahasa") + audit coordinator.

Format pesan (satu baris JSON):
{"ts":"ISO8601","from":"robot-id","to":"robot-id|all|coordinator",
 "type":"...","text":"...","thread_id":"th-...","warning":"..."}
"""
import json
import os
import uuid
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUS = os.path.join(BASE, "bus")
INBOX_DIR = os.path.join(BUS, "inbox")
LOG_PATH = os.path.join(BUS, "log.jsonl")

# ---- Tipe pesan yang dikenal -------------------------------------------
BASE_TYPES = {"message", "task", "result", "alert"}
DISCUSSION_TYPES = {"idea", "build", "alternative", "concern", "synthesis", "decision"}
USER_TYPES = {"user_approval", "user_rejection", "user_command"}
MESSAGE_TYPES = BASE_TYPES | DISCUSSION_TYPES | USER_TYPES

# Tipe yang wajib mencantumkan thread_id (menanggapi sebuah ide/keputusan)
REPLY_TYPES = {"build", "alternative", "concern", "synthesis", "decision",
               "user_approval", "user_rejection"}

# Tipe yang wajib substansial (dilarang persetujuan kosong / teks terlalu pendek)
SUBSTANCE_TYPES = DISCUSSION_TYPES | {"message"}

MIN_TEXT_LEN = 20
MAX_ROUNDS = 3  # batas ronde tanggapan per ide (lihat PROTOCOL.md)

APPROVAL_WORDS = {
    "setuju", "ok", "oke", "okay", "siap", "bagus", "mantap", "baik",
    "iya", "ya", "yes", "deal", "lengkap", "sip", "acc", "gas",
    "gaskeun", "lanjut", "okei", "banget",
}

# Kata umum Bahasa Indonesia untuk heuristik deteksi bahasa (~90 kata)
ID_WORDS = {
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "untuk", "dengan",
    "pada", "adalah", "tidak", "tak", "saya", "aku", "kamu", "kita",
    "kami", "kita", "mereka", "dia", "beliau", "robot", "bisa", "akan",
    "ada", "dalam", "juga", "seperti", "karena", "oleh", "sudah",
    "telah", "agar", "supaya", "tentang", "antara", "atau", "sebagai",
    "lebih", "sangat", "hanya", "semua", "setiap", "jika", "kalau",
    "saat", "ketika", "maka", "harus", "wajib", "dapat", "para",
    "bahwa", "secara", "terhadap", "sebuah", "seorang", "beberapa",
    "banyak", "lalu", "kemudian", "namun", "tetapi", "tapi", "serta",
    "tanpa", "sampai", "hingga", "selama", "setelah", "sebelum",
    "sejak", "demi", "kecuali", "selain", "yaitu", "yakni", "sangat",
    "cukup", "kurang", "paling", "amat", "sungguh", "benar", "salah",
    "baru", "lama", "besar", "kecil", "baik", "buruk", "cepat",
    "lambat", "masih", "belum", "pernah", "sering", "jarang",
    "konten", "ide", "diskusi", "keputusan", "persetujuan", "laporan",
}


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def new_thread_id():
    return "th-" + datetime.now().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:6]


def _normalize_words(text):
    return [w.strip(".,!?;:\"'()«»—–-").lower() for w in text.split()]


def is_empty_approval(text):
    """True bila teks HANYA berisi kata persetujuan kosong (tanpa substansi)."""
    words = [w for w in _normalize_words(text) if w]
    return len(words) > 0 and all(w in APPROVAL_WORDS for w in words)


def indonesian_ratio(text):
    """Rasio kata yang cocok dengan daftar kata umum Bahasa Indonesia."""
    words = [w for w in _normalize_words(text) if w]
    if not words:
        return 0.0
    hits = sum(1 for w in words if w in ID_WORDS)
    return hits / len(words)


def send(from_id, to, msg_type, text, thread_id=None):
    # 1. Tipe harus dikenal
    if msg_type not in MESSAGE_TYPES:
        raise ValueError(
            f"Tipe pesan '{msg_type}' tidak dikenal. "
            f"Tipe yang diizinkan: {sorted(MESSAGE_TYPES)}"
        )

    text = (text or "").strip()

    # 2. Validasi substansi untuk tipe diskusi (+ 'message')
    if msg_type in SUBSTANCE_TYPES:
        if len(text) < MIN_TEXT_LEN:
            raise ValueError(
                f"Pesan '{msg_type}' DITOLAK: teks terlalu pendek "
                f"({len(text)} karakter, minimal {MIN_TEXT_LEN}). "
                f"Tulis tanggapan yang substansial, bukan basa-basi."
            )
        if is_empty_approval(text):
            raise ValueError(
                f"Pesan '{msg_type}' DITOLAK: persetujuan kosong "
                f"('{text}') tidak diizinkan. Pilih salah satu: "
                f"'build' (lengakapi ide + alasan), 'alternative' "
                f"(tawarkan alternatif + alasan), atau 'concern' "
                f"(risiko + mitigasi)."
            )

    # 3. Aturan threading
    if msg_type == "idea":
        thread_id = new_thread_id()  # setiap ide = thread baru
    elif msg_type in REPLY_TYPES and not thread_id:
        raise ValueError(
            f"Pesan '{msg_type}' DITOLAK: wajib mencantumkan thread_id "
            f"ide yang ditanggapi."
        )

    entry = {
        "ts": now_iso(),
        "from": from_id,
        "to": to,
        "type": msg_type,
        "text": text,
    }
    if thread_id:
        entry["thread_id"] = thread_id

    # 4. Heuristik bahasa: tandai, JANGAN tolak (false positive berisiko)
    if len(text) >= 30 and indonesian_ratio(text) < 0.12:
        entry["warning"] = "non_indonesian"

    line = json.dumps(entry, ensure_ascii=False)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if to not in ("all", "coordinator"):
        os.makedirs(INBOX_DIR, exist_ok=True)
        with open(os.path.join(INBOX_DIR, f"{to}.jsonl"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    return entry


def read_inbox(robot_id, clear=False):
    path = os.path.join(INBOX_DIR, f"{robot_id}.jsonl")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        msgs = [json.loads(line) for line in f if line.strip()]
    if clear:
        open(path, "w").close()
    return msgs


def touch_registry(robot_id):
    path = os.path.join(BASE, "robots", "registry.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for r in data.get("robots", []):
        if r.get("id") == robot_id:
            r["last_run"] = now_iso()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def latest_thread(from_id=None):
    """Kembalikan thread_id dari pesan 'idea' terakhir (opsional filter pengirim)."""
    if not os.path.exists(LOG_PATH):
        return None
    last = None
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("type") == "idea" and (from_id is None or e.get("from") == from_id):
                last = e.get("thread_id")
    return last


def round_count(thread_id):
    """Jumlah tanggapan (build/alternative/concern) dalam satu thread."""
    if not os.path.exists(LOG_PATH) or not thread_id:
        return 0
    n = 0
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("thread_id") == thread_id and e.get("type") in {
                "build", "alternative", "concern",
            }:
                n += 1
    return n
