from core.state import DisplayState
from core.plugins import PluginManager
from plugins.clock import ClockPlugin
from plugins.spotify import SpotifyPlugin
from core.renderer import Renderer


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


        self.renderer = Renderer()



    def create_frame(self):

        frame = self.renderer.create_frame()


        spotify_data = self.spotify.get_data()


        if spotify_data["playing"]:

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
