# YouTube Upload — One-Time Setup

The **transcribe** and **compress** features work out of the box. Only the
**"Upload to YouTube"** button needs this extra setup, because uploading on
your behalf requires Google credentials that only you control.

You'll create a free Google Cloud project, turn on the YouTube API, and
download a small `.json` file. Takes about 5 minutes.

---

## Why do I have to do this myself?

The transcriber is open-source, so I can't ship my own Google credentials
with it — anyone could copy them and spam YouTube under my name, and
Google would shut them down. The clean solution is that **you create your
own credentials** and plug them into the app. You only do this once.

If you ever stop using the app, you can delete the Google Cloud project and
the credentials vanish with it.

---

## Step 1 — Create a Google Cloud project

1. Go to **<https://console.cloud.google.com>**
2. Sign in with the Google account that **owns the YouTube channel** you
   want to upload to.
3. Top of the page, click the project dropdown → **New Project**.
4. Name it something like `transcriber-upload`. Click **Create**.
5. Make sure the new project is selected in the dropdown.

---

## Step 2 — Enable the YouTube Data API

1. In the left menu, go to **APIs & Services → Library**.
   (Or paste this: <https://console.cloud.google.com/apis/library>)
2. Search for **YouTube Data API v3**.
3. Click it, then click **Enable**.

---

## Step 3 — Configure the OAuth consent screen

This is the screen you'll see in your browser when the app asks for
permission. Since only you will use it, keep it simple.

1. Left menu → **APIs & Services → OAuth consent screen**.
2. Pick **External**, click **Create**.
3. Fill in the required fields:
   - **App name:** `Transcriber` (or anything you like)
   - **User support email:** your email
   - **Developer contact email:** your email
   - Everything else: leave blank
4. Click **Save and Continue** through the remaining screens. You don't
   need to add scopes here — the app requests them at sign-in time.
5. On the **Test users** page, click **Add Users** and add **your own
   Google email address**. This is important — unverified apps can only
   be used by listed test users.
6. Click **Save and Continue**, then **Back to Dashboard**.

> You don't need to publish the app or submit it for verification. "Testing"
> mode is fine for personal use.

---

## Step 4 — Create OAuth credentials

1. Left menu → **APIs & Services → Credentials**.
2. Click **+ Create Credentials** → **OAuth client ID**.
3. **Application type:** pick **Desktop app**.
4. **Name:** `Transcriber Desktop` (or anything).
5. Click **Create**.
6. A popup appears with your client ID. Click **Download JSON**.

You'll get a file named something like
`client_secret_123456789-abc...apps.googleusercontent.com.json`.

---

## Step 5 — Drop it into the transcriber

1. In the Transcriber app, click **Sign in to YouTube**. It'll detect the
   missing file and offer an **"Open secrets folder"** button — click it
   and the folder opens in Explorer.
2. Drag the downloaded `client_secret_*.json` file into that folder.
3. Back in the app, click **Sign in to YouTube** again.
4. Browser opens → sign in with the same Google account → approve the
   permissions → tab shows "Authorized!"

You're done. Every upload from now on uses the saved token — you won't
need to sign in again unless you move to a new machine.

---

## Troubleshooting

**"This app isn't verified"** — Normal. Click **Advanced → Go to
Transcriber (unsafe)**. It's marked unsafe because Google hasn't reviewed
your personal app, but it only has the access you just granted it.

**"Access blocked: authorization error"** — Usually means you didn't add
your email as a test user in Step 3. Go back and add it.

**"Error 403: access_denied"** — Same cause as above, or you signed in with
a different Google account than the one you added as a test user.

**Want to revoke access later?** Go to
<https://myaccount.google.com/permissions>, find "Transcriber", and remove
it. The next sign-in will ask for permission again.

**Want to delete everything?** Go to the Cloud Console, pick the project,
and click **IAM & Admin → Settings → Shut Down**. Gone.

---

## YouTube API quota

Google gives every project **10,000 quota units per day** for free, and
uploads cost **1,600 units each**. That means you can upload **about 6
videos per day** before hitting the limit. For a personal project that's
usually plenty; the quota resets at midnight Pacific time.

If you need more, you can request a quota increase in the Cloud Console,
but you probably won't.
