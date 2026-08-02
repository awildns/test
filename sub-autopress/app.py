#!/usr/bin/env python3
"""SUB Autopress — every run: scan music/fashion/subculture news for
SUB word-bank matches, write a headline + article, render a cover and
an article page (blank photo slot), and post the lot to a Discord webhook.

Env vars:
  DISCORD_WEBHOOK_URL   where to post (if unset, prints instead of posting)
  ANTHROPIC_API_KEY     enables Claude-written headline/article
  SUB_MODEL             Claude model id (default: claude-opus-4-8)
  SUB_MAX_AGE_DAYS      freshness window in days (default: 7)

Usage:
  python app.py           normal run (fetch news, maybe post one story)
  python app.py --test    skip fetching, use a built-in sample story
"""
import email.utils
import hashlib
import html
import json
import os
import random
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
os.chdir(BASE)  # make_cover/make_article resolve fonts + logo from cwd

import make_cover as mc          # noqa: E402
import make_article as ma        # noqa: E402
from word_bank import CATEGORIES, WEAK_ALONE  # noqa: E402

STATE_FILE = BASE / "state" / "seen.json"
OUTPUT_DIR = BASE / "output"
BLANK_PNG = "_blank_slot.png"
UA = {"User-Agent": "Mozilla/5.0 (SUB Autopress; +https://github.com)"}

# Only cover stories published within this many days of now. Items with no
# usable publication date are dropped — an undated item can't be shown to be
# recent, and stale news is worse than a quiet run.
MAX_AGE_DAYS = int(os.environ.get("SUB_MAX_AGE_DAYS", "7"))

# Cap on article-page fetches per run when a feed omits publication dates.
MAX_DATE_LOOKUPS = 8

# Native RSS feeds that publish real <pubDate> values.
FIXED_FEEDS = [
    "https://www.nme.com/feed",
    "https://hypebeast.com/feed",
    "https://www.dazeddigital.com/rss",
]

# Publications whose own feeds omit dates (Mixmag ships empty <pubDate>, and
# its article pages carry no date metadata either) are read through Google
# News instead, which supplies a reliable publication date for every item.
SITE_QUERIES = [
    "site:mixmag.net",
    "site:crackmagazine.net",
    "site:thefader.com",
]

FIXED_QUERIES = [
    '"UK garage" OR grime OR "UK drill" music',
    'London streetwear OR "London Fashion Week"',
    'London "youth culture" OR subculture',
]


# --------------------------------------------------------------------------
# Feed fetching (stdlib XML parsing — handles RSS 2.0 and Atom)
# --------------------------------------------------------------------------
def google_news_url(query):
    """Google News RSS search, server-side limited to the freshness window
    via the `when:Nd` operator so stale results never even arrive."""
    q = urllib.parse.quote(f"{query} when:{MAX_AGE_DAYS}d")
    return f"https://news.google.com/rss/search?q={q}&hl=en-GB&gl=GB&ceid=GB:en"


def strip_tags(text):
    return html.unescape(re.sub(r"<[^>]+>", " ", text or "")).strip()


