import os
import json
import glob
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Load environment variables
load_dotenv()

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Videos"  # Temporary folder for downloads
PUBLISHED_LOG = "published_videos.json"
ROTATION_LOG = "rotation_state.json"

def get_rotation_state():
    """Get the current rotation state (last posted OLD video index)."""
    if os.path.exists(ROTATION_LOG):
        with open(ROTATION_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"last_index": -1}
    return {"last_index": -1}


def save_rotation_state(last_index):
    """Save the current rotation state."""
    state = {"last_index": last_index, "updated_at": datetime.now().isoformat()}
    with open(ROTATION_LOG, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)


def get_next_video_for_rotation(all_video_names):
    """
    Get the NEXT video name from Dropbox for rotation.
    Tracks last posted video and returns the next one in sequence.
    Never returns the same video twice in a row.
    
    Args:
        all_video_names: List of ALL video names from Dropbox
        
    Returns:
        Video name (string) or None if no videos
    """
    if not all_video_names:
        return None
    
    # Get current rotation state
    state = get_rotation_state()
    last_index = state.get("last_index", -1)
    
    # Calculate next index (cycle through all videos)
    next_index = (last_index + 1) % len(all_video_names)
    
    # Get the video name at next index
    video_name = all_video_names[next_index]
    
    # Save new rotation state
    save_rotation_state(next_index)
    
    print(f"📊 Rotation: Video {next_index + 1}/{len(all_video_names)} (last was #{last_index + 1})")
    return video_name

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    """
    Select a video to publish.
    Only used when a specific video path is provided.
    
    Returns:
        (video_path, video_name) or (None, None)
    """
    published = [item["video_name"] for item in get_already_published()]

    if specific_video:
        # specific_video is a full path to processed video
        if os.path.exists(specific_video):
            vid_path = specific_video
            name = os.path.basename(specific_video)
            
            if name in published:
                print(f"🔄 Video {name} was already published - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None
    
    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")
    if not api_key:
        print("Warning: POLLINATIONS_API_KEY not found. Using default captions.")
        return "Stunning walk!", "A walk to remember... 🔥 #fashion #walking #model #beautiful"

    vibes = ["sassy and confident", "mysterious and elegant", "playful and cheeky", "high-fashion boss", "romantic and dreamy"]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique and engaging LONG title and LONG description for a short video "
        f"of Margot Robbie. In the video, Margot Robbie is a beautiful actress and model walking, "
        f"posing, or being interviewed on the red carpet. Speak in the third person about Margot Robbie. "
        f"Make the vibe {chosen_vibe}. "
        f"Make it interaction-bait to gain followers - ask questions, encourage comments, and create engagement. "
        f"The description should be LONG and detailed (at least 3-4 sentences) perfect for Facebook and Instagram. "
        f"Include relevant hashtags in ALL LOWERCASE like #margotrobbie #actress #hollywood #redcarpet #fashion #model #celebrity #style. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        # Clean up any potential markdown block markers
        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        return result.get("title", "Stunning walk!"), result.get("description", "A beautiful walk... #fashion")
    except Exception as e:
        print(f"Error generating caption: {e}")
        return "Stunning walk!", "A beautiful walk... #fashion #model"

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)

    # Get specific video if provided
    specific_video = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            specific_video = arg
            break

    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No video provided. Exiting.")
        return

    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()

    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")

    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"

    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }

    # Check which platforms are configured
    print("\n" + "=" * 60)
    print("📱 PLATFORM AVAILABILITY CHECK")
    print("=" * 60)

    instagram_available = bool(os.getenv('INSTAGRAM_ACCESS_TOKEN') or os.getenv('FACEBOOK_ACCESS_TOKEN'))
    facebook_available = bool(os.getenv('FACEBOOK_ACCESS_TOKEN'))
    threads_available = bool(os.getenv('THREADS_ACCESS_TOKEN'))
    youtube_available = bool(os.getenv('YT_REFRESH_TOKEN'))

    if instagram_available:
        print("✅ Instagram: Configured")
    else:
        print("⚠️  Instagram: Not configured - will skip")

    if facebook_available:
        print("✅ Facebook: Configured")
    else:
        print("⚠️  Facebook: Not configured - will skip")

    if threads_available:
        print("✅ Threads: Configured")
    else:
        print("⚠️  Threads: Not configured - will skip")

    if youtube_available:
        print("✅ YouTube: Configured")
    else:
        print("⚠️  YouTube: Not configured - will skip")

    print("=" * 60)

    # Instagram Reels
    if instagram_available:
        try:
            upload_to_instagram(video_path, combined_caption, is_story=False)
            success_flags["instagram_reel"] = True
        except Exception as e:
            print(f"❌ Instagram Reel upload failed: {e}")
    else:
        print("⏭️  Skipping Instagram (no access token)")

    # Instagram Stories
    if instagram_available:
        try:
            upload_to_instagram(video_path, combined_caption, is_story=True)
            success_flags["instagram_story"] = True
        except Exception as e:
            print(f"❌ Instagram Story upload failed: {e}")

    # Facebook Reels
    if facebook_available:
        try:
            upload_to_facebook(video_path, description, title=title)
            success_flags["facebook_reel"] = True
        except Exception as e:
            print(f"❌ Facebook Reel upload failed: {e}")
    else:
        print("⏭️  Skipping Facebook (no access token)")

    # Facebook Stories
    if facebook_available:
        try:
            upload_to_facebook_story(video_path)
            success_flags["facebook_story"] = True
        except Exception as e:
            print(f"❌ Facebook Story upload failed: {e}")

    # Threads
    if threads_available:
        try:
            upload_to_threads(video_path, combined_caption)
            success_flags["threads"] = True
        except Exception as e:
            print(f"❌ Threads upload failed: {e}")
    else:
        print("⏭️  Skipping Threads (no access token)")

    # YouTube Shorts
    if youtube_available:
        try:
            upload_to_youtube(video_path, title, description, tags=["fashion", "model", "walking", "explore"])
            success_flags["youtube"] = True
        except Exception as e:
            print(f"❌ YouTube upload failed: {e}")
    else:
        print("⏭️  Skipping YouTube (no credentials)")

    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags
    })

    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)

    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")

    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
