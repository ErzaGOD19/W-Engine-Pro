import logging

import mpv

from engines.base_engine import WallpaperEngineInterface


class MpvEngine(WallpaperEngineInterface):
    """
    Video renderer using libmpv.
    """

    def __init__(self):
        self.player = None
        self.surface_handle = None
        self.monitor_info = None

    def init(self, surface_handle, monitor_info, config=None):
        self.surface_handle = surface_handle
        self.monitor_info = monitor_info
        self.config = config

        # Check if video path is a YouTube URL to enable ytdl
        video_path = config.get_setting("last_wallpaper", "") if config else ""
        is_youtube = (
            "youtube.com" in video_path or "youtu.be" in video_path
            if video_path
            else False
        )

        # Enable yt-dlp for YouTube URLs
        ytdl_enabled = is_youtube

        try:
            self.player = mpv.MPV(
                vo="null",
                hwdec="auto",
                loop_playlist="inf",
                ytdl=ytdl_enabled,
                terminal=False,
                input_default_bindings=False,
                input_vo_keyboard=False,
                log_handler=logging.debug,
            )
            if ytdl_enabled:
                logging.info("[MPV Engine] YouTube support enabled (yt-dlp)")
        except Exception as e:
            logging.error(f"Failed to initialize MPV: {e}")

    def start(self):
        if self.player:
            self.player.play("null")
            logging.info("MPV Engine started.")

    def stop(self):
        if self.player:
            self.player.terminate()
            self.player = None
            logging.info("MPV Engine stopped.")

    def set_wallpaper(self, path):
        if self.player:
            self.player.play(path)
            logging.info(f"MPV playing: {path}")

    def pause(self):
        if self.player:
            self.player.pause = True

    def resume(self):
        if self.player:
            self.player.pause = False

    def set_transition(self, type):
        pass

    def reload(self):
        if self.player:
            self.player.command("loadfile", self.player.filename)

    def set_option(self, key, value):
        if not self.player:
            return

        try:
            if key == "volume":
                self.player.volume = int(value)
            elif key == "brightness":
                self.player.brightness = int(value)
            elif key == "contrast":
                self.player.contrast = int(value)
            elif key == "saturation":
                self.player.saturation = int(value)
            elif key == "gamma":
                # Gamma mapping: UI (0.1 to 5.0, neutral 1.0) -> MPV (-100 to 100, neutral 0)
                try:
                    gamma_ui = float(value)
                    if gamma_ui > 1.0:
                        gamma_mpv = int((gamma_ui - 1.0) / 4.0 * 100)
                    else:
                        gamma_mpv = int((gamma_ui - 1.0) / 0.9 * 100)
                    self.player.gamma = gamma_mpv
                except:
                    self.player.gamma = 0
            elif key == "loop":
                if value == "Loop":
                    self.player.loop_playlist = "inf"
                    self.player.pause = False
                else:
                    self.player.loop_playlist = "no"
            elif key == "mute":
                self.player.mute = bool(value)
        except Exception as e:
            logging.error(f"MPV option error {key}={value}: {e}")
