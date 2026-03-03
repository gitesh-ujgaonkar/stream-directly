# 🚀 Deployment Guide — TG Stream

Complete checklist to deploy the **backend** (Render, free tier) and the **frontend** (Vercel, free tier) and link them together.

---

## Prerequisites

| Item | How to get it |
|---|---|
| **Telegram API ID & Hash** | [my.telegram.org](https://my.telegram.org) → API Development Tools |
| **Bot Token** | [@BotFather](https://t.me/BotFather) → `/newbot` |
| **GitHub repo** | Push this entire project to a GitHub repository |

---

## 1 · Deploy the Backend to Render

1. Go to [render.com](https://render.com) and sign up (free, no card required).
2. Click **New +** → **Web Service**.
3. Connect your GitHub repo.
4. Configure:
   | Setting | Value |
   |---|---|
   | **Name** | `tg-stream-api` |
   | **Root Directory** | `backend` |
   | **Runtime** | Docker |
   | **Plan** | Free |
5. Add **Environment Variables**:
   ```
   API_ID       = <your Telegram API ID>
   API_HASH     = <your Telegram API Hash>
   BOT_TOKEN    = <your Bot Token>
   FRONTEND_URL = https://your-app.vercel.app   ← update after Vercel deploy
   ```
6. Click **Create Web Service** and wait for the build.
7. Once live, note your Render URL (e.g. `https://tg-stream-api.onrender.com`).
8. Test: open `https://tg-stream-api.onrender.com/health` — you should see `{"status":"ok"}`.

---

## 2 · Deploy the Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) and sign up with GitHub.
2. Click **Import Project** → select your GitHub repo.
3. Configure:
   | Setting | Value |
   |---|---|
   | **Framework Preset** | Vite |
   | **Root Directory** | `frontend` |
   | **Build Command** | `npm run build` |
   | **Output Directory** | `dist` |
4. Add **Environment Variable**:
   ```
   VITE_BACKEND_URL = https://tg-stream-api.onrender.com   ← your Render URL from step 1
   ```
5. Click **Deploy**.
6. Note your Vercel URL (e.g. `https://your-app.vercel.app`).

---

## 3 · Link the URLs (CRITICAL)

After both are deployed, you need to cross-reference the URLs:

```
┌─────────────┐  VITE_BACKEND_URL   ┌──────────────┐
│   Vercel     │ ──────────────────► │   Render     │
│  (Frontend)  │                     │  (Backend)   │
│              │ ◄────────────────── │              │
└─────────────┘  FRONTEND_URL (CORS) └──────────────┘
```

1. **On Render** → Environment → set `FRONTEND_URL` to your Vercel domain (e.g. `https://your-app.vercel.app`). Redeploy.
2. **On Vercel** → Settings → Environment Variables → `VITE_BACKEND_URL` should already point to Render. If you changed the Render URL, update it and redeploy.

---

## 4 · Test End-to-End

1. Open Telegram → find your bot → send `/start`.
2. Forward any video file to the bot.
3. The bot replies with a streaming link → click it.
4. The video should play in the Plyr.js player on your Vercel site.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| CORS error in browser console | Ensure `FRONTEND_URL` on Render matches your exact Vercel domain (including `https://`) |
| Video doesn't load | Check Render logs → the Pyrogram client may not have started (invalid credentials) |
| Bot doesn't reply | Verify `BOT_TOKEN` is correct; check Render logs for handler errors |
| Render spins down after inactivity | Free-tier services sleep after 15 min of no traffic — first request takes ~30s to wake |

---

## ⚠️ Free Tier Limitations

- **Render Free**: 750 hours/month, auto-sleep after 15 min idle, 512 MB RAM.
- **Vercel Free**: 100 GB bandwidth/month, serverless functions limited, but static hosting is unlimited.
- **Telegram**: Max file size for bots is **50 MB** download / **2 GB** upload. For larger files, use a user-account session string instead of a bot token.
