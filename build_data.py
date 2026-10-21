"""Generuje docs/index.html – report hledanosti pro Teta drogerie (barvy Proficio).

Vstupy:  config.json (klíčová slova po pohledech), raw/planner.csv (historie z Keyword Planneru),
         template.html, brand/*.otf (písmo BC Novatica), node_modules/chart.js
Výstup:  docs/index.html, history/TETA.json, history/kw_ids.json

Pohledy (lišta nahoře): vertikala (10 podkategorií z GA4), znacky (12 značek výrobců),
brand (Brand Teta), konkurence (Teta, dm, Rossmann, Notino, Pilulka).
Duplicity: stejná průměrná hledanost + dolní a horní CPC + měsíční řada = jedna skupina Plánovače,
ponechá se první slovo (pořadí v config.json = podle hledanosti), ostatní se odstraní.
"""
import base64, csv, json, re, datetime, unicodedata
from pathlib import Path

ROOT = Path(__file__).parent
REPO = ROOT
cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
HIST = REPO / "history"
HIST.mkdir(exist_ok=True)
ids_path = HIST / "kw_ids.json"
kw_ids = json.loads(ids_path.read_text(encoding="utf-8")) if ids_path.exists() else {}


def norm(x):
    return unicodedata.normalize("NFC", x.strip().lower())


def plain(x):
    return "".join(c for c in unicodedata.normalize("NFD", x.lower()) if unicodedata.category(c) != "Mn")


def words(x):
    return re.findall(r"[a-z0-9]+", plain(x))


# --- závěrečné čištění (značky a témata, která prošla výběrem) ---
EXCL_WORDS = set(cfg.get("exclude_words", []))
EXCL_PHRASES = cfg.get("exclude_phrases", [])
EXCL_EXACT = set(cfg.get("exclude_exact", []))  # celé slovo = příliš obecné / nejednoznačné
NAV_WORDS = set(cfg.get("navigational_words", []))


def excluded(kw):
    w = words(kw)
    t = " " + " ".join(w) + " "
    return (" ".join(w) in EXCL_EXACT or any(x in EXCL_WORDS for x in w)
            or any(f" {p} " in t for p in EXCL_PHRASES))


def navigational(kw, tokens):
    rest = [x for x in words(kw) if not any(x == t or x.startswith(t) for t in tokens)]
    return all(x in NAV_WORDS for x in rest)


