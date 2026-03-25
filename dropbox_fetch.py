"""
Dropbox Integration Module with Auto Token Refresh
Uses refresh token to get new access tokens automatically for automation.
"""
import os
import json
import dropbox
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_FOLDER = os.getenv("DROPBOX_FOLDER", "/margot")
LOCAL_INPUT_DIR = os.getenv("LOCAL_INPUT_DIR", "Videos")

PUBLISHED_LOG = "published_videos.json"


def get_dropbox_client():
    """Initialize and return Dropbox client with refresh token."""
    if DROPBOX_REFRESH_TOKEN and DROPBOX_APP_KEY and DROPBOX_APP_SECRET:
        dbx = dropbox.Dropbox(
            app_key=DROPBOX_APP_KEY,
            app_secret=DROPBOX_APP_SECRET,
            oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
        )
        print("Dropbox initialized with refresh token (NEVER EXPIRES)")
        return dbx
    elif DROPBOX_ACCESS_TOKEN:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        print("Dropbox initialized with access token (expires in 4 hours)")
        return dbx
    else:
        raise ValueError("No Dropbox credentials found")


def get_all_video_names_from_dropbox():
    """
    Get list of ALL video names from Dropbox (NO DOWNLOAD).
    Returns only filenames for comparison.
    
    Returns:
        List of video filenames (strings)
    """
    try:
        dbx = get_dropbox_client()
    except ValueError as e:
        print(f"Error: {e}")
        return []
    
    try:
        entries = dbx.files_list_folder(DROPBOX_FOLDER).entries
        video_extensions = ('.mp4', '.mov', '.avi', '.mkv')
        video_names = [
            entry.name for entry in entries
            if entry.name.lower().endswith(video_extensions)
        ]
        return sorted(video_names)
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox API error: {e}")
        return []


def download_video_by_name(video_name):
    """
    Download ONE specific video from Dropbox.
    
    Args:
        video_name: Name of the video file to download
        
    Returns:
        Local path to downloaded video, or None if failed
    """
    # Ensure local input directory exists
    Path(LOCAL_INPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    try:
        dbx = get_dropbox_client()
    except ValueError as e:
        print(f"Error: {e}")
        return None
    
    local_path = os.path.join(LOCAL_INPUT_DIR, video_name)
    
    try:
        dbx.files_download_to_file(local_path, f"{DROPBOX_FOLDER}/{video_name}")
        print(f"✅ Downloaded: {video_name}")
        return local_path
    except dropbox.exceptions.ApiError as e:
        print(f"❌ Failed to download {video_name}: {e}")
        return None


def fetch_one_video_from_dropbox():
    """
    Fetch ONE NEW video from Dropbox for processing.
    Checks published_videos.json to skip already processed videos.
    
    Returns:
        Path to downloaded video or None
    """
    # Ensure local input directory exists
    Path(LOCAL_INPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("FETCHING VIDEO FROM DROPBOX")
    print("=" * 60)
    
    # Get list of already published videos
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                published = [item.get('video_name', '') for item in data]
            except json.JSONDecodeError:
                published = []
    else:
        published = []
        
    print(f"Already published: {len(published)} video(s)")
    
    try:
        dbx = get_dropbox_client()
    except ValueError as e:
        print(f"Error: {e}")
        return None
    
    try:
        entries = dbx.files_list_folder(DROPBOX_FOLDER).entries
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox API error: {e}")
        return []
    
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv')
    videos = [entry for entry in entries if entry.name.lower().endswith(video_extensions)]
    
    if not videos:
        print("No videos found in Dropbox folder.")
        return None
    
    print(f"\nFound {len(videos)} video(s) in Dropbox.")
    
    # Find first video NOT in published list
    for entry in videos:
        video_name = entry.name
        
        if video_name in published:
            print(f"Skipping {video_name} - already published")
            continue
        
        local_path = os.path.join(LOCAL_INPUT_DIR, video_name)
        try:
            dbx.files_download_to_file(local_path, f"{DROPBOX_FOLDER}/{video_name}")
            print(f"\n✅ Selected: {video_name}")
            return local_path
        except dropbox.exceptions.ApiError as e:
            print(f"Failed to download {video_name}: {e}")
            continue
    
    print("\n✅ All videos have already been published.")
    return None


if __name__ == "__main__":
    # Test: List video names
    names = get_all_video_names_from_dropbox()
    print(f"\nVideos in Dropbox: {len(names)}")
    for name in names[:5]:
        print(f"  - {name}")
    if len(names) > 5:
        print(f"  ... and {len(names) - 5} more")
