"""
Main Automation Pipeline for GitHub Actions
1. Check Dropbox for NEW videos (by name only)
2. If new videos exist → Download → Process → Upload
3. If NO new videos → Re-download OLD video → Reprocess → Upload (rotation)

CONTINUOUS MODE: Runs forever by re-downloading and reprocessing old videos.
No local storage needed - everything from Dropbox.
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
    1. NEW videos in Dropbox → Download, process, upload
    2. NO new videos → Get next old video (rotation) → Re-download, reprocess, upload
    
    Runs forever - always has content from Dropbox.
    """
    print("\n" + "=" * 60)
    print("🚀 STARTING AUTOMATION PIPELINE")
    print("=" * 60 + "\n")

    # Step 1: Get ALL video names from Dropbox (no download yet)
    print("📥 STEP 1: Checking Dropbox for videos...")
    from dropbox_fetch import get_all_video_names_from_dropbox
    
    all_video_names = get_all_video_names_from_dropbox()
    
    if not all_video_names:
        print("\n❌ No videos found in Dropbox!")
        print("   Please add videos to your Dropbox folder.")
        return
    
    print(f"📚 Found {len(all_video_names)} video(s) in Dropbox")
    
    # Check which videos are already published
    from daily_publisher import get_already_published, get_next_video_for_rotation
    
    published_data = get_already_published()
    published_names = [item["video_name"] for item in published_data]
    
    # Find NEW videos (not in published list)
    new_videos = [name for name in all_video_names if name not in published_names]
    
    print(f"   - Published: {len(published_names)} video(s)")
    print(f"   - New: {len(new_videos)} video(s)")
    
    # Decide: New videos or rotate old videos?
    videos_to_download = []
    
    if new_videos:
        print(f"\n✅ NEW VIDEOS FOUND: {len(new_videos)} video(s)")
        print("   Priority: Processing new videos first")
        videos_to_download = new_videos
    else:
        print("\n⚠️  No new videos in Dropbox")
        print("   Fallback: Rotating through old videos...")
        
        # Get NEXT old video in rotation (not the same as last time)
        next_old_video = get_next_video_for_rotation(all_video_names)
        
        if next_old_video:
            print(f"   Selected: {next_old_video}")
            videos_to_download = [next_old_video]
        else:
            print("\n❌ No videos available to post!")
            return
    
    # Step 2: Download, Process, and Upload each video
    print("\n" + "=" * 60)
    print("📥 STEP 2: Downloading, Processing & Uploading...")
    print("=" * 60 + "\n")
    
    from dropbox_fetch import download_video_by_name
    from process_videos import process_single_video
    from daily_publisher import main as publish_video
    
    for video_name in videos_to_download:
        # Download this video
        print(f"\n📥 Downloading: {video_name}")
        video_path = download_video_by_name(video_name)
        
        if not video_path:
            print(f"❌ Failed to download: {video_name}")
            continue
        
        # Process this video
        print(f"🎬 Processing: {video_name}")
        processed_path = process_single_video(video_path)
        
        if not processed_path:
            print(f"❌ Failed to process: {video_name}")
            # Clean up downloaded video
            if os.path.exists(video_path):
                os.remove(video_path)
            continue
        
        # Upload this video
        print(f"📤 Uploading: {video_name}")
        sys.argv = ["daily_publisher.py", processed_path]
        publish_video()
        print(f"✅ Posted: {video_name}")
        
        # Clean up downloaded files (save space)
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"🗑️  Cleaned up: {os.path.basename(video_path)}")
            if os.path.exists(processed_path):
                os.remove(processed_path)
                print(f"🗑️  Cleaned up: {os.path.basename(processed_path)}")
        except Exception as e:
            print(f"⚠️  Could not remove files: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎉 PIPELINE COMPLETE - {len(videos_to_download)} VIDEO(S) POSTED")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
