import time

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
    ALBUM_CACHE_PATH
)

from core.renderer import Renderer


if RENDERER_MODE == "premium":
    from core.v2.renderer import PremiumRenderer


class NowFrameApp:

    def __init__(self):

        self.state = DisplayState()

        self.plugins = PluginManager()

        self.clock = ClockPlugin()
        self.spotify = SpotifyPlugin()

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

        else:

            print("Using Classic Renderer")

            self.renderer = Renderer()


        # =================================
        # Display state
        # =================================

        self.last_mode = None
        self.last_track_key = None
        self.last_clock_text = None


        # =================================
        # Pause grace period
        #
        # Keep the current Spotify screen
        # visible for this many seconds
        # after playback pauses.
        # =================================

        self.pause_grace_seconds = (
            PAUSE_GRACE_SECONDS
        )

        self.pause_started = None


    def create_update(self):

        spotify_data = (
            self.spotify.get_data()
        )

        now = time.monotonic()


        # =================================
        # SPOTIFY PLAYING
        # =================================

        if spotify_data["playing"]:

            # Playback is active again.
            # Cancel any pending pause timer.

            self.pause_started = None


            track_key = (
                spotify_data["title"],
                spotify_data["artist"],
                spotify_data.get(
                    "album_url"
                )
            )


            was_playing = (
                self.last_mode
                ==
                "playing"
            )


            was_clock = (
                self.last_mode
                ==
                "clock"
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


            full_update = (
                mode_changed
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
                        ]
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


            # New song while already playing.

            if track_changed:

                transition = "song"


            # Returning from idle clock.

            elif was_clock:

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


            # Keep the current Spotify screen
            # untouched during the grace period.

            if (
                paused_for
                <
                self.pause_grace_seconds
            ):

                return None


            print(
                "Pause grace period ended - "
                "switching to clock"
            )


        # =================================
        # CLOCK
        # =================================

        if not CLOCK_ENABLED:

            return None


        clock_data = (
            self.clock.get_data()
        )

        clock_text = (
            clock_data["time"]
        )


        # Once already on the clock,
        # only redraw when the displayed
        # minute changes.

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


        self.last_mode = (
            "clock"
        )

        self.last_clock_text = (
            clock_text
        )

        self.pause_started = None


        frame = (
            self.renderer.create_frame()
        )

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
