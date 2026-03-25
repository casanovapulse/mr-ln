# 🎬 Social Media Video Automation Pipeline

Automated video processing and social media publishing pipeline. Fetches videos from Dropbox, upscales them, removes watermarks, and publishes to multiple social media platforms.

## 🚀 Features

- **GitHub Actions Automation**: Runs 3 times a day automatically
- **Dropbox Integration**: Automatically fetch videos from your Dropbox folder
- **Smart Processing**: Only downloads and processes videos when needed
- **Video Processing**:
  - Upscale to 1080x1920 (vertical format for Reels/Shorts/TikTok)
  - Watermark removal (bottom-right corner)
  - Audio enhancement (normalize volume, improve clarity)
- **Multi-Platform Upload**:
  - Instagram Reels & Stories
  - Facebook Reels & Stories
  - Threads
  - YouTube Shorts
- **Continuous Mode**: Runs forever by re-downloading and reprocessing old videos

## 🔄 Automation Workflow

```
GitHub Actions (3 times daily)
        ↓
Check Dropbox video NAMES (no download)
        ↓
New videos exist?
   ├─ YES → Download NEW → Process → Upload → Mark as published ✅
   └─ NO  → Get NEXT old video (rotation) → Download → Process → Upload ✅
```

### How It Works (Step by Step)

**Scenario 1: New Video in Dropbox**
```
1. GitHub Actions runs (3x daily)
2. Gets video NAMES from Dropbox (no download yet)
3. Compares names with published_videos.json
4. Finds NEW video (not in published list)
5. Downloads ONLY new video
6. Processes video (upscale + watermark removal)
7. Uploads to all social media platforms
8. Marks as published in published_videos.json
9. Cleans up downloaded files (saves space)
```

**Scenario 2: No New Videos (Continuous Mode)**
```
1. GitHub Actions runs (3x daily)
2. Gets video NAMES from Dropbox
3. All videos already published
4. Gets NEXT video name from rotation (tracks in rotation_state.json)
5. Downloads that video
6. Reprocesses video (fresh upscale + watermark removal)
7. Uploads to all social media platforms
8. Marks as published (increment count)
9. Cleans up downloaded files (saves space)
10. Next run: Gets DIFFERENT video (never same twice in a row)
```

### Why This Works Forever

✅ **No storage needed** - Everything from Dropbox  
✅ **Rotation tracking** - `rotation_state.json` tracks last posted video  
✅ **Never repeats** - Always gets next video in sequence  
✅ **Fresh processing** - Every video reprocessed each time  
✅ **Clean** - Downloads deleted after upload (saves GitHub space)  

## 📋 Prerequisites

1. **Python 3.8+**
2. **FFmpeg** installed and in PATH
3. **Dropbox App** with API access
4. **Social Media API Credentials** (Instagram, Facebook, YouTube, etc.)

## 🔧 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install FFmpeg

**Windows:**
```bash
winget install FFmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 3. Configure Dropbox

**Step A: Create Dropbox App**
1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Click "Create app"
3. Choose:
   - **Scoped access**
   - **Full Dropbox** access
4. Name your app and create it

**Step B: Get Credentials**
1. Copy **App key** → `DROPBOX_APP_KEY`
2. Copy **App secret** → `DROPBOX_APP_SECRET`

**Step C: Generate Refresh Token**
1. Run:
   ```bash
   py generate_dropbox_token.py
   ```
2. Follow the prompts
3. Copy `DROPBOX_REFRESH_TOKEN` to `.env`

**Step D: Add to `.env`**
```env
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret
DROPBOX_REFRESH_TOKEN=the_refresh_token
DROPBOX_FOLDER=/margot
```

### 4. Set Up GitHub Actions

**Step A: Push to GitHub**
```bash
git add .
git commit -m "Setup video automation"
git push
```

**Step B: Add GitHub Secrets**
Go to **Settings** → **Secrets and variables** → **Actions**

**Required secrets:**
- `DROPBOX_APP_KEY`
- `DROPBOX_APP_SECRET`
- `DROPBOX_REFRESH_TOKEN`
- `POLLINATIONS_API_KEY`

**Optional secrets:**
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_ACCOUNT_ID`
- `FACEBOOK_ACCESS_TOKEN`
- `FACEBOOK_PAGE_ID`
- `THREADS_ACCESS_TOKEN`
- `THREADS_USER_ID`
- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

