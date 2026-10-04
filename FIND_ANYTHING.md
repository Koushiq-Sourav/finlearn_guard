> **CONTRIBUTION:** Index that maps every task to its exact file and section.

# FIND ANYTHING — task to file map

Start here when you don't know where something lives.
Rule of thumb: looks = `static/` + `templates/`, behavior = `src/`,
papers = `docs/`, demo = `live/` + `instructor/`.

## I want to RUN / SHOW it
| Want | Open |
|---|---|
| Start the server before class | `live/start_live.bat` (double-click, keep window open) |
| Dashboard / Support links | http://127.0.0.1:8000/ and http://127.0.0.1:8000/support |
| 3-minute demo path | `instructor/DEMO_SCRIPT.txt` |
| Deploy online (Render/Docker) | `live/README_LIVE.txt`, `live/render.yaml`, `Dockerfile` |
| Prove it works (tests) | run `.venv/Scripts/python -m pytest tests -q` (uses `tests/`) |

## I want to CHANGE the look (save file, refresh browser, no restart)
| Want | Open | Section |
|---|---|---|
| Big headline / subtitle / hero buttons | `templates/pages/dashboard.html` | BLOCK 1: HERO |
| Feed, Simulate button, inspector, graphs | `templates/pages/dashboard.html` | BLOCK 2: LIVE FEED |
| Employees table + add form | `templates/pages/dashboard.html` | BLOCK 3: EMPLOYEES |
| Support ask box / Steps-Voice-Video tabs | `templates/pages/support.html` | PART A (ask) / PART B (answer) |
| Topbar on every page (brand, links, LIVE pill) | `templates/layouts/base.html` | TOPBAR |
| Colors of everything | `static/css/style.css` | S0 theme tokens (`:root`) |
| Navbar / topbar style | `static/css/style.css` | S2 TOPBAR |
| ALL buttons in one place | `static/css/style.css` | S3 BUTTONS |
| Hero, cards, feed, tables, support, graphs | `static/css/style.css` | S4-S8 (see section map at file top) |
| Inspector box + danger meter style | `static/css/style.css` | S11 INSPECTOR |

## I want to CHANGE behavior (see golden rule in docs/GUIDE_BOOK.md)
| Want | Open | Section |
|---|---|---|
| Feed rows, inspector steps, graphs, auto-feed | `static/js/app.js` | S4 (feed), S4f (inspector), S4d (graphs) |
| Danger words / detection weights (needs restart) | `src/detection/rules.py` | PATTERN TABLE |
| What the AI is told (needs restart) | `src/llm/prompts/detector.txt`, `src/llm/prompts/support.txt` | whole file |
| Add a new page (needs restart) | `src/web/routes_web.py` | PAGE 1-4 blocks (+ new template + nav link in `base.html`) |
| API doors (needs restart) | `src/api/routes_api.py` | HEALTH / EMPLOYEES / THREATS / SUPPORT / DEVICES |
| Live push channel (needs restart) | `src/api/ws.py` | SUBSCRIBERS / BROADCAST / HANDLER |
| Detection steps (needs restart) | `src/agents/detector.py` | §2 STEP 1 rules, STEP 2 AI, STEP 3 safety, STEP 4 medium lock |
| Guide writing (needs restart) | `src/agents/support.py` | §3 diagnose() + §2 pools (7 kinds: phishing/otp/bec/sqli/xss/malware) |
| Voice mp3 / video mp4 (needs restart) | `src/media/voice.py`, `src/media/video.py` | PATHS / RENDER |
| Employees, threats, devices data (needs restart) | `src/storage/database.py` | MongoDB collections |
| Server wiring (needs restart) | `src/main.py` | APP / MEDIA / WEBSOCKET |
| Endpoint agent on other PCs | `agent/agent.py` (+ `install.bat`) | CONFIG / SNAPSHOT / MAIN LOOP |

## I want to READ / SHOW papers
| Want | Open |
|---|---|
| Thesis for madam (PDF) | `docs/THESIS.pdf` (editable source: `docs/THESIS.html`) |
| Live-edit guide book (PDF) | `docs/GUIDE_BOOK.pdf` (editable source: `docs/GUIDE_BOOK.md`) |
| Architecture / API table / report points | `instructor/` (4 txt files) |

## I want CONFIG / SECRETS (never show on projector, never push to git)
| Want | Open |
|---|---|
| AI key, model, database URL | `.env` (edit) / `.env.example` (safe template) |
| Python packages | `requirements.txt` |
| Which Python runs it | `.venv/` (Python 3.13 64-bit, already installed) |
| Generated voice/video cache | `data/media/` (safe to delete; regenerates) |
