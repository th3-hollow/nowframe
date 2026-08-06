import datetime


class ClockPlugin:


    def get_data(self):

        now = datetime.datetime.now()


        return {

            "time": now.strftime("%H:%M"),

            "date": now.strftime("%A %d %B")

        }
