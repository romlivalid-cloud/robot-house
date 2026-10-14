#!/usr/bin/env python3
"""
Bot cadangan Rumah Robot — siaga, GRATIS (API gratis via Secure Vault).

Prinsip (keputusan Bos 2026-10-13):
- Bot asli (Vela/Sultan) TETAP yang utama untuk diskusi.
- Cadangan DORMAN selama bot asli aktif.
- Cadangan AKTIF hanya saat failover menurut contingency-v3:
  teguran -> 24 jam -> notifikasi pra-alih -> KONFIRMASI BOS -> aktif.
- Tanpa API key gratis: worker hanya memantau + notifikasi (tidak membalas).

Perintah:
  python3 cadangan.py check                 # cek kesehatan bot asli
  python3 cadangan.py reply-check           # balas giliran utk cadangan AKTIF
  python3 cadangan.py run                   # check + reply-check (untuk cron)
  python3 cadangan.py activate --bot ID     # Bos setuju -> aktifkan cadangan
  python3 cadangan.py deactivate --bot ID   # kembalikan ke siaga
"""
import json, os, sys, time, subprocess, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(BASE, "config.json")
STATE = os.path.join(BASE, "state.json")
HOUSE = os.path.expanduser("~/workspace/robot-house")
GH_API = os.path.expanduser("~/workspace/skills/github/bin/gh-api.py")
KIRIM_ROOM = os.path.join(HOUSE, "cross-bot", "kirim_room.py")
REPO = "romlivalid-cloud/robot-house"

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import (
    add_surrogate_to_request, url_with_surrogate_query_param,
    read_json_response, DynamicCredentialError,
)

# ---------- util ----------
def load(p, default):
    return json.load(open(p)) if os.path.exists(p) else default

def save(p, d):
    json.dump(d, open(p, "w"), indent=1, ensure_ascii=False)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def gh(method, path, data=None):
    cmd = ["python3", GH_API, method, path]
    if data is not None:
        cmd += ["-"]
        inp = json.dumps(data)
    else:
        inp = None
    r = subprocess.run(cmd, input=inp, capture_output=True, text=True, timeout=60)
    return json.loads(r.stdout)

def post_issue_comment(issue, body):
    r = gh("POST", f"/repos/{REPO}/issues/{issue}/comments", {"body": body})
    return r.get("body", {}).get("html_url", "?")

def kirim_wall(msg):
    try:
        subprocess.run(["python3", KIRIM_ROOM, msg], timeout=60,
                       capture_output=True)
    except Exception:
        pass

# ---------- LLM gratis via Secure Vault ----------
def llm_ask(provider, system, user_text):
    """provider: 'gemini' | 'groq'. Key dari vault custom.llm-gratis."""
    if provider == "gemini":
        model = "gemini-2.5-flash"
        url_t = (f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
                 ":generateContent")
        try:
            url = url_with_surrogate_query_param(
                url_t, "custom.llm-gratis", entry_name="gemini_key",
                allowed_hosts=["generativelanguage.googleapis.com"])
        except DynamicCredentialError as e:
            raise RuntimeError(f"API key Gemini belum dikonfigurasi: {e}")
        payload = {"system_instruction": {"parts": [{"text": system}]},
                   "contents": [{"role": "user", "parts": [{"text": user_text}]}],
                   "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}}
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "rumah-robot-cadangan/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            d = read_json_response(r)
        return d["candidates"][0]["content"]["parts"][0]["text"]
    elif provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {"model": "openai/gpt-oss-20b",
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user_text}],
                   "temperature": 0.7, "max_tokens": 800}
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "rumah-robot-cadangan/1.0"})
        try:
            add_surrogate_to_request(req, "custom.llm-gratis",
                                     allowed_hosts=["api.groq.com"])
        except DynamicCredentialError as e:
            raise RuntimeError(f"API key Groq belum dikonfigurasi: {e}")
        with urllib.request.urlopen(req, timeout=60) as r:
            d = read_json_response(r)
        return d["choices"][0]["message"]["content"]
    raise RuntimeError(f"provider tidak dikenal: {provider}")

# ---------- kesehatan bot ----------
DATE_ONLY_RE = None  # diisi di bawah (butuh re)

