# Google Drive Evidence Setup — NETRA

SOS confirm hone par engine automatically snapshot + Gemini forensic report ko
Google Drive pe upload karta hai. Iske liye ek **Service Account** chahiye.

---

## Step 1: Google Cloud Project banao

1. https://console.cloud.google.com/ par jao
2. "Select a project" → **New Project** → naam do (e.g. `netra-evidence`)
3. Project select karke **Create**

## Step 2: Google Drive API enable karo

1. Sidebar → **APIs & Services** → **Library**
2. Search "Google Drive API" → uspe click karo → **Enable**

## Step 3: Service Account banao

1. **APIs & Services** → **Credentials** → **Create Credentials** → **Service Account**
2. Naam do (e.g. `netra-uploader`) → **Create and Continue** → **Done**
3. Service account list me uspe click karo
4. **Keys** tab → **Add Key** → **Create new key** → **JSON** → **Create**
5. Ek `.json` file download hogi — ise project root me `credentials.json` naam se save karo

## Step 4: Ek Drive folder banao aur share karo

1. Google Drive me ek folder banao (e.g. `NETRA Evidence`)
2. Folder ka ID URL se nikaalo: `https://drive.google.com/drive/folders/THIS_IS_THE_FOLDER_ID`
3. Folder ko service account ke email se share karo:
   - Folder pe right-click → **Share**
   - Service account ka email (jo JSON me `client_email` field me hai, e.g. `netra-uploader@netra-evidence.iam.gserviceaccount.com`)
   - **Editor** permission do → **Send**

## Step 5: .env file me daalo

Apne `.env` me ye 2 lines update karo:

```
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
DRIVE_FOLDER_ID=your_folder_id_here
```

`credentials.json` ka path — agar file project root me hai toh bas `credentials.json`
likhna kaafi hai. `DRIVE_FOLDER_ID` optional hai, lekin recommended taaki saare
evidence files ek folder me aayein.

## Step 6: Test karo

1. Engine start karo: `python engine\netra_engine.py`
2. Console me dekho — agar Drive ON dikhta hai:
   ```
   [NETRA ENGINE] drive archive  -> ON
   ```
3. SOS gesture trigger hone par (3 second haath upar) console me:
   ```
   [NETRA ENGINE] 🗂 evidence archived -> https://drive.google.com/...
   [NETRA ENGINE] 📄 forensic report  -> https://drive.google.com/...
   ```

---

## Important Notes

- **`credentials.json` kabhi commit mat karo** — ye `.gitignore` me already hai
- Service account ka free quota: 15GB Drive storage (enough for demo)
- Agar Drive setup nahi karna, toh bhi engine chalega — bas upload skip ho jayega
- Gemini forensic report bina Drive ke bhi console me print hoti hai
