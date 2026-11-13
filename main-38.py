# -*- coding: utf-8 -*-
"""
بوصلة — أتمتة قناة يوتيوب كاملة في ملف واحد (فيديو طويل + شورت يومي).
الملفات المطلوبة في المستودع: main.py (هذا) + requirements.txt + .github/workflows/publish.yml + .github/workflows/short.yml
الإعدادات (المواعيد، الأصوات، الشعار…) في قسم config تحت — وهو أول قسم.
تشغيل: python main.py            (فيديو طويل وجدولته)
       python main.py --short    (شورت يومي وجدولته)
       python main.py --health   (فحص المفاتيح والخدمات)
"""
import linecache, os, sys, types

_SRC = {}

# ======================================================================
# القسم: config
# ======================================================================
_SRC['config'] = r'''# -*- coding: utf-8 -*-
"""كل الإعدادات في مكان واحد. غالباً ما تحتاج تعدّل شي هنا."""
import os

CHANNEL_NAME = "بوصلة"
BASE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("WORK_DIR", os.path.join(BASE, "work"))
STATE_FILE = os.path.join(BASE, "state", "state.json")
STATE_SHORT_FILE = os.path.join(BASE, "state", "shorts.json")
ASSETS = os.path.join(BASE, "assets")

# ---- الجدولة (توقيت الرياض UTC+3 بدون توقيت صيفي) ----
TZ_HOURS = 3
# weekday: الاثنين=0 ... الأحد=6  ->  (ساعة, دقيقة)
SLOTS = {
    6: (11, 30),   # الأحد قبل الظهر
    1: (13, 0),    # الثلاثاء ظهراً
    3: (19, 30),   # الخميس مساءً
    4: (16, 0),    # الجمعة عصراً
}
MIN_LEAD_MIN = 35                                   # أقل مدة بين الرفع وموعد النشر
LOOKAHEAD_HOURS = float(os.environ.get("LOOKAHEAD_HOURS", "30") or 30)

# تسلسل أنواع الفيديوهات (يتكرر): مشاريع / ماذا لو / طلبات التعليقات / ماذا لو
TOPIC_CYCLE = ["projects", "whatif", "requests", "whatif"]

# ---- الصوت ----
VOICES = ["fr-FR-RemyMultilingualNeural", "ko-KR-HyunsuMultilingualNeural", "ar-SA-HamedNeural", "ar-EG-ShakirNeural"]
VOICES_SHORT = ["ko-KR-HyunsuMultilingualNeural", "fr-FR-RemyMultilingualNeural", "ar-SA-HamedNeural", "ar-EG-ShakirNeural"]
TTS_RATE = "+6%"
TTS_PITCH = "+0Hz"
PAUSE = {"sentence": 0.62, "comma": 0.30, "colon": 0.42, "wrap": 0.22, "scene": 0.55}
LEAD_IN = 0.6      # ثواني صمت قبل أول كلمة
TAIL_OUT = 2.5     # ثواني بعد آخر كلمة (الموسيقى وحدها)
MAX_CHUNK_WORDS = 14

# ---- طول الفيديو ----
MIN_WORDS, MAX_WORDS = 820, 1250
MIN_SEC, MAX_SEC = 300, 600         # المطلوب: ٥ إلى ١٠ دقايق
HARD_MAX_SEC = 630

# ---- الفيديو ----
W, H, FPS = 1920, 1080, 30
CRF, PRESET = 22, "superfast"
SHOT_MIN, SHOT_MAX = 2.2, 4.6       # طول اللقطة (مونتاج سريع)
WATERMARK_OPACITY = 0.70            # شفافية الشعار أعلى اليسار
WATERMARK_W = 150
WATERMARK_MARGIN = 38

# ---- ألوان الهوية ----
NAVY = (7, 22, 34); GREEN = (14, 120, 84); GOLD = (222, 176, 84); WHITE = (244, 246, 244)

# ---- كلمات ممنوعة (سياسة / نزاعات) ----
BAN_WORDS = [
    "انتخابات", "حزب سياسي", "رئيس الوزراء", "حرب ", "حروب ", "غزو", "احتلال", "عقوبات",
    "قصف", "إرهاب", "ارهاب", "ترامب", "بايدن", "بوتين", "نتنياهو", "إسرائيل", "اسرائيل",
    "فلسطين", "غزة", "أوكرانيا", "اوكرانيا", "الحوثي", "حماس", "حزب الله", "داعش",
    "الإخوان", "المعارضة", "الانقلاب", "مظاهرات", "احتجاجات",
]

YT_CATEGORY = "27"      # Education
YT_LANG = "ar"

# ---- الشورت اليومي (٣٠ ثانية تقريباً) — بين ٨ و١٠ صباحاً بتوقيت الرياض، لكل يوم وقته ----
SHORT_SLOTS = {
    6: (8, 30),    # الأحد
    0: (9, 10),    # الاثنين
    1: (8, 15),    # الثلاثاء
    2: (9, 30),    # الأربعاء
    3: (8, 50),    # الخميس
    4: (9, 45),    # الجمعة
    5: (8, 5),     # السبت
}
SHORT_LOOKAHEAD_HOURS = float(os.environ.get("LOOKAHEAD_HOURS", "8") or 8)
TOPIC_CYCLE_SHORT = ["whatif", "projects", "fact", "whatif", "projects", "fact", "whatif"]
SHORT_W, SHORT_H = 1080, 1920
SHORT_MIN_WORDS, SHORT_MAX_WORDS = 55, 100
SHORT_MIN_SEC, SHORT_MAX_SEC = 20, 48
SHORT_SHOT_MIN, SHORT_SHOT_MAX = 1.5, 3.2

# ---- توليد الصور بالذكاء الاصطناعي (Pollinations بدون مفتاح؛ الحد المجاني ~ صورة كل ١٥ ثانية) ----
IMG_MIN_INTERVAL = 15.5
IMG_MAX_LONG = 34          # أقصى عدد صور مولدة في الفيديو الطويل
IMG_MAX_SHORT = 9
IMG_STYLE = ("cinematic digital illustration, highly detailed, dramatic lighting, rich teal and warm gold color palette, "
             "clean composition, no text, no letters, no watermark, no logo")
'''

# ======================================================================
# القسم: util
# ======================================================================
_SRC['util'] = r'''# -*- coding: utf-8 -*-
import json, os, subprocess, sys, time, traceback
import requests

UA = "BawsalaBot/1.0 (educational channel; contact via YouTube)"

def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)

def clean_secret(v):
    """ينظف المفاتيح من المسافات وعلامات التنصيص والأسطر الجديدة (أشهر سبب لفشل المفاتيح)."""
    if not v:
        return ""
    v = v.strip().strip("'\"").strip()
    for p in ("Authorization:", "Bearer ", "key="):
        if v.lower().startswith(p.lower()):
            v = v[len(p):].strip()
    return "".join(v.split())

def env(name, default=""):
    return clean_secret(os.environ.get(name, default))

class HTTPFail(Exception):
    def __init__(self, status, body, url=""):
        super().__init__(f"HTTP {status} {url[:90]} :: {str(body)[:300]}")
        self.status, self.body, self.url = status, body, url

def http(method, url, tries=4, timeout=40, ok=(200, 201, 204), backoff=2.0, **kw):
    """طلب HTTP مع إعادة محاولة ذكية: 429/5xx/انقطاع شبكة فقط."""
    headers = kw.pop("headers", {}) or {}
    headers.setdefault("User-Agent", UA)
    last = None
    for i in range(tries):
        try:
            r = requests.request(method, url, headers=headers, timeout=timeout, **kw)
            if r.status_code in ok:
                return r
            last = HTTPFail(r.status_code, r.text, url)
            if r.status_code in (429, 500, 502, 503, 504):
                ra = r.headers.get("Retry-After")
                wait = float(ra) if ra and ra.replace(".", "").isdigit() else backoff * (2 ** i)
                time.sleep(min(wait, 60))
                continue
            raise last
        except (requests.ConnectionError, requests.Timeout) as e:
            last = e
            time.sleep(backoff * (2 ** i))
    raise last if last else RuntimeError("http failed")

def run(cmd, timeout=3600, check=True):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError("cmd failed: " + " ".join(map(str, cmd))[:300] + "\n" + (p.stderr or "")[-1500:])
    return p

def probe_duration(path):
    p = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path])
    return float(p.stdout.strip())

def retry(fn, tries=3, delay=3.0, what="op"):
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa
            last = e
            log(f"retry {what} {i+1}/{tries}: {str(e)[:160]}")
            time.sleep(delay * (i + 1))
    raise last

def summary(md):
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write(md + "\n")
'''

# ======================================================================
# القسم: arabic_numbers
# ======================================================================
_SRC['arabic_numbers'] = r'''# -*- coding: utf-8 -*-
"""تحويل الأرقام إلى كلمات عربية (بدون أي مكتبة خارجية) عشان الصوت ينطقها صح."""
import re

ONES = ["صفر", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة", "عشرة",
        "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر",
        "ثمانية عشر", "تسعة عشر"]
TENS = {2: "عشرون", 3: "ثلاثون", 4: "أربعون", 5: "خمسون", 6: "ستون", 7: "سبعون", 8: "ثمانون", 9: "تسعون"}
HUND = {1: "مئة", 2: "مئتان", 3: "ثلاثمئة", 4: "أربعمئة", 5: "خمسمئة", 6: "ستمئة", 7: "سبعمئة",
        8: "ثمانمئة", 9: "تسعمئة"}
SCALES = [(10 ** 12, "تريليون", "تريليونان", "تريليونات"),
          (10 ** 9, "مليار", "ملياران", "مليارات"),
          (10 ** 6, "مليون", "مليونان", "ملايين"),
          (10 ** 3, "ألف", "ألفان", "آلاف")]

def _join(parts):
    parts = [p for p in parts if p]
    if not parts:
        return ""
    return parts[0] + "".join(" و" + p for p in parts[1:])

def _below_1000(n):
    parts = []
    h, r = divmod(n, 100)
    if h:
        parts.append(HUND[h])
    if 0 < r < 20:
        parts.append(ONES[r])
    elif r >= 20:
        t, o = divmod(r, 10)
        if o:
            parts.append(ONES[o])
        parts.append(TENS[t])
    return _join(parts)

def number_to_words(n):
    n = int(n)
    if n < 0:
        return "سالب " + number_to_words(-n)
    if n == 0:
        return ONES[0]
    if n >= 10 ** 15:
        return " ".join(ONES[int(d)] for d in str(n))
    parts = []
    for val, sing, dual, plur in SCALES:
        c, n = divmod(n, val)
        if not c:
            continue
        if c == 1:
            parts.append(sing)
        elif c == 2:
            parts.append(dual)
        elif 3 <= c <= 10:
            parts.append(_below_1000(c) + " " + plur)
        else:
            w = _below_1000(c)
            if c % 100 == 0 and c // 100 == 2:
                w = "مئتا"
            parts.append(w + " " + sing)
    if n:
        parts.append(_below_1000(n))
    return _join(parts)

_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

def digits_to_words(text):
    t = text.translate(_AR_DIGITS)
    t = t.replace("٫", ".").replace("٬", ",").replace("٪", "%")
    t = re.sub(r"(?<=\d)[,،](?=\d{3}(?!\d))", "", t)               # 1,200 -> 1200
    t = re.sub(r"(\d+)\s*[-–—]\s*(\d+)", r"\1 إلى \2", t)           # 5-10 -> 5 إلى 10

    def dec(m):
        ip, fp = m.group(1), m.group(2)
        zeros = len(fp) - len(fp.lstrip("0"))
        fw = " ".join(["صفر"] * zeros) + (" " if zeros and fp.strip("0") else "")
        if fp.strip("0"):
            fw += number_to_words(int(fp))
        elif not zeros:
            fw = "صفر"
        return number_to_words(int(ip)) + " فاصل " + fw.strip()

    t = re.sub(r"(\d+)\.(\d+)", dec, t)
    t = re.sub(r"(\d+(?:\s*فاصل[^%\d]*?)?)\s*%", lambda m: m.group(1) + " بالمئة", t)
    t = re.sub(r"\d+", lambda m: number_to_words(int(m.group(0))), t)
    t = t.replace("%", " بالمئة")
    return re.sub(r"[ \t]+", " ", t)
'''

# ======================================================================
# القسم: gemini
# ======================================================================
_SRC['gemini'] = r'''# -*- coding: utf-8 -*-
"""Gemini: يكتشف الموديلات المتاحة بنفسه (ما يحتاج اسم موديل)، ويعيد المحاولة، ويجرب موديل ثاني عند 404/503/429."""
import json, os, re, time
import requests
from util import log, clean_secret, UA

API = "https://generativelanguage.googleapis.com/v1beta"
_models_cache = None

def _keys():
    raw = os.environ.get("GEMINI_API_KEY", "") + "," + os.environ.get("GEMINI_API_KEY_2", "")
    ks = [clean_secret(k) for k in re.split(r"[,\s]+", raw) if clean_secret(k)]
    if not ks:
        raise RuntimeError("GEMINI_API_KEY غير موجود في الـSecrets")
    return ks

def _version(name):
    m = re.search(r"gemini-(\d+(?:\.\d+)?)", name)
    return float(m.group(1)) if m else 0.0

def list_models(key):
    global _models_cache
    if _models_cache is not None:
        return _models_cache
    out = []
    try:
        r = requests.get(f"{API}/models?pageSize=200&key={key}", timeout=30, headers={"User-Agent": UA})
        if r.status_code == 200:
            for m in r.json().get("models", []):
                n = m.get("name", "").replace("models/", "")
                if "generateContent" not in m.get("supportedGenerationMethods", []):
                    continue
                if not n.startswith("gemini"):
                    continue
                if any(x in n for x in ("image", "tts", "live", "audio", "embedding", "robotics", "computer", "learnlm", "-exp", "preview-0")):
                    continue
                out.append(n)
    except Exception as e:  # noqa
        log("gemini list_models failed:", str(e)[:120])
    def rank(n):
        tier = 0 if ("flash" in n and "lite" not in n) else 1 if "flash-lite" in n or "lite" in n else 2
        return (tier, -_version(n), n)
    out = sorted(set(out), key=rank)
    # احتياط لو فشل جلب القائمة
    fallback = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-flash-lite-latest"]
    for f in fallback:
        if f not in out:
            out.append(f)
    _models_cache = out
    log("gemini models order:", out[:6])
    return out

def _extract_json(text):
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.S).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    a, b = t.find("{"), t.rfind("}")
    if a != -1 and b > a:
        return json.loads(t[a:b + 1])
    raise ValueError("no JSON found")

def _call(model, key, prompt, system, temperature, max_tokens, mode):
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if mode >= 1:
        body["generationConfig"]["responseMimeType"] = "application/json"
    if mode == 0 and "2.5" in model:
        body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
    r = requests.post(f"{API}/models/{model}:generateContent?key={key}", json=body, timeout=180,
                      headers={"User-Agent": UA, "Content-Type": "application/json"})
    return r

def generate_json(prompt, validate=None, system=None, temperature=0.85, max_tokens=14000, rounds=6):
    """يرجع dict صالح. validate(obj) ترجع None لو تمام أو نص الخطأ ليرسله للموديل في المحاولة التالية."""
    keys = _keys()
    models = list_models(keys[0])
    extra = ""
    last_err = "unknown"
    attempt = 0
    dead = set()
    for rnd in range(rounds):
        for model in models[:6]:
            if model in dead:
                continue
            for ki, key in enumerate(keys):
                attempt += 1
                mode = 0
                for _ in range(3):   # أنماط: مع thinking=0 + json، ثم json فقط، ثم نص عادي
                    try:
                        r = _call(model, key, prompt + extra, system, temperature, max_tokens, mode)
                    except requests.RequestException as e:
                        last_err = f"net {e}"; time.sleep(3); break
                    if r.status_code == 200:
                        try:
                            j = r.json()
                            cand = (j.get("candidates") or [{}])[0]
                            parts = cand.get("content", {}).get("parts", [])
                            text = "".join(p.get("text", "") for p in parts)
                            if not text.strip():
                                last_err = f"empty ({cand.get('finishReason')}, {j.get('promptFeedback')})"
                                break
                            obj = _extract_json(text)
                            err = validate(obj) if validate else None
                            if err is None:
                                return obj
                            last_err = "validation: " + err
                            extra = "\n\nتنبيه: المحاولة السابقة رُفضت للسبب التالي، صححه بدقة وأعد JSON كاملاً:\n" + err
                            log("gemini validation failed:", err[:200])
                            break
                        except Exception as e:  # noqa
                            last_err = f"parse {e}"
                            extra = "\n\nتنبيه: أعد الناتج كـJSON صالح فقط بدون أي نص خارجه."
                            break
                    body = r.text[:400]
                    if r.status_code == 400 and mode < 2 and ("thinking" in body.lower() or "mime" in body.lower() or "response" in body.lower()):
                        mode += 1; continue
                    if r.status_code == 404:
                        dead.add(model); last_err = f"404 {model}"; break
                    if r.status_code in (429, 500, 503, 504):
                        last_err = f"{r.status_code} {model}"
                        time.sleep(min(5 * (rnd + 1), 30)); break
                    if r.status_code in (400, 401, 403):
                        last_err = f"{r.status_code} {body}"
                        if r.status_code in (401, 403) or "API key" in body:
                            continue_next_key = True
                        break
                    last_err = f"{r.status_code} {body}"; break
        time.sleep(4 * (rnd + 1))
    raise RuntimeError("Gemini فشل بعد كل المحاولات: " + last_err)
'''

