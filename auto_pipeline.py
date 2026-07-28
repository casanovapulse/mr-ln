"""
Main Automation Pipeline for GitHub Actions
1. Fetch ONE video from Dropbox
2. Process (upscale + remove watermark)
3. Upload to social media platforms

IF NO NEW VIDEOS: Repost already processed videos (with randomness & frequency tracking)
"""
import os
import sys
import random
import json
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"


def get_published_history():
    """Get full publishing history with repost counts."""
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    history = get_published_history()
    counts = {}
    for entry in history:
        video_name = entry.get('video_name', '')
        counts[video_name] = counts.get(video_name, 0) + 1
    return counts


def select_random_processed_video():
    """
    Select a random processed video, prioritizing less-posted ones.
    Returns path to selected video or None if no videos available.
    """
    if not os.path.exists(PROCESSED_DIR):
        print(f"  ⚠️  Processed_Videos folder not found")
        return None

    all_videos = [f for f in os.listdir(PROCESSED_DIR) if f.endswith('.mp4')]

    if not all_videos:
        print(f"  ⚠️  No processed videos found in {PROCESSED_DIR}")
        return None

    repost_counts = get_repost_counts()

    # Calculate weights: videos with fewer posts get higher weight
    weights = []
    for vid in all_videos:
        count = repost_counts.get(vid, 0)
        # Weight decreases exponentially with repost count
        # 0 posts = weight 1000, 1 post = weight 100, 2 posts = weight 10, etc.
        weight = max(1, 1000 // (3 ** count))
        weights.append(weight)

    # Random selection weighted by post count (less posted = more likely)
    selected = random.choices(all_videos, weights=weights, k=1)[0]
    selected_path = os.path.join(PROCESSED_DIR, selected)

    post_count = repost_counts.get(selected, 0)
    print(f"  🎲 Selected (posted {post_count} time(s) before): {selected}")

    return selected_path


def run_pipeline():
    """
    Complete automation pipeline:
    Dropbox → Process → Upload to Social Media

    FALLBACK: If no new videos, repost old videos from Dropbox (random selection)
    """
    print("\n" + "=" * 60)
    print("🚀 STARTING AUTOMATION PIPELINE")
    print("=" * 60 + "\n")

    # Step 1: Fetch ONE video from Dropbox
    print("📥 STEP 1: Fetching video from Dropbox...")
    from dropbox_fetch import fetch_one_video_from_dropbox

    # First try: fetch new video
    downloaded = fetch_one_video_from_dropbox(allow_repost=False)

    if not downloaded:
        print("\n⚠️  No new videos in Dropbox")
        print("🔄 REPOST MODE: Fetching random published video for repost...\n")

        # Fallback: fetch random already-published video from Dropbox
        downloaded = fetch_one_video_from_dropbox(allow_repost=True)

        if not downloaded:
            print("\n✅ No videos to post (Dropbox is empty). Pipeline complete.")
            print("   💡 Add new videos to Dropbox")
            return

        print(f"\n✅ Repost Mode: Using existing video\n")

    print(f"\n✅ Step 1 complete: Video downloaded\n")

    # Step 2: Process video (upscale + watermark removal)
    print("🎬 STEP 2: Processing video (upscaling + watermark removal)...")
    from process_videos import process_single_video

    processed_video = process_single_video(downloaded)

    if not processed_video or not os.path.exists(processed_video):
        print("\n❌ Video processing failed!")
        sys.exit(1)

    print("\n✅ Step 2 complete: Video processed\n")

    print("STEP 2b: Verifying video resolution...")
    import subprocess
    try:
        res = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", processed_video]).decode().strip()
        pw, ph = map(int, res.split("x"))
        if pw != 1080 or ph != 1920:
            print(f"⚠️  WARNING: Video is {pw}x{ph}, expected 1080x1920")
        else:
            print(f"✅ Resolution verified: {pw}x{ph}")
    except Exception as e:
        print(f"⚠️  Could not verify resolution: {e}")
    print("")

    # Step 3: Upload to social media
    print("📤 STEP 3: Uploading to social media platforms...")
    print("   Platforms: Instagram, Facebook, Threads, YouTube")
    print("\n" + "=" * 60 + "\n")

    # Run the daily publisher with the processed video
    from daily_publisher import main as publish_video
    sys.argv = ["daily_publisher.py", processed_video]
    publish_video()

    print("\n" + "=" * 60)
    print("🎉 AUTOMATION PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
