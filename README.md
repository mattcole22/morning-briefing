# 📊 Portfolio Morning Briefing — Automated Emailer

Automatically generates your full Portfolio Morning Briefing using the Claude API and emails it to you at **6:00 AM ET every weekday**, via GitHub Actions (free, cloud-hosted, no computer required).

---

## How It Works

```
GitHub Actions (6 AM ET)
       ↓
  run_briefing.py
       ↓
  Claude API (Sonnet 4)
  [runs full briefing prompt with web search + FMP + Twelvedata]
       ↓
  HTML email formatted briefing
       ↓
  Your inbox
```

---

## One-Time Setup (~15 minutes)

### Step 1 — Get Your Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Click **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-...`) — you'll only see it once
5. Add a credit card and load at least $5 in credits
   - Each briefing costs approximately **$0.10–$0.25** (Sonnet 4 rates)
   - $5 covers ~3–6 weeks of daily briefings

---

### Step 2 — Set Up Gmail App Password

You need a special "App Password" — Gmail won't accept your regular login password for automated sending.

1. Go to your Google Account → **Security**
2. Make sure **2-Step Verification** is turned ON (required)
3. Search for **"App passwords"** in the Security settings
4. Click **App passwords** → **Select app: Mail** → **Select device: Other** → type "Morning Briefing"
5. Click **Generate** — copy the 16-character password shown (e.g. `abcd efgh ijkl mnop`)
6. Save it — you won't see it again

> 💡 If you don't use Gmail, see the **Alternative Email Providers** section at the bottom.

---

### Step 3 — Create the GitHub Repository

1. Go to [github.com](https://github.com) and log in
2. Click the **+** icon → **New repository**
3. Name it: `morning-briefing` (or anything you like)
4. Set it to **Private** ✅ (important — keeps your prompt confidential)
5. Click **Create repository**
6. Upload these files from this package (drag & drop onto the GitHub file upload page):

```
.github/
  workflows/
    morning_briefing.yml
scripts/
  run_briefing.py
  briefing_prompt.txt
requirements.txt
README.md
```

**To upload:**
- Click **Add file** → **Upload files**
- Drag all files/folders in
- Click **Commit changes**

> ⚠️ You must preserve the folder structure. The `.github/workflows/` path is required by GitHub Actions.

---

### Step 4 — Add Your Secrets

GitHub Secrets store your sensitive credentials — they're encrypted and never visible in logs.

1. In your repository, click **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** for each of the following:

| Secret Name | Value | Example |
|---|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-api03-...` |
| `EMAIL_FROM` | Your Gmail address | `yourname@gmail.com` |
| `EMAIL_TO` | Where to send the briefing | `yourname@gmail.com` |
| `SMTP_USER` | Your Gmail address (same as FROM) | `yourname@gmail.com` |
| `SMTP_PASS` | Your Gmail App Password | `abcd efgh ijkl mnop` |

> Enter each one individually. The name must match exactly (case-sensitive).

---

### Step 5 — Test It Manually

Before waiting for 6 AM, trigger a test run right now:

1. In your repository, click the **Actions** tab
2. Click **Portfolio Morning Briefing** in the left sidebar
3. Click **Run workflow** → **Run workflow** (green button)
4. Watch the run — click on it to see live logs
5. Check your inbox in ~3–5 minutes

If it fails, click the failed step to see the error log — the most common issues are listed in the Troubleshooting section below.

---

### Step 6 — Adjust the Schedule (Summer vs. Winter)

GitHub Actions uses UTC. The schedule needs a small tweak twice a year:

| Season | ET Offset | UTC Equivalent of 6 AM ET | Cron Line |
|---|---|---|---|
| **EDT (Mar–Nov)** | UTC-4 | **10:00 UTC** | `0 10 * * 1-5` |
| **EST (Nov–Mar)** | UTC-5 | **11:00 UTC** | `0 11 * * 1-5` |

The workflow ships with `0 10 * * 1-5` (EDT / summer).

**To switch to winter (EST):**
1. Open `.github/workflows/morning_briefing.yml`
2. Change `0 10 * * 1-5` to `0 11 * * 1-5`
3. Commit the change

> 📅 Daylight saving time ends first Sunday of November, resumes second Sunday of March.

---

## Updating the Briefing Prompt

To add/remove portfolio tickers or change the prompt:

1. Edit `scripts/briefing_prompt.txt` directly in GitHub (click the file → pencil icon)
2. Commit the change
3. It takes effect on the next scheduled run

---

## Troubleshooting

### "Authentication Failed" email error
→ Your Gmail App Password is wrong. Re-generate it in Google Account → Security → App passwords.
→ Make sure 2-Step Verification is enabled on your Google account.

### "Invalid API key" error
→ Double-check the `ANTHROPIC_API_KEY` secret. It must start with `sk-ant-`.
→ Make sure you have credits loaded at console.anthropic.com.

### Email sends but briefing is incomplete
→ Claude timed out on a long run. The 30-minute timeout in the workflow is generous, but occasionally a run can stall. Just re-run manually via the Actions tab.

### Action doesn't run at 6 AM
→ GitHub Actions schedules can run up to 15 minutes late during high traffic periods — this is normal.
→ If it never runs: check that the workflow file is in `.github/workflows/` (not just `workflows/`).

### "Module not found: zoneinfo"
→ `zoneinfo` is built into Python 3.9+. The workflow uses Python 3.12, so this shouldn't occur. If it does, the install step handles it with a fallback.

---

## Alternative Email Providers

If you don't use Gmail, update these environment variables:

**Outlook / Hotmail:**
```
SMTP_HOST = smtp-mail.outlook.com
SMTP_PORT = 587
```

**Yahoo Mail:**
```
SMTP_HOST = smtp.mail.yahoo.com
SMTP_PORT = 587
```
(Yahoo also requires an App Password — generate at Yahoo Account Security)

**iCloud Mail:**
```
SMTP_HOST = smtp.mail.me.com
SMTP_PORT = 587
```

Add `SMTP_HOST` and `SMTP_PORT` as additional GitHub Secrets if using a non-Gmail provider.

---

## Cost Estimate

| Item | Cost |
|---|---|
| GitHub Actions | Free (2,000 min/month free tier, briefing uses ~5 min) |
| Claude API (Sonnet 4) | ~$0.10–$0.25 per briefing |
| 22 trading days/month | ~$2.20–$5.50/month |
| Email delivery (Gmail SMTP) | Free |

---

## File Structure

```
morning-briefing/
├── .github/
│   └── workflows/
│       └── morning_briefing.yml    ← Schedule + runner config
├── scripts/
│   ├── run_briefing.py             ← Main script (Claude API + email)
│   └── briefing_prompt.txt         ← Your full briefing prompt (edit here)
├── requirements.txt                ← Python dependencies
└── README.md                       ← This file
```

---

*For informational purposes only. Not investment advice.*