# ======================================================================
# القسم: stock
# ======================================================================
_SRC['stock'] = r'''# -*- coding: utf-8 -*-
"""مصادر اللقطات (مجانية): تسلسل ذكي يتخطى أي مصدر مفتاحه خربان بدل ما يوقف الفيديو.

فيديو : Pexels -> Pixabay -> NASA (مواضيع الفضاء) -> Wikimedia Commons
صور   : Pexels -> Pixabay -> Wikimedia Commons -> NASA -> Openverse
(NASA / Wikimedia / Openverse بدون مفتاح إطلاقاً)
"""
import os, re, hashlib, time
import requests
from config import WORK
from util import log, env, http, HTTPFail, UA

SPACE_WORDS = ("space", "planet", "earth from", "moon", "mars", "satellite", "rocket", "galaxy", "orbit",
               "astronaut", "nasa", "solar", "sun ", "star", "telescope", "cosmos", "iss ")
GOOD_LICENSES = ("public domain", "pd", "cc0", "cc by")      # بدون SA/NC/ND
BAD_LICENSE_PARTS = ("sa", "nc", "nd")

class Asset:
    def __init__(self, kind, url, source, uid, w=0, h=0, dur=0.0, credit=""):
        self.kind, self.url, self.source, self.uid = kind, url, source, f"{source}:{uid}"
        self.w, self.h, self.dur, self.credit = w, h, dur, credit
        self.path = None
    def __repr__(self):
        return f"<{self.kind} {self.uid} {self.w}x{self.h} {self.dur:.0f}s>"

class Source:
    name = "?"
    needs_key = False
    def __init__(self):
        self.disabled = False
        self.reason = ""
        self.fails = 0
        self.ok_calls = 0
        self.last_error = ""
        self.portrait = False
    def disable(self, why):
        if not self.disabled:
            log(f"[stock] تعطيل {self.name}: {why}")
        self.disabled, self.reason = True, why
    def guard(self, fn, *a):
        if self.disabled:
            return []
        try:
            res = fn(*a)
            self.ok_calls += 1
            self.fails = 0
            return res
        except HTTPFail as e:
            self.last_error = f"HTTP {e.status}"
            if e.status in (401, 403):
                self.disable(f"مفتاح مرفوض ({e.status}) — تأكد إنه بدون مسافات/علامات تنصيص في Secrets")
            elif e.status == 429:
                self.fails += 1
                if self.fails >= 2:
                    self.disable("تجاوز الحد المسموح (429)")
            else:
                self.fails += 1
                if self.fails >= 4:
                    self.disable(f"أخطاء متكررة {e.status}")
            return []
        except Exception as e:  # noqa
            self.last_error = str(e)[:100]
            self.fails += 1
            if self.fails >= 4:
                self.disable(f"أخطاء متكررة: {str(e)[:80]}")
            return []
    def videos(self, q): return []
    def images(self, q): return []
    def check(self):
        """للفحص الصحي: يرجع (ok, رسالة)."""
        try:
            n = len(self.videos("city skyline")) + len(self.images("city skyline"))
            return (n > 0, f"{n} نتيجة" + ("" if n else f" ({self.last_error or self.reason or 'بدون سبب ظاهر'})"))
        except Exception as e:  # noqa
            return (False, str(e)[:160])

class Pexels(Source):
    name = "pexels"; needs_key = True
    def __init__(self):
        super().__init__()
        self.key = env("PEXELS_API_KEY")
        if not self.key: self.disable("لا يوجد مفتاح")
    def _h(self): return {"Authorization": self.key}
    def videos(self, q):
        return self.guard(self._v, q)
    def _v(self, q):
        r = http("GET", "https://api.pexels.com/videos/search", params={"query": q, "per_page": 15, "orientation": "portrait" if self.portrait else "landscape", "size": "medium"}, headers=self._h(), tries=2)
        out = []
        for v in r.json().get("videos", []):
            files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("width")]
            if not files: continue
            files.sort(key=lambda f: (abs(min(f["width"], 1920) - 1920), -f["width"]))
            good = [f for f in files if 1280 <= f["width"] <= 2560] or files
            f = good[0]
            out.append(Asset("video", f["link"], "pexels", v["id"], f["width"], f["height"], float(v.get("duration") or 0)))
        return out
    def images(self, q):
        return self.guard(self._i, q)
    def _i(self, q):
        r = http("GET", "https://api.pexels.com/v1/search", params={"query": q, "per_page": 12, "orientation": "portrait" if self.portrait else "landscape"}, headers=self._h(), tries=2)
        return [Asset("image", p["src"].get("large2x") or p["src"]["large"], "pexels", p["id"], p.get("width", 0), p.get("height", 0)) for p in r.json().get("photos", [])]

class Pixabay(Source):
    name = "pixabay"; needs_key = True
    def __init__(self):
        super().__init__()
        self.key = env("PIXABAY_API_KEY")
        if not self.key: self.disable("لا يوجد مفتاح")
    def videos(self, q): return self.guard(self._v, q)
    def _v(self, q):
        r = http("GET", "https://pixabay.com/api/videos/", params={"key": self.key, "q": q[:100], "per_page": 15, "safesearch": "true"}, tries=2)
        out = []
        for h in r.json().get("hits", []):
            vs = h.get("videos", {})
            for k in ("large", "medium", "small"):
                if vs.get(k, {}).get("url") and vs[k].get("width", 0) >= 1280:
                    out.append(Asset("video", vs[k]["url"], "pixabay", h["id"], vs[k]["width"], vs[k]["height"], float(h.get("duration") or 0)))
                    break
        return out
    def images(self, q): return self.guard(self._i, q)
    def _i(self, q):
        r = http("GET", "https://pixabay.com/api/", params={"key": self.key, "q": q[:100], "per_page": 12, "image_type": "photo", "orientation": "vertical" if self.portrait else "horizontal", "min_width": 720 if self.portrait else 1280, "safesearch": "true"}, tries=2)
        return [Asset("image", h.get("largeImageURL") or h["webformatURL"], "pixabay", h["id"], h.get("imageWidth", 0), h.get("imageHeight", 0)) for h in r.json().get("hits", [])]

class Nasa(Source):
    name = "nasa"
    @staticmethod
    def relevant(q): return any(w in q.lower() + " " for w in SPACE_WORDS)
    def videos(self, q):
        return self.guard(self._v, q) if self.relevant(q) else []
    def images(self, q):
        return self.guard(self._i, q) if self.relevant(q) else []
    def _search(self, q, media):
        r = http("GET", "https://images-api.nasa.gov/search", params={"q": q, "media_type": media, "page_size": 12}, tries=2)
        return r.json().get("collection", {}).get("items", [])
    def _i(self, q):
        out = []
        for it in self._search(q, "image"):
            d = (it.get("data") or [{}])[0]; links = it.get("links") or []
            if links and d.get("nasa_id"):
                url = links[0]["href"].replace("~thumb", "~large").replace("~small", "~large")
                out.append(Asset("image", url, "nasa", d["nasa_id"], 1600, 900))
        return out
    def _v(self, q):
        out = []
        for it in self._search(q, "video")[:6]:
            d = (it.get("data") or [{}])[0]
            href = it.get("href")
            if not href or not d.get("nasa_id"): continue
            try:
                files = http("GET", href, tries=2).json()
            except Exception:
                continue
            mp4 = [f for f in files if isinstance(f, str) and f.endswith(".mp4") and "~orig" not in f]
            pref = [f for f in mp4 if "medium" in f or "large" in f] or mp4
            if pref:
                out.append(Asset("video", pref[0].replace(" ", "%20"), "nasa", d["nasa_id"], 1280, 720, 0.0))
        return out

class Wikimedia(Source):
    name = "wikimedia"
    API = "https://commons.wikimedia.org/w/api.php"
    def _q(self, q, ftype):
        params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:{ftype} {q}",
                  "gsrnamespace": 6, "gsrlimit": 15, "prop": "imageinfo",
                  "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1920}
        r = http("GET", self.API, params=params, tries=2)
        return (r.json().get("query") or {}).get("pages", {}).values()
    @staticmethod
    def _license_ok(meta):
        lic = (meta.get("LicenseShortName", {}).get("value", "") or "").lower()
        if not lic: return False, ""
        if "public domain" in lic or lic.startswith("pd") or "cc0" in lic:
            return True, ""
        if lic.startswith("cc by") and not any(f"-{p}" in lic or f" {p}" in lic for p in BAD_LICENSE_PARTS):
            artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "") or "").strip()
            return True, f"{artist or 'Wikimedia Commons'} ({meta.get('LicenseShortName', {}).get('value', '')})"
        return False, ""
    def images(self, q): return self.guard(self._i, q)
    def _i(self, q):
        out = []
        for p in self._q(q, "bitmap"):
            ii = (p.get("imageinfo") or [{}])[0]
            ok, credit = self._license_ok(ii.get("extmetadata", {}))
            if ok and ii.get("width", 0) >= 1280 and ii.get("mime", "").startswith("image/") and "svg" not in ii.get("mime", ""):
                out.append(Asset("image", ii.get("thumburl") or ii["url"], "wikimedia", p["pageid"], ii["width"], ii["height"], credit=credit))
        return out
    def videos(self, q): return self.guard(self._v, q)
    def _v(self, q):
        out = []
        for p in self._q(q, "video"):
            ii = (p.get("imageinfo") or [{}])[0]
            ok, credit = self._license_ok(ii.get("extmetadata", {}))
            if ok and ii.get("width", 0) >= 640:
                out.append(Asset("video", ii["url"], "wikimedia", p["pageid"], ii["width"], ii["height"], 0.0, credit))
        return out

class Openverse(Source):
    name = "openverse"
    def images(self, q): return self.guard(self._i, q)
    def _i(self, q):
        r = http("GET", "https://api.openverse.org/v1/images/", params={"q": q, "license": "cc0,pdm,by", "page_size": 15, "aspect_ratio": "wide", "size": "large"}, tries=2)
        out = []
        for it in r.json().get("results", []):
            if it.get("url"):
                cr = f"{it.get('creator') or 'Unknown'} ({(it.get('license') or '').upper()})" if it.get("license") == "by" else ""
                out.append(Asset("image", it["url"], "openverse", it["id"], it.get("width") or 0, it.get("height") or 0, credit=cr))
        return out

class Stock:
    def __init__(self):
        os.makedirs(os.path.join(WORK, "stock"), exist_ok=True)
        self.px, self.pb, self.na, self.wk, self.ov = Pexels(), Pixabay(), Nasa(), Wikimedia(), Openverse()
        self.video_chain = [self.px, self.pb, self.na, self.wk]
        self.image_chain = [self.px, self.pb, self.wk, self.na, self.ov]
        self.used = set()
        self.credits = []
        self.cache = {}

    def sources(self):
        return [self.px, self.pb, self.na, self.wk, self.ov]

    def _variants(self, q):
        q = re.sub(r"[^\w\s\-]", " ", q).strip()
        words = q.split()
        yield q
        if len(words) > 2: yield " ".join(words[:2])
        if len(words) > 1: yield words[-1]

    def find(self, query, want_video=True, fallback_queries=(), portrait=False):
        """يرجع قائمة Assets مرتبة (فيديو أولاً ثم صور)."""
        for src in self.sources(): src.portrait = portrait
        key = (query, want_video, portrait)
        if key in self.cache: return self.cache[key]
        found = []
        qs = list(self._variants(query)) + [q for fq in fallback_queries for q in self._variants(fq)]
        if want_video:
            for q in qs:
                for src in self.video_chain:
                    found += [a for a in src.videos(q) if a.uid not in self.used]
                if len(found) >= 3: break
        if len(found) < 2:
            for q in qs:
                for src in self.image_chain:
                    found += [a for a in src.images(q) if a.uid not in self.used]
                if len(found) >= 3: break
        self.cache[key] = found
        return found

    def download(self, a):
        if a.path and os.path.exists(a.path): return a.path
        ext = os.path.splitext(a.url.split("?")[0])[1].lower()
        if ext not in (".mp4", ".webm", ".ogv", ".mov", ".jpg", ".jpeg", ".png", ".webp"):
            ext = ".mp4" if a.kind == "video" else ".jpg"
        p = os.path.join(WORK, "stock", hashlib.md5(a.uid.encode()).hexdigest()[:14] + ext)
        if not (os.path.exists(p) and os.path.getsize(p) > 5000):
            hdr = {"User-Agent": UA}
            with requests.get(a.url, stream=True, timeout=60, headers=hdr) as r:
                if r.status_code != 200:
                    raise HTTPFail(r.status_code, "download", a.url)
                size = 0
                with open(p, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        size += len(chunk)
                        if size > 150 * 1024 * 1024:
                            raise RuntimeError("file too big")
                        f.write(chunk)
        if os.path.getsize(p) < 5000:
            raise RuntimeError("download too small")
        a.path = p
        self.used.add(a.uid)
        if a.credit and a.credit not in self.credits:
            self.credits.append(a.credit)
        return p

    def report(self):
        lines = []
        for s in self.sources():
            lines.append(f"{s.name}: {'معطل — ' + s.reason if s.disabled else 'يعمل'} (طلبات ناجحة {s.ok_calls})")
        return lines
'''

# ======================================================================
# القسم: imagegen
# ======================================================================
_SRC['imagegen'] = r'''# -*- coding: utf-8 -*-
"""توليد صور بالذكاء الاصطناعي بدون مفتاح (Pollinations). لو فشل: يرجع None والمونتاج يستخدم بديلاً."""
import hashlib, io, os, time, threading
from urllib.parse import quote
import requests
from PIL import Image, ImageStat
from config import WORK, IMG_MIN_INTERVAL, IMG_STYLE
from util import log, UA

ENDPOINT = os.environ.get("IMG_ENDPOINT", "https://image.pollinations.ai/prompt/")

class ImageGen:
    def __init__(self, max_images=30):
        self.dir = os.path.join(WORK, "img"); os.makedirs(self.dir, exist_ok=True)
        self.max_images = max_images
        self.count = 0; self.fails = 0; self.disabled = False; self.reason = ""
        self._last = 0.0; self._lock = threading.Lock()

    def _wait_turn(self):
        with self._lock:
            gap = IMG_MIN_INTERVAL - (time.time() - self._last)
            if gap > 0: time.sleep(gap)
            self._last = time.time()

    @staticmethod
    def _valid(data):
        try:
            im = Image.open(io.BytesIO(data)); im.load()
            if im.width < 400 or im.height < 400: return None
            st = ImageStat.Stat(im.convert("L"))
            if st.stddev[0] < 6: return None           # صورة فاضية/لون واحد
            return im.convert("RGB")
        except Exception:
            return None

    def generate(self, prompt, w, h, seed=0, tries=3):
        """يرجع مسار JPG أو None. w,h حجم الصورة المطلوبة (نطلب أكبر قليلاً ونقص الحواف لإزالة أي علامة مائية)."""
        if self.disabled or self.count >= self.max_images or not prompt:
            return None
        full = f"{prompt.strip()[:420]}, {IMG_STYLE}"
        key = hashlib.md5(f"{full}|{w}x{h}|{seed}".encode()).hexdigest()[:16]
        path = os.path.join(self.dir, key + ".jpg")
        if os.path.exists(path) and os.path.getsize(path) > 10000:
            return path
        rw, rh = (1280, 720) if w >= h else (720, 1280)
        for i in range(tries):
            self._wait_turn()
            try:
                url = ENDPOINT + quote(full) + f"?width={rw}&height={rh}&seed={seed + i}&model=flux&nologo=true&private=true&safe=true"
                r = requests.get(url, timeout=150, headers={"User-Agent": UA})
                if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                    im = self._valid(r.content)
                    if im is not None:
                        # قص ٦٪ من الحواف (يُخفي أي علامة مائية في الزوايا)
                        cx, cy = int(im.width * 0.03), int(im.height * 0.045)
                        im = im.crop((cx, cy, im.width - cx, im.height - cy))
                        im.save(path, "JPEG", quality=92)
                        self.count += 1; self.fails = 0
                        return path
                    log("[img] صورة غير صالحة، إعادة المحاولة")
                else:
                    log(f"[img] HTTP {r.status_code} — محاولة {i+1}/{tries}")
                    if r.status_code in (402, 403): self.fails += 2
            except Exception as e:  # noqa
                log("[img] خطأ:", str(e)[:100])
            time.sleep(3 * (i + 1))
        self.fails += 1
        if self.fails >= 4:
            self.disabled = True; self.reason = "فشل متكرر"
            log("[img] تعطيل توليد الصور في هذا التشغيل (سيُستخدم الستوك والإنفوجرافيك)")
        return None
'''

# ======================================================================
# القسم: arfont
# ======================================================================
_SRC['arfont'] = r'''# -*- coding: utf-8 -*-
"""رسم النص العربي بشكل صحيح (تشكيل الحروف + اتجاه RTL) مع بدائل لو raqm غير متوفر."""
import os, glob
from PIL import Image, ImageDraw, ImageFont, features
from config import BASE

HAS_RAQM = features.check("raqm")
_CANDS = [
    os.path.join(BASE, "assets", "fonts", "*.ttf"),
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabicUI-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansArabic-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
_font_path = None

def font_path():
    global _font_path
    if _font_path: return _font_path
    for pat in _CANDS:
        for p in sorted(glob.glob(pat)):
            if os.path.exists(p):
                _font_path = p; return p
    for p in glob.glob("/usr/share/fonts/**/*.ttf", recursive=True):
        if "arab" in p.lower():
            _font_path = p; return p
    raise RuntimeError("لا يوجد خط عربي — ثبّت fonts-noto-core أو ضع ملف .ttf في assets/fonts")

def font(size):
    return ImageFont.truetype(font_path(), size)

def _prep(text):
    if HAS_RAQM:
        return text, {"direction": "rtl", "language": "ar"}
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text)), {}
    except Exception:
        return text, {}

def text_width(text, f):
    t, kw = _prep(text)
    return f.getlength(t, **kw)

def draw_text(d, xy, text, f, fill, anchor="mm", stroke=0, stroke_fill=(0, 0, 0)):
    t, kw = _prep(text)
    d.text(xy, t, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill, **kw)

def wrap(text, f, max_w, max_lines=3):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    if len(lines) > max_lines:
        keep = lines[:max_lines - 1] + [" ".join(lines[max_lines - 1:])]
        lines = keep
    return lines
'''

# ======================================================================
# القسم: brand
# ======================================================================
_SRC['brand'] = r'''# -*- coding: utf-8 -*-
"""هوية القناة بالكود: شعار البوصلة (يُرسم وقت التشغيل، بدون ملفات صور)."""
import math
from PIL import Image, ImageDraw
from config import GOLD

GOLD_D = (176, 132, 52); GREEN = (14, 120, 84); NAVY1 = (7, 22, 34)

def compass(d, cx, cy, R):
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=GOLD, width=int(R * 0.07))
    r2 = R * 0.84
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=GOLD_D, width=max(2, int(R * 0.015)))
    for i in range(48):
        a = math.radians(i * 7.5); major = i % 12 == 0; mid = i % 6 == 0
        r_out = R * 0.80; r_in = R * (0.64 if major else 0.70 if mid else 0.75)
        w = max(2, int(R * (0.04 if major else 0.022 if mid else 0.012)))
        d.line([(cx + r_in * math.sin(a), cy - r_in * math.cos(a)), (cx + r_out * math.sin(a), cy - r_out * math.cos(a))],
               fill=GOLD if (major or mid) else GOLD_D, width=w)
    for s in (1, -1):
        d.polygon([(cx + s * R * 0.50, cy), (cx + s * R * 0.18, cy - R * 0.09), (cx + s * R * 0.18, cy + R * 0.09)], fill=GOLD_D)
    w = R * 0.17; N = (cx, cy - R * 0.56); S = (cx, cy + R * 0.56)
    d.polygon([N, (cx - w, cy), (cx, cy)], fill=(22, 150, 106))
    d.polygon([N, (cx + w, cy), (cx, cy)], fill=GREEN)
    d.polygon([S, (cx - w, cy), (cx, cy)], fill=(214, 218, 214))
    d.polygon([S, (cx + w, cy), (cx, cy)], fill=(168, 174, 170))
    tip = R * 0.20
    d.polygon([N, (cx - w * 0.30, cy - R * 0.56 + tip), (cx + w * 0.30, cy - R * 0.56 + tip)], fill=GOLD)
    hr = R * 0.075
    d.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=NAVY1, outline=GOLD, width=max(2, int(R * 0.025)))

def logo_rgba(size=400):
    """شعار البوصلة على قرص كحلي شفاف الأطراف."""
    S = 3; N = size * S
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.ellipse([6 * S, 6 * S, N - 6 * S, N - 6 * S], fill=(7, 22, 34, 215))
    compass(d, N // 2, N // 2, int(N * 0.40))
    return img.resize((size, size), Image.LANCZOS)


def wordmark_rgba(height=110):
    """شعار احترافي للعلامة المائية: أيقونة بوصلة بخطوط ذهبية + كلمة «بوصلة» بيضاء مع ظل ناعم (بدون قرص خلفي)."""
    import arfont
    from PIL import ImageFilter
    S = 4
    H = height * S
    f = arfont.font(int(H * 0.60))
    tw = int(arfont.text_width("بوصلة", f))
    pad = int(H * 0.18)
    icon = H
    Wd = icon + int(H * 0.12) + tw + pad * 2
    img = Image.new("RGBA", (Wd, H + pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy, R = pad + icon // 2 - pad // 2, (H + pad) // 2, int(H * 0.42)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=GOLD, width=max(3, int(R * 0.10)))
    for a in range(0, 360, 90):
        r1, r2 = R * 0.80, R * 0.62
        rad = math.radians(a)
        d.line([(cx + r1 * math.sin(rad), cy - r1 * math.cos(rad)), (cx + r2 * math.sin(rad), cy - r2 * math.cos(rad))], fill=GOLD, width=max(2, int(R * 0.08)))
    w = R * 0.20
    d.polygon([(cx, cy - R * 0.62), (cx - w, cy), (cx + w, cy)], fill=(255, 255, 255, 255))
    d.polygon([(cx, cy + R * 0.62), (cx - w, cy), (cx + w, cy)], fill=GOLD)
    d.ellipse([cx - R * 0.09, cy - R * 0.09, cx + R * 0.09, cy + R * 0.09], fill=(7, 22, 34, 255))
    tx = icon + int(H * 0.12) + tw // 2 + pad // 2
    arfont.draw_text(d, (tx, cy - int(H * 0.02)), "بوصلة", f, (255, 255, 255, 255), "mm")
    # ظل ناعم
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    a = img.split()[3].filter(ImageFilter.GaussianBlur(int(H * 0.05)))
    sh.putalpha(a.point(lambda v: int(v * 0.75)))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (int(H * 0.025), int(H * 0.035)))
    out.alpha_composite(img)
    return out.resize((Wd // S, (H + pad) // S), Image.LANCZOS)
'''