# --- data z Plánovače ---
rows = {}
with open(ROOT / "raw" / "planner.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if not r.get("keyword") or r["keyword"].startswith("#"):
            continue
        series = json.loads(r["monthly_search_volumes"]) if r.get("monthly_search_volumes") else []
        rows[norm(r["keyword"])] = {
            "kw": r["keyword"].strip(), "avg": int(r["avg_monthly_searches"] or 0),
            "low": int(r["low_top_of_page_bid_micros"] or 0), "high": int(r["high_top_of_page_bid_micros"] or 0),
            "series": {m: int(v or 0) for m, v in series},
        }
months = sorted({m for r in rows.values() for m in r["series"]})


def kw_id(sec, kw):
    m = kw_ids.setdefault(sec, {})
    if kw not in m:
        m[kw] = max(m.values(), default=0) + 1
    return m[kw]


def brand_id(name):
    return "".join(ch for ch in plain(name) if ch.isalnum())


def build(sec, wanted):
    """wanted = [(kw, group)] -> (kept [(group, kwobj)], removed, missing)"""
    seen_sig, seen_kw, kept, removed, missing = {}, set(), [], [], []
    for k, g in wanted:
        nk = norm(k)
        if nk in seen_kw:
            continue
        seen_kw.add(nk)
        r = rows.get(nk)
        if r is None:
            missing.append(k)
            continue
        sig = (r["avg"], r["low"], r["high"], tuple(r["series"].get(m, 0) for m in months))
        if sig in seen_sig:
            removed.append({"kw": r["kw"], "dupOf": seen_sig[sig]})
            continue
        seen_sig[sig] = r["kw"]
        kept.append((g, {"kw": r["kw"], "id": kw_id(sec, r["kw"]),
                         "monthly": [r["series"].get(m, 0) for m in months], "avg": r["avg"],
                         "grp": None, "same": None, "foreign": False,
                         "cpc_low": round(r["low"] / 1e6, 2), "cpc_high": round(r["high"] / 1e6, 2)}))
    return kept, removed, missing


def by_avg(lst):
    return sorted(lst, key=lambda k: (-k["avg"], k["kw"]))


today = datetime.date.today().isoformat()
base = {"generated": today, "history_start": months[0], "months": months, "geo_label": "Česko a češtinu",
        "country": "CZ", "country_name": "Česko"}
out = {"generated": today, "countries": {}}
report = []

# 1) Vertikála
wanted = [(k, g) for k, g in cfg["vertical_kws"] if not excluded(k)]
kept, removed, missing = build("vertikala", wanted)
cats = [{"id": "vertikala", "name": "Vertikála celkem", "keywords": by_avg([k for g, k in kept])}]
for c in cfg["categories"]:
    cats.append({"id": c["id"], "name": c["name"], "keywords": by_avg([k for g, k in kept if g == c["id"]])})
out["countries"]["vertikala"] = dict(base, brands=[], removed=removed, categories=cats)
report.append(f"vertikala: {len(kept)} slov, {len(removed)} duplicit, {len(missing)} nevráceno")

# 2) Značky výrobců a 4) Konkurence (režim značek: přepínač, share of search, korelace)
for sec, key, title in (("znacky", "znacky", "Značky"), ("konkurence", "konkurence", "Konkurence")):
    items = cfg[key]
    wanted = []
    for b in items:
        toks = [plain(t) for t in b.get("tokens", [b["name"]])]
        for k in b["keywords"]:
            if excluded(k):
                continue
            if b.get("navigational_only") and not navigational(k, toks):
                continue
            wanted.append((k, brand_id(b["name"])))
    kept, removed, missing = build(sec, wanted)
    kws = [dict(k, brand=g) for g, k in kept]
    brands = [{"id": brand_id(b["name"]), "name": b["name"], "color": b["color"], "client": b.get("client", False),
               "dash": b.get("dash", False)} for b in items]
    out["countries"][sec] = dict(base, brands=brands, removed=removed,
                                 categories=[{"id": "konkurence", "name": title, "keywords": by_avg(kws)}])
    report.append(f"{sec}: {len(kept)} slov, {len(removed)} duplicit, {len(missing)} nevráceno")

# 3) Brand Teta (jen navigační dotazy na Tetu)
teta = [b for b in cfg["konkurence"] if b.get("client")][0]
toks = [plain(t) for t in teta.get("tokens", [teta["name"]])]
wanted = [(k, "brand") for k in teta["keywords"] if not excluded(k) and navigational(k, toks)]
kept, removed, missing = build("brand", wanted)
out["countries"]["brand"] = dict(base, brands=[], removed=removed,
                                 categories=[{"id": "brand", "name": "Brand Teta", "keywords": by_avg([k for g, k in kept])}])
report.append(f"brand: {len(kept)} slov, {len(removed)} duplicit, {len(missing)} nevráceno")

# pořadí pohledů v liště
out["countries"] = {k: out["countries"][k] for k in ("vertikala", "znacky", "brand", "konkurence")}
(HIST / "TETA.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
ids_path.write_text(json.dumps(kw_ids, ensure_ascii=False, indent=1), encoding="utf-8")

# --- stránka ---
data_json = json.dumps(out, ensure_ascii=False).replace("</", "<\\/")
chart_js = (ROOT / "node_modules/chart.js/dist/chart.umd.js").read_text(encoding="utf-8")
font_reg = base64.b64encode((ROOT / "brand" / "novatica-regular.otf").read_bytes()).decode()
font_semi = base64.b64encode((ROOT / "brand" / "novatica-semibold.otf").read_bytes()).decode()
html = (ROOT / "template.html").read_text(encoding="utf-8")
cdn = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>'
assert cdn in html and "<<DATA>>" in html
html = (html.replace(cdn, "<script>" + chart_js + "</script>").replace("<<DATA>>", data_json)
        .replace("<<FONT_REG>>", font_reg).replace("<<FONT_SEMI>>", font_semi))
(REPO / "docs").mkdir(exist_ok=True)
(REPO / "docs" / "index.html").write_text(html, encoding="utf-8")
print(f"měsíce {months[0]}..{months[-1]}")
print("\n".join(report))