def parse_date(raw):
    """Parse an RSS (RFC 822) or Atom (ISO 8601) date into an aware datetime.
    Returns None if the value is missing or unparseable."""
    raw = (raw or "").strip()
    if not raw:
        return None
    try:                                   # RSS 2.0: Tue, 28 Jul 2026 09:15:00 +0100
        dt = email.utils.parsedate_to_datetime(raw)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        pass
    try:                                   # Atom: 2026-07-28T09:15:00Z
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_feed(xml_bytes, strip_publisher=False):
    """Yield dicts {title, link, summary, published} from RSS or Atom.

    Google News titles are formatted "Headline - Publisher"; the publisher
    name is not part of the story and scoring it causes false matches (a
    story from tyla.com scoring as the artist Tyla), so strip it there."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return
    ns = {"atom": "http://www.w3.org/2005/Atom",
          "dc": "http://purl.org/dc/elements/1.1/"}
    items = root.findall(".//item") or root.findall(".//atom:entry", ns)
    for it in items:
        def grab(*tags):
            for t in tags:
                el = it.find(t, ns)
                if el is not None and (el.text or el.get("href")):
                    return el.text or el.get("href")
            return ""
        title = strip_tags(grab("title", "atom:title"))
        if strip_publisher:
            title = re.sub(r"\s+-\s+[^-]{2,40}$", "", title).strip()
        link = (grab("link", "atom:link") or "").strip()
        summary = strip_tags(grab("description", "atom:summary", "atom:content"))
        published = parse_date(
            grab("pubDate", "dc:date", "atom:published", "atom:updated"))
        if title:
            yield {"title": title, "link": link,
                   "summary": summary[:800], "published": published}


DATE_META_PATTERNS = [
    r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']article:published_time["\']',
    r'<meta[^>]+itemprop=["\']datePublished["\'][^>]+content=["\']([^"\']+)',
    r'"datePublished"\s*:\s*"([^"]+)"',
    r'<time[^>]+datetime=["\']([^"\']+)',
]


def resolve_published(item):
    """Some feeds (Mixmag) ship empty <pubDate>. Fetch the article page and
    read the date out of its metadata. Returns a datetime or None."""
    if not item.get("link"):
        return None
    try:
        r = requests.get(item["link"], headers=UA, timeout=12)
        r.raise_for_status()
        head = r.text[:60000]          # metadata lives near the top
    except Exception:
        return None
    for pat in DATE_META_PATTERNS:
        m = re.search(pat, head, re.I)
        if m:
            dt = parse_date(m.group(1))
            if dt:
                return dt
    return None


def is_fresh(item, now=None):
    now = now or datetime.now(timezone.utc)
    pub = item.get("published")
    if pub is None:
        return False
    # Allow a small future skew for feeds with sloppy clocks/timezones.
    return (now - pub) <= timedelta(days=MAX_AGE_DAYS) and pub <= now + timedelta(hours=12)


def describe_age(item):
    pub = item.get("published")
    if pub is None:
        return "unknown date"
    hours = (datetime.now(timezone.utc) - pub).total_seconds() / 3600
    if hours < 1:
        return "under an hour ago"
    if hours < 24:
        return f"{int(hours)}h ago"
    return f"{int(hours // 24)}d ago"


def fetch_items():
    """Pull items from fixed feeds plus a rotating batch of Google News
    searches built from the word bank."""
    keywords = [k for kws in CATEGORIES.values() for k in kws]
    sampled = random.sample(keywords, min(6, len(keywords)))
    urls = [(u, False) for u in FIXED_FEEDS]
    urls += [(google_news_url(q), True) for q in SITE_QUERIES + FIXED_QUERIES]
    urls += [(google_news_url(f'"{k}"'), True) for k in sampled]

    items, stale = [], 0
    for url, is_news in urls:
        try:
            r = requests.get(url, headers=UA, timeout=15)
            r.raise_for_status()
            for it in parse_feed(r.content, strip_publisher=is_news):
                # Drop clearly-stale dated items now (cheap). Undated items
                # survive to the scoring stage, where the few that matter get
                # their date resolved from the article page.
                if it["published"] is not None and not is_fresh(it):
                    stale += 1
                else:
                    items.append(it)
        except Exception as e:
            print(f"  feed skipped ({e.__class__.__name__}): {url[:80]}")
    undated = sum(1 for i in items if i["published"] is None)
    print(f"  {len(items)} kept ({undated} undated), "
          f"{stale} dropped as older than {MAX_AGE_DAYS}d")
    return items


# --------------------------------------------------------------------------
# Word-bank scoring
# --------------------------------------------------------------------------
def score_item(item):
    """Return (score, matched_keywords, category). Multi-word keywords are
    worth 3, strong single words 2, weak single words 1 — and weak words
    can never qualify an item on their own."""
    text = f"{item['title']} {item['summary']}".lower()
    matched, score, best_cat, cat_scores = [], 0, None, {}
    for cat, kws in CATEGORIES.items():
        for kw in kws:
            if re.search(r"(?<!\w)" + re.escape(kw.lower()) + r"(?!\w)", text):
                # WEAK_ALONE wins over the multi-word bonus: "Crack Magazine"
                # is two words but still just tells us who published the story.
                if kw.lower() in WEAK_ALONE:
                    w = 1
                else:
                    w = 3 if " " in kw else 2
                matched.append(kw)
                score += w
                cat_scores[cat] = cat_scores.get(cat, 0) + w
    if cat_scores:
        best_cat = max(cat_scores, key=cat_scores.get)
    # An item made up only of weak terms doesn't qualify at all.
    if not any(m.lower() not in WEAK_ALONE for m in matched):
        score = 0
    return score, matched, best_cat


# --------------------------------------------------------------------------
# Dedupe state
# --------------------------------------------------------------------------
def item_key(item):
    basis = (item["link"] or item["title"]).strip().lower()
    return hashlib.sha256(basis.encode()).hexdigest()[:20]


def load_seen():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return []


def save_seen(seen):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(seen[-2000:], indent=0))


# --------------------------------------------------------------------------
# Headline + article writing
# --------------------------------------------------------------------------
SUB_STYLE = """You write for SUB Magazine, an independent London title covering
music, fashion and subcultures. Voice: sharp, wry, culturally fluent, British
English. Reference points: grime, UK garage, jungle, drill, streetwear drops,
vintage resale, club culture, estate culture.