# ======================================================================
# القسم: anim
# ======================================================================
_SRC['anim'] = r'''# -*- coding: utf-8 -*-
"""إنفوجرافيك متحرك بالكود: أرقام تعدّ، أعمدة تنمو، خط زمني، مقارنة، قائمة، كلمات متحركة، وبطاقة ختام.
كل لقطة تُرسم فريماً فريماً بـPillow وتُرسل لـffmpeg (بدون أي مفتاح أو خدمة)."""
import functools, math, re, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from config import FPS, CRF, PRESET, NAVY, GOLD, WHITE, GREEN
import arfont, brand

TYPES = ("number", "bars", "timeline", "compare", "list", "kinetic")
RED = (225, 48, 48)

# ---------- أدوات ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else (1.0 if t >= b else 0.0)
def ease_out(x): return 1 - (1 - x) ** 3
def ease_inout(x): return 3 * x * x - 2 * x ** 3
def ease_back(x):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

@functools.lru_cache(maxsize=512)
def _font(size): return arfont.font(max(8, int(size)))

def _num(v):
    try:
        s = re.sub(r"[^\d.\-]", "", str(v).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩٫", "0123456789.")))
        return float(s) if s not in ("", ".", "-") else None
    except Exception:
        return None

def _fmt(x, dec):
    s = f"{x:,.{dec}f}" if dec else f"{int(round(x)):,}"
    return s

@functools.lru_cache(maxsize=8)
def _bg(W, H, hue):
    """خلفية: تدرج كحلي + شبكة خفيفة + توهج."""
    c1, c2 = NAVY, [(13, 52, 66), (22, 40, 70), (14, 66, 58)][hue % 3]
    im = Image.new("RGB", (1, H))
    px = im.load()
    for y in range(H):
        t = y / (H - 1)
        px[0, y] = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
    im = im.resize((W, H)).convert("RGBA")
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(grid)
    step = int(min(W, H) / 9)
    for x in range(0, W, step): d.line([(x, 0), (x, H)], fill=(255, 255, 255, 12), width=2)
    for y in range(0, H, step): d.line([(0, y), (W, y)], fill=(255, 255, 255, 12), width=2)
    im.alpha_composite(grid)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    g.ellipse([W * 0.15, H * 0.2, W * 0.85, H * 0.8], fill=GREEN + (95,))
    glow = glow.filter(ImageFilter.GaussianBlur(min(W, H) * 0.16))
    im.alpha_composite(glow)
    return im

def _text(d, xy, s, size, fill, a=1.0, anchor="mm", stroke=0):
    if a <= 0.01 or not s: return
    arfont.draw_text(d, xy, s, _font(size), tuple(fill[:3]) + (int(255 * clamp(a)),), anchor, stroke=stroke, stroke_fill=(4, 10, 16, int(255 * clamp(a))))

def _wrap(s, size, maxw, lines=3):
    return arfont.wrap(s, _font(size), maxw, lines)

# ---------- التحقق من بيانات الإنفوجرافيك ----------
def validate_info(info):
    """يرجع None لو سليم، أو نص الخطأ."""
    try:
        if not isinstance(info, dict): return "info ليس كائناً"
        t = info.get("type")
        if t not in TYPES: return f"type غير معروف: {t}"
        if t == "number":
            if not str(info.get("value", "")).strip(): return "number بدون value"
            if not str(info.get("label", "")).strip(): return "number بدون label"
        elif t == "bars":
            it = info.get("items")
            if not isinstance(it, list) or not (2 <= len(it) <= 5): return "bars يحتاج ٢-٥ عناصر"
            for x in it:
                if not str(x.get("label", "")).strip() or _num(x.get("value")) is None: return "عنصر في bars بدون label/value رقمي"
        elif t == "timeline":
            ev = info.get("events")
            if not isinstance(ev, list) or not (3 <= len(ev) <= 5): return "timeline يحتاج ٣-٥ أحداث"
            for x in ev:
                if not str(x.get("year", "")).strip() or not str(x.get("text", "")).strip(): return "حدث بدون year/text"
        elif t == "compare":
            for k in ("left", "right"):
                side = info.get(k)
                if not isinstance(side, dict) or not str(side.get("title", "")).strip(): return f"compare.{k} بدون title"
                if not isinstance(side.get("items"), list) or not (2 <= len(side["items"]) <= 4): return f"compare.{k}.items يحتاج ٢-٤"
        elif t == "list":
            it = info.get("items")
            if not isinstance(it, list) or not (3 <= len(it) <= 4) or not all(str(x).strip() for x in it): return "list يحتاج ٣-٤ عناصر"
        elif t == "kinetic":
            w = info.get("words")
            if not isinstance(w, list) or not (1 <= len(w) <= 4) or not all(str(x).strip() for x in w): return "kinetic يحتاج ١-٤ كلمات"
        return None
    except Exception as e:  # noqa
        return f"info غير صالح: {e}"

def fallback_info(text):
    words = [w for w in (text or "").split() if w][:3] or ["بوصلة"]
    return {"type": "kinetic", "words": words}

# ---------- الرسم ----------
def draw_number(d, W, H, u, t, info):
    cx, cy = W / 2, H * 0.54
    R = 300 * u
    prog = ease_out(seg(t, 0.05, 0.7))
    tgt = _num(info["value"]); dec = len(str(info["value"]).split(".")[-1]) if "." in str(info["value"]) else 0
    shown = _fmt((tgt or 0) * prog, dec) if tgt is not None else str(info["value"])
    # حلقة (مرسومة بدقة مضاعفة)
    S = 2; box = int(R * 2 + 80 * u)
    ring = Image.new("RGBA", (box * S, box * S), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
    b = [40 * u * S, 40 * u * S, (box - 40 * u) * S, (box - 40 * u) * S]
    rd.ellipse(b, outline=GOLD + (45,), width=int(26 * u * S))
    if prog > 0.01:
        rd.arc(b, -90, -90 + 360 * prog, fill=GOLD + (255,), width=int(26 * u * S))
    ring = ring.resize((box, box), Image.LANCZOS)
    d._img.alpha_composite(ring, (int(cx - box / 2), int(cy - box / 2)))
    _text(d, (cx, cy - 20 * u), shown, 230 * u, WHITE, ease_out(seg(t, 0, 0.15)), stroke=int(4 * u))
    if info.get("unit"): _text(d, (cx, cy + 135 * u), str(info["unit"]), 66 * u, GOLD, seg(t, 0.3, 0.5))
    for i, ln in enumerate(_wrap(str(info["label"]), 64 * u, W * 0.82, 2)):
        _text(d, (cx, H * (0.15 if H > W else 0.1) + i * 76 * u), ln, 62 * u, WHITE, ease_out(seg(t, 0.05, 0.3)))

def draw_bars(d, W, H, u, t, info):
    items = info["items"]; n = len(items)
    vals = [_num(x["value"]) or 0 for x in items]; mx = max(vals) or 1
    if info.get("title"): _text(d, (W / 2, H * (0.15 if H > W else 0.12)), str(info["title"]), 70 * u, GOLD, ease_out(seg(t, 0, 0.2)))
    top, bot = (H * 0.26 if H > W else H * 0.24), H * 0.86
    row = (bot - top) / n
    x_r, x_l = W * 0.92, W * 0.08
    for i, (it, v) in enumerate(zip(items, vals)):
        a0 = 0.08 + i * 0.1
        p = ease_out(seg(t, a0, a0 + 0.5)); y = top + row * i
        _text(d, (x_r, y + row * 0.22), str(it["label"]), 54 * u, WHITE, ease_out(seg(t, a0 - 0.04, a0 + 0.2)), "rm")
        bh = row * 0.34; by = y + row * 0.40
        d.rounded_rectangle([x_l, by, x_r, by + bh], radius=bh / 2, fill=(255, 255, 255, 28))
        L = (x_r - x_l) * (v / mx) * p
        if L > bh:
            d.rounded_rectangle([x_r - L, by, x_r, by + bh], radius=bh / 2, fill=GOLD + (255,))
        shown = _fmt(v * p, len(str(it["value"]).split(".")[-1]) if "." in str(it["value"]) else 0)
        if L > 190 * u:
            _text(d, (x_r - L + 22 * u, by + bh / 2), shown, 50 * u, NAVY, seg(t, a0, a0 + 0.2), "lm")
        else:
            _text(d, (x_r - L - 16 * u, by + bh / 2), shown, 50 * u, WHITE, seg(t, a0, a0 + 0.2), "rm")

def draw_timeline(d, W, H, u, t, info):
    ev = info["events"]; n = len(ev)
    if info.get("title"): _text(d, (W / 2, H * (0.14 if H > W else 0.1)), str(info["title"]), 68 * u, GOLD, ease_out(seg(t, 0, 0.2)))
    horiz = W >= H
    prog = ease_inout(seg(t, 0.05, 0.75))
    if horiz:
        x0, x1, y = W * 0.9, W * 0.1, H * 0.52
        d.line([(x0, y), (x0 + (x1 - x0) * prog, y)], fill=GOLD + (255,), width=int(8 * u))
    else:
        x, y0, y1 = W * 0.28, H * 0.24, H * 0.88
        d.line([(x, y0), (x, y0 + (y1 - y0) * prog)], fill=GOLD + (255,), width=int(8 * u))
    for i, e in enumerate(ev):
        f = i / (n - 1)
        pp = ease_back(seg(prog, f - 0.05, f + 0.08)) if prog >= f - 0.05 else 0
        if pp <= 0: continue
        r = 22 * u * clamp(pp, 0, 1.2)
        if horiz:
            px = x0 + (x1 - x0) * f; up = (i % 2 == 0)
            d.ellipse([px - r, y - r, px + r, y + r], fill=WHITE + (255,), outline=GOLD + (255,), width=int(6 * u))
            ty = y - 150 * u if up else y + 150 * u
            _text(d, (px, ty), str(e["year"]), 74 * u, GOLD, clamp(pp))
            for k, ln in enumerate(_wrap(str(e["text"]), 46 * u, W * 0.2, 3)):
                _text(d, (px, ty + (80 + k * 54) * u * (1 if up else 1)), ln, 46 * u, WHITE, clamp(pp))
        else:
            py = y0 + (y1 - y0) * f
            d.ellipse([x - r, py - r, x + r, py + r], fill=WHITE + (255,), outline=GOLD + (255,), width=int(6 * u))
            _text(d, (x - 50 * u, py - 20 * u), str(e["year"]), 70 * u, GOLD, clamp(pp), "rm")
            for k, ln in enumerate(_wrap(str(e["text"]), 46 * u, W * 0.62, 2)):
                _text(d, (x + 50 * u, py - 20 * u + k * 56 * u), ln, 46 * u, WHITE, clamp(pp), "lm")

def draw_compare(d, W, H, u, t, info):
    horiz = W >= H
    sides = [("right", info["right"], GOLD), ("left", info["left"], (90, 200, 170))]
    for idx, (name, s, col) in enumerate(sides):
        p = ease_out(seg(t, 0.05 + idx * 0.12, 0.5 + idx * 0.12))
        if horiz:
            cw, ch = W * 0.4, H * 0.66; cx = W * (0.70 if idx == 0 else 0.30); cy = H * 0.5
            ox = (W * 0.5) * (1 - p) * (1 if idx == 0 else -1)
        else:
            cw, ch = W * 0.84, H * 0.34; cx = W * 0.5; cy = H * (0.31 if idx == 0 else 0.70)
            ox = 0
        x0, y0 = cx - cw / 2 + ox, cy - ch / 2
        a = int(255 * p)
        d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], radius=28 * u, fill=(255, 255, 255, int(26 * p)), outline=col + (a,), width=int(5 * u))
        _text(d, (cx + ox, y0 + 70 * u), str(s["title"]), 62 * u, col, p)
        for k, it in enumerate(s["items"]):
            pk = ease_out(seg(t, 0.3 + k * 0.1 + idx * 0.1, 0.5 + k * 0.1 + idx * 0.1))
            ln = _wrap(str(it), 46 * u, cw * 0.84, 2)
            yy = y0 + (160 + k * 105) * u if horiz else y0 + (150 + k * 82) * u
            for j, l in enumerate(ln):
                _text(d, (cx + ox, yy + j * 52 * u), l, 46 * u, WHITE, pk)
    pv = ease_back(seg(t, 0.4, 0.6))
    if pv > 0:
        r = 60 * u * clamp(pv, 0, 1.2)
        d.ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], fill=NAVY + (255,), outline=GOLD + (255,), width=int(6 * u))
        _text(d, (W / 2, H / 2), "VS", 54 * u * clamp(pv, 0, 1.2), GOLD, clamp(pv))

def draw_list(d, W, H, u, t, info):
    items = info["items"]; n = len(items)
    if info.get("title"): _text(d, (W / 2, H * (0.15 if H > W else 0.14)), str(info["title"]), 72 * u, GOLD, ease_out(seg(t, 0, 0.2)))
    top = H * (0.3 if H > W else 0.28); row = (H * 0.6) / n
    for i, it in enumerate(items):
        p = ease_back(seg(t, 0.1 + i * 0.14, 0.3 + i * 0.14))
        if p <= 0: continue
        y = top + row * i + row / 2
        r = 46 * u * clamp(p, 0, 1.15); cxr = W * 0.88
        d.ellipse([cxr - r, y - r, cxr + r, y + r], fill=GOLD + (255,))
        _text(d, (cxr, y - 4 * u), str(i + 1), 54 * u, NAVY, clamp(p))
        for j, ln in enumerate(_wrap(str(it), 58 * u, W * 0.7, 2)):
            _text(d, (cxr - 80 * u, y - 28 * u * (len(_wrap(str(it), 58 * u, W * 0.7, 2)) - 1) + j * 64 * u), ln, 58 * u, WHITE, clamp(p), "rm")

def draw_kinetic(d, W, H, u, t, info):
    words = [str(w) for w in info["words"]]; n = len(words)
    size = (150 if W >= H else 130) * u
    gap = size * 1.25
    y0 = H / 2 - gap * (n - 1) / 2
    for i, w in enumerate(words):
        p = ease_back(seg(t, 0.04 + i * 0.16, 0.3 + i * 0.16))
        if p <= 0: continue
        sz = size * clamp(p, 0.1, 1.12)
        while arfont.text_width(w, _font(sz)) > W * 0.88 and sz > 40: sz *= 0.92
        _text(d, (W / 2, y0 + gap * i), w, sz, GOLD if i % 2 else WHITE, clamp(p * 1.5), stroke=int(5 * u))
    ul = ease_out(seg(t, 0.35 + n * 0.1, 0.8))
    d.rounded_rectangle([W / 2 - W * 0.18 * ul, y0 + gap * (n - 1) + size * 0.75, W / 2 + W * 0.18 * ul, y0 + gap * (n - 1) + size * 0.75 + 10 * u], radius=5 * u, fill=GOLD + (255,))

@functools.lru_cache(maxsize=2)
def _wm_big(): return brand.wordmark_rgba(220)

def draw_endcard(d, W, H, u, t, info):
    wm = _wm_big()
    k = ease_back(seg(t, 0.02, 0.3))
    if k > 0:
        s = clamp(k, 0.05, 1.1) * (W / 1920 if W >= H else W / 1080) * 1.5
        im = wm.resize((max(2, int(wm.width * s)), max(2, int(wm.height * s))), Image.LANCZOS)
        d._img.alpha_composite(im, (int(W / 2 - im.width / 2), int(H * 0.28 - im.height / 2)))
    b = ease_out(seg(t, 0.25, 0.5)); pulse = 1 + 0.04 * math.sin(t * 22)
    bw, bh = 520 * u * pulse, 128 * u * pulse
    cy = H * 0.52
    d.rounded_rectangle([W / 2 - bw / 2, cy - bh / 2, W / 2 + bw / 2, cy + bh / 2], radius=bh / 2, fill=RED + (int(255 * b),))
    _text(d, (W / 2, cy), "اشترك في القناة", 62 * u, WHITE, b)
    _text(d, (W / 2, H * 0.68), "نكمل الرحلة في الفيديو القادم", 56 * u, WHITE, ease_out(seg(t, 0.45, 0.7)))
    _text(d, (W / 2, H * 0.76), "اكتب لنا في التعليقات فكرة الفيديو التالي", 44 * u, GOLD, ease_out(seg(t, 0.55, 0.8)))

DRAW = {"number": draw_number, "bars": draw_bars, "timeline": draw_timeline, "compare": draw_compare,
        "list": draw_list, "kinetic": draw_kinetic, "endcard": draw_endcard}

class _D:
    """غلاف ImageDraw يحتفظ بالصورة (لدمج طبقات جاهزة)."""
    def __init__(self, img):
        self._img = img; self._d = ImageDraw.Draw(img, "RGBA")
    def __getattr__(self, k): return getattr(self._d, k)

def render_anim(info, frames, W, H, out, wm=None, wm_xy=(40, 36), p0=0.0, p1=1.0, seed=0):
    """يرسم الإنفوجرافيك فريماً فريماً → mp4 (بنفس مواصفات بقية اللقطات)."""
    kind = info.get("type", "kinetic"); fn = DRAW[kind]
    u = min(W, H) / 1080.0
    base = _bg(W, H, seed)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", PRESET, "-crf", str(CRF), "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-g", str(FPS * 2), "-profile:v", "high", "-level", "4.1", "-movflags", "+faststart", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for i in range(frames):
            t = i / max(1, frames - 1)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = _D(layer)
            fn(d, W, H, u, t, info)
            pbw = W * (p0 + (p1 - p0) * t)
            ImageDraw.Draw(layer).rectangle([0, H - 8 * u, pbw, H], fill=GOLD + (235,))
            fr = base.copy(); fr.alpha_composite(layer)
            if wm is not None: fr.alpha_composite(wm, (int(wm_xy[0]), int(wm_xy[1])))
            pr.stdin.write(fr.convert("RGB").tobytes())
        pr.stdin.close()
        err = pr.stderr.read().decode(errors="ignore")
        if pr.wait() != 0: raise RuntimeError("ffmpeg anim failed: " + err[-400:])
    except BrokenPipeError:
        raise RuntimeError("ffmpeg anim pipe broke: " + pr.stderr.read().decode(errors="ignore")[-400:])
    return out
'''

