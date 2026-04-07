import os
import subprocess
import hashlib
import logging


class ResourceManager:
    def __init__(self, config=None):
        self.config = config
        self.wallpaper_dir = os.path.expanduser("~/Vídeos/Wallpapers/")
        self.thumb_dir = os.path.expanduser("~/.cache/w-engine-pro/thumbnails/")

        os.makedirs(self.wallpaper_dir, exist_ok=True)
        os.makedirs(self.thumb_dir, exist_ok=True)

    def list_local_wallpapers(self):
        """Lista archivos de video en el directorio de wallpapers."""
        valid_exts = {".mp4", ".webm", ".mkv", ".avi", ".mov"}
        files = []
        if os.path.exists(self.wallpaper_dir):
            try:
                for f in os.listdir(self.wallpaper_dir):
                    if os.path.splitext(f)[1].lower() in valid_exts:
                        files.append(os.path.join(self.wallpaper_dir, f))
            except Exception as e:
                logging.error(f"Error listando wallpapers: {e}")
        return files

    def get_thumbnail(self, video_path):
        """Genera o recupera una miniatura para el video dado."""
        h = hashlib.md5(video_path.encode("utf-8")).hexdigest()
        thumb_path = os.path.join(self.thumb_dir, f"{h}.jpg")

        if os.path.exists(thumb_path):
            return thumb_path

        # Remote URLs (HTTP/HTTPS): try to obtain thumbnail using yt-dlp
        if isinstance(video_path, str) and video_path.startswith(("http://", "https://")):
            return self.get_remote_thumbnail(video_path, thumb_path)

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-ss",
                "00:00:01.000",
                "-vframes",
                "1",
                "-vf",
                "scale=320:-1",
                thumb_path,
            ]
            subprocess.run(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
            )
            return thumb_path if os.path.exists(thumb_path) else None
        except Exception as e:
            logging.error(f"Error generando thumbnail para {video_path}: {e}")
            return None

    def get_remote_thumbnail(self, url, thumb_path=None):
        """Attempt to retrieve a thumbnail for a remote URL (YouTube supported via yt-dlp)."""
        try:
            import urllib.request
            # Try to obtain the thumbnail URL via yt-dlp if available
            thumb_url = None
            try:
                out = subprocess.check_output(
                    ["yt-dlp", "--skip-download", "--no-warnings", "--get-thumbnail", url],
                    stderr=subprocess.DEVNULL,
                ).decode().strip()
                if out:
                    thumb_url = out.splitlines()[0].strip()
            except Exception:
                thumb_url = None

            if not thumb_url:
                return None

            if not thumb_path:
                h = hashlib.md5(url.encode("utf-8")).hexdigest()
                thumb_path = os.path.join(self.thumb_dir, f"{h}.jpg")

            try:
                urllib.request.urlretrieve(thumb_url, thumb_path)
                return thumb_path if os.path.exists(thumb_path) else None
            except Exception as e:
                logging.debug(f"Failed to download thumbnail {thumb_url}: {e}")
                return None
        except Exception as e:
            logging.debug(f"[get_remote_thumbnail] error: {e}")
            return None

    def list_remote_wallpapers(self):
        """Return list of remote wallpapers persisted in config as dicts {'name','url','type'}."""
        try:
            entries = self.config.get_setting("remote_wallpapers", []) if self.config else []
            result = []
            for e in entries:
                if isinstance(e, dict) and "url" in e:
                    result.append({"name": e.get("name") or e.get("url").split("/")[-1], "url": e["url"], "type": e.get("type","Web")})
                elif isinstance(e, str):
                    result.append({"name": e.split("/")[-1], "url": e, "type": "Web"})
            return result
        except Exception:
            return []