Write from the source story provided. It is breaking news from the last few
days — write it in present tense as something happening now, not as a
retrospective. Do not invent quotes, numbers or events that are not in the
source; you may add genuine, well-known cultural context. If the source is
clearly not current news (an anniversary piece, a listicle, an old story
resurfacing), say so by returning a headline of exactly "SKIP".

Headline: 5-10 words, punchy, magazine-cover energy, no ending punctuation
unless it's a question. Body: exactly 4 paragraphs, 180-230 words total,
separated by blank lines. Open mid-scene, end on a landed one-liner.
red_words: 1-3 words copied verbatim from the headline that should print in
SUB red on the cover."""

ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "red_words": {"type": "array", "items": {"type": "string"}},
        "body": {"type": "string"},
        "layout": {"type": "string", "enum": ["photo-left", "text-top"]},
    },
    "required": ["headline", "red_words", "body", "layout"],
    "additionalProperties": False,
}


def write_with_claude(item, matched, category):
    import anthropic
    client = anthropic.Anthropic()
    model = os.environ.get("SUB_MODEL", "claude-opus-4-8")
    published = item.get("published")
    source = (
        f"TODAY: {datetime.now(timezone.utc):%A %d %B %Y}\n"
        f"STORY PUBLISHED: "
        f"{published:%A %d %B %Y} ({describe_age(item)})\n"
        f"CATEGORY: {category}\n"
        f"SOURCE HEADLINE: {item['title']}\n"
        f"SOURCE SUMMARY: {item['summary']}\n"
        f"LINK: {item['link']}\n"
        f"SUB WORD-BANK MATCHES: {', '.join(matched)}"
    )
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SUB_STYLE,
        output_config={"format": {"type": "json_schema", "schema": ARTICLE_SCHEMA}},
        messages=[{"role": "user", "content": source}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("model refused; falling back to template")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def write_with_template(item, matched):
    """No-API fallback: reshape the source item into SUB furniture."""
    headline = re.sub(r"\s+-\s+[^-]+$", "", item["title"]).strip()
    words = headline.split()
    if len(words) > 10:
        headline = " ".join(words[:10])
    red = [m for m in matched if " " not in m and m.lower() in headline.lower()][:2]
    if not red:
        red = [w.strip(".,!?") for w in headline.split()[:1]]
    summary = item["summary"] or item["title"]
    body = (
        f"{summary}\n\n"
        f"That's the story doing the rounds today, and it lands squarely in "
        f"SUB territory: {', '.join(matched[:4])}.\n\n"
        f"As ever with this corner of the culture, the detail matters less than "
        f"the direction of travel. Keep an eye on where this one goes."
    )
    return {"headline": headline, "red_words": red, "body": body,
            "layout": random.choice(["photo-left", "text-top"])}


# --------------------------------------------------------------------------
# Discord
# --------------------------------------------------------------------------
def post_to_discord(webhook, headline, body, cover_path, page_path, link):
    payload = {
        "content": f"**{headline}**",
        "embeds": [{
            "title": headline,
            "description": body[:4000],
            "url": link or None,
            "color": 0x9E3738,
            "footer": {"text": "SUB Autopress"},
        }],
    }
    with open(cover_path, "rb") as f1, open(page_path, "rb") as f2:
        r = requests.post(
            webhook,
            data={"payload_json": json.dumps(payload)},
            files={
                "files[0]": (Path(cover_path).name, f1, "image/png"),
                "files[1]": (Path(page_path).name, f2, "image/png"),
            },
            timeout=30,
        )
    r.raise_for_status()
    print(f"  posted to Discord ({r.status_code})")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
SAMPLE_ITEM = {
    "title": "Nia Archives announces surprise jungle all-nighter at Corsica Studios",
    "link": "https://example.com/nia-archives-corsica",
    "summary": ("Mercury-nominated producer Nia Archives will headline a "
                "surprise all-night jungle session at Corsica Studios next "
                "month, with support from Sherelle and special guests, weeks "
                "after her Up Ya Archives label night sold out Colour Factory."),
    "published": datetime.now(timezone.utc) - timedelta(hours=3),
}


def slugify(text, limit=40):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:limit]


def main():
    test_mode = "--test" in sys.argv
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

    if test_mode:
        candidates = [SAMPLE_ITEM]
        print("test mode: using sample story")
    else:
        print("fetching feeds...")
        candidates = fetch_items()
        print(f"  {len(candidates)} items fetched")

    seen = load_seen()
    scored = []
    for it in candidates:
        if item_key(it) in seen:
            continue
        s, matched, cat = score_item(it)
        if s >= 2:
            scored.append([s, it, matched, cat])
    scored.sort(key=lambda x: x[0], reverse=True)

    # Resolve dates for the best undated candidates (page fetch), then take
    # the first that lands inside the freshness window.
    lookups = 0
    picked = None
    for entry in scored:
        it = entry[1]
        if it["published"] is None:
            if lookups >= MAX_DATE_LOOKUPS:
                continue
            lookups += 1
            it["published"] = resolve_published(it)
            if it["published"] is None:
                print(f"  no date found, skipping: {it['title'][:60]}")
                continue
        if is_fresh(it):
            picked = entry
            break

    if picked is None:
        print(f"no new word-bank matches from the last {MAX_AGE_DAYS} days "
              f"— nothing to post")
        return

    score, item, matched, category = picked
    print(f"picked [{category} | score {score} | {describe_age(item)}]: "
          f"{item['title']}")
    print(f"  matches: {', '.join(matched)}")

    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            art = write_with_claude(item, matched, category)
            if art["headline"].strip().upper() == "SKIP":
                print("  Claude flagged this as not-current news — skipping")
                seen.append(item_key(item))
                save_seen(seen)
                return
            print("  article written by Claude")
        except Exception as e:
            print(f"  Claude failed ({e}); using template fallback")
            art = write_with_template(item, matched)
    else:
        art = write_with_template(item, matched)
        print("  article written by template (no ANTHROPIC_API_KEY)")

    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = slugify(art["headline"])
    cover_out = str(OUTPUT_DIR / f"{slug}-cover.png")
    page_out = str(OUTPUT_DIR / f"{slug}-page.png")
    mc.make_cover(BLANK_PNG, art["headline"], art["red_words"], cover_out)
    ma.make_article(BLANK_PNG, art["body"], page_out, layout=art["layout"])

    if webhook:
        post_to_discord(webhook, art["headline"], art["body"],
                        cover_out, page_out, item["link"])
    else:
        print("  DISCORD_WEBHOOK_URL not set — skipping post. Payload preview:")
        print(f"  headline: {art['headline']}")
        print(f"  red words: {art['red_words']}")
        print(f"  body:\n{art['body']}")
        print(f"  images: {cover_out}, {page_out}")

    seen.append(item_key(item))
    save_seen(seen)


if __name__ == "__main__":
    main()