# ======================================================================
# القسم: tts
# ======================================================================
_SRC['tts'] = r'''# -*- coding: utf-8 -*-
"""الصوت: تقطيع النص لجمل قصيرة + فواصل صمت حقيقية بين الجمل + الأرقام حروف."""
import asyncio, os, re, subprocess, wave
import numpy as np
from config import (WORK, VOICES, TTS_RATE, TTS_PITCH, PAUSE, LEAD_IN, TAIL_OUT, MAX_CHUNK_WORDS, MAX_SEC)
from util import log, run, probe_duration
from arabic_numbers import digits_to_words

SR = 44100
_PUNCT = re.compile(r"([\.!\?؟…]+|[،,]|[;؛:])")

def clean_for_tts(text):
    t = digits_to_words(text)
    t = re.sub(r"[\*#_`~\[\]\(\)\{\}<>|\\/\"“”«»]", " ", t)
    t = t.replace("&", " و ").replace("+", " زائد ").replace("=", " يساوي ").replace("$", " دولار ")
    t = t.replace("\u200f", "").replace("\u200e", "")
    t = re.sub(r"\s*([،,;؛:\.!\?؟])\s*", r"\1 ", t)
    t = re.sub(r"([\.!\?؟])\1+", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()

def _pause_for(p):
    if not p: return PAUSE["wrap"]
    if p[0] in ".!?؟…": return PAUSE["sentence"]
    if p[0] in "،,": return PAUSE["comma"]
    return PAUSE["colon"]

def split_chunks(text):
    """يرجع [(نص, صمت_بعده)] — كل جزء ≤ MAX_CHUNK_WORDS كلمة."""
    t = clean_for_tts(text)
    parts = _PUNCT.split(t)
    pieces = []
    i = 0
    while i < len(parts):
        body = parts[i].strip()
        punct = parts[i + 1] if i + 1 < len(parts) else ""
        i += 2
        if not body and not punct:
            continue
        if not body:
            continue
        pieces.append([body, punct])
    # دمج القطع القصيرة جداً (<3 كلمات) مع التالية
    merged = []
    carry = ""
    for body, punct in pieces:
        if carry:
            body = carry + " " + body; carry = ""
        if len(body.split()) < 3 and (punct and punct[0] in "،,;؛:"):
            carry = body + punct[0]
            continue
        merged.append([body, punct])
    if carry:
        if merged: merged[-1][0] += " " + carry
        else: merged.append([carry, ""])
    out = []
    for body, punct in merged:
        words = body.split()
        if len(words) <= MAX_CHUNK_WORDS:
            out.append((body + (punct[0] if punct else ""), _pause_for(punct)))
            continue
        n = -(-len(words) // MAX_CHUNK_WORDS)
        # نقاط التقسيم: الأقرب لنهاية كل جزء متساوٍ، ونفضّل قبل أدوات الربط
        conj = {"ثم", "لكن", "ولكن", "حتى", "الذي", "التي", "لأن", "بينما", "كما", "أو", "و", "مع", "عندما", "لذلك"}
        cuts = []
        for k in range(1, n):
            target = round(k * len(words) / n)
            best = target
            for off in (0, -1, 1, -2, 2, -3, 3):
                j = target + off
                if 2 <= j <= len(words) - 2 and words[j] in conj:
                    best = j; break
            cuts.append(best)
        bounds = [0] + sorted(set(cuts)) + [len(words)]
        for k in range(len(bounds) - 1):
            seg = " ".join(words[bounds[k]:bounds[k + 1]])
            if not seg: continue
            last = (k == len(bounds) - 2)
            out.append((seg + (punct[0] if (last and punct) else ""), _pause_for(punct) if last else PAUSE["wrap"]))
    return out

def _decode(path):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("decode failed " + p.stderr.decode(errors="ignore")[-200:])
    return np.frombuffer(p.stdout, dtype=np.float32).copy()

def _trim(x, thr=0.006, keep=0.03):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(keep * SR)); b = min(len(x), idx[-1] + int(keep * SR))
    return x[a:b]

async def _edge_synth(text, voice, path):
    import edge_tts
    com = edge_tts.Communicate(text, voice, rate=TTS_RATE, pitch=TTS_PITCH)
    await com.save(path)

def default_synth(text, voice, path):
    asyncio.run(_edge_synth(text, voice, path))

SYNTH = default_synth      # قابل للاستبدال في الاختبار

def _synth_ok(text, voice, path, tries=5):
    import time
    last = None
    for i in range(tries):
        try:
            if os.path.exists(path): os.remove(path)
            SYNTH(text, voice, path)
            if os.path.exists(path) and os.path.getsize(path) > 1200 and probe_duration(path) > 0.15:
                return True
            last = "ملف صوت فارغ"
        except Exception as e:  # noqa
            last = str(e)[:200]
        time.sleep(1.5 * (i + 1))
    log(f"[tts] فشل '{text[:30]}…' صوت {voice}: {last}")
    return False

def pick_voice(voices=None):
    os.makedirs(os.path.join(WORK, "tts"), exist_ok=True)
    probe = os.path.join(WORK, "tts", "probe.mp3")
    for v in (voices or VOICES):
        if _synth_ok("مرحبا بكم في قناة بوصلة. اليوم نتكلم عن موضوع مهم.", v, probe, tries=3):
            log("[tts] الصوت المستخدم:", v)
            return v
        log("[tts] الصوت غير متاح:", v)
    raise RuntimeError("كل الأصوات فشلت — حدّث edge-tts (pip install -U edge-tts)")

def build_voice(scenes, out_wav, voices=None, lead_in=None, tail_out=None):
    lead_in = LEAD_IN if lead_in is None else lead_in
    tail_out = TAIL_OUT if tail_out is None else tail_out
    """scenes: list of dict with 'narration'. يضيف لكل مشهد start/end/dur ويرجع المدة الكلية."""
    voice = pick_voice(voices)
    d = os.path.join(WORK, "tts"); os.makedirs(d, exist_ok=True)
    jobs = []
    for si, sc in enumerate(scenes):
        for ci, (txt, pause) in enumerate(split_chunks(sc["narration"])):
            jobs.append((si, ci, txt, pause))
    log(f"[tts] {len(jobs)} جزء صوتي")
    paths = {}
    from concurrent.futures import ThreadPoolExecutor
    def work(j):
        si, ci, txt, _ = j
        p = os.path.join(d, f"s{si:03d}_{ci:02d}.mp3")
        ok = _synth_ok(txt, voice, p)
        return j, (p if ok else None)
    with ThreadPoolExecutor(max_workers=3) as ex:
        for j, p in ex.map(work, jobs):
            if p is None:
                raise RuntimeError(f"فشل توليد صوت المشهد {j[0]}")
            paths[(j[0], j[1])] = p
    audio = [np.zeros(int(lead_in * SR), dtype=np.float32)]
    t = lead_in
    n_scenes = len(scenes)
    by_scene = {}
    for si, ci, txt, pause in jobs:
        by_scene.setdefault(si, []).append((ci, pause))
    for si, sc in enumerate(scenes):
        sc["start"] = t
        sc["chunks"] = []
        items = by_scene[si]
        for k, (ci, pause) in enumerate(items):
            x = _trim(_decode(paths[(si, ci)]))
            if k == len(items) - 1:
                pause = max(pause, PAUSE["scene"])
            seg = np.concatenate([x, np.zeros(int(pause * SR), dtype=np.float32)])
            ctext = next(j[2] for j in jobs if j[0] == si and j[1] == ci)
            sc["chunks"].append((ctext, t, t + len(x) / SR))
            audio.append(seg); t += len(seg) / SR
        sc["end"] = t
        sc["dur"] = sc["end"] - sc["start"]
    audio.append(np.zeros(int(tail_out * SR), dtype=np.float32)); t += tail_out
    y = np.concatenate(audio)
    peak = float(np.max(np.abs(y))) or 1.0
    y = y * (0.9 / peak)
    _write_wav(out_wav, y)
    total = len(y) / SR
    # لو الفيديو أطول من ١٠ دقايق: تسريع خفيف جداً (حتى ×١.١٢)
    if total > MAX_SEC + 5:
        f = min(1.12, total / (MAX_SEC - 5))
        tmp = out_wav + ".fast.wav"
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", out_wav, "-filter:a", f"atempo={f:.4f}", tmp])
        os.replace(tmp, out_wav)
        for sc in scenes:
            sc["start"] /= f; sc["end"] /= f; sc["dur"] /= f
            sc["chunks"] = [(a, b / f, c / f) for (a, b, c) in sc["chunks"]]
        total = probe_duration(out_wav)
        log(f"[tts] تسريع ×{f:.3f} لأن المدة كانت طويلة")
    log(f"[tts] مدة الصوت {total:.1f}s")
    return total

def _write_wav(path, y):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())
'''

# ======================================================================
# القسم: visuals
# ======================================================================
_SRC['visuals'] = r'''# -*- coding: utf-8 -*-
"""المونتاج: صور مولدة بالذكاء الاصطناعي (حركات كاميرا متنوعة) + إنفوجرافيك متحرك + ستوك احتياطي،
شعار احترافي أعلى اليسار بشفافية ٧٠٪، شريط تقدّم، وبطاقة ختام. يدعم الأفقي (فيديو طويل) والعمودي (شورت)."""
import math, os, random
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
from config import (WORK, W, H, FPS, CRF, PRESET, SHOT_MIN, SHOT_MAX, SHORT_SHOT_MIN, SHORT_SHOT_MAX, WATERMARK_OPACITY,
                    NAVY, GREEN, GOLD, WHITE)
import arfont, brand, anim
from util import log, run, probe_duration

VDIR = os.path.join(WORK, "video")
MOVES = ["zin", "panl", "zout", "panr", "zin", "panu", "zout", "pand"]

def make_watermark(vertical=False):
    os.makedirs(VDIR, exist_ok=True)
    im = brand.wordmark_rgba(84 if vertical else 96)
    a = im.split()[3].point(lambda v: int(v * WATERMARK_OPACITY))
    im.putalpha(a)
    path = os.path.join(VDIR, "wm_v.png" if vertical else "wm.png")
    im.save(path)
    return path, im, ((36, 70) if vertical else (40, 30))

def make_text_overlay(text, path, size=(W, H)):
    w, h = size; u = min(w, h) / 1080.0
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fsz = 92 * u
    f = arfont.font(int(fsz))
    while arfont.text_width(text, f) > w - 420 * u and fsz > 48 * u:
        fsz -= 6 * u; f = arfont.font(int(fsz))
    tw = arfont.text_width(text, f)
    pad_x, bar_h = 64 * u, fsz + 70 * u
    x1, x2 = w / 2 - tw / 2 - pad_x, w / 2 + tw / 2 + pad_x
    y2 = h - 120 * u; y1 = y2 - bar_h
    d.rounded_rectangle([x1, y1, x2, y2], radius=18 * u, fill=NAVY + (214,))
    d.rounded_rectangle([x2 - 12 * u, y1, x2, y2], radius=6 * u, fill=GOLD + (255,))
    arfont.draw_text(d, (w / 2 - 4 * u, (y1 + y2) / 2 - 4 * u), text, f, WHITE + (255,), "mm")
    im.save(path)
    return path

def make_card(text, path, seed=0, size=(W, H)):
    """بطاقة بديلة (لو ما لقينا صورة ولا لقطة): خلفية بهوية القناة."""
    w, h = size; u = min(w, h) / 1080.0
    rnd = random.Random(seed)
    col = Image.new("RGB", (1, h)); px = col.load()
    c1, c2 = NAVY, (13, 60, 66)
    for y in range(h):
        t = y / (h - 1); px[0, y] = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
    im = col.resize((w, h)).convert("RGBA")
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for _ in range(14):
        cx, cy, r = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(int(120 * u), int(420 * u))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD + (40,), width=3)
    if text:
        f = arfont.font(int(110 * u))
        lines = arfont.wrap(text, f, w - 300 * u, 3)
        y = h / 2 - (len(lines) - 1) * 75 * u
        for ln in lines:
            arfont.draw_text(d, (w / 2, y), ln, f, WHITE + (255,), "mm", stroke=4, stroke_fill=NAVY)
            y += 150 * u
    im.alpha_composite(ov)
    im.convert("RGB").save(path)
    return path

def _bar_png(size, path):
    w, h = size; u = min(w, h) / 1080.0
    Image.new("RGBA", (w, max(2, int(8 * u))), GOLD + (235,)).save(path)
    return path

def _enc():
    return ["-an", "-c:v", "libx264", "-preset", PRESET, "-crf", str(CRF), "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-g", str(FPS * 2), "-profile:v", "high", "-level", "4.1", "-movflags", "+faststart"]

def _zoompan(move, frames, w, h, src_w, src_h):
    N = max(2, frames)
    z, x, y = {
        "zin":  (f"1+0.10*on/{N}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        "zout": (f"1.10-0.10*on/{N}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        "panl": ("1.14", f"(iw-iw/zoom)*on/{N}", "ih/2-(ih/zoom/2)"),
        "panr": ("1.14", f"(iw-iw/zoom)*(1-on/{N})", "ih/2-(ih/zoom/2)"),
        "panu": ("1.14", "iw/2-(iw/zoom/2)", f"(ih-ih/zoom)*(1-on/{N})"),
        "pand": ("1.14", "iw/2-(iw/zoom/2)", f"(ih-ih/zoom)*on/{N}"),
    }[move]
    return (f"scale={src_w}:{src_h}:force_original_aspect_ratio=increase,crop={src_w}:{src_h},"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={N}:s={w}x{h}:fps={FPS}")

def render_shot(src, kind, frames, out, overlay, wm, bar, p0, p1, move="zin", start=0.0, loop=False, size=(W, H), wm_xy=(40, 30)):
    w, h = size; vertical = h > w; u = min(w, h) / 1080.0
    dur = frames / FPS
    ins = []
    if kind == "video":
        if loop: ins += ["-stream_loop", "-1"]
        elif start > 0: ins += ["-ss", f"{start:.3f}"]
        ins += ["-i", src]
        zexpr = f"(1+0.07*t/{dur:.4f})" if move in ("zin", "panl", "panu") else f"(1.07-0.07*t/{dur:.4f})"
        bg = (f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={FPS},setsar=1,"
              f"scale=w='trunc({w}*{zexpr}/2)*2':h=-2:eval=frame,crop={w}:{h},"
              f"eq=contrast=1.05:saturation=1.10,format=yuv420p[bg]")
    else:
        ins += ["-i", src]
        sw, sh = (1440, 2560) if vertical else (2560, 1440)
        bg = f"[0:v]{_zoompan(move, frames, w, h, sw, sh)},eq=contrast=1.05:saturation=1.12,format=yuv420p[bg]"
    ins += ["-loop", "1", "-i", wm, "-loop", "1", "-i", bar]
    chain = (f"{bg};[bg][1:v]overlay={wm_xy[0]}:{wm_xy[1]}:format=auto[v1];"
             f"[v1][2:v]overlay=x='-w+w*({p0:.5f}+({p1:.5f}-{p0:.5f})*t/{dur:.4f})':y={h}-h:format=auto[v2]")
    outlab = "[v2]"
    if overlay:
        ins += ["-loop", "1", "-i", overlay]
        chain += (f";[3:v]format=rgba,fade=t=in:st=0.12:d=0.22:alpha=1,fade=t=out:st={max(0.2, dur - 0.32):.3f}:d=0.2:alpha=1[tx];"
                  f"[v2][tx]overlay=0:0:format=auto[vout]")
        outlab = "[vout]"
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", chain, "-map", outlab, "-frames:v", str(frames)] + _enc() + [out]
    run(cmd, timeout=600)
    return out

def plan_shots(dur, vertical=False):
    lo, hi = (SHORT_SHOT_MIN, SHORT_SHOT_MAX) if vertical else (SHOT_MIN, SHOT_MAX)
    k = max(1, math.ceil(dur / hi))
    if dur / k < lo:
        k = max(1, int(dur // lo))
    return k

def build_video(scenes, total_sec, stock, out_path, imgen=None, size=(W, H), generic_queries=("city skyline", "business", "technology"), endcard=True):
    """scenes: narration/visual/image_prompt/info/search/text/start. يرجع مسار فيديو بدون صوت."""
    w, h = size; vertical = h > w
    os.makedirs(VDIR, exist_ok=True)
    wm_path, wm_img, wm_xy = make_watermark(vertical)
    bar = _bar_png(size, os.path.join(VDIR, "bar.png"))
    # ---- الجدول الزمني (فريمات صحيحة بدون انجراف عن الصوت)
    timeline = []; cum = 0
    total_frames = round(total_sec * FPS)
    for si, sc in enumerate(scenes):
        vs = 0.0 if si == 0 else sc["start"]
        ve = total_sec if si == len(scenes) - 1 else scenes[si + 1]["start"]
        sc["_endcard"] = bool(endcard and si == len(scenes) - 1 and (ve - vs) >= 4.0 and not vertical)
        k = 1 if sc["_endcard"] or (sc.get("visual") == "info") else plan_shots(ve - vs, vertical)
        for j in range(k):
            f_end = round((vs + (ve - vs) * (j + 1) / k) * FPS)
            frames = max(2, f_end - cum)
            cum += frames
            timeline.append((si, j, k, frames))
    log(f"[video] {len(scenes)} مشهد → {len(timeline)} لقطة")
    # ---- تجهيز مصدر كل مشهد (تسلسلي)
    n_img = n_info = n_stock = n_card = 0
    for si, sc in enumerate(scenes):
        k = sum(1 for t in timeline if t[0] == si)
        vis = "endcard" if sc["_endcard"] else sc.get("visual") or "stock"
        sc["_mode"] = None; sc["_assets"] = []; sc["_img"] = None
        if vis == "endcard":
            sc["_mode"] = "anim"; sc["_info"] = {"type": "endcard"}; continue
        if vis == "info":
            err = anim.validate_info(sc.get("info"))
            sc["_info"] = sc["info"] if err is None else anim.fallback_info(sc.get("text") or sc["narration"])
            sc["_mode"] = "anim"; n_info += 1; continue
        if vis == "image" and imgen is not None:
            p = imgen.generate(sc.get("image_prompt") or sc.get("search") or "", w, h, seed=1000 + si)
            if p:
                sc["_mode"] = "image"; sc["_img"] = p; n_img += 1; continue
        found = stock.find(sc.get("search") or sc.get("image_prompt") or "", True, generic_queries[:2], portrait=vertical)
        picked = []
        for a in found:
            if len(picked) >= k: break
            try:
                stock.download(a); picked.append(a)
            except Exception as e:  # noqa
                log(f"[video] تحميل فشل {a.uid}: {str(e)[:80]}")
        if picked:
            sc["_mode"] = "stock"; sc["_assets"] = picked; n_stock += 1
        else:
            sc["_mode"] = "card"; n_card += 1
    log(f"[video] صور مولدة {n_img} | إنفوجرافيك {n_info} | ستوك {n_stock} | بطاقات {n_card}")
    overlays = {}
    if not vertical:
        for si, sc in enumerate(scenes):
            if sc.get("text") and sc["_mode"] in ("image", "stock", "card"):
                overlays[si] = make_text_overlay(sc["text"], os.path.join(VDIR, f"tx{si:03d}.png"), size)
    # ---- الرندر
    starts = []; acc = 0
    for t in timeline: starts.append(acc); acc += t[3]
    shots = [None] * len(timeline)
    def do(job):
        idx, (si, j, k, frames) = job
        sc = scenes[si]; out = os.path.join(VDIR, f"shot{idx:04d}.mp4")
        p0, p1 = starts[idx] / total_frames, (starts[idx] + frames) / total_frames
        move = MOVES[idx % len(MOVES)]
        ov = overlays.get(si) if j == 0 else None
        mode = sc["_mode"]
        try:
            if mode == "anim":
                return idx, anim.render_anim(sc["_info"], frames, w, h, out, wm_img, wm_xy, p0, p1, seed=si)
            if mode == "image":
                return idx, render_shot(sc["_img"], "image", frames, out, ov, wm_path, bar, p0, p1, MOVES[(idx + j) % len(MOVES)], size=size, wm_xy=wm_xy)
            if mode == "stock":
                assets = sc["_assets"]; a = assets[j % len(assets)]
                if a.kind == "video":
                    cd = a.dur or probe_duration(a.path); dur = frames / FPS
                    loop = cd < dur + 0.3
                    start = 0.0 if loop else random.Random(idx).uniform(0, max(0.0, cd - dur - 0.2))
                    return idx, render_shot(a.path, "video", frames, out, ov, wm_path, bar, p0, p1, move, start, loop, size, wm_xy)
                return idx, render_shot(a.path, "image", frames, out, ov, wm_path, bar, p0, p1, move, size=size, wm_xy=wm_xy)
        except Exception as e:  # noqa
            log(f"[video] لقطة {idx} فشلت ({mode}): {str(e)[:140]}")
        card = make_card(sc.get("text") or "", os.path.join(VDIR, f"card{idx:04d}.png"), seed=idx, size=size)
        return idx, render_shot(card, "image", frames, out, ov, wm_path, bar, p0, p1, move, size=size, wm_xy=wm_xy)
    with ThreadPoolExecutor(max_workers=2) as ex:
        for idx, p in ex.map(do, list(enumerate(timeline))):
            shots[idx] = p
    lst = os.path.join(VDIR, "list.txt")
    with open(lst, "w") as f:
        for p in shots: f.write(f"file '{p}'\n")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out_path], timeout=900)
    return out_path

# ---------- ترجمة الشورت (كلمات متحركة) ----------
def caption_phrases(scenes):
    """يرجع [(نص, بداية, نهاية)] — ٣ كلمات كحد أقصى، التوقيت موزع على حسب طول الكلمات داخل كل جزء صوتي."""
    out = []
    for sc in scenes:
        for (txt, a, b) in sc.get("chunks", []):
            words = txt.split()
            if not words: continue
            lens = [max(1, len(x)) for x in words]; tot = sum(lens)
            phrases = [words[i:i + 3] for i in range(0, len(words), 3)]
            t = a; idx = 0
            for ph in phrases:
                share = sum(lens[idx:idx + len(ph)]) / tot
                dt = (b - a) * share
                out.append((" ".join(ph).strip("،,.؟?!:؛"), t, t + dt)); t += dt; idx += len(ph)
    return out

def render_short_final(video, audio, phrases, out, size=(1080, 1920)):
    w, h = size; u = min(w, h) / 1080.0
    os.makedirs(VDIR, exist_ok=True)
    pngs = []
    f = arfont.font(int(96 * u))
    for i, (txt, a, b) in enumerate(phrases):
        im = Image.new("RGBA", (w, int(300 * u)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        sz = 96 * u; ff = f
        while arfont.text_width(txt, ff) > w * 0.9 and sz > 50 * u:
            sz -= 6 * u; ff = arfont.font(int(sz))
        col = GOLD if i % 2 else WHITE
        arfont.draw_text(d, (w / 2, 150 * u), txt, ff, col + (255,), "mm", stroke=int(9 * u), stroke_fill=(4, 10, 16, 255))
        p = os.path.join(VDIR, f"cap{i:03d}.png"); im.save(p); pngs.append((p, a, b))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio]
    for p, a, b in pngs: cmd += ["-loop", "1", "-i", p]
    y = int(h * 0.66)
    chain = "[0:v]null[c0]"; prev = "c0"
    for i, (p, a, b) in enumerate(pngs):
        nxt = f"c{i+1}"
        chain += f";[{prev}][{i+2}:v]overlay=0:{y}:enable='between(t,{a:.3f},{b:.3f})':format=auto[{nxt}]"
        prev = nxt
    cmd += ["-filter_complex", chain, "-map", f"[{prev}]", "-map", "1:a:0", "-c:v", "libx264", "-preset", PRESET, "-crf", str(CRF),
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "copy", "-shortest", "-movflags", "+faststart", out]
    run(cmd, timeout=1200)
    return out
'''

