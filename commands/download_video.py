from yt_dlp import YoutubeDL

def download_youtube_video(url, save_path):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Download best quality
        'outtmpl': f'{save_path}/%(title)s.mp4',  # Save as MP4 format
        'merge_output_format': 'mp4'  # Ensure the final output is in MP4
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            print(f"Downloaded video from {url}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Replace 'video_url' with your desired YouTube link
video_url = 'https://www.youtube.com/watch?v=YY56_502obA'
save_location = 'downloaded_video'  # e.g., '/Users/yourusername/Downloads'

download_youtube_video(video_url, save_location)
