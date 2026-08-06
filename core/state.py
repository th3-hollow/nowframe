class DisplayState:


    def __init__(self):

        self.mode = "idle"


    def set_mode(self, mode):

        self.mode = mode


    def is_idle(self):

        return self.mode == "idle"


    def is_playing(self):

        return self.mode == "playing"