# ======================================================================
# القسم: music
# ======================================================================
_SRC['music'] = r'''# -*- coding: utf-8 -*-
"""ترتيب الموسيقى تلقائياً على طول الفيديو: مقدمة -> تصاعد -> (الجزء الأساسي × عدة مرات) -> ذروة -> خاتمة،
مع ضبط السرعة بنسبة بسيطة (≤٦٪ غالباً) عشان تنتهي الذروة والخاتمة مع نهاية الفيديو، ثم خفض تلقائي تحت صوت المعلق."""
import json, os, subprocess, wave
import numpy as np
from config import ASSETS, WORK
from util import log, run

SR = 44100

PARAMS = {"a": (0, 100, 7), "b": (-2, 96, 11), "c": (3, 104, 23)}

def _scan(d):
    out = []
    if os.path.isdir(d):
        for n in sorted(os.listdir(d)):
            if os.path.exists(os.path.join(d, n, "manifest.json")):
                out.append(os.path.join(d, n))
    return out

def ensure_music():
    """لو ما فيه موسيقى: يولدها بالكود (مرة واحدة فقط، ~٣ دقايق)، وتُحفظ في المستودع."""
    import sys
    d = os.path.join(ASSETS, "music"); os.makedirs(d, exist_ok=True)
    for name, (tr, bpm, seed) in PARAMS.items():
        if os.path.exists(os.path.join(d, name, "manifest.json")):
            continue
        log(f"[music] توليد النسخة {name} …")
        run([sys.executable, "-c", MAKE_MUSIC_SRC, "--out", os.path.join(d, name), "--tr", str(tr), "--bpm", str(bpm), "--seed", str(seed)], timeout=1200)

def variants():
    d = os.path.join(ASSETS, "music")
    out = _scan(d)
    if not out:
        ensure_music()
        out = _scan(d)
    if not out:
        raise RuntimeError("تعذر توليد الموسيقى (تأكد من scipy في requirements.txt)")
    return out

def _decode(path):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("decode music failed: " + p.stderr.decode(errors="ignore")[-200:])
    return np.frombuffer(p.stdout, dtype=np.float32).reshape(-1, 2).T.copy()

def layout(man, total_sec):
    """يرجع (قائمة (اسم, بداية_ثواني), طول_بدون_ذيل, عدد_التكرارات, معامل_السرعة).
    للفيديوهات القصيرة (<٩٠ ثانية) يختار أنسب تركيبة من الأقسام."""
    bar = man["bar_sec"]; B = {k: v["bars"] for k, v in man["sections"].items()}
    if total_sec < 90:
        combos = [["climax"], ["main"], ["build", "climax"], ["main", "outro"], ["build", "climax", "outro"], ["main", "climax"],
                  ["intro", "build", "climax", "outro"], ["build", "main", "climax"]]
        best = None
        for c in combos:
            L = sum(B[x] for x in c) * bar; s = L / total_sec
            if best is None or abs(s - 1) < abs(best[2] - 1): best = (c, L, s)
        c, L, s = best
        plan = []; t = 0.0
        for x in c:
            plan.append((x, t)); t += B[x] * bar
        return plan, L, 0, s
    fixed = B["intro"] + B["build"] + B["climax"] + B["outro"]
    best = None
    for n in range(0, 80):
        L = (fixed + n * B["main"]) * bar
        s = L / total_sec
        score = abs(s - 1)
        if best is None or score < best[0]:
            best = (score, n, L, s)
    _, n, L, s = best
    plan = []; t = 0.0
    plan.append(("intro", t)); t += B["intro"] * bar
    plan.append(("build", t)); t += B["build"] * bar
    for _ in range(n):
        plan.append(("main", t)); t += B["main"] * bar
    plan.append(("climax", t)); t += B["climax"] * bar
    plan.append(("outro", t)); t += B["outro"] * bar
    return plan, L, n, s

def build_music(total_sec, out_wav, index=0):
    vs = variants(); vdir = vs[index % len(vs)]
    man = json.load(open(os.path.join(vdir, "manifest.json")))
    plan, L, n, s = layout(man, total_sec)
    s = min(2.0, max(0.5, s))
    log(f"[music] نسخة {os.path.basename(vdir)} | تكرار الأساسي ×{n} | معامل السرعة {s:.3f}")
    cache = {k: _decode(os.path.join(vdir, v["file"])) for k, v in man["sections"].items()}
    total = int((L + man["tail_sec"] + 1) * SR)
    tl = np.zeros((2, total), dtype=np.float32)
    for name, t0 in plan:
        x = cache[name]; i = int(t0 * SR); m = min(x.shape[1], total - i)
        if m > 0: tl[:, i:i + m] += x[:, :m]
    peak = float(np.max(np.abs(tl))) or 1.0
    if peak > 0.98: tl *= 0.98 / peak
    raw = out_wav + ".raw.wav"
    with wave.open(raw, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(tl.T, -1, 1) * 32767).astype("<i2").tobytes())
    fade = min(3.0, total_sec / 4)
    flt = f"atempo={s:.5f},atrim=0:{total_sec:.3f},apad=whole_dur={total_sec:.3f},afade=t=out:st={total_sec - fade:.3f}:d={fade:.3f}"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-filter:a", flt, "-ar", str(SR), "-ac", "2", out_wav])
    os.remove(raw)
    return plan, s

def mix(voice_wav, music_wav, out_m4a, total_sec, music_gain=0.24):
    """الصوت يُضبط أولاً على -16 LUFS، ثم الموسيقى بمستوى ثابت تحته مع خفض تلقائي أثناء الكلام."""
    fc = ("[0:a]highpass=f=75,lowpass=f=15000,acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2,"
          "loudnorm=I=-16:TP=-1.5:LRA=7,aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[v1][v2];"
          f"[1:a]volume={music_gain},aformat=sample_rates=44100:channel_layouts=stereo[m0];"
          "[m0][v2]sidechaincompress=threshold=0.03:ratio=4:attack=12:release=500:makeup=1[md];"
          "[v1][md]amix=inputs=2:duration=first:normalize=0:dropout_transition=0,alimiter=limit=0.93[o]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", voice_wav, "-i", music_wav, "-filter_complex", fc,
         "-map", "[o]", "-t", f"{total_sec:.3f}", "-ar", "44100", "-c:a", "aac", "-b:a", "192k", out_m4a])
'''

# ======================================================================
# القسم: thumbnail
# ======================================================================
_SRC['thumbnail'] = r'''# -*- coding: utf-8 -*-
"""الصورة المصغرة: خلفية لقطة قوية + نص كبير عالي التباين + هوية القناة. أي فشل هنا ما يوقف النشر."""
import os, random
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from config import ASSETS, NAVY, GOLD, WHITE, GREEN
import arfont, brand
from util import log

TW, TH = 1280, 720

def _bg(path):
    if path and os.path.exists(path):
        try:
            im = Image.open(path).convert("RGB")
            r = max(TW / im.width, TH / im.height)
            im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
            x, y = (im.width - TW) // 2, (im.height - TH) // 2
            im = im.crop((x, y, x + TW, y + TH))
            im = ImageEnhance.Color(im).enhance(1.35)
            im = ImageEnhance.Contrast(im).enhance(1.18)
            return im
        except Exception as e:  # noqa
            log("[thumb] خلفية تالفة:", str(e)[:80])
    im = Image.new("RGB", (TW, TH)); px = im.load()
    for y in range(TH):
        t = y / (TH - 1)
        c = tuple(int(NAVY[i] * (1 - t) + (13, 70, 72)[i] * t) for i in range(3))
        for x in range(TW): px[x, y] = c
    return im

def make_thumbnail(title_text, out_path, bg_path=None, accent_words=1):
    im = _bg(bg_path).convert("RGBA")
    # تعتيم تدريجي من اليمين لأن النص عربي (يبدأ من اليمين)
    shade = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); sp = shade.load()
    for x in range(TW):
        a = int(215 * max(0.0, (x - TW * 0.18) / (TW * 0.82)) ** 1.1)
        for y in range(TH): sp[x, y] = (5, 14, 22, min(225, a))
    im.alpha_composite(shade)
    d = ImageDraw.Draw(im)
    words = title_text.split()
    size = 170
    while True:
        f = arfont.font(size)
        lines = arfont.wrap(title_text, f, 800, 3)
        widest = max(arfont.text_width(l, f) for l in lines)
        if (widest <= 800 and len(lines) * size * 1.12 <= TH - 140) or size <= 80: break
        size -= 8
    lh = size * 1.14
    y0 = TH / 2 - (len(lines) - 1) * lh / 2 - 10
    right = TW - 70
    for i, ln in enumerate(lines):
        col = GOLD if i == 0 else WHITE
        arfont.draw_text(d, (right, y0 + i * lh), ln, f, col + (255,), "rm", stroke=max(6, size // 18), stroke_fill=(4, 10, 16))
    # شريط ذهبي + شعار صغير
    d.rounded_rectangle([TW - 70 - 190, TH - 78, TW - 70, TH - 66], radius=6, fill=GOLD + (255,))
    wmk = brand.wordmark_rgba(84)
    im.alpha_composite(wmk, (30, TH - wmk.height - 24))
    rgb = im.convert("RGB")
    q = 90
    while True:
        rgb.save(out_path, "JPEG", quality=q, optimize=True)
        if os.path.getsize(out_path) < 1_900_000 or q <= 60: break
        q -= 6
    return out_path
'''

# ======================================================================
# القسم: youtube
# ======================================================================
_SRC['youtube'] = r'''# -*- coding: utf-8 -*-
"""يوتيوب: مصادقة (refresh token) + رفع مجدول (resumable مع استئناف) + صورة مصغرة + قراءة التعليقات."""
import json, os, time
import requests
from util import log, env, http, HTTPFail, UA

TOKEN_URL = os.environ.get("YT_TOKEN_URL", "https://oauth2.googleapis.com/token")
API = os.environ.get("YT_API", "https://www.googleapis.com/youtube/v3")
UPLOAD = os.environ.get("YT_UPLOAD", "https://www.googleapis.com/upload/youtube/v3")
CHUNK = 8 * 1024 * 1024    # لازم يكون من مضاعفات 256KB

class AuthDead(Exception):
    """التوكن ميت — لازم تجديد يدوي (يحصل فقط لو التطبيق Testing أو سحبت الصلاحية)."""

class YouTube:
    def __init__(self):
        self.cid = env("YT_CLIENT_ID"); self.secret = env("YT_CLIENT_SECRET"); self.refresh = env("YT_REFRESH_TOKEN")
        if not (self.cid and self.secret and self.refresh):
            raise AuthDead("أسرار يوتيوب ناقصة: YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN")
        self._tok = None; self._exp = 0

    def token(self, force=False):
        if self._tok and time.time() < self._exp - 120 and not force:
            return self._tok
        last = None
        for i in range(4):
            try:
                r = requests.post(TOKEN_URL, data={"client_id": self.cid, "client_secret": self.secret,
                                  "refresh_token": self.refresh, "grant_type": "refresh_token"}, timeout=30, headers={"User-Agent": UA})
            except requests.RequestException as e:
                last = e; time.sleep(2 * (i + 1)); continue
            if r.status_code == 200:
                j = r.json(); self._tok = j["access_token"]; self._exp = time.time() + int(j.get("expires_in", 3000))
                return self._tok
            body = r.text
            if r.status_code in (400, 401) and ("invalid_grant" in body or "unauthorized_client" in body or "invalid_client" in body):
                raise AuthDead("التوكن منتهي أو مسحوب (" + body[:160] + ") — اتبع خطوة تجديد التوكن في README (وتأكد التطبيق In production)")
            last = HTTPFail(r.status_code, body, TOKEN_URL)
            if r.status_code in (429, 500, 502, 503): time.sleep(2 * (i + 1)); continue
            raise last
        raise last if last else RuntimeError("token refresh failed")

    def _h(self, extra=None):
        h = {"Authorization": f"Bearer {self.token()}", "User-Agent": UA}
        if extra: h.update(extra)
        return h

    def api(self, method, path, **kw):
        for attempt in range(2):
            try:
                return http(method, f"{API}/{path}", headers=self._h(kw.pop("headers", None)), **kw)
            except HTTPFail as e:
                if e.status == 401 and attempt == 0:
                    self.token(force=True); continue
                raise

    # ---------- قناة / تعليقات ----------
    def channel_info(self):
        r = self.api("GET", "channels", params={"part": "id,snippet,statistics", "mine": "true"}, tries=3)
        items = r.json().get("items", [])
        if not items:
            raise RuntimeError("لا توجد قناة مرتبطة بهذا الحساب")
        return items[0]

    def recent_comments(self, channel_id, limit=100):
        try:
            r = self.api("GET", "commentThreads", params={"part": "snippet", "allThreadsRelatedToChannelId": channel_id,
                         "maxResults": min(limit, 100), "order": "time", "textFormat": "plainText"}, tries=2)
            out = []
            for it in r.json().get("items", []):
                s = it["snippet"]["topLevelComment"]["snippet"]
                out.append({"id": it["id"], "text": s.get("textDisplay", ""), "likes": s.get("likeCount", 0)})
            return out
        except Exception as e:  # noqa
            log("[yt] تعذر قراءة التعليقات (غير ضروري):", str(e)[:120])
            return []

    # ---------- الرفع ----------
    def _session(self, meta, size):
        h = self._h({"Content-Type": "application/json; charset=UTF-8", "X-Upload-Content-Length": str(size),
                     "X-Upload-Content-Type": "video/mp4"})
        r = http("POST", f"{UPLOAD}/videos", params={"uploadType": "resumable", "part": "snippet,status", "notifySubscribers": "true"},
                 headers=h, data=json.dumps(meta).encode("utf-8"), tries=4, ok=(200,))
        loc = r.headers.get("Location")
        if not loc: raise RuntimeError("لم يرجع رابط جلسة الرفع")
        return loc

    @staticmethod
    def _range_sent(resp):
        rg = resp.headers.get("Range")
        if not rg: return 0
        return int(rg.split("-")[-1]) + 1

    def _query(self, loc, size):
        r = requests.put(loc, headers={"Content-Length": "0", "Content-Range": f"bytes */{size}"}, timeout=60)
        if r.status_code in (200, 201): return "done", r
        if r.status_code == 308: return "partial", self._range_sent(r)
        return "error", r

    def upload(self, path, meta):
        size = os.path.getsize(path)
        loc = self._session(meta, size)
        sent = 0; fails = 0
        with open(path, "rb") as f:
            while True:
                f.seek(sent); data = f.read(CHUNK)
                end = sent + len(data) - 1
                hdr = {"Content-Length": str(len(data)), "Content-Range": f"bytes {sent}-{end}/{size}", "Content-Type": "video/mp4"}
                try:
                    r = requests.put(loc, data=data, headers=hdr, timeout=600)
                except requests.RequestException as e:
                    fails += 1
                    if fails > 8: raise RuntimeError("انقطاع متكرر أثناء الرفع: " + str(e)[:100])
                    time.sleep(min(5 * fails, 40))
                    st, v = self._query(loc, size)
                    if st == "done": return v.json()
                    if st == "partial": sent = v
                    continue
                if r.status_code in (200, 201):
                    return r.json()
                if r.status_code == 308:
                    fails = 0; sent = self._range_sent(r)
                    log(f"[yt] رُفع {sent*100//size}%")
                    continue
                if r.status_code in (500, 502, 503, 504):
                    fails += 1
                    if fails > 8: raise HTTPFail(r.status_code, r.text, "upload")
                    time.sleep(min(5 * fails, 40))
                    st, v = self._query(loc, size)
                    if st == "done": return v.json()
                    if st == "partial": sent = v
                    continue
                if r.status_code == 401:
                    raise AuthDead("رُفض الرفع (401)")
                raise HTTPFail(r.status_code, r.text, "upload")

    def set_thumbnail(self, video_id, jpg):
        """غير حرج: لو فشل يكمل النشر عادي."""
        try:
            with open(jpg, "rb") as f: data = f.read()
            for i in range(3):
                try:
                    http("POST", f"{UPLOAD}/thumbnails/set", params={"videoId": video_id, "uploadType": "media"},
                         headers=self._h({"Content-Type": "image/jpeg"}), data=data, tries=2)
                    return True
                except HTTPFail as e:
                    if e.status in (400, 403):
                        log("[yt] الصورة المصغرة مرفوضة (غالباً القناة غير موثقة بالهاتف):", str(e)[:140]); return False
                    time.sleep(3 * (i + 1))
        except Exception as e:  # noqa
            log("[yt] فشل رفع الصورة المصغرة (لن يمنع النشر):", str(e)[:120])
        return False

    def verify(self, video_id):
        try:
            r = self.api("GET", "videos", params={"part": "status", "id": video_id}, tries=2)
            it = r.json().get("items", [{}])[0]
            return it.get("status", {})
        except Exception as e:  # noqa
            log("[yt] تعذر التحقق من الحالة:", str(e)[:100]); return {}
'''

# ======================================================================
# القسم: schedule
# ======================================================================
_SRC['schedule'] = r'''# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, timezone
from config import SLOTS, TZ_HOURS, MIN_LEAD_MIN, LOOKAHEAD_HOURS

TZ = timezone(timedelta(hours=TZ_HOURS))

def slot_key(dt):
    return dt.astimezone(TZ).strftime("%Y-%m-%dT%H:%M")

def next_slot(now_utc, taken, lookahead_hours=None, slots=None):
    """أقرب موعد نشر فاضي بين (الآن + المدة الدنيا) و(الآن + نافذة البحث). None لو ما في."""
    slots = SLOTS if slots is None else slots
    la = LOOKAHEAD_HOURS if lookahead_hours is None else lookahead_hours
    earliest = now_utc + timedelta(minutes=MIN_LEAD_MIN)
    latest = now_utc + timedelta(hours=la)
    day0 = now_utc.astimezone(TZ).date()
    for d in range(0, int(la // 24) + 3):
        day = day0 + timedelta(days=d)
        if day.weekday() not in slots:
            continue
        h, m = slots[day.weekday()]
        dt = datetime(day.year, day.month, day.day, h, m, tzinfo=TZ)
        if dt < earliest or dt > latest:
            continue
        if slot_key(dt) in taken:
            continue
        return dt
    return None

def to_rfc3339_utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
'''

