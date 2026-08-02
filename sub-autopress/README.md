# SUB Autopress

Automated SUB Magazine news bot. Every 5 minutes it:

1. Scans music / fashion / subculture news feeds (NME, Hypebeast, Dazed,
   Mixmag, Crack Magazine, The Fader + rotating Google News searches built
   from the SUB word bank)
2. Throws away anything **published more than 7 days ago** (see Freshness)
3. Scores each story against the SUB word bank (`word_bank.py`) and picks
   the best unseen match
4. Writes a SUB-style headline + 4-paragraph article (Claude if an API key
   is set, otherwise a simple template)
5. Renders a **cover** and an **article page** (2080x2600) using the
   existing `make_cover.py` / `make_article.py` scripts, with the photo
   slot left as the blank placeholder PNG
6. Posts both images, the headline and the article text to your Discord
   webhook

It only posts when a *new* word-bank match appears — quiet runs post nothing.
Seen stories are tracked in `state/seen.json`.

## Freshness: nothing older than a week

Every story that ships is date-verified against a 7-day window. Three layers
enforce it:

- **At the source** — Google News searches carry the `when:7d` operator, so
  stale results never even arrive.
- **At parse time** — each item's `pubDate` (RSS) or `published`/`updated`
  (Atom) is parsed and anything outside the window is dropped. Items dated in
  the future by more than 12 hours are dropped too (sloppy feed clocks).
- **Before publishing** — a final check runs on the chosen story, and if
  Claude judges the source to be an anniversary piece, listicle or resurfaced
  old story rather than current news, it returns `SKIP` and nothing is posted.

**An item with no verifiable date is never published.** Where a feed omits
dates, the app fetches the article page and reads the date out of its
metadata (`article:published_time`, JSON-LD `datePublished`, `<time
datetime>`), capped at 8 lookups per run so the job stays fast.

Mixmag is a special case: its RSS ships empty `<pubDate>` tags *and* its
article pages carry no date metadata at all, so it is read through a
`site:mixmag.net` Google News query instead — same coverage, with a reliable
date on every item. Crack Magazine and The Fader are pulled the same way.

Change the window with the `SUB_MAX_AGE_DAYS` env var (default `7`), e.g.
`SUB_MAX_AGE_DAYS=3` for a tighter feed.

## Host it for free (GitHub Actions)

GitHub Actions gives unlimited free minutes on **public** repos and supports
5-minute cron schedules (note: GitHub sometimes delays scheduled runs by a
few minutes under load).

1. Create a new **public** GitHub repo and push this folder to it
   (make sure `.github/workflows/sub-autopress.yml` is included):

   ```bash
   cd sub-autopress
   git init && git add -A && git commit -m "SUB Autopress"
   gh repo create sub-autopress --public --source=. --push
   ```

2. In the repo: **Settings → Secrets and variables → Actions → New repository
   secret** and add:

   | Secret | Required | What |
   |---|---|---|
   | `DISCORD_WEBHOOK_URL` | yes | Discord: channel → Edit → Integrations → Webhooks → New Webhook → Copy URL |
   | `ANTHROPIC_API_KEY` | optional | enables Claude-written headlines/articles (recommended — the no-key fallback is basic, and the `SKIP` check for non-current news only runs with a key) |

3. In the repo: **Settings → Actions → General → Workflow permissions** →
   select **Read and write permissions** (needed to commit `state/seen.json`).

4. Test it: **Actions → SUB Autopress → Run workflow**. After that it runs
   itself every 5 minutes.

Cost note: the hosting is free; the Claude API is pay-as-you-go. The default
model is `claude-opus-4-8` (best writing). Set a repo **variable** or edit
`SUB_MODEL` env in the workflow to use a cheaper model (e.g.
`claude-haiku-4-5`) if the spend adds up — it only calls the API when a new
story is actually found.

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..." \
ANTHROPIC_API_KEY="sk-ant-..." \
.venv/bin/python app.py

# dry test with a canned story (no posting if no webhook set):
.venv/bin/python app.py --test
```

## Tuning

- **Freshness** — `SUB_MAX_AGE_DAYS` env var, default `7`.
- **Word bank** — edit `word_bank.py`. Multi-word names score 3, strong
  single words 2, and anything in `WEAK_ALONE` scores 1 and can never
  qualify a story on its own. `WEAK_ALONE` holds generic words (`drill`,
  `jungle`) plus publication and platform names (`Dazed`, `Crack Magazine`,
  `Depop`) — those appear in the boilerplate of the very feeds being read,
  so a Dazed article mentioning "Dazed" is not a SUB story. An item needs a
  score of 2+ from at least one non-weak term to be picked.
- **Feeds** — edit `FIXED_FEEDS` (native RSS), `SITE_QUERIES` (publications
  read via Google News for reliable dates) and `FIXED_QUERIES` in `app.py`.
  Six random word-bank keywords are also searched on Google News each run.
  If you add a native RSS feed, check it actually publishes `<pubDate>`
  values — one that doesn't will have every item dropped as undated.
- **Voice** — edit `SUB_STYLE` in `app.py`.
- **Images** — swap `_blank_slot.png` for a real photo any time; the
  layouts come straight from `make_cover.py` / `make_article.py`.
