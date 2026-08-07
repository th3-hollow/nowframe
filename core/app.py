from core.state import DisplayState
from core.plugins import PluginManager

from plugins.clock import ClockPlugin
from plugins.spotify import SpotifyPlugin

from config import (
    RENDERER_MODE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FONT_REGULAR,
    FONT_BOLD
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

            print(
                "Using Premium Renderer"
            )

            self.renderer = PremiumRenderer(
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                FONT_REGULAR,
                FONT_BOLD
            )

        else:

            print(
                "Using Classic Renderer"
            )

            self.renderer = Renderer()


        self.last_mode = None
        self.last_track_key = None
        self.last_clock_text = None


    def create_update(self):

        spotify_data = self.spotify.get_data()


        # ==========================
        # SPOTIFY PLAYING
        # ==========================

        if spotify_data["playing"]:

            track_key = (
                spotify_data["title"],
                spotify_data["artist"],
                spotify_data.get(
                    "album_url"
                )
            )


            full_update = (
                self.last_mode != "playing"
                or
                track_key != self.last_track_key
            )


            self.last_mode = "playing"
            self.last_track_key = track_key


            if (
                RENDERER_MODE == "premium"
                and not full_update
            ):

                region = (
                    self.renderer.render_progress_region(
                        spotify_data["progress"]
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
                        "y": y
                    }


            frame = self.renderer.create_frame()


            if RENDERER_MODE == "premium":

                frame = self.renderer.render(
                    "assets/images/album.jpg",
                    spotify_data["title"],
                    spotify_data["artist"],
                    spotify_data["progress"]
                )

            else:

                frame = self.renderer.draw_spotify(
                    frame,
                    spotify_data
                )


            return {
                "type": "full",
                "image": frame
            }


        # ==========================
        # CLOCK / PAUSED
        # ==========================

        clock_data = self.clock.get_data()

        clock_text = clock_data["time"]


        if (
            self.last_mode == "clock"
            and
            clock_text == self.last_clock_text
        ):

            return None


        self.last_mode = "clock"
        self.last_clock_text = clock_text


        frame = self.renderer.create_frame()

        frame = self.renderer.draw_clock(
            frame,
            clock_data
        )


        return {
            "type": "full",
            "image": frame
        }


    def create_frame(self):

        update = self.create_update()

        if update is None:
            return self.renderer.create_frame()

        return update["image"]