# ======================================================================
# القسم: state
# ======================================================================
_SRC['state'] = r'''# -*- coding: utf-8 -*-
import json, os, tempfile
from datetime import datetime, timezone
from config import STATE_FILE

DEFAULT = {"version": 1, "scheduled": {}, "history": [], "topics": [], "used_comments": [], "last_run": None, "music_index": 0}

def load(path=None):
    try:
        with open(path or STATE_FILE, "r", encoding="utf-8") as f:
            s = json.load(f)
        for k, v in DEFAULT.items():
            s.setdefault(k, json.loads(json.dumps(v)))
        return s
    except Exception:
        return json.loads(json.dumps(DEFAULT))

def save(s, path=None):
    path = path or STATE_FILE
    s["last_run"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    s["history"] = s["history"][-120:]
    s["topics"] = s["topics"][-150:]
    s["used_comments"] = s["used_comments"][-400:]
    # نحتفظ بالمواعيد القديمة قليلاً فقط
    keys = sorted(s["scheduled"].keys())
    for k in keys[:-40]:
        s["scheduled"].pop(k, None)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
'''

# ======================================================================
# القسم: content
# ======================================================================
_SRC['content'] = r'''# -*- coding: utf-8 -*-
"""اختيار الموضوع (مشاريع / ماذا لو / طلبات التعليقات) + كتابة السكربت + العنوان والوصف."""
import re, random, urllib.parse
import xml.etree.ElementTree as ET
from config import BAN_WORDS, MIN_WORDS, MAX_WORDS, CHANNEL_NAME, SHORT_MIN_WORDS, SHORT_MAX_WORDS
from util import log, http
import gemini, anim

SYSTEM = (
    "أنت محرر ومعد برامج لقناة يوتيوب عربية اسمها «بوصلة» تشرح المشاريع الكبرى حول العالم والنهضة العمرانية والاقتصادية "
    "وتقدم فيديوهات «ماذا لو» العلمية. أسلوبك مثل برامج الشرح الإخبارية السريعة: جمل قصيرة، معلومات مكثفة، حماس تدريجي. "
    "قاعدة صارمة: لا سياسة ولا أحزاب ولا نزاعات ولا حروب ولا رموز سياسية ولا جدل ديني. التركيز على الاقتصاد والهندسة والمدن والطاقة والعلوم. "
    "الدقة أهم من الإثارة: لا تخترع أرقاماً أو أسماء أو تواريخ؛ إذا لم تكن متأكداً استخدم صياغة تقريبية أو اذكر أنه تقدير."
)

_AR_NORM = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"})
_STOP = set("في من على الى عن ما ماذا لو هل كيف لماذا هذا هذه ذلك التي الذي مع كل او ان بعد قبل عند".split())

def norm_tokens(s):
    s = re.sub(r"[\u064B-\u0652ـ]", "", s).translate(_AR_NORM).lower()
    return {w for w in re.findall(r"[\w]+", s) if w not in _STOP and len(w) > 1}

def too_similar(title, previous, thr=0.45):
    a = norm_tokens(title)
    if not a: return False
    for p in previous:
        b = norm_tokens(p)
        if b and len(a & b) / len(a | b) >= thr:
            return True
    return False

def banned_hits(text):
    t = re.sub(r"[\u064B-\u0652]", "", text) + " "
    return [w.strip() for w in BAN_WORDS if w in t]

# ---------------- إشارات الطلب ----------------
def autosuggest(seed, hl="ar"):
    try:
        r = http("GET", "https://suggestqueries.google.com/complete/search",
                 params={"client": "firefox", "ds": "yt", "hl": hl, "q": seed}, tries=2, timeout=15)
        j = r.json()
        return [s for s in j[1] if isinstance(s, str)][:10]
    except Exception as e:  # noqa
        log("[signals] autosuggest فشل:", seed, str(e)[:60]); return []

def news_titles(q, hl="ar", gl="SA", ceid="SA:ar", limit=10):
    try:
        url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(q) + f"&hl={hl}&gl={gl}&ceid={ceid}"
        r = http("GET", url, tries=2, timeout=20)
        root = ET.fromstring(r.content)
        out = []
        for it in root.iter("item"):
            t = (it.findtext("title") or "").strip()
            if t and not banned_hits(t): out.append(t)
            if len(out) >= limit: break
        return out
    except Exception as e:  # noqa
        log("[signals] news فشل:", q, str(e)[:60]); return []

def gather_signals(kind, yt=None, channel_id=None, state=None):
    sig = {"headlines": [], "suggest": [], "comments": []}
    if kind == "projects":
        for q in ("مشروع عملاق", "أكبر مشروع بنية تحتية", "مدينة جديدة مشروع ضخم", "مشروع طاقة ضخم"):
            sig["headlines"] += news_titles(q)
        for q, hl, gl, ce in (("megaproject", "en-US", "US", "US:en"), ("world's largest infrastructure project", "en-US", "US", "US:en"),
                              ("giga project new city", "en-US", "US", "US:en")):
            sig["headlines"] += news_titles(q, hl, gl, ce, 8)
        for s in ("أكبر مشروع في", "أضخم مشروع في العالم", "مشروع جديد في"):
            sig["suggest"] += autosuggest(s)
    elif kind == "whatif":
        for s in ("ماذا لو", "ماذا لو اختفى", "ماذا لو جف", "ماذا لو تحولت", "ماذا لو بنينا", "ماذا لو غطت"):
            sig["suggest"] += autosuggest(s)
    elif kind == "fact":
        for q in ("حقائق مدهشة عن", "هل تعلم أن", "أغرب مشروع في", "كيف يعمل"):
            sig["suggest"] += autosuggest(q)
    elif kind == "requests" and yt and channel_id:
        used = set((state or {}).get("used_comments", []))
        kw = ("ماذا لو", "اتمنى", "أتمنى", "ممكن", "تكلم", "تكلموا", "سوي", "سوّ", "فيديو عن", "اريد", "أريد", "حلقة عن", "موضوع")
        for c in yt.recent_comments(channel_id):
            if c["id"] in used or banned_hits(c["text"]) or len(c["text"]) > 220: continue
            if any(k in c["text"] for k in kw):
                sig["comments"].append(c)
    sig["headlines"] = list(dict.fromkeys(sig["headlines"]))[:30]
    sig["suggest"] = list(dict.fromkeys(sig["suggest"]))[:30]
    return sig

# ---------------- اختيار الموضوع ----------------
def choose_topic(kind, sig, state):
    prev = state.get("topics", [])[-40:]
    if kind == "requests" and not sig["comments"]:
        kind = "projects"
    hint = {
        "projects": "اختر مشروعاً أو نهضة عمرانية/اقتصادية/هندسية حول العالم لها طلب عالٍ (جديد أو مثير للفضول). يفضل أن يكون مبنياً على العناوين المرفقة.",
        "whatif": "اختر سؤال «ماذا لو» علمي مثير للفضول وله إجابة علمية مبنية على أرقام تقريبية (جغرافيا، طاقة، بيئة، اقتصاد، فضاء…) وليس سياسياً.",
        "requests": "اختر أنسب طلب من تعليقات المشاهدين وحوّله لموضوع فيديو غير سياسي.",
        "fact": "اختر حقيقة اقتصادية أو علمية أو عمرانية مدهشة قصيرة تصلح لشورت من ٣٠ ثانية.",
    }[kind]
    ctx = ""
    if sig["headlines"]: ctx += "عناوين أخبار حديثة:\n- " + "\n- ".join(sig["headlines"]) + "\n\n"
    if sig["suggest"]: ctx += "اقتراحات بحث شائعة (طلب حقيقي):\n- " + "\n- ".join(sig["suggest"]) + "\n\n"
    if sig["comments"]: ctx += "تعليقات المشاهدين:\n" + "\n".join(f"[{i}] {c['text']}" for i, c in enumerate(sig["comments"][:40])) + "\n\n"
    prompt = (f"{hint}\n\n{ctx}مواضيع سابقة يجب عدم تكرارها:\n- " + ("\n- ".join(prev) if prev else "لا يوجد") +
              "\n\nأعد JSON فقط بهذا الشكل:\n"
              '{"topic":"عنوان الموضوع بالعربي","kind":"projects أو whatif","comment_index":null أو رقم التعليق,'
              '"grounding":["العناوين/الحقائق الموجودة أعلاه التي يعتمد عليها الفيديو"],"why":"سبب الطلب العالي في جملة"}')
    def val(o):
        if not isinstance(o, dict) or not str(o.get("topic", "")).strip(): return "topic مفقود"
        t = o["topic"]
        h = banned_hits(t)
        if h: return f"الموضوع فيه كلمات سياسية ممنوعة: {h}"
        if too_similar(t, prev): return "الموضوع مكرر أو قريب جداً من موضوع سابق، اختر موضوعاً مختلفاً تماماً"
        return None
    o = gemini.generate_json(prompt, val, SYSTEM, temperature=0.95, max_tokens=3000)
    o["kind"] = "whatif" if (str(o.get("kind", "")).startswith("what") or kind == "whatif") else ("fact" if kind == "fact" else "projects")
    ci = o.get("comment_index")
    o["comment_id"] = sig["comments"][ci]["id"] if isinstance(ci, int) and 0 <= ci < len(sig["comments"]) else None
    if not isinstance(o.get("grounding"), list): o["grounding"] = []
    return o

# ---------------- السكربت ----------------
INFO_SHAPES = (
    '{"type":"number","value":"450","unit":"مليار دولار","label":"التكلفة التقديرية"}  |  '
    '{"type":"bars","title":"...","items":[{"label":"...","value":120},{"label":"...","value":80}]}  |  '
    '{"type":"timeline","title":"...","events":[{"year":"2017","text":"..."},{"year":"2021","text":"..."},{"year":"2030","text":"..."}]}  |  '
    '{"type":"compare","left":{"title":"...","items":["...","..."]},"right":{"title":"...","items":["...","..."]}}  |  '
    '{"type":"list","title":"...","items":["...","...","..."]}  |  '
    '{"type":"kinetic","words":["كلمة","كلمتان"]}')

SHAPE = ('{"title": "عنوان جذاب ≤ 70 حرفاً، الكلمة المفتاحية في أوله، فضول بدون كذب",'
         ' "thumb_text": "٢ إلى ٤ كلمات قوية للصورة المصغرة",'
         ' "thumb_prompt": "English prompt for a striking thumbnail background image (no text)",'
         ' "thumb_query": "2-4 English words",'
         ' "description_intro": "جملتان أو ثلاث تلخص الفيديو وفيها الكلمات المفتاحية",'
         ' "keywords": ["١٢ كلمة مفتاحية عربية وإنجليزية"], "hashtags": ["#وسم1", "#وسم2", "#وسم3"],'
         ' "sections": [{"title": "عنوان الفصل (≤ 40 حرفاً)", "scenes": [SCENE]}]}')
SCENE = ('{"narration": "جملة أو جملتان بالفصحى المبسطة، الأرقام حروفاً", "visual": "image أو info أو stock",'
         ' "image_prompt": "English: concrete picture that literally shows what the sentence says (if visual=image)",'
         ' "info": INFO أو null, "search": "English 2-4 words (fallback)", "text": "نص قصير ≤ ٣ كلمات أو فارغ"}')

VISUAL_RULES = (
    "قواعد الصور (مهمة جداً — المشاهد يمل من لقطات لا تناسب الكلام):\n"
    "• visual=image: صورة يولدها الذكاء الاصطناعي. image_prompt بالإنجليزية يصف بدقة ما يقوله التعليق حرفياً (مكان، أشياء، حدث، زاوية كاميرا)، "
    "بدون نصوص أو أسماء أشخاص أو شعارات. حوالي نصف المشاهد.\n"
    "• visual=info: إنفوجرافيك متحرك للأرقام والمقارنات والمراحل. استخدمه كلما ذُكرت أرقام أو مقارنة أو ترتيب زمني أو قائمة أسباب، "
    "ومرة كل ١٥-٢٠ ثانية تقريباً لكسر الملل. أنواع info (استخدم هذه الأشكال بالضبط): " + INFO_SHAPES + ". "
    "الأرقام داخل info بالأرقام العادية، ويجب أن تطابق ما في التعليق ولا تخترع أرقاماً غير موجودة في المصادر؛ وإن لم تتوفر أرقام فاستخدم list أو kinetic.\n"
    "• visual=stock: لقطات ستوك عامة جداً فقط (حتى ١٥٪ من المشاهد) وحقل search بالإنجليزية.\n"
    "• حقل search دائماً موجود (بديل احتياطي)، وحقل info يكون null إن لم يكن المشهد info.\n")

def _count_visuals(scenes):
    n = {"image": 0, "info": 0, "stock": 0}; bad = 0
    for x in scenes:
        v = x.get("visual")
        if v == "info":
            if anim.validate_info(x.get("info")) is None: n["info"] += 1
            else: bad += 1
        elif v == "image":
            if len(str(x.get("image_prompt", "")).strip()) >= 20: n["image"] += 1
            else: bad += 1
        else:
            n["stock"] += 1
    return n, bad

def _validate_script(o, kind):
    try:
        secs = o["sections"]
        if not isinstance(secs, list) or not (5 <= len(secs) <= 10): return "عدد الفصول لازم بين ٥ و١٠"
        words = 0; n = 0; allsc = []
        for si, s in enumerate(secs):
            if not str(s.get("title", "")).strip(): return f"الفصل {si} بدون عنوان"
            sc = s.get("scenes")
            if not isinstance(sc, list) or not sc: return f"الفصل {si} بدون مشاهد"
            for j, x in enumerate(sc):
                nar = str(x.get("narration", "")).strip()
                if not nar: return f"مشهد فارغ في الفصل {si}"
                w = len(nar.split())
                if w > 38: return f"مشهد طويل ({w} كلمة) في الفصل {si}؛ قسّمه لمشهدين"
                if re.search(r"[A-Za-z]{3,}", nar): return f"حروف لاتينية داخل النص المنطوق في الفصل {si}؛ اكتب الأسماء بالعربي"
                if not re.search(r"[A-Za-z]", str(x.get("search", ""))): return f"حقل search لازم إنجليزي في الفصل {si}"
                words += w; n += 1; allsc.append(x)
        if not (MIN_WORDS <= words <= MAX_WORDS): return f"عدد كلمات التعليق {words}؛ المطلوب بين {MIN_WORDS} و{MAX_WORDS}"
        if n < 45: return f"عدد المشاهد {n} قليل؛ المطلوب ٥٥ إلى ١٠٠ مشهد"
        cnt, bad = _count_visuals(allsc)
        if cnt["image"] < 16: return f"عدد مشاهد image الصالحة {cnt['image']}؛ المطلوب ١٦ على الأقل مع image_prompt مفصل بالإنجليزية"
        if cnt["info"] < 8: return f"عدد مشاهد info الصالحة {cnt['info']}؛ المطلوب ٨ على الأقل بالأشكال المحددة بالضبط (راجع الأخطاء: {bad} مشهد غير صالح)"
        if cnt["stock"] > n * 0.25: return "مشاهد stock كثيرة؛ الحد ١٥٪"
        t = str(o.get("title", "")).strip()
        if not (12 <= len(t) <= 80): return "طول العنوان لازم بين ١٢ و٧٠ حرفاً"
        tt = str(o.get("thumb_text", "")).strip()
        if not (3 <= len(tt) <= 34): return "thumb_text لازم ٢-٤ كلمات قصيرة"
        if not isinstance(o.get("keywords"), list) or len(o["keywords"]) < 6: return "keywords أقل من ٦"
        full = " ".join([t, tt] + [x["narration"] for x in allsc])
        h = banned_hits(full)
        if h: return f"كلمات سياسية/نزاعات ممنوعة وردت: {h}؛ أعد الصياغة بدونها"
        return None
    except Exception as e:  # noqa
        return f"بنية JSON غير صحيحة: {e}"

def write_script(topic, kind):
    ground = "\n".join("- " + g for g in topic.get("grounding", [])[:12]) or "لا توجد مصادر مرفقة؛ اعتمد فقط على معلومات عامة موثوقة جداً."
    if kind == "whatif":
        style = ("هذا فيديو «ماذا لو»: ابدأ بسؤال صادم، ثم اشرح خطوة بخطوة ماذا سيحدث (خلال ساعات، أيام، سنوات) "
                 "بأرقام تقريبية مع كلمة «تقريباً»، ثم الخلاصة. وضّح أنه سيناريو افتراضي.")
    else:
        style = ("هذا فيديو عن مشروع/نهضة اقتصادية: ابدأ بحقيقة تشد الانتباه، ثم ما هو المشروع، لماذا بُني، الأرقام والتحديات، "
                 "الأثر الاقتصادي، ثم المستقبل. اعتمد على المصادر المرفقة فقط للأرقام الدقيقة، وغير ذلك قدّره بحذر.")
    prompt = (f"اكتب سكربت فيديو مدته ٦ إلى ٩ دقائق عن: «{topic['topic']}».\n{style}\n\n"
              f"المصادر/العناوين المتاحة:\n{ground}\n\n"
              "القواعد:\n"
              "١) بين ٩٠٠ و١١٥٠ كلمة تعليق إجمالاً، موزعة على ٦ إلى ٨ فصول و٦٠ إلى ٩٠ مشهداً.\n"
              "٢) كل مشهد جملة أو جملتان (≤ ٢٨ كلمة)، وجمل قصيرة بفواصل واضحة (،) لأن المعلق يتوقف عندها.\n"
              "٣) اكتب كل الأرقام والسنوات والنسب حروفاً بالعربي في التعليق (مثال: ألفان وثلاثون، اثنا عشر بالمئة). ممنوع الأرقام داخل narration.\n"
              "٤) أسماء الأماكن والشركات بالعربي فقط داخل التعليق (لا حروف لاتينية).\n"
              "٥) المشهد الأول خطاف قوي يثير الفضول في أقل من ١٠ ثواني (سؤال أو حقيقة صادمة)، وكل ٢٠ ثانية تقريباً نقطة تشويق أو سؤال أو رقم جديد حتى لا يمل المشاهد. "
              "والمشهد الأخير: خلاصة + دعوة للاشتراك + سؤال يشجع على التعليق.\n"
              "٦) حقل text: رقم أو اسم مهم يظهر على الشاشة (٣ كلمات كحد أقصى) في بعض مشاهد image فقط، والباقي فارغ.\n"
              "٧) لا سياسة إطلاقاً. لا مبالغة ولا معلومات غير مؤكدة.\n\n"
              + VISUAL_RULES + "\n" +
              (("ملاحظة مهمة: " + topic["note"] + "\n\n") if topic.get("note") else "") +
              "أعد JSON فقط بهذا الشكل بالضبط (SCENE يتكرر لكل مشهد، INFO هو أحد الأشكال المذكورة):\n" + SHAPE + "\nحيث SCENE = " + SCENE)
    return gemini.generate_json(prompt, lambda o: _validate_script(o, kind), SYSTEM, temperature=0.8, max_tokens=20000, rounds=6)

def flatten(script):
    scenes = []
    for si, s in enumerate(script["sections"]):
        for x in s["scenes"]:
            scenes.append({"narration": x["narration"].strip(), "search": str(x.get("search", "")).strip(),
                           "text": str(x.get("text", "") or "").strip()[:40], "section": si,
                           "visual": x.get("visual") if x.get("visual") in ("image", "info", "stock") else "stock",
                           "image_prompt": str(x.get("image_prompt", "") or "").strip(),
                           "info": x.get("info") if isinstance(x.get("info"), dict) else None})
    return scenes

# ---------------- الشورت ----------------
SHORT_SHAPE = ('{"title": "عنوان ≤ 60 حرفاً يثير الفضول", "description_intro": "جملتان",'
               ' "keywords": ["١٠ كلمات مفتاحية"], "hashtags": ["#وسم1", "#وسم2", "#وسم3"],'
               ' "scenes": [SCENE]}')

def _validate_short(o):
    try:
        sc = o["scenes"]
        if not isinstance(sc, list) or not (9 <= len(sc) <= 18): return "عدد المشاهد لازم بين ٩ و١٨"
        words = 0
        for j, x in enumerate(sc):
            nar = str(x.get("narration", "")).strip()
            if not nar: return f"مشهد {j} فارغ"
            w = len(nar.split())
            if w > 16: return f"مشهد {j} طويل ({w} كلمة)؛ الحد ١٦ للشورت"
            if re.search(r"[A-Za-z]{3,}", nar): return f"حروف لاتينية في مشهد {j}"
            if not re.search(r"[A-Za-z]", str(x.get("search", ""))): return f"search إنجليزي مفقود في مشهد {j}"
            words += w
        if not (SHORT_MIN_WORDS <= words <= SHORT_MAX_WORDS): return f"عدد الكلمات {words}؛ المطلوب بين {SHORT_MIN_WORDS} و{SHORT_MAX_WORDS}"
        if len(str(sc[0]["narration"]).split()) > 10: return "المشهد الأول (الخطاف) لازم ≤ ١٠ كلمات"
        cnt, bad = _count_visuals(sc)
        if cnt["image"] < 5: return f"مشاهد image الصالحة {cnt['image']}؛ المطلوب ٥ على الأقل"
        if cnt["info"] < 2: return f"مشاهد info الصالحة {cnt['info']}؛ المطلوب ٢ على الأقل بالأشكال المحددة"
        t = str(o.get("title", "")).strip()
        if not (10 <= len(t) <= 70): return "طول العنوان لازم بين ١٠ و٦٠ حرفاً"
        if not isinstance(o.get("keywords"), list) or len(o["keywords"]) < 5: return "keywords أقل من ٥"
        full = t + " " + " ".join(x["narration"] for x in sc)
        h = banned_hits(full)
        if h: return f"كلمات سياسية ممنوعة: {h}"
        return None
    except Exception as e:  # noqa
        return f"بنية JSON غير صحيحة: {e}"

def write_short(topic, kind):
    ground = "\n".join("- " + g for g in topic.get("grounding", [])[:8]) or "لا توجد مصادر؛ معلومات عامة موثوقة جداً فقط."
    style = {"whatif": "فيديو «ماذا لو» سريع: سؤال صادم ثم نتيجتين أو ثلاث مدهشة بأرقام تقريبية.",
             "projects": "حقيقة مدهشة عن مشروع أو مدينة أو إنجاز هندسي حول العالم بأرقام واضحة.",
             "fact": "حقيقة اقتصادية/علمية/عمرانية مدهشة معلومة قد لا يعرفها المشاهد، مع التفسير بسرعة."}.get(kind, "")
    prompt = (f"اكتب سكربت فيديو شورت عمودي مدته ٢٥ إلى ٤٠ ثانية عن: «{topic['topic']}».\n{style}\n\nالمصادر:\n{ground}\n\n"
              "القواعد:\n"
              "١) من ٦٥ إلى ٩٠ كلمة تعليق إجمالاً، موزعة على ١٠ إلى ١٥ مشهداً، كل مشهد ≤ ١٤ كلمة.\n"
              "٢) المشهد الأول خطاف صادم ≤ ٩ كلمات يبدأ بسؤال أو حقيقة غريبة، ولا مقدمات ولا تحيات.\n"
              "٣) إيقاع سريع، جمل قصيرة بفواصل، وكل ٣ ثوانٍ معلومة أو تحول جديد. والمشهد الأخير: جملة ختامية قصيرة تدعو للمتابعة وتحفز التعليق.\n"
              "٤) الأرقام حروفاً في narration، والأسماء بالعربي بدون حروف لاتينية.\n"
              "٥) لا سياسة إطلاقاً ولا معلومات غير مؤكدة (استخدم «تقريباً» عند التقدير).\n"
              "٦) المشاهد: ٥ على الأقل visual=image (image_prompt إنجليزي مفصل بتكوين عمودي)، و٢ على الأقل visual=info (يفضل number أو list أو kinetic أو bars)، والستوك نادر.\n\n"
              + VISUAL_RULES + "\n" +
              (("ملاحظة مهمة: " + topic["note"] + "\n\n") if topic.get("note") else "") +
              "أعد JSON فقط بهذا الشكل (SCENE يتكرر، INFO أحد الأشكال):\n" + SHORT_SHAPE + "\nحيث SCENE = " + SCENE)
    return gemini.generate_json(prompt, _validate_short, SYSTEM, temperature=0.85, max_tokens=9000, rounds=6)

def flatten_short(script):
    return flatten({"sections": [{"scenes": script["scenes"]}]})

def build_description_short(script):
    kws = [k for k in script.get("keywords", []) if isinstance(k, str)][:10]
    tags = [h if h.startswith("#") else "#" + h.replace(" ", "_") for h in script.get("hashtags", [])][:3]
    parts = [script["description_intro"].strip(), "",
             f"🧭 {CHANNEL_NAME}: المشاريع الكبرى والاقتصاد والعالم بأسلوب سريع.",
             "👍 تابع القناة واكتب في التعليقات فكرة الشورت القادم.", "",
             "الكلمات المفتاحية: " + "، ".join(kws), "", " ".join(tags + ["#Shorts"])]
    return re.sub(r"[<>]", "", "\n".join(parts))[:4500]

# ---------------- العنوان والوصف ----------------
def _ts(sec):
    sec = int(sec); m, s = divmod(sec, 60); h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def chapters(script, scenes):
    starts = []
    for si, s in enumerate(script["sections"]):
        first = next((sc for sc in scenes if sc["section"] == si), None)
        if first: starts.append((0.0 if not starts else first["start"], s["title"].strip()))
    out = []
    for t, title in starts:
        if out and t - out[-1][0] < 10: continue
        out.append((t, title))
    return out if len(out) >= 3 else []

def build_description(script, scenes, credits=()):
    ch = chapters(script, scenes)
    parts = [script["description_intro"].strip(), ""]
    if ch:
        parts.append("⏱ فصول الفيديو:")
        parts += [f"{_ts(t)} {title}" for t, title in ch]
        parts.append("")
    parts += [f"🧭 قناة {CHANNEL_NAME}: نشرح المشاريع الكبرى والاقتصاد والعالم بأسلوب سريع وواضح.",
              "👍 إذا أعجبك الفيديو اشترك وفعّل الجرس، واكتب في التعليقات فكرة الفيديو القادم.",
              "ℹ️ المعلومات والأرقام تقريبية وللتثقيف، وسيناريوهات «ماذا لو» افتراضية.", ""]
    if credits:
        parts.append("📷 مصادر بعض اللقطات: " + "، ".join(credits[:8])); parts.append("")
    kws = [k for k in script["keywords"] if isinstance(k, str)][:12]
    if kws: parts.append("الكلمات المفتاحية: " + "، ".join(kws)); parts.append("")
    tags = [h if h.startswith("#") else "#" + h.replace(" ", "_") for h in script.get("hashtags", [])][:3]
    parts.append(" ".join(tags))
    d = "\n".join(parts)
    d = re.sub(r"[<>]", "", d)
    return d[:4800]

def clean_title(t):
    t = re.sub(r"[<>]", "", t).strip().strip('"«»')
    return t[:95]

def tags_for(script):
    out, total = [], 0
    for k in script["keywords"]:
        k = re.sub(r"[<>,\"]", "", str(k)).strip()
        if not k or len(k) > 40: continue
        if total + len(k) + 3 > 470: break
        out.append(k); total += len(k) + 3
    return out
'''