def bot_last_active(bot_id):
    """Detik sejak aktivitas terakhir bot.
    Sumber: registry last_run (HANYA bila bertimestamp penuh — stempel
    tanggal-harian tanpa jam adalah stempel blanket cron denyut untuk semua
    bot, BUKAN sinyal aktivitas, jadi diabaikan; perbaikan 2026-10-15),
    tag [bot] di bus/log.jsonl lokal, dan tag [bot] di komentar GitHub
    issue diskusi (langsung via API)."""
    import re
    global DATE_ONLY_RE
    if DATE_ONLY_RE is None:
        DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    last = None

    def consider(ts):
        nonlocal last
        if ts and (not last or ts > last):
            last = ts

    reg = load(os.path.join(HOUSE, "robots", "registry.json"), {})
    robots = reg.get("robots", []) if isinstance(reg, dict) else []
    for r in robots:
        if isinstance(r, dict) and r.get("id") == bot_id and r.get("last_run"):
            raw = str(r["last_run"]).strip()
            if DATE_ONLY_RE.match(raw):
                continue  # stempel harian blanket — bukan aktivitas asli
            try:
                ts = datetime.fromisoformat(raw)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                consider(ts)
            except Exception:
                pass
    tag_re = re.compile(r"^\[([a-z0-9-]+)\]")
    try:
        with open(os.path.join(HOUSE, "bus", "log.jsonl")) as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                # identitas bot ada di field `from` (sync_diskusi) ATAU prefix
                # [tag] di awal teks (pesan yang diposting worker sendiri)
                is_bot = d.get("from") == bot_id
                if not is_bot:
                    m = tag_re.match(d.get("text") or "")
                    is_bot = bool(m) and m.group(1) == bot_id
                if not is_bot:
                    continue
                try:
                    consider(datetime.fromisoformat(
                        str(d.get("ts")).replace("Z", "+00:00")))
                except Exception:
                    pass
    except Exception:
        pass
    # cek langsung ke GitHub (tag bisa ada di komentar yg belum tersinkron).
    # API komentar mengembalikan yang TERLAMA dulu dan mengabaikan
    # direction=desc (pelajaran AGENTS.md 2026-10-14), jadi baca dari halaman
    # TERAKHIR mundur — tanpa ini komentar terbaru di issue ramai (>100
    # komentar, mis. #16) tidak pernah terbaca (perbaikan 2026-10-15).
    try:
        since_dt = datetime.now(timezone.utc) - timedelta(days=7)
        issues = {}
        for label in ("diskusi-bot", "tugas-bot"):
            r = gh("GET", f"/repos/{REPO}/issues?labels={label}"
                          f"&state=open&per_page=30")
            for it in r.get("body", []) or []:
                if isinstance(it, dict) and it.get("number"):
                    issues[it["number"]] = it.get("comments", 0)
        for n, total in sorted(issues.items()):
            pages = max(1, -(-int(total or 0) // 100))
            for page in range(pages, 0, -1):
                r = gh("GET", f"/repos/{REPO}/issues/{n}/comments"
                              f"?per_page=100&page={page}")
                comments = r.get("body", [])
                if not isinstance(comments, list):
                    break
                newest = None
                for c in comments:
                    # Kepengarangan = tag di AWAL body (konvensi room), bukan
                    # sekadar disebut — komentar teguran [saras-koordinator]
                    # yang mengutip "[vela]" bukan aktivitas Vela.
                    body = (c.get("body") or "").lstrip()
                    if not body.startswith(f"[{bot_id}]"):
                        continue
                    try:
                        ts = datetime.fromisoformat(
                            str(c["created_at"]).replace("Z", "+00:00"))
                    except Exception:
                        continue
                    if ts >= since_dt and (not newest or ts > newest):
                        newest = ts
                if newest:
                    consider(newest)
                    break  # halaman ini memuat tagged-comment terbaru issue tsb
    except Exception:
        pass
    if not last:
        return None
    return (datetime.now(timezone.utc) - last).total_seconds()

def is_bermasalah(bot_id):
    idle = bot_last_active(bot_id)
    if idle is None:
        return True, "tidak ada data denyut"
    if idle > 24 * 3600:
        return True, f"tidak aktif {idle/3600:.1f} jam (>24 jam)"
    return False, f"aktif {idle/3600:.1f} jam lalu"

BRIDGE_WARNINGS = os.path.expanduser(
    "~/workspace/goals/connect-saras-with-numbervoucher-bot-via-its-backend"
    "/hidden_files/contingency_warnings.json")

def bridge_warning_ts(bot_id):
    """Timestamp teguran formal jembatan (contingency-v3) untuk bot, atau None.
    Dipakai agar worker cadangan tidak mengirim notifikasi pra-alih ganda /
    mendahului tenggat 24 jam yang sudah diumumkan jembatan (2026-10-15)."""
    try:
        w = json.load(open(BRIDGE_WARNINGS))
    except Exception:
        return None
    e = w.get(bot_id)
    if not isinstance(e, dict) or not e.get("peringatan_pertama"):
        return None
    try:
        ts = datetime.fromisoformat(str(e["peringatan_pertama"]))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts
    except Exception:
        return None

def bridge_sudah_eskalasi(bot_id, sejak):
    """True bila failover_log repo memuat event notifikasi-pra-alih untuk
    bot_id pada/setelah `sejak` (artinya jembatan sudah menjalankan
    eskalasinya sendiri — cadangan tidak perlu duplikat)."""
    import base64
    try:
        r = gh("GET", f"/repos/{REPO}/contents/docs/data/failover_log.jsonl")
        body = (r.get("body") or {}).get("content", "")
        txt = base64.b64decode(body).decode("utf-8", "replace")
    except Exception:
        return False
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("bot") != bot_id or d.get("event") != "notifikasi-pra-alih":
            continue
        try:
            ts = datetime.fromisoformat(str(d.get("ts")))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if ts >= sejak:
            return True
    return False

# ---------- state machine ----------
def get_state():
    return load(STATE, {"backups": {}})

def cmd_check():
    cfg = load(CFG, {})
    st = get_state()
    out = []
    for b in cfg.get("backups", []):
        bid, mirrors = b["id"], b["mirrors"]
        bs = st["backups"].setdefault(bid, {"status": "standby"})
        if bs["status"] == "active":
            out.append(f"{bid}: AKTIF (menggantikan {mirrors} yang off)")
            continue
        bermasalah, info = is_bermasalah(mirrors)
        if bermasalah and bs["status"] == "standby":
            # Hormati proses teguran formal jembatan (contingency-v3):
            # jangan kirim notifikasi ganda / mendahului tenggat 24 jam.
            wts = bridge_warning_ts(mirrors)
            now = datetime.now(timezone.utc)
            if wts and now < wts + timedelta(hours=24):
                tenggat = (wts + timedelta(hours=24)).astimezone(
                    timezone(timedelta(hours=7))).strftime("%d %b %H:%M WIB")
                out.append(f"{bid}: {mirrors} bermasalah ({info}) — "
                           f"teguran formal jembatan aktif, tenggat {tenggat}; "
                           f"menunggu, tidak notifikasi ganda")
                continue
            if wts and bridge_sudah_eskalasi(mirrors, wts):
                out.append(f"{bid}: {mirrors} bermasalah ({info}) — "
                           f"jembatan sudah mengirim notifikasi pra-alih; "
                           f"cadangan tetap siaga")
                continue
            # Tidak ada teguran aktif / jembatan belum eskalasi: cadangan
            # bertindak sebagai backstop sesuai perintah cron-nya.
            msg = (f"[saras-koordinator]\n\n**Notifikasi pra-alih (contingency-v3)**\n\n"
                   f"Bot `{mirrors}` terdeteksi bermasalah: {info}.\n"
                   f"Cadangan `{bid}` ({b['role']}) siap mengambil alih.\n\n"
                   f"Bos, setujui pengalihan? Balas **\"setuju alih {mirrors}\"** "
                   f"atau kirim perintah dashboard.\n\n[lanjut: pemilik]")
            url = post_issue_comment(3, msg)
            kirim_wall(f"Notifikasi pra-alih: {mirrors} bermasalah ({info}). "
                       f"Cadangan {bid} menunggu konfirmasi Bos.")
            bs.update(status="notified", notified_at=now_iso(), info=info)
            out.append(f"{bid}: NOTIFIKASI pra-alih dikirim ({url})")
        elif not bermasalah and bs["status"] == "notified":
            bs.update(status="standby")
            out.append(f"{bid}: {mirrors} pulih ({info}) -> kembali siaga")
        else:
            out.append(f"{bid}: siaga ({mirrors}: {info})")
    save(STATE, st)
    print("\n".join(out) if out else "tidak ada backup terdaftar")

def cmd_activate(bot_id):
    cfg = load(CFG, {})
    st = get_state()
    b = next((x for x in cfg.get("backups", []) if x["id"] == bot_id), None)
    if not b:
        sys.exit(f"backup '{bot_id}' tidak dikenal")
    bs = st["backups"].setdefault(bot_id, {})
    bs.update(status="active", activated_at=now_iso())
    save(STATE, st)
    msg = (f"[saras-koordinator]\n\n**Failover aktif**: `{b['mirrors']}` off, "
           f"cadangan `{bot_id}` ({b['role']}) mengambil alih sampai ada "
           f"keputusan lain dari Bos. Ditandai `[{bot_id}]` di setiap pesan.\n\n"
           f"[lanjut: pemilik]")
    post_issue_comment(3, msg)
    kirim_wall(f"Failover aktif: cadangan {bot_id} menggantikan {b['mirrors']}.")
    print(f"{bot_id} AKTIF")

def cmd_deactivate(bot_id):
    st = get_state()
    bs = st["backups"].setdefault(bot_id, {})
    bs.update(status="standby", deactivated_at=now_iso())
    save(STATE, st)
    print(f"{bot_id} kembali SIAGA")

def open_issues(numbers):
    out = []
    for n in numbers:
        r = gh("GET", f"/repos/{REPO}/issues/{n}/comments?per_page=100")
        comments = r.get("body", [])
        if isinstance(comments, dict):
            comments = []
        out.append((n, comments))
    return out

def cmd_reply_check():
    cfg = load(CFG, {})
    st = get_state()
    active = [b for b in cfg.get("backups", [])
              if st["backups"].get(b["id"], {}).get("status") == "active"]
    if not active:
        print("tidak ada cadangan aktif")
        return
    # issue open berlabel diskusi-bot / tugas-bot
    issues = set()
    for label in ("diskusi-bot", "tugas-bot"):
        r = gh("GET", f"/repos/{REPO}/issues?labels={label}&state=open&per_page=50")
        for it in r.get("body", []) or []:
            issues.add(it["number"])
    for b in active:
        mirrors, tag = b["mirrors"], b["tag"]
        key = f"{b['id']}:replied"
        replied = set(st.get(key, []))
        for n, comments in open_issues(sorted(issues)):
            for c in comments:
                cid = str(c.get("id"))
                body = c.get("body", "") or ""
                if cid in replied:
                    continue
                # giliran untuk bot asli yang off?
                if f"[lanjut: {mirrors}]" in body and f"[{b['id']}]" not in body:
                    # pastikan belum ada balasan sesudahnya
                    idx = comments.index(c)
                    later = " ".join(x.get("body", "") or "" for x in comments[idx+1:])
                    if f"[{mirrors}]" in later or f"[{b['id']}]" in later:
                        continue
                    try:
                        reply = llm_ask(b.get("provider", "gemini"),
                                        b["system_prompt"],
                                        f"Konteks diskusi:\n{body[-1500:]}\n\n"
                                        f"Balas sebagai {b['id']} ({b['role']}). "
                                        f"Format: build/alternative/concern + alasan, "
                                        f" Bahasa Indonesia, ringkas.")
                    except RuntimeError as e:
                        print(f"{b['id']}: {e}")
                        continue
                    msg = (f"{tag}\n_(cadangan — {mirrors} sedang off)_\n\n{reply}\n\n"
                           f"[lanjut: pemilik]")
                    url = post_issue_comment(n, msg)
                    replied.add(cid)
                    print(f"{b['id']}: membalas #{n} ({url})")
        st[key] = sorted(replied)[-200:]
    save(STATE, st)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("pakai: check | reply-check | run | activate --bot ID | deactivate --bot ID")
    cmd = sys.argv[1]
    if cmd == "check":
        cmd_check()
    elif cmd == "reply-check":
        cmd_reply_check()
    elif cmd == "run":
        cmd_check(); cmd_reply_check()
    elif cmd == "activate" and "--bot" in sys.argv:
        cmd_activate(sys.argv[sys.argv.index("--bot") + 1])
    elif cmd == "deactivate" and "--bot" in sys.argv:
        cmd_deactivate(sys.argv[sys.argv.index("--bot") + 1])
    else:
        sys.exit("perintah tidak dikenal")
