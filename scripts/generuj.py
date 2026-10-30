"""Generuje poranne wydanie Przeglądu wiadomości: docs/data/RRRR-MM-DD.json + docs/data/index.json.

Uruchamianie:
  python scripts/generuj.py              – generuje wydanie na dziś (nadpisuje istniejące)
  python scripts/generuj.py --scheduled  – tryb GitHub Actions: tylko gdy w Warszawie jest już ≥ 6:00
                                           i dzisiejszego wydania jeszcze nie ma
Gdy ustawiona jest zmienna ANTHROPIC_API_KEY, wybór i streszczenia przygotowuje Claude (po polsku);
w przeciwnym razie działa tryb RSS (streszczenia = leady ze źródeł, ranking heurystyczny).
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import email.utils
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from zrodla import FEEDS, KRAKOW, EUROPE, WORLD, POLAND, TOPICS, TOPIC_LABELS, CULTURE, CULTURE_LABELS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "data"
KEEP_DAYS = 4  # dzisiejsze wydanie + 3 dni wstecz
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
CATS = ["europa", "swiat", "polska", "krakow", "kultura"]
TARGET = {"europa": 12, "swiat": 12, "polska": 14, "krakow": 10, "kultura": 14}
# w działach kultury trafiają się kryminał, plotki i telewizja rozrywkowa – to nie jest wiadomość o kulturze
CULTURE_JUNK = (r"(zamordowa|zabójst|murder|killed|police|policj|prokurat|chorob|disease|amputac|szpital|hospital|"
                r"reality|traitors|big brother|taniec z gwiazdami|love island|bake off|strictly|celebryt|plotk|rozw[óo]d|divorce|"
                r"ślub|wedding|ciąż|pregnan|odchudz|diet|stadium|stadion|recipe|horoscope|trump|wybor|election)")
CULTURE_BONUS = {"muzea": 0.8, "sztuka": 0.4}  # muzea i sztuka wyżej w rankingu Kultury
MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")


# ───────────────────────── czas warszawski ─────────────────────────
def warsaw_now():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("Europe/Warsaw"))
    except Exception:
        # brak bazy stref (Windows bez tzdata) – reguła UE: czas letni od ostatniej niedzieli marca do ostatniej niedzieli października, 1:00 UTC
        now = dt.datetime.now(dt.timezone.utc)

        def last_sunday(month):
            d = dt.datetime(now.year, month, 31 if month in (3, 10) else 30, 1, tzinfo=dt.timezone.utc)
            return d - dt.timedelta(days=(d.weekday() + 1) % 7)

        summer = last_sunday(3) <= now < last_sunday(10)
        return now.astimezone(dt.timezone(dt.timedelta(hours=2 if summer else 1)))


# ───────────────────────── pobieranie ─────────────────────────
def fetch(url, timeout=20, limit=3_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pl,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(limit)


def clean(text):
    if not text:
        return ""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(html.unescape(text))
    text = re.sub(r"\s+", " ", text).strip()
    # typowe dopiski z kanałów RSS
    text = re.sub(r"\s*(Czytaj (więcej|dalej)|Read more|Continue reading|The post .* appeared first on .*|Artykuł .* pochodzi z serwisu .*)\s*\.*$", "", text, flags=re.I)
    return text.strip(" …")


def shorten(text, n=320):
    if len(text) <= n:
        return text
    cut = text[:n]
    dot = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if dot > n * 0.55:
        return cut[:dot + 1]
    return cut[:cut.rfind(" ")].rstrip(",;:–-") + "…"


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)
    except Exception:
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def local(tag):
    return tag.rsplit("}", 1)[-1].lower()


def find_image(el, desc_html):
    for child in el.iter():
        t = local(child.tag)
        if t in ("content", "thumbnail") and child.get("url") and (child.get("medium") in (None, "image") or t == "thumbnail"):
            if re.search(r"\.(mp4|mp3|m4a)(\?|$)", child.get("url"), re.I):
                continue
            return child.get("url")
        if t == "enclosure" and (child.get("type") or "").startswith("image") and child.get("url"):
            return child.get("url")
        if t == "image" and child.text and child.text.strip().startswith("http"):
            return child.text.strip()
    m = re.search(r"<img[^>]+src=[\"']([^\"']+)", desc_html or "", re.I)
    return html.unescape(m.group(1)) if m else None


def parse_feed(raw):
    items = []
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"^[^<]+", "", text)
    try:
        root = ET.fromstring(text.encode("utf-8"))
    except ET.ParseError:
        # niepoprawny XML – zapasowy parser na wyrażeniach regularnych
        for block in re.findall(r"<item[\s>].*?</item>", text, re.S):
            def g(tag):
                m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", block, re.S)
                v = m.group(1) if m else ""
                return re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", v, flags=re.S)
            desc = g("description") or g("content:encoded")
            img = re.search(r"<(?:media:content|media:thumbnail|enclosure)[^>]+url=[\"']([^\"']+)", block)
            items.append({"title": clean(g("title")), "link": clean(g("link")), "desc_html": desc,
                          "date": parse_date(g("pubDate") or g("dc:date")),
                          "image": html.unescape(img.group(1)) if img else find_image(ET.Element("x"), desc)})
        return items
    for el in root.iter():
        if local(el.tag) not in ("item", "entry"):
            continue
        d = {"title": "", "link": "", "desc_html": "", "date": None}
        content_html = ""
        for c in el:
            t = local(c.tag)
            if t == "title":
                d["title"] = clean(c.text or "")
            elif t == "link":
                d["link"] = (c.get("href") if c.get("href") and c.get("rel") in (None, "alternate") else (c.text or "").strip()) or d["link"]
            elif t in ("description", "summary"):
                d["desc_html"] = c.text or ""
            elif t == "encoded" or (t == "content" and c.text):
                content_html = c.text or ""
            elif t in ("pubdate", "published", "updated", "date") and not d["date"]:
                d["date"] = parse_date(c.text)
        if not d["desc_html"]:
            d["desc_html"] = content_html
        d["image"] = find_image(el, d["desc_html"] or content_html)
        items.append(d)
    return items


def load_feed(feed):
    try:
        items = parse_feed(fetch(feed["url"]))
    except Exception as e:
        print(f"  ✗ {feed['name']}: {e}", file=sys.stderr)
        return feed, []
    return feed, items


# ───────────────────────── klasyfikacja ─────────────────────────
def kw_hits(text, words):
    return sum(1 for w in words if re.search(r"(?<![\wąćęłńóśźż])" + re.escape(w), text))


def classify_region(feed, text, title):
    k, e, w, p = (kw_hits(text, KRAKOW), kw_hits(text, EUROPE), kw_hits(text, WORLD), kw_hits(text, POLAND))
    te, tw = kw_hits(title, EUROPE), kw_hits(title, WORLD)
    scope = feed["scope"]
    if scope == "kul":
        return "kultura"
    if scope == "krk":
        return "krakow"
    if scope == "pl":
        if k:
            return "krakow"
        if te or tw or e >= 2 or w >= 2:
            # polski serwis pisze o zagranicy; sprawy krajowe z wątkiem zagranicznym zostają w „Polsce”
            if kw_hits(text, ["polsk", "polsc", "polak", "polac", "tusk", "nawrock", "sejm", "warszaw"]) >= 2:
                return "polska"
            return "europa" if (te, e) >= (tw, w) else "swiat"
        return "polska"
    if p and not (e or w) and feed.get("topic") is None:
        return "polska"
    if scope == "eu":
        return "swiat" if w > e else "europa"
    return "europa" if e > w else "swiat"


def culture_section(feed, text, title):
    """Dział w kategorii Kultura; None, gdy wpis ze źródła „strict” nie dotyczy kultury."""
    scores = {t: kw_hits(text, words) + kw_hits(title, words) for t, words in CULTURE.items()}
    best = max(scores, key=scores.get)
    if scores[best]:
        return best
    return None if feed.get("strict") else feed.get("sub", "kultura")


def classify_topic(feed, text, title):
    if feed.get("topic"):
        return feed["topic"]
    scores = {t: kw_hits(text, words) + kw_hits(title, words) for t, words in TOPICS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "społeczeństwo"


# kraje w nagłówkach (PL i EN) – w trybie RSS najwyżej 2 wiadomości o tym samym kraju w kategorii
GEO = {"ES": "hiszpan spain spanish madryt madrid", "UA": "ukrai kijów kijow kyiv kiev zełensk zelensk",
       "RU": "rosj russia rosyj moskw moscow kreml kremlin putin", "DE": "niemc niemie german berlin merz",
       "FR": "franc french paryż paris macron", "IT": "włoch włosz ital rzym rome meloni",
       "GB": "brytyj britain british london londyn starmer england angli", "US": "usa trump amerykań american waszyngton washington",
       "CN": "chin china chinese pekin beijing xi", "IL": "izrael israel netanjahu netanyahu gaza", "TR": "turcj turkey turkish erdogan",
       "HU": "węgr węgier hungar orbán orban", "EU": "unia unii brussels bruksel von"}
GEO_IDX = {w: k for k, ws in GEO.items() for w in ws.split()}


def geo_key(title):
    for w in re.findall(r"[\wąćęłńóśźż]+", title.lower()):
        for stem, k in GEO_IDX.items():
            if w.startswith(stem):
                return k
    return None


STOP = set("oraz które który która przez jako jest będzie został została zostało także tylko jednak może mogą ponad podczas "
           "after about their there which would could while with from that this have been were will into over says said "
           "dlaczego czego kiedy gdzie jakie jaki jaka".split())


def names(title):
    """Nazwy własne z nagłówka (słowa z wielkiej litery poza pierwszym) – do wyłapania tego samego wydarzenia w dwóch językach."""
    words = re.findall(r"[\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{4,}", title)[1:]
    return {w.lower()[:6] for w in words if w[0].isupper()}


def stems(title):
    words = re.findall(r"[\wąćęłńóśźż]{4,}", title.lower())
    return {w[:6] for w in words if w not in STOP}


# ───────────────────────── obrazki ─────────────────────────
def og_image(url):
    try:
        page = fetch(url, timeout=12, limit=400_000).decode("utf-8", errors="replace")
    except Exception:
        return None
    for pat in (r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)'):
        m = re.search(pat, page, re.I)
        if m:
            return html.unescape(m.group(1))
    return None


def fix_image(url):
    if not url:
        return None
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    if not url.startswith("http"):
        return None
    if re.search(r"(logo|placeholder|default[-_]?image|1x1|pixel|spacer)", url, re.I):
        return None
    # BBC: większa wersja miniatury
    url = re.sub(r"(ichef\.bbci\.co\.uk/(?:ace/standard|news))/\d+/", r"\1/976/", url)
    return url


# ───────────────────────── wybór ─────────────────────────
def pick(cands, n, loose=False):
    """Wybór z dbałością o różnorodność: limity na temat i źródło, najpierw po jednym z każdego tematu."""
    cands = sorted(cands, key=lambda x: -x["score"])
    chosen, per_topic, per_source, per_geo = [], {}, {}, {}
    cap_topic = {"polityka": 4, "bezpieczeństwo": 3}
    caps = (99, 12, 99) if loose else (3, 3, 2)  # temat / źródło / kraj; luźne limity dla krótkiej listy dla Claude

    def ok(c):
        return (per_topic.get(c["topic"], 0) < (caps[0] if loose else cap_topic.get(c["topic"], caps[0]))
                and per_source.get(c["source"], 0) < caps[1] and per_geo.get(c["geo"], 0) < caps[2] and c not in chosen)

    def take(c):
        chosen.append(c)
        per_topic[c["topic"]] = per_topic.get(c["topic"], 0) + 1
        per_source[c["source"]] = per_source.get(c["source"], 0) + 1
        if c["geo"]:
            per_geo[c["geo"]] = per_geo.get(c["geo"], 0) + 1

    seen_topics = []
    for c in cands:
        if c["topic"] not in seen_topics:
            seen_topics.append(c["topic"])
    top = cands[:2 * n]  # różnorodność – ale tylko spośród mocnych kandydatów
    for t in seen_topics:  # po jednym najlepszym z każdego tematu
        if len(chosen) >= n:
            break
        best = next((c for c in top if c["topic"] == t and ok(c) and c["summary"]), None)
        if best:
            take(best)
    for c in cands:
        if len(chosen) >= n:
            break
        if ok(c):
            take(c)
    return sorted(chosen, key=lambda x: -x["score"])


def claude_select(cat, cands, n):
    """Claude wybiera najważniejsze i różnorodne wiadomości oraz pisze polskie streszczenia wyłącznie na podstawie leadów."""
    import anthropic

    names = {"europa": "Europa (bez Polski)", "swiat": "Świat (poza Europą lub o znaczeniu globalnym)",
             "polska": "Polska", "krakow": "Kraków i Małopolska",
             "kultura": "Kultura: muzea, wystawy, sztuka, zabytki, film, muzyka, książki, teatr, historia – polska i zagraniczna"}
    if cat == "kultura":
        variety = ("różnorodne: w pierwszej kolejności muzea, wystawy, sztuka i zabytki, ale też film, muzyka, książki, teatr "
                   "i historia; mniej więcej połowa wiadomości o kulturze polskiej, połowa o zagranicznej")
        topics = list(CULTURE_LABELS)
    else:
        variety = ("różnorodne: nie tylko polityka i wojna, ale też gospodarka, kultura, nauka, społeczeństwo, zdrowie, "
                   "klimat, technologie, sport – proporcjonalnie do wagi wydarzeń")
        topics = list(TOPIC_LABELS)
    lines = []
    for i, c in enumerate(cands):
        lines.append(f"[{i}] ({c['source']}) {c['title']}\n    {c['raw_summary'][:450] or '(brak leadu – tylko nagłówek)'}")
    prompt = (
        f"Jesteś redaktorem porannego przeglądu wiadomości dla polskiego czytelnika (nauczyciela historii z Krakowa). "
        f"Kategoria: {names[cat]}. Poniżej kandydaci z ostatniej doby z renomowanych źródeł.\n\n"
        f"Wybierz {n} najważniejszych wiadomości tak, by wydanie było {variety}. "
        f"Pomiń duplikaty tego samego wydarzenia (wybierz najlepsze źródło), plotki, horoskopy, treści sponsorowane, "
        f"porady zakupowe i wiadomości bez znaczenia. Jeśli kandydat nie pasuje do kategorii, pomiń go.\n\n"
        f"Dla każdej wybranej podaj: id, tytuł po polsku (rzeczowy, bez clickbaitu), streszczenie po polsku w 2–3 "
        f"zdaniach oraz temat. Streszczenie musi opierać się WYŁĄCZNIE na podanym nagłówku i leadzie – nie dopisuj faktów, "
        f"liczb ani ocen, których tam nie ma. Gdy jest tylko nagłówek, napisz jedno zdanie. Kolejność: od najważniejszej.\n\n"
        + "\n".join(lines)
    )
    schema = {
        "type": "object",
        "properties": {"items": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "topic": {"type": "string", "enum": topics},
            },
            "required": ["id", "title", "summary", "topic"],
            "additionalProperties": False,
        }}},
        "required": ["items"],
        "additionalProperties": False,
    }
    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason in ("refusal", "max_tokens"):
        raise RuntimeError(f"stop_reason={response.stop_reason}")
    text = next(b.text for b in response.content if b.type == "text")
    out = []
    for it in json.loads(text)["items"]:
        if 0 <= it["id"] < len(cands):
            c = dict(cands[it["id"]])
            c.update(title=it["title"].strip(), summary=it["summary"].strip(), topic=it["topic"])
            if c not in out:
                out.append(c)
    return out[:n]


# ───────────────────────── główny przebieg ─────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scheduled", action="store_true")
    ap.add_argument("--no-ai", action="store_true", help="wymuś tryb RSS")
    args = ap.parse_args()

    now_w = warsaw_now()
    today = now_w.date().isoformat()
    out_file = DATA / f"{today}.json"
    if args.scheduled:
        if now_w.hour < 6:
            print(f"Za wcześnie ({now_w:%H:%M} w Warszawie) – pomijam.")
            return
        if out_file.exists():
            print(f"Wydanie {today} już istnieje – pomijam.")
            return

    now_utc = dt.datetime.now(dt.timezone.utc)
    print(f"Pobieram {len(FEEDS)} kanałów…")
    with cf.ThreadPoolExecutor(16) as ex:
        results = list(ex.map(load_feed, FEEDS))

    pool = []
    for feed, items in results:
        for it in items:
            if not it["title"] or not it["link"].startswith("http"):
                continue
            age_h = (now_utc - it["date"]).total_seconds() / 3600 if it["date"] else 12
            if age_h > feed.get("hours", 30) or age_h < -3:
                continue
            title = it["title"]
            if feed.get("gnews"):
                title = re.sub(r"\s+[-–|]\s+[^-–|]{2,40}$", "", title)  # „… - Reuters”
            summary = clean(it["desc_html"])
            if feed.get("gnews") or summary.lower().startswith(title.lower()[:40]) and len(summary) < len(title) + 20:
                summary = ""
            text = f" {title} {summary} ".lower()
            if re.search(r"(horoskop|sponsorowan|partner materiału|artykuł partnerski|promocj[ae] w|kod rabatowy|quiz|^ ?live|na żywo|transmisj|przepis|sałat|kulinar|ciast[oa]|tart[ay] |przekąsk|obiad|audycja|podcast|galeria|zdjęcia:|^ ?watch:|^ ?wideo|^ ?video|lotto|eurojackpot|multi multi|kup teraz|wyprzedaż|black friday|newsletter|ranking kont|ranking lokat|program tv|tv guide)", text):
                continue
            region = classify_region(feed, text, f" {title} ".lower())
            if region == "kultura":
                topic = culture_section(feed, text, f" {title} ".lower())
                if topic is None or len(title) < 15 or re.search(CULTURE_JUNK, text):
                    continue
            else:
                topic = classify_topic(feed, text, f" {title} ".lower())
            pool.append({
                "title": title,
                "raw_summary": shorten(summary, 600),
                "summary": shorten(summary),
                "link": it["link"],
                "image": None if feed.get("gnews") else fix_image(it.get("image")),
                "source": feed["name"],
                "published": it["date"].isoformat() if it["date"] else None,
                "region": region,
                "topic": topic,
                "pl": bool(feed.get("pl")),
                "_w": feed["w"],
                "_age": max(age_h, 0),
                "_stems": stems(title),
                "geo": geo_key(title),
            })
    print(f"Świeżych wpisów: {len(pool)}")

    # deduplikacja i „waga” wydarzenia: ile różnych źródeł o nim pisze
    pool.sort(key=lambda x: -x["_w"])
    uniq = []
    for c in pool:
        dup = None
        for u in uniq:
            s1, s2 = c["_stems"], u["_stems"]
            if s1 and s2 and len(s1 & s2) / min(len(s1), len(s2)) >= 0.6:
                dup = u
                break
        if c["link"] in {u["link"] for u in uniq}:
            continue
        if dup:
            dup["_coverage"].add(c["source"])
            if not dup["image"] and c["image"]:
                dup["image"] = c["image"]
            if not dup["summary"] and c["summary"] and dup["region"] == c["region"]:
                dup["summary"], dup["raw_summary"] = c["summary"], c["raw_summary"]
            continue
        c["_coverage"] = {c["source"]}
        uniq.append(c)
    for c in uniq:
        c["score"] = (c["_w"] + 1.6 * (len(c["_coverage"]) - 1) + (1.0 if c["summary"] else -1.5)
                      + (0.6 if c["image"] else 0) - min(c["_age"], 48) / 16)
        if c["region"] == "kultura":
            c["score"] += CULTURE_BONUS.get(c["topic"], 0)

    use_ai = bool(os.environ.get("ANTHROPIC_API_KEY")) and not args.no_ai
    edition = {"date": today, "generated": now_w.isoformat(timespec="minutes"), "mode": "ai" if use_ai else "rss",
               "topics": {**TOPIC_LABELS, **CULTURE_LABELS}, "categories": {}}
    for cat in CATS:
        cands = [c for c in uniq if c["region"] == cat]
        n = TARGET[cat]
        chosen = None
        if use_ai and cands:
            try:
                shortlist = pick(cands, 70, loose=True)
                chosen = claude_select(cat, shortlist, n)
                print(f"  {cat}: Claude wybrał {len(chosen)} z {len(shortlist)}")
            except Exception as e:
                print(f"  {cat}: Claude niedostępny ({e}) – tryb RSS", file=sys.stderr)
                edition["mode"] = "mixed"
        if not chosen and cat == "kultura":
            # mniej więcej po połowie: kultura polska i zagraniczna
            good = [c for c in cands if c["summary"] or c["_w"] >= 3]
            chosen = pick([c for c in good if not c["pl"]], n // 2)
            seen = [names(c["title"]) for c in chosen]
            pl = [c for c in good if c["pl"] and not any(len(names(c["title"]) & s) >= 2 for s in seen)]
            chosen = sorted(chosen + pick(pl, n - len(chosen)), key=lambda x: -x["score"])
            print(f"  {cat}: {len(chosen)} z {len(cands)} kandydatów")
        if not chosen:
            chosen = pick([c for c in cands if c["summary"] or c["_w"] >= 3.5], n)
            print(f"  {cat}: {len(chosen)} z {len(cands)} kandydatów")
        edition["categories"][cat] = chosen

    # brakujące zdjęcia: og:image ze strony artykułu (bez linków Google News)
    need = [c for cat in CATS for c in edition["categories"][cat] if not c["image"] and "news.google.com" not in c["link"]]
    with cf.ThreadPoolExecutor(12) as ex:
        for c, img in zip(need, ex.map(lambda c: og_image(c["link"]), need)):
            c["image"] = fix_image(img)

    for cat in CATS:
        edition["categories"][cat] = [{
            "title": c["title"], "summary": c["summary"], "link": c["link"], "image": c["image"],
            "source": c["source"], "also": sorted(c["_coverage"] - {c["source"]})[:4],
            "published": c["published"], "topic": c["topic"],
        } for c in edition["categories"][cat]]

    DATA.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(edition, ensure_ascii=False, indent=1), encoding="utf-8")

    # archiwum: tylko dzisiejsze wydanie + 3 dni wstecz
    files = sorted((p for p in DATA.glob("????-??-??.json")), reverse=True)
    for old in files[KEEP_DAYS:]:
        old.unlink()
    dates = [p.stem for p in files[:KEEP_DAYS]]
    (DATA / "index.json").write_text(json.dumps({"editions": dates, "updated": edition["generated"]}, ensure_ascii=False),
                                     encoding="utf-8")
    total = sum(len(v) for v in edition["categories"].values())
    print(f"Zapisano {out_file.name}: {total} wiadomości (tryb {edition['mode']}).")


if __name__ == "__main__":
    main()