# ======================================================================
# القسم: health
# ======================================================================
_SRC['health'] = r'''# -*- coding: utf-8 -*-
from util import summary, log

def run_health():
    rows = []; critical = []
    def add(name, ok, msg, crit=True):
        rows.append((name, ok, msg))
        log(("✅" if ok else "❌"), name, "—", msg)
        if not ok and crit: critical.append(name)

    # Gemini
    try:
        import gemini
        o = gemini.generate_json('أعد JSON فقط: {"ok": true}', lambda x: None if isinstance(x, dict) else "no", rounds=2, max_tokens=200)
        add("Gemini", True, f"يعمل (أول موديل: {gemini.list_models(gemini._keys()[0])[0]})")
    except Exception as e:
        add("Gemini", False, str(e)[:200])

    # مصادر اللقطات
    from stock import Stock
    st = Stock(); any_ok = False
    for s in st.sources():
        if s.disabled:
            add(f"ستوك/{s.name}", False, f"معطل: {s.reason}", crit=False); continue
        ok, msg = s.check()
        add(f"ستوك/{s.name}", ok, msg + ("" if ok else f" | {s.reason}"), crit=False)
        any_ok = any_ok or ok
    if not any_ok:
        add("ستوك (لا مصدر شغال)", False, "كل المصادر فشلت", crit=True)

    # توليد الصور (غير حرج)
    try:
        from imagegen import ImageGen
        g = ImageGen(1)
        p = g.generate("a simple blue sphere on a white table, studio photo", 1280, 720, seed=1, tries=2)
        add("توليد الصور (Pollinations)", bool(p), "يعمل" if p else "لم يرجع صورة — الكود يتحول للستوك والإنفوجرافيك", crit=False)
    except Exception as e:
        add("توليد الصور (Pollinations)", False, str(e)[:160], crit=False)

    # الصوت
    try:
        import tts
        add("الصوت (edge-tts)", True, tts.pick_voice())
    except Exception as e:
        add("الصوت (edge-tts)", False, str(e)[:200])

    # يوتيوب
    try:
        from youtube import YouTube
        yt = YouTube(); info = yt.channel_info()
        add("يوتيوب (التوكن)", True, "القناة: " + info.get("snippet", {}).get("title", "?"))
    except Exception as e:
        add("يوتيوب (التوكن)", False, str(e)[:260])

    md = "### فحص بوصلة\n| الفحص | الحالة | التفاصيل |\n|---|---|---|\n" + "\n".join(f"| {n} | {'✅' if ok else '❌'} | {m.replace('|','/')} |" for n, ok, m in rows)
    summary(md)
    if critical:
        print("\nحرج:", critical)
        return 1
    print("\nكل شيء سليم ✅")
    return 0

'''

# ======================================================================
# القسم: pipeline
# ======================================================================
_SRC['pipeline'] = r'''# -*- coding: utf-8 -*-
"""بوصلة — خط إنتاج: موضوع -> سكربت -> صوت -> صور مولدة + إنفوجرافيك -> موسيقى -> رفع مجدول (فيديو طويل + شورت يومي)."""
import os, shutil, sys, time, traceback
from datetime import datetime, timezone

import config
from config import (WORK, TOPIC_CYCLE, MIN_SEC, HARD_MAX_SEC, YT_CATEGORY, YT_LANG, VOICES, VOICES_SHORT, IMG_MAX_LONG, IMG_MAX_SHORT,
                    SHORT_SLOTS, SHORT_LOOKAHEAD_HOURS, TOPIC_CYCLE_SHORT, SHORT_W, SHORT_H, SHORT_MIN_SEC, SHORT_MAX_SEC, STATE_SHORT_FILE)
from util import log, run, probe_duration, summary
import state as st
import schedule as sch
import content, tts, visuals, music, thumbnail
from stock import Stock
from imagegen import ImageGen
from youtube import YouTube, AuthDead

def mux(video, audio, out):
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", out], timeout=900)

def _visual_report(stock, imgen):
    return [f"الصور المولدة: {imgen.count} " + ("(معطلة: " + imgen.reason + ")" if imgen.disabled else "")] + stock.report()

# ======================= الفيديو الطويل =======================
def pipeline():
    t0 = time.time()
    S = st.load()
    yt = YouTube()
    info = yt.channel_info()
    channel_id = info["id"]
    log("القناة:", info.get("snippet", {}).get("title"), "| id", channel_id)

    now = datetime.now(timezone.utc)
    slot = sch.next_slot(now, set(S["scheduled"].keys()))
    if slot is None:
        log("لا يوجد موعد نشر فاضي ضمن النافذة الحالية — لا شيء للعمل الآن ✅")
        summary("✅ لا يوجد موعد نشر فاضي الآن (أو الفيديو القادم مجدول مسبقاً).")
        st.save(S); return 0
    log("موعد النشر المستهدف:", sch.slot_key(slot), "(توقيت الرياض)")

    shutil.rmtree(WORK, ignore_errors=True); os.makedirs(WORK, exist_ok=True)
    kind = TOPIC_CYCLE[len(S["history"]) % len(TOPIC_CYCLE)]
    log("نوع الفيديو:", kind)
    sig = content.gather_signals(kind, yt, channel_id, S)
    topic = content.choose_topic(kind, sig, S)
    kind = topic["kind"]
    log("الموضوع:", topic["topic"])

    scenes = None; script = None; total = 0.0
    voice_wav = os.path.join(WORK, "voice.wav")
    for attempt in range(3):
        script = content.write_script(topic, kind)
        scenes = content.flatten(script)
        total = tts.build_voice(scenes, voice_wav, VOICES)
        if MIN_SEC - 25 <= total <= HARD_MAX_SEC:
            break
        log(f"مدة الفيديو {total:.0f}s خارج المطلوب — إعادة كتابة ({attempt+1}/3)")
        topic["note"] = ("النسخة السابقة كانت قصيرة جداً؛ زد التفاصيل والمشاهد." if total < MIN_SEC - 25
                         else "النسخة السابقة كانت طويلة جداً؛ اختصر وقلل عدد الكلمات.")
    else:
        log("⚠️ المدة خارج النطاق بعد ٣ محاولات — سنكمل بما لدينا")
    log(f"المدة النهائية للصوت: {total:.1f}s ({total/60:.1f} دقيقة)")

    stock = Stock(); imgen = ImageGen(IMG_MAX_LONG)
    video_silent = os.path.join(WORK, "video_silent.mp4")
    visuals.build_video(scenes, total, stock, video_silent, imgen=imgen)

    music_wav = os.path.join(WORK, "music.wav"); mixed = os.path.join(WORK, "mix.m4a")
    music.build_music(total, music_wav, S.get("music_index", 0))
    music.mix(voice_wav, music_wav, mixed, total)

    final = os.path.join(WORK, "final.mp4")
    mux(video_silent, mixed, final)
    dur = probe_duration(final)
    log(f"الفيديو النهائي {dur:.1f}s")
    if dur < 60 or abs(dur - total) > 3:
        raise RuntimeError(f"مدة الفيديو النهائي ({dur:.0f}s) لا تطابق الصوت ({total:.0f}s) — خلل في المونتاج")

    thumb = _make_thumb(script, topic, stock, imgen)
    title = content.clean_title(script["title"])
    desc = content.build_description(script, scenes, stock.credits)
    meta = {"snippet": {"title": title, "description": desc, "tags": content.tags_for(script),
                        "categoryId": YT_CATEGORY, "defaultLanguage": YT_LANG, "defaultAudioLanguage": YT_LANG},
            "status": {"privacyStatus": "private", "publishAt": sch.to_rfc3339_utc(slot),
                       "selfDeclaredMadeForKids": False, "embeddable": True, "publicStatsViewable": True}}
    log("رفع الفيديو… العنوان:", title)
    res = yt.upload(final, meta)
    vid = res["id"]
    log("تم الرفع ✅ id =", vid)
    if thumb:
        yt.set_thumbnail(vid, thumb)
    warn = _verify(yt, vid)

    S["scheduled"][sch.slot_key(slot)] = {"video_id": vid, "title": title, "kind": kind}
    S["history"].append({"slot": sch.slot_key(slot), "video_id": vid, "title": title, "kind": kind, "sec": round(dur)})
    S["topics"] += [topic["topic"], title]
    if topic.get("comment_id"): S["used_comments"].append(topic["comment_id"])
    S["music_index"] = S.get("music_index", 0) + 1
    st.save(S)
    mins = (time.time() - t0) / 60
    summary(f"### ✅ تمت جدولة فيديو طويل\n- **{title}**\n- الموعد: {sch.slot_key(slot)} (الرياض)\n- المدة: {dur/60:.1f} دقيقة | النوع: {kind}\n"
            f"- https://youtu.be/{vid}\n- المصادر:\n" + "\n".join("  - " + l for l in _visual_report(stock, imgen)) + (f"\n- {warn}" if warn else "") +
            f"\n- زمن التشغيل: {mins:.0f} دقيقة")
    log(f"انتهى ✅ في {mins:.1f} دقيقة")
    return 0

def _make_thumb(script, topic, stock, imgen):
    """صورة مصغرة (غير حرجة): خلفية مولدة بالذكاء الاصطناعي، وإلا ستوك، وإلا تدرج بهوية القناة."""
    try:
        bg = None
        imgen.max_images += 1
        if script.get("thumb_prompt") and not imgen.disabled:
            bg = imgen.generate(script["thumb_prompt"], 1280, 720, seed=777)
        if not bg:
            for a in stock.find(script.get("thumb_query") or topic["topic"], False)[:3]:
                try:
                    bg = stock.download(a); break
                except Exception as e:  # noqa
                    log("[thumb] خلفية فشلت:", str(e)[:80])
        return thumbnail.make_thumbnail(script["thumb_text"], os.path.join(WORK, "thumb.jpg"), bg)
    except Exception as e:  # noqa
        log("⚠️ تعذر إنشاء الصورة المصغرة (لن يمنع النشر):", str(e)[:150])
        return None

def _verify(yt, vid):
    status = yt.verify(vid)
    if status and not status.get("publishAt"):
        w = "⚠️ لم يظهر publishAt — إن بقي الفيديو خاصاً فمشروع API غير موثق (Compliance Audit)."
        log(w); return w
    return ""

# ======================= الشورت اليومي =======================
def pipeline_short():
    t0 = time.time()
    S = st.load(STATE_SHORT_FILE)
    L = st.load()
    yt = YouTube()
    info = yt.channel_info()
    channel_id = info["id"]
    log("القناة:", info.get("snippet", {}).get("title"))
    now = datetime.now(timezone.utc)
    slot = sch.next_slot(now, set(S["scheduled"].keys()), SHORT_LOOKAHEAD_HOURS, SHORT_SLOTS)
    if slot is None:
        log("لا يوجد موعد شورت فاضي الآن ✅")
        summary("✅ لا يوجد موعد شورت فاضي الآن (أو مجدول مسبقاً).")
        st.save(S, STATE_SHORT_FILE); return 0
    log("موعد الشورت:", sch.slot_key(slot), "(الرياض)")

    shutil.rmtree(WORK, ignore_errors=True); os.makedirs(WORK, exist_ok=True)
    kind = TOPIC_CYCLE_SHORT[len(S["history"]) % len(TOPIC_CYCLE_SHORT)]
    sig = content.gather_signals(kind, yt, channel_id, S)
    topic = content.choose_topic(kind, sig, {"topics": S["topics"] + L["topics"]})
    kind = topic["kind"]
    log("موضوع الشورت:", topic["topic"], "| النوع:", kind)

    voice_wav = os.path.join(WORK, "voice.wav")
    for attempt in range(3):
        script = content.write_short(topic, kind)
        scenes = content.flatten_short(script)
        total = tts.build_voice(scenes, voice_wav, VOICES_SHORT, lead_in=0.25, tail_out=0.9)
        if SHORT_MIN_SEC <= total <= SHORT_MAX_SEC + 8:
            break
        log(f"مدة الشورت {total:.0f}s خارج المطلوب — إعادة ({attempt+1}/3)")
        topic["note"] = "النسخة السابقة قصيرة جداً؛ زد المعلومات." if total < SHORT_MIN_SEC else "النسخة السابقة طويلة؛ اختصر."
    log(f"مدة الشورت: {total:.1f}s")

    stock = Stock(); imgen = ImageGen(IMG_MAX_SHORT)
    silent = os.path.join(WORK, "video_silent.mp4")
    visuals.build_video(scenes, total, stock, silent, imgen=imgen, size=(SHORT_W, SHORT_H), endcard=False)
    music_wav = os.path.join(WORK, "music.wav"); mixed = os.path.join(WORK, "mix.m4a")
    music.build_music(total, music_wav, S.get("music_index", 0) + 1)
    music.mix(voice_wav, music_wav, mixed, total)
    final = os.path.join(WORK, "final.mp4")
    visuals.render_short_final(silent, mixed, visuals.caption_phrases(scenes), final, (SHORT_W, SHORT_H))
    dur = probe_duration(final)
    log(f"الشورت النهائي {dur:.1f}s")
    if dur < 12 or abs(dur - total) > 3:
        raise RuntimeError(f"مدة الشورت ({dur:.0f}s) لا تطابق الصوت ({total:.0f}s)")

    title = content.clean_title(script["title"])[:95]
    desc = content.build_description_short(script)
    meta = {"snippet": {"title": title, "description": desc, "tags": content.tags_for(script) + ["Shorts"],
                        "categoryId": YT_CATEGORY, "defaultLanguage": YT_LANG, "defaultAudioLanguage": YT_LANG},
            "status": {"privacyStatus": "private", "publishAt": sch.to_rfc3339_utc(slot),
                       "selfDeclaredMadeForKids": False, "embeddable": True, "publicStatsViewable": True}}
    log("رفع الشورت… العنوان:", title)
    res = yt.upload(final, meta)
    vid = res["id"]
    warn = _verify(yt, vid)
    S["scheduled"][sch.slot_key(slot)] = {"video_id": vid, "title": title, "kind": kind}
    S["history"].append({"slot": sch.slot_key(slot), "video_id": vid, "title": title, "kind": kind, "sec": round(dur)})
    S["topics"] += [topic["topic"], title]
    S["music_index"] = S.get("music_index", 0) + 1
    st.save(S, STATE_SHORT_FILE)
    mins = (time.time() - t0) / 60
    summary(f"### ✅ تمت جدولة شورت\n- **{title}**\n- الموعد: {sch.slot_key(slot)} (الرياض)\n- المدة: {dur:.0f} ثانية | النوع: {kind}\n"
            f"- https://youtube.com/shorts/{vid}\n- المصادر:\n" + "\n".join("  - " + l for l in _visual_report(stock, imgen)) + (f"\n- {warn}" if warn else "") +
            f"\n- زمن التشغيل: {mins:.0f} دقيقة")
    log(f"انتهى ✅ في {mins:.1f} دقيقة")
    return 0

def cli():
    try:
        if "--health" in sys.argv:
            import health
            return health.run_health()
        if "--short" in sys.argv:
            return pipeline_short()
        return pipeline()
    except AuthDead as e:
        log("❌ مشكلة مصادقة يوتيوب:", e)
        summary(f"### ❌ مصادقة يوتيوب\n{e}\n\nالحل: جدّد YT_REFRESH_TOKEN (وتأكد أن تطبيق OAuth بحالة In production).")
        return 2
    except Exception as e:  # noqa
        traceback.print_exc()
        summary(f"### ❌ فشل التشغيل\n```\n{str(e)[:1500]}\n```")
        return 1
'''

