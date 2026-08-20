import os
import time
from concurrent.futures import ThreadPoolExecutor

from core.state import DisplayState
from core.plugins import PluginManager

from plugins.clock import ClockPlugin
from plugins.spotify import SpotifyPlugin

from config import (
    RENDERER_MODE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FONT_REGULAR,
    FONT_BOLD,
    PAUSE_GRACE_SECONDS,
    CLOCK_ENABLED,
    ALBUM_CACHE_PATH,
    IDLE_DISPLAY_MODE,
    IDLE_BLACK_TIMEOUT
)

from core.renderer import Renderer


if RENDERER_MODE == "premium":
    from core.v2.renderer import PremiumRenderer
    from core.v2.spotify_code import SpotifyCodeGenerator


def environment_enabled(name, default=False):

    value = os.environ.get(name)

    if value is None:
        return bool(default)

    return value.strip().lower() in (
        "1",
        "true",
        "yes",
        "on"
    )


class NowFrameApp:

    def __init__(self):

        self.state = DisplayState()

        self.plugins = PluginManager()

        self.clock = ClockPlugin()
        self.spotify = SpotifyPlugin()

        self.spotify_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="spotify")
        self.spotify_future = None
        self.next_spotify_refresh_check = 0.0

        self.plugins.register(
            self.clock
        )

        self.plugins.register(
            self.spotify
        )


        if RENDERER_MODE == "premium":

            print("Using Premium Renderer")

            self.renderer = PremiumRenderer(
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                FONT_REGULAR,
                FONT_BOLD
            )

            self.spotify_code = (
                SpotifyCodeGenerator()
            )

        else:

            print("Using Classic Renderer")

            self.renderer = Renderer()


        # =================================
        # Display state
        # =================================

        self.last_mode = None
        self.last_track_key = None
        self.last_artwork_revision = None
        self.last_clock_text = None


        # =================================
        # Idle timing
        # =================================

        self.pause_grace_seconds = (
            PAUSE_GRACE_SECONDS
        )

        self.pause_started = None
        self.idle_started = None

        self.away_mode = environment_enabled(
            "NOWFRAME_AWAY_MODE"
        )


    def _refresh_spotify_async(self):

        now = time.monotonic()

        if self.spotify_future is not None and self.spotify_future.done():
            try:
                self.spotify_future.result()
            except Exception as error:
                print("Spotify background refresh error:", error)

            self.spotify_future = None

        if self.spotify_future is None and now >= self.next_spotify_refresh_check:
            self.spotify_future = self.spotify_executor.submit(
                self.spotify.refresh_if_due
            )
            self.next_spotify_refresh_check = now + 0.25


    def create_update(self):

        if self.away_mode:

            if self.last_mode == "away":
                return None

            print("Away mode enabled")

            frame = self.renderer.create_frame()

            self.last_mode = "away"
            self.last_clock_text = None
            self.pause_started = None
            self.idle_started = None

            return {
                "type": "full",
                "image": frame,
                "transition": "mode"
            }

        self._refresh_spotify_async()

        spotify_data = (
            self.spotify.get_cached_data()
        )

        now = time.monotonic()


        # =================================
        # SPOTIFY PLAYING
        # =================================

        if spotify_data["playing"]:

            self.pause_started = None
            self.idle_started = None


            track_key = (
                spotify_data["title"],
                spotify_data["artist"],
                spotify_data.get(
                    "album_url"
                ),
                spotify_data.get(
                    "uri"
                )
            )
            artwork_revision = spotify_data.get(
                "album_revision",
                0
            )



            was_playing = (
                self.last_mode
                ==
                "playing"
            )


            was_idle = (
                self.last_mode
                in (
                    "clock",
                    "black",
                    "keep_album"
                )
            )


            track_changed = (
                was_playing
                and
                self.last_track_key
                is not None
                and
                track_key
                !=
                self.last_track_key
            )


            mode_changed = (
                self.last_mode
                !=
                "playing"
            )


            artwork_changed = (
                artwork_revision
                !=
                self.last_artwork_revision
            )

            full_update = (
                mode_changed
                or
                artwork_changed
                or
                track_key
                !=
                self.last_track_key
            )


            self.last_mode = (
                "playing"
            )

            self.last_track_key = (
                track_key
            )


            # ---------------------------------
            self.last_artwork_revision = artwork_revision

            # Fast progress-only update
            # ---------------------------------

            if (
                RENDERER_MODE
                ==
                "premium"
                and
                not full_update
            ):

                region = (
                    self.renderer.render_progress_region(
                        spotify_data[
                            "progress"
                        ]
                    )
                )

                if region is not None:

                    x, y = (
                        self.renderer.layout.progress_position()
                    )

                    return {
                        "type": "region",
                        "image": region,
                        "x": x,
                        "y": y,
                        "transition": None
                    }


            # ---------------------------------
            # Full Spotify render
            # ---------------------------------

            frame = (
                self.renderer.create_frame()
            )


            if (
                RENDERER_MODE
                ==
                "premium"
            ):

                spotify_code_path = None

                if spotify_data.get("album_ready", True):
                    spotify_code_path = (
                        self.spotify_code.get_code(
                            spotify_data.get("uri")
                        )
                    )

                frame = (
                    self.renderer.render(
                        ALBUM_CACHE_PATH,
                        spotify_data[
                            "title"
                        ],
                        spotify_data[
                            "artist"
                        ],
                        spotify_data[
                            "progress"
                        ],
                        spotify_code_path=(
                            spotify_code_path
                        )
                    )
                )

            else:

                frame = (
                    self.renderer.draw_spotify(
                        frame,
                        spotify_data
                    )
                )


            transition = None


            if track_changed:

                transition = "song"


            elif was_idle:

                transition = "mode"


            return {
                "type": "full",
                "image": frame,
                "transition": transition
            }


        # =================================
        # NOT PLAYING
        # =================================

        if (
            self.last_mode
            ==
            "playing"
        ):

            if self.pause_started is None:

                self.pause_started = now

                print(
                    f"Playback paused - starting "
                    f"{self.pause_grace_seconds:g} "
                    f"second grace period"
                )


            paused_for = (
                now
                -
                self.pause_started
            )


            if (
                paused_for
                <
                self.pause_grace_seconds
            ):

                return None


            print(
                "Pause grace period ended - "
                "entering idle mode"
            )


            if self.idle_started is None:

                self.idle_started = now


        elif (
            self.last_mode
            in (
                "clock",
                "black",
                "keep_album"
            )
        ):

            if self.idle_started is None:

                self.idle_started = now


        # =================================
        # SECONDARY BLACK TIMEOUT
        # =================================

        if (
            IDLE_BLACK_TIMEOUT
            is not None
            and
            self.idle_started
            is not None
        ):

            idle_for = (
                now
                -
                self.idle_started
            )


            if (
                idle_for
                >=
                IDLE_BLACK_TIMEOUT
            ):

                if (
                    self.last_mode
                    ==
                    "black"
                ):

                    return None


                print(
                    "Idle black timeout reached"
                )


                frame = (
                    self.renderer.create_frame()
                )


                self.last_mode = "black"
                self.last_clock_text = None


                return {
                    "type": "full",
                    "image": frame,
                    "transition": "mode"
                }


        # =================================
        # KEEP LAST ALBUM ART
        # =================================

        if (
            IDLE_DISPLAY_MODE
            ==
            "keep_album"
        ):

            if self.last_mode != "keep_album":

                print(
                    "Idle mode - keeping last album art"
                )

            self.last_mode = "keep_album"
            self.last_clock_text = None
            self.pause_started = None

            return None


        # =================================
        # DIRECT BLACK MODE
        # =================================

        if (
            IDLE_DISPLAY_MODE
            ==
            "black"
        ):

            if (
                self.last_mode
                ==
                "black"
            ):

                return None


            frame = (
                self.renderer.create_frame()
            )

            self.last_mode = "black"
            self.last_clock_text = None


            return {
                "type": "full",
                "image": frame,
                "transition": "mode"
            }


        # =================================
        # CLOCK MODE
        # =================================

        if not CLOCK_ENABLED:

            return None


        clock_data = (
            self.clock.get_data()
        )

        clock_text = (
            clock_data["time"]
        )


        if (
            self.last_mode
            ==
            "clock"
            and
            clock_text
            ==
            self.last_clock_text
        ):

            return None


        entering_clock = (
            self.last_mode
            !=
            "clock"
        )


        self.last_mode = "clock"
        self.last_clock_text = clock_text

        self.pause_started = None


        frame = (
            self.renderer.create_frame()
        )


        # The renderer will decide later
        # whether clock mode uses album background
        # or pure black based on config.

        frame = (
            self.renderer.draw_clock(
                frame,
                clock_data
            )
        )


        return {
            "type": "full",
            "image": frame,
            "transition": (
                "mode"
                if entering_clock
                else None
            )
        }


    def create_frame(self):

        update = (
            self.create_update()
        )

        if update is None:

            return (
                self.renderer.create_frame()
            )

        return update["image"]