**Step C: Workflow runs automatically**
- Runs 3 times a day: 8:00 AM, 4:00 PM, 12:00 AM UTC
- Manual trigger from **Actions** tab

## 📁 Folder Structure

```
.
├── Videos/                 # Temporary download folder (cleaned after upload)
├── published_videos.json   # Track published videos
├── rotation_state.json     # Track rotation position
├── dropbox_fetch.py        # Dropbox integration (name check + download)
├── process_videos.py       # Video processing (upscale + delogo)
├── daily_publisher.py      # Social media uploader
├── auto_pipeline.py        # Main automation script
├── .env                    # Environment variables
└── requirements.txt        # Dependencies
```

**Note:** No `Processed_Videos` folder! Everything is temporary and cleaned up after upload.

## 🎯 Usage

### Automatic (GitHub Actions)

Runs 3 times daily:
- **8:00 AM UTC**
- **4:00 PM UTC**
- **12:00 AM UTC**

**Workflow:**
1. Add video to Dropbox `/margot` folder
2. GitHub Actions automatically:
   - Checks video names (no download)
   - Downloads only what's needed
   - Processes and uploads
   - Cleans up temporary files

### Manual Run

```bash
python auto_pipeline.py
```

## ⚙️ Customization

### Watermark Position

Edit `process_videos.py`:
```python
w_delogo = 180  # Width of watermark area
h_delogo = 80   # Height of watermark area
x_delogo = 1080 - w_delogo - 5  # Position from right
y_delogo = 1920 - h_delogo - 5  # Position from bottom
```

### Output Resolution

Edit `process_videos.py`:
```python
# Current: 1080x1920 (vertical)
vf_filter = f"...scale=1080:1920:flags=lanczos..."
```

## 🔄 Rotation System

### How Rotation Works

```
Run 1: Video 1/37 → Download → Process → Upload → Save state (index=0)
Run 2: Video 2/37 → Download → Process → Upload → Save state (index=1)
Run 3: Video 3/37 → Download → Process → Upload → Save state (index=2)
...
Run 37: Video 37/37 → Download → Process → Upload → Save state (index=36)
Run 38: Video 1/37 → (cycles back to start)
```

### Tracking Files

**`rotation_state.json`** (auto-generated):
```json
{
  "last_index": 5,
  "updated_at": "2025-03-25T14:00:00"
}
```

**`published_videos.json`** (auto-generated):
```json
[
  {
    "video_name": "video1.mp4",
    "metadata": {
      "title": "Amazing walk!",
      "description": "...",
      "success_flags": {...}
    },
    "published_at": "2025-03-25T10:00:00"
  }
]
```

## 🛠️ Troubleshooting

### FFmpeg not found
```bash
ffmpeg -version  # Check installation
winget install FFmpeg  # Install if missing
```

### Dropbox connection error
- Verify `DROPBOX_REFRESH_TOKEN` in `.env`
- Check Dropbox app permissions

### Rotation stuck
Delete `rotation_state.json` to reset rotation.

### No videos found
- Ensure videos are in Dropbox `/margot` folder
- Check `DROPBOX_FOLDER` in `.env`

## 📝 Notes

- **No permanent storage** - All files temporary, cleaned after upload
- **Rotation is automatic** - Cycles through all videos before repeating
- **New videos always priority** - New videos processed first
- **Fresh processing** - Every video reprocessed each time (new AI caption)
- **Original audio preserved** - Enhanced but not replaced

## 🚨 Important

- Keep `.env` private (add to `.gitignore`)
- Never commit API tokens to GitHub
- Test with one video before bulk operations
- Rotation ensures variety - never same video twice in a row
- GitHub Actions starts fresh each run - no persistent storage