# ======================================================================
# القسم: make_music_src
# ======================================================================
_SRC['make_music_src'] = r'''import numpy as np, scipy.signal as sg, argparse, json, os, subprocess, tempfile
from scipy.io import wavfile
_ap=argparse.ArgumentParser()
_ap.add_argument('--out',required=True); _ap.add_argument('--tr',type=int,default=0)
_ap.add_argument('--bpm',type=float,default=100); _ap.add_argument('--seed',type=int,default=7)
ARGS=_ap.parse_args()
SR=44100; BPM=ARGS.bpm; BEAT=60/BPM; BAR=4*BEAT; TAIL=3.0; TR=ARGS.tr
rng=np.random.default_rng(ARGS.seed)
def mtof(m): return 440*2**((m+TR-69)/12)
def lp(x,fc,o=2): b,a=sg.butter(o,min(fc,SR*0.45)/(SR/2),'low'); return sg.lfilter(b,a,x)
def hp(x,fc,o=2): b,a=sg.butter(o,fc/(SR/2),'high'); return sg.lfilter(b,a,x)
def bp(x,lo,hi,o=2): b,a=sg.butter(o,[lo/(SR/2),hi/(SR/2)],'band'); return sg.lfilter(b,a,x)
def T(d): return np.arange(int(d*SR))/SR
def env(n,a,r,p=1.5):
    e=np.ones(n); na=min(int(a*SR),n); nr=min(int(r*SR),n)
    if na>0: e[:na]=np.linspace(0,1,na)**p
    if nr>0: e[-nr:]*=np.linspace(1,0,nr)**p
    return e
def add(buf,sig,t0,gain=1.0,pan=0.0):
    i=int(t0*SR)
    if i>=buf.shape[1] or i<0: return
    n=min(len(sig),buf.shape[1]-i)
    l=np.cos((pan+1)*np.pi/4); r=np.sin((pan+1)*np.pi/4)
    buf[0,i:i+n]+=sig[:n]*gain*l; buf[1,i:i+n]+=sig[:n]*gain*r
def saw_stack(f,t,dets=(-8,0,8)):
    s=0
    for d in dets:
        ff=f*2**(d/1200); ph=rng.random()
        s=s+(2*((ff*t+ph)%1)-1)
    return s/len(dets)
def pad(midis,dur,a=1.0,r=1.0,cut=1800,dets=(-9,0,9)):
    t=T(dur); s=sum(saw_stack(mtof(m),t,dets) for m in midis)/len(midis)
    return lp(s,cut)*env(len(t),a,r,1.2)
def strings(midis,dur,a=0.5,r=0.6,cut=3200):
    t=T(dur); vib=1+0.003*np.sin(2*np.pi*5.5*t)
    s=0
    for m in midis:
        for d in (-12,-4,4,12):
            f=mtof(m)*2**(d/1200); ph=rng.random()
            s=s+(2*((np.cumsum(f*vib)/SR+ph)%1)-1)
    s/= (len(midis)*4)
    return lp(s,cut)*env(len(t),a,r,1.2)
def pluck_ks(f,dur,decay=0.997,cut=3500):
    N=int(round(SR/f)); n=int(dur*SR); buf=rng.uniform(-1,1,N); out=[]
    tot=0
    while tot<n+N:
        out.append(buf.copy()); buf=decay*0.5*(buf+np.roll(buf,-1)); tot+=N
    x=np.concatenate(out); fa=SR/N; ratio=f/fa
    idx=np.arange(n)*ratio; x=np.interp(idx,np.arange(len(x)),x)
    x=lp(x,cut)*np.exp(-T(dur)*1.3)
    return x/ (np.max(np.abs(x))+1e-9)
def pl(f,dur=0.45):
    t=T(dur); return (np.sin(2*np.pi*f*t)+0.4*np.sin(2*np.pi*2*f*t)+0.15*np.sin(2*np.pi*3*f*t))*np.exp(-t*7)
def bell(f,dur=3.0):
    t=T(dur); return (np.sin(2*np.pi*f*t)*np.exp(-t*1.4)+0.35*np.sin(2*np.pi*2.76*f*t)*np.exp(-t*2.6)+0.15*np.sin(2*np.pi*5.4*f*t)*np.exp(-t*4))
def kick(dur=0.5):
    t=T(dur); f=42+110*np.exp(-t*30); ph=2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*np.exp(-t*8)+0.25*np.exp(-t*300)*rng.standard_normal(len(t))
def taiko(dur=1.4):
    t=T(dur); f=52+60*np.exp(-t*18); ph=2*np.pi*np.cumsum(f)/SR
    n=lp(rng.standard_normal(len(t)),500)*np.exp(-t*30)
    return (np.sin(ph)*np.exp(-t*3.2)+0.6*n)
def clap(dur=0.35):
    t=T(dur); n=bp(rng.standard_normal(len(t)),1200,6500); e=np.zeros(len(t))
    for k,d in enumerate((0,0.011,0.022)):
        i=int(d*SR); e[i:]+=np.exp(-(t[:len(t)-i])*(60 if k<2 else 18))
    return n*e
def hat(dur=0.09,o=False):
    t=T(0.3 if o else dur); return hp(rng.standard_normal(len(t)),7000)*np.exp(-t*(14 if o else 70))
def riser(dur,lo=300):
    t=T(dur); n=hp(rng.standard_normal(len(t)),lo)*(t/dur)**2.4
    sw=np.sin(2*np.pi*np.cumsum(200+1800*(t/dur)**2)/SR)*0.25*(t/dur)**2.4
    return n+sw
def crash(dur=4.0):
    t=T(dur); return hp(rng.standard_normal(len(t)),3000)*np.exp(-t*1.1)
def impact(dur=3.2):
    t=T(dur); f=34+70*np.exp(-t*6); ph=2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*np.exp(-t*1.1)+0.5*lp(rng.standard_normal(len(t)),400)*np.exp(-t*3)
def bass(m,dur):
    t=T(dur); s=np.sin(2*np.pi*mtof(m)*t)
    s=np.tanh(3*s)*0.8; return lp(s,500)*env(len(t),0.01,0.08)
def ost(m,dur=0.2,cut=1400):
    t=T(dur); s=saw_stack(mtof(m),t,(-6,0,6)); return lp(s,cut)*env(len(t),0.008,0.09)
def lead(m,dur):
    t=T(dur); s=saw_stack(mtof(m),t,(-10,0,10)); return lp(s,3200)*env(len(t),0.03,0.25)
def reverb(x,wet=0.3):
    L=int(2.6*SR); t=np.arange(L)/SR; out=np.zeros_like(x)
    for c in range(2):
        ir=rng.standard_normal(L)*np.exp(-t/0.6); ir=lp(ir,5500); ir[:int(0.02*SR)]=0
        ir/=np.sqrt(np.sum(ir**2)); out[c]=sg.fftconvolve(x[c],ir)[:x.shape[1]]
    return x+wet*out

# chords: pad voicing, bass root
CH={'Dm':([50,57,62,65],38),'Bb':([46,53,58,62],34),'Gm':([55,58,62,67],31),'A':([57,61,64,69],33)}
PROG=['Dm','Bb','Gm','A']
HIJ_A=[(69,0,1),(67,1,.5),(66,1.5,.5),(63,2,1),(62,3,1.5),(63,4.5,.5),(66,5,1),(67,6,.5),(66,6.5,.5),(62,7,1.5)]
HIJ_B=[(74,0,.5),(70,.5,.5),(69,1,.5),(67,1.5,.5),(66,2,1),(63,3,.5),(62,3.5,1)]
def oud(buf,phrase,t0,gain=0.6,pan=-0.25):
    for m,b,d in phrase: add(buf,pluck_ks(mtof(m),1.6),t0+b*BEAT,gain,pan)
def newbuf(bars): return np.zeros((2,int((bars*BAR+TAIL)*SR)))

def sec_intro():
    B=8; buf=newbuf(B)
    add(buf,pad([38,45,50,57],B*BAR+1.5,a=5,r=2.5,cut=1200),0,0.30)
    add(buf,pad([62,69,74],B*BAR,a=7,r=2.5,cut=2200),0,0.12,0.2)
    oud(buf,HIJ_A,1*BAR,0.65); oud(buf,HIJ_A,5*BAR,0.7)
    for b,m in ((2,81),(4,86),(6,81),(7,86)): add(buf,bell(mtof(m)),b*BAR+2*BEAT,0.10,0.4 if b%2 else -0.4)
    for b in range(4,8): add(buf,kick(),b*BAR,0.30+0.04*(b-4)); add(buf,kick(),b*BAR+0.75*BEAT,0.14)
    add(buf,riser(2*BAR,lo=2500),6*BAR,0.10)
    return buf
def sec_build():
    B=8; buf=newbuf(B)
    for k in range(B):
        ch,root=CH[PROG[k//2%4]]; 
        if k%2==0: add(buf,strings(ch,2*BAR+0.8,a=0.7,r=0.8),k*BAR,0.30+0.025*k)
        add(buf,bass(root,BAR),k*BAR,0.55)
        for e in range(8):  # 8th arpeggio
            m=ch[e%4]+12 if e%4<3 else ch[1]+24
            add(buf,pl(mtof(m)),k*BAR+e*BEAT/2,0.10+0.01*k,-0.3+0.085*e)
        if k>=2: add(buf,kick(),k*BAR,0.65); add(buf,kick(),k*BAR+2*BEAT,0.55)
        if k>=4:
            add(buf,clap(),k*BAR+BEAT,0.30); add(buf,clap(),k*BAR+3*BEAT,0.30)
            for e in range(8): add(buf,hat(),k*BAR+e*BEAT/2,0.10)
    for k in (6,7):  # snare roll accelerating
        n=8 if k==6 else 16
        for e in range(n): add(buf,clap(0.2),k*BAR+e*BAR/n,0.12+0.2*(e/n)+(0.1 if k==7 else 0))
    add(buf,riser(B*BAR,lo=500),0,0.09)
    oud(buf,HIJ_B,7*BAR+0*BEAT,0.45)
    return buf
def sec_main():
    B=12; buf=newbuf(B)
    for k in range(B):
        ch,root=CH[PROG[k%4]]
        add(buf,strings(ch,BAR+0.5,a=0.25,r=0.5),k*BAR,0.27)
        add(buf,pad([c-12 for c in ch[:3]],BAR+0.3,a=0.2,r=0.3,cut=900),k*BAR,0.22)
        for e in range(8):
            add(buf,bass(root if e%4!=3 else root+12,BEAT/2*0.95),k*BAR+e*BEAT/2,0.55)
            m=root+12+(7 if e%4==3 else 0) if root+12>=36 else root+24
            add(buf,ost(root+24,0.2),k*BAR+e*BEAT/2,0.16,-0.35+0.1*e)
        add(buf,kick(),k*BAR,0.72); add(buf,kick(),k*BAR+2*BEAT,0.62); add(buf,kick(),k*BAR+2.5*BEAT,0.28)
        add(buf,clap(),k*BAR+BEAT,0.42); add(buf,clap(),k*BAR+3*BEAT,0.42)
        for e in range(8): add(buf,hat(o=(e%4==3)),k*BAR+e*BEAT/2,0.13 if e%2==0 else 0.09)
        if k%4==3: oud(buf,HIJ_B,k*BAR,0.5)
        if k%4==0 and k>0: add(buf,crash(2.5),k*BAR,0.12)
    add(buf,bell(mtof(86)),0,0.10,0.4)
    return buf
def sec_climax():
    B=8; buf=newbuf(B)
    add(buf,impact(),0,0.9); add(buf,crash(4),0,0.35)
    for k in range(B):
        ch,root=CH[PROG[k%4]]
        add(buf,strings([c+12 for c in ch],BAR+0.5,a=0.15,r=0.5,cut=4200),k*BAR,0.40)
        add(buf,strings(ch,BAR+0.5,a=0.15,r=0.5),k*BAR,0.38)
        add(buf,pad([c-12 for c in ch[:3]],BAR+0.3,a=0.1,r=0.3,cut=900),k*BAR,0.28)
        lm={'Dm':[69,74,77,81],'Bb':[70,74,77,82],'Gm':[70,74,79,82],'A':[69,73,76,81]}[PROG[k%4]]
        for q,m in enumerate(lm): add(buf,lead(m,BEAT*0.95),k*BAR+q*BEAT,0.26,0.15)
        for e in range(8):
            add(buf,bass(root,BEAT/2*0.95),k*BAR+e*BEAT/2,0.60)
            add(buf,ost(root+24,0.2,1800),k*BAR+e*BEAT/2,0.24,-0.4+0.11*e)
            add(buf,taiko(),k*BAR+e*BEAT/2,0.80 if e%2==0 else 0.42)
        add(buf,kick(),k*BAR,0.95); add(buf,kick(),k*BAR+2*BEAT,0.85)
        add(buf,clap(),k*BAR+BEAT,0.48); add(buf,clap(),k*BAR+3*BEAT,0.48)
        for e in range(8): add(buf,hat(o=(e%4==3)),k*BAR+e*BEAT/2,0.15)
        if k%4==0 and k>0: add(buf,crash(3),k*BAR,0.18)
        if k%2==0: add(buf,bell(mtof(93 if k%4==0 else 86)),k*BAR,0.10,-0.4 if k%4==0 else 0.4)
    add(buf,riser(BAR,lo=1500),7*BAR-0.0,0.0)  # (placeholder silent)
    return buf
def sec_outro():
    B=4; buf=newbuf(B)
    add(buf,strings([50,57,62,65],B*BAR+2.5,a=1.0,r=5,cut=2200),0,0.17)
    add(buf,pad([38,45,50],B*BAR+2.5,a=1.0,r=5,cut=900),0,0.16)
    bb=bass(38,B*BAR+2.5); bb=bb*np.linspace(1,0,len(bb))**0.8; add(buf,bb,0,0.38)
    add(buf,kick(),0,0.45); add(buf,crash(4),0,0.08)
    oud(buf,HIJ_A,0.5*BAR,0.6)
    add(buf,bell(mtof(86)),2*BAR,0.12,0.3); add(buf,bell(mtof(81)),3*BAR,0.10,-0.3)
    return buf

SECS=[('intro',sec_intro,8),('build',sec_build,8),('main',sec_main,12),('climax',sec_climax,8),('outro',sec_outro,4)]
bufs={}
for name,fn,B in SECS:
    b=fn(); b=np.vstack([hp(b[0],30),hp(b[1],30)]); b=reverb(b,0.30); bufs[name]=(b,B)
total=int((sum(B for _,_,B in SECS)*BAR+TAIL)*SR)
full=np.zeros((2,total)); off=0
for name,fn,B in SECS:
    b,_=bufs[name]; i=int(off*SR); full[:,i:i+b.shape[1]]+=b[:, :total-i]; off+=B*BAR
def soft(x): return np.tanh(1.25*x)/np.tanh(1.25)
scale=0.89/np.max(np.abs(soft(full)))
os.makedirs(ARGS.out,exist_ok=True)
manifest={'bpm':BPM,'bar_sec':BAR,'tail_sec':TAIL,'sections':{}}
for name,(b,B) in bufs.items():
    y=soft(b)*scale; fi=int(0.03*SR); y[:,:fi]*=np.linspace(0,1,fi); fo=int(1.2*SR); y[:,-fo:]*=np.linspace(1,0,fo)
    with tempfile.TemporaryDirectory() as td:
        w=os.path.join(td,'x.wav'); wavfile.write(w,SR,(np.clip(y.T,-1,1)*32767).astype(np.int16))
        subprocess.run(['ffmpeg','-loglevel','error','-y','-i',w,'-codec:a','libmp3lame','-b:a','160k',os.path.join(ARGS.out,name+'.mp3')],check=True)
    manifest['sections'][name]={'file':name+'.mp3','bars':B}
json.dump(manifest,open(os.path.join(ARGS.out,'manifest.json'),'w'),indent=1)
print('done',ARGS.out)
'''

_ORDER = ['config', 'util', 'arabic_numbers', 'gemini', 'stock', 'imagegen', 'arfont', 'brand', 'anim', 'tts', 'visuals', 'music', 'thumbnail', 'youtube', 'schedule', 'state', 'content', 'health', 'pipeline']

def _load():
    me = os.path.abspath(__file__)
    for name in _ORDER:
        mod = types.ModuleType(name)
        mod.__file__ = me
        if name == "music":
            mod.MAKE_MUSIC_SRC = _SRC["make_music_src"]
        fname = f"<bawsala:{name}>"
        src = _SRC[name]
        linecache.cache[fname] = (len(src), None, src.splitlines(True), fname)
        sys.modules[name] = mod
        exec(compile(src, fname, "exec"), mod.__dict__)

_load()

if __name__ == "__main__":
    sys.exit(sys.modules["pipeline"].cli())
