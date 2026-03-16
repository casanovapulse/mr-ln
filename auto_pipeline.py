"""
Main Automation Pipeline for GitHub Actions
1. Fetch ONE video from Dropbox
2. Process (upscale + remove watermark)
3. Upload to social media platforms

SMART FALLBACK: If no new videos in Dropbox, uses existing processed videos
from Processed_Videos folder, selecting the least-published one.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()


def run_pipeline():
    """
    Complete automation pipeline:
    Dropbox → Process → Upload to Social Media

    Priority:
    1. If new video in Dropbox → download, process, upload
    2. If no new videos → fallback to existing processed videos (least published first)
    """
    print("\n" + "=" * 60)
    print("🚀 STARTING AUTOMATION PIPELINE")
    print("=" * 60 + "\n")

    # Step 1: Fetch ONE video from Dropbox
    print("📥 STEP 1: Fetching video from Dropbox...")
    from dropbox_fetch import fetch_one_video_from_dropbox

    downloaded = fetch_one_video_from_dropbox()

    if not downloaded:
        print("\n⚠️  No new videos in Dropbox.")
        print("   Will use existing processed videos from Processed_Videos folder.")
        print("   Selecting least-published video for rotation...\n")
        # Skip to Step 3 with fallback mode
        from daily_publisher import main as publish_video
        sys.argv = ["daily_publisher.py"]  # No specific video - let it select from fallback
        publish_video()
        return

    print(f"\n✅ Step 1 complete: Video downloaded ({os.path.basename(downloaded)})\n")

    # Step 2: Process video (upscale + watermark removal)
    print("🎬 STEP 2: Processing video (upscaling + watermark removal)...")
    from process_videos import process_single_video

    processed_video = process_single_video(downloaded)

    if not processed_video or not os.path.exists(processed_video):
        print("\n❌ Video processing failed!")
        sys.exit(1)

    print("\n✅ Step 2 complete: Video processed\n")

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
