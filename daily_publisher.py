import os
import json
import glob
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

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

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

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
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            # For reposts, we allow already published videos
            if name in published:
                print(f"ℹ️ Reposting video: {name}")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    for vid in all_videos:
        name = os.path.basename(vid)
        if name not in published:
            return vid, name
    return None, None

def generate_caption():
    """
    Generate title and description for Margot Robbie video.
    Uses hardcoded viral captions - always works, no API dependency.
    All hashtags are lowercase, max 5 per post.
    """
    import random

    # 15 Hardcoded viral captions about Margot Robbie
    viral_captions = [
        {
            "title": "Margot Robbie Red Carpet Magic ✨",
            "description": "Margot Robbie absolutely slaying the red carpet! That confident walk, the stunning smile, pure Hollywood royalty energy. Who else thinks she's one of the most elegant actresses of our generation? Drop a 🔥 if you agree! #margotrobbie #redcarpet #hollywood #actress #glam"
        },
        {
            "title": "Margot Robbie Serving Looks 💫",
            "description": "Margot Robbie walking into our hearts like... This Australian queen never misses! From Barbie to Oscar winner, she's redefining Hollywood elegance. What's your favorite Margot Robbie movie? Tell us below! #margotrobbie #barbie #oscars #celebrity #style"
        },
        {
            "title": "Queen Margot Doing Queen Things 👑",
            "description": "Margot Robbie proving once again why she's A-list royalty! That poise, that grace, that IT factor nobody can replicate. Australian representation at its finest! Double tap if Margot is your icon! #margotrobbie #australian #queen #icon #fashion"
        },
        {
            "title": "Margot Robbie's Iconic Walk 🌟",
            "description": "Can we talk about how Margot Robbie owns every single step she takes? Pure confidence, pure talent, pure star power! From Wolf of Wall Street to Barbie - what a journey! Comment your fave role! #margotrobbie #wolfwallstreet #barbie #star #cinema"
        },
        {
            "title": "Margot Being Absolutely Iconic 💎",
            "description": "Margot Robbie serving pure elegance and we're here for it! This woman can act, produce, AND slay every red carpet. Is there anything she can't do? Show some love for this multi-talented queen! #margotrobbie #talented #producer #actress #goals"
        },
        {
            "title": "Hollywood's Golden Girl ✨",
            "description": "Margot Robbie shining bright like the Hollywood star she is! That smile could light up the entire red carpet. From Harley Quinn to Barbie, she's given us ICONIC moments! What's your favorite? #margotrobbie #harleyquinn #hollywood #golden #smile"
        },
        {
            "title": "Margot Robbie Confidence Level 💯",
            "description": "Margot Robbie walking with the confidence of a main character because SHE IS! Leading lady energy through the roof! This Australian actress took over Hollywood and we're obsessed! #margotrobbie #confidence #maincharacter #leadinglady #obsessed"
        },
        {
            "title": "Slay Queen Margot! 🔥",
            "description": "Margot Robbie absolutely KILLING it as always! That walk, that look, that EVERYTHING! No wonder she's one of the most sought-after actresses in the world. Drop a 💖 for Margot! #margotrobbie #slay #killing #worldwide #stunning"
        },
        {
            "title": "Margot's Red Carpet Moment 💫",
            "description": "Margot Robbie making every red carpet moment unforgettable! Elegance, beauty, and talent all in one package. She's the complete package Hollywood needed! Who else is a lifelong fan? #margotrobbie #elegant #beautiful #talented #fan"
        },
        {
            "title": "Margot Robbie Pure Glamour ✨",
            "description": "Margot Robbie radiating pure glamour and sophistication! From Down Under to Hollywood domination - what an inspiration! She proves hard work and talent pay off! Share if you're inspired! #margotrobbie #glamour #inspiration #hollywood #success"
        },
        {
            "title": "The One And Only Margot 👑",
            "description": "There's Margot Robbie and then there's everyone else! This woman is in a league of her own. Acting chops, producing skills, and red carpet perfection! Tag a fellow Margot fan! #margotrobbie #oneandonly #unique #perfection #legend"
        },
        {
            "title": "Margot Robbie Magic Hour 🌙",
            "description": "Margot Robbie glowing like the superstar she is! Every appearance is a masterclass in elegance and charm. No wonder brands and directors flock to her! Comment your favorite Margot look! #margotrobbie #glowing #superstar #masterclass #charm"
        },
        {
            "title": "Barbie Energy IRL 💖",
            "description": "Margot Robbie IS Barbie in human form! That pink carpet energy, that perfect smile, that iconic presence! She made Barbie dreams come true and we're still living for it! #margotrobbie #barbie #iconic #dreams #perfect"
        },
        {
            "title": "Margot's Power Walk 💪",
            "description": "Margot Robbie power walking into another successful premiere like the BOSS she is! Producer, actress, entrepreneur - she does it all! What a woman! Show respect! #margotrobbie #boss #power #entrepreneur #respect"
        },
        {
            "title": "Stunning Margot Moment 📸",
            "description": "Another day, another stunning moment from Margot Robbie! She never has a bad look, never a bad performance, never a bad anything! Truly Hollywood perfection! Double tap for the queen! #margotrobbie #stunning #perfection #neverfails #queen"
        }
    ]
    
    # Select random caption from the viral list
    selected = random.choice(viral_captions)
    
    print(f"  📝 Using hardcoded caption #{viral_captions.index(selected) + 1}/15")
    
    return selected["title"], selected["description"]

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)

    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
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
    # ONLY if it's a NEW video (not a repost from Processed_Videos)
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)

    # Check if this is a repost (video is already in Processed_Videos)
    # If reposting, DON'T move the file - keep it in Processed_Videos for future reposts
    video_in_processed = os.path.join(PROCESSED_DIR, video_name)
    is_repost = os.path.exists(video_in_processed) and os.path.samefile(video_path, video_in_processed)

    if is_repost:
        print(f"♻️ Repost: Keeping video in Processed_Videos (available for future reposts)")
    else:
        try:
            dest_path = os.path.join(published_dir, video_name)
            shutil.move(video_path, dest_path)
            print(f"📦 Moved published video to {dest_path}")
        except Exception as e:
            print(f"❌ Failed to move published video: {e}")

    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
