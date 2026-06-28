# ☕ Upsarpanch ChaiFi – Billing App

Streamlit billing + sales dashboard with **Google Sheets** as the permanent database.
Every confirmed bill is written to a Google Sheet automatically, so your data survives restarts and is accessible from any device.

---

## Quick Start (local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Google Sheets Setup (one-time, ~10 minutes)

### Step 1 — Create a Google Cloud project & service account

1. Go to https://console.cloud.google.com
2. Click **Select a project → New Project**. Name it `chaifi-billing` and click **Create**.
3. In the left menu go to **APIs & Services → Library**.
   - Search **Google Sheets API** → Enable it.
   - Search **Google Drive API** → Enable it.
4. Go to **APIs & Services → Credentials → Create Credentials → Service Account**.
   - Name: `chaifi-billing`
   - Click **Create and Continue → Done**.
5. Click the service account email you just created.
6. Go to the **Keys** tab → **Add Key → Create new key → JSON** → Download the file.

### Step 2 — Create the Google Sheet

1. Go to https://sheets.google.com and create a new blank spreadsheet.
2. Name it exactly: **`ChaiFi_Bills`**
3. Open the JSON key file you downloaded. Find the `client_email` field (looks like `chaifi-billing@your-project.iam.gserviceaccount.com`).
4. In the Google Sheet, click **Share** and share the sheet with that email address as **Editor**.

### Step 3 — Add credentials to Streamlit

**Local:**
Edit `.streamlit/secrets.toml` and paste each value from the downloaded JSON file into the matching field.

**Streamlit Cloud:**
1. Go to your app in https://share.streamlit.io
2. Click **⋮ → Settings → Secrets**
3. Paste the entire contents of `.streamlit/secrets.toml` (with your real values filled in)

### Step 4 — Deploy

Push all files to GitHub, deploy on https://share.streamlit.io — done!
The green badge at the top of the app confirms Google Sheets is connected.

---

## What gets saved to the Sheet

| Column | Example |
|--------|---------|
| Bill No | 1042 |
| Date | 2026-06-28 |
| Time | 14:35:00 |
| Customer | Walk-in |
| Token | T-3 |
| Items (JSON) | `{"Spl Gud ki Chai (Cup)": 2, "Bun Maska": 1}` |
| Subtotal | 70 |
| Discount | 0 |
| Total | 70 |

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit app |
| `requirements.txt` | Python dependencies |
| `.streamlit/secrets.toml` | Credentials template (fill in your values) |
