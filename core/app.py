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



    def create_frame(self):

        frame = self.renderer.create_frame()


        spotify_data = self.spotify.get_data()


        if spotify_data["playing"]:


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


        else:

            clock_data = self.clock.get_data()

            frame = self.renderer.draw_clock(
                frame,
                clock_data
            )


        return frame