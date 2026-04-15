# Indonesia Macro Dashboard

Real-time macro intelligence dashboard for Indonesia — built for investors and fund managers.

## Stack
- **Data collectors**: Python + GitHub Actions (free)
- **Database**: Supabase Postgres (free tier)
- **Backend API**: FastAPI on Render (free tier)
- **Frontend**: Vanilla HTML/JS on Vercel or GitHub Pages (free)
- **AI briefs**: Claude API (your enterprise subscription)

---

## Setup (30 minutes)

### 1. Supabase
1. Create project at [supabase.com](https://supabase.com)
2. Go to SQL Editor → paste contents of `schema.sql` → Run
3. Copy your **Project URL** and **service_role key** (Settings → API)

### 2. API Keys (all free)
| Key | Where to get |
|---|---|
| `SUPABASE_URL` | Supabase → Settings → API |
| `SUPABASE_SERVICE_KEY` | Supabase → Settings → API → service_role |
| `FRED_API_KEY` | [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `BPS_API_KEY` | [webapi.bps.go.id](https://webapi.bps.go.id) → Register → Request key |
| `ANTHROPIC_API_KEY` | Your enterprise Claude account |

### 3. GitHub Actions
1. Push this repo to GitHub
2. Go to Settings → Secrets and variables → Actions
3. Add all 5 keys above as repository secrets
4. Collectors will run automatically on schedule
5. Manual trigger: Actions tab → "Macro Data Collectors" → Run workflow

### 4. Backend API (Render)
1. Create account at [render.com](https://render.com)
2. New → Web Service → connect your GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
6. Deploy → copy your `.onrender.com` URL

### 5. Frontend (GitHub Pages — zero setup)
1. Enable GitHub Pages in repo Settings → Pages → Deploy from `dashboard/` folder
2. Edit `dashboard/index.html` line with `API_BASE` → paste your Render URL
3. Push → live at `https://yourusername.github.io/indonesia-macro/`

---

## Running Collectors Manually

```bash
pip install -r requirements.txt

# Set env vars
export SUPABASE_URL=...
export SUPABASE_SERVICE_KEY=...
export FRED_API_KEY=...
export ANTHROPIC_API_KEY=...

# Run individual collectors
python collectors/fx_jci.py
python collectors/commodities.py
python collectors/fred_data.py
python collectors/bps_data.py

# Generate this week's brief
python collectors/weekly_brief.py
```

---

## BPS API Note
BPS variable IDs can change. Verify current IDs at:
`https://webapi.bps.go.id/developer/` → API Explorer

Key variables to confirm:
- CPI headline YoY: search "inflasi year on year"
- Trade exports/imports: search "ekspor impor"

---

## Data Sources
| Data | Source | Update frequency |
|---|---|---|
| USD/IDR, JCI | Yahoo Finance | Hourly |
| DXY | Yahoo Finance | Hourly |
| CPO, Coal, Nickel, Brent | Yahoo Finance | Daily |
| Fed Funds Rate, VIX, China PMI | FRED (St. Louis Fed) | Daily |
| CPI, Trade Balance | BPS Indonesia | Monthly |
| BI Rate | Manual entry (post-RDG) | ~8x/year |
| Foreign Reserves | Manual entry (BI press release) | Monthly |
| SBN Foreign Ownership | Manual entry (DJPPR) | Weekly |
| AI Weekly Brief | Claude API | Weekly (Monday) |

---

## Cost
**$0/month** to start.

Upgrade triggers:
- Supabase → >500MB data or >5GB bandwidth ($25/mo)
- Render → need always-on or more RAM ($7–25/mo)
- Mapbox → only if you add a map layer (free up to 50k loads)
