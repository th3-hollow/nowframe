class PluginManager:

    def __init__(self):

        self.plugins = []


    def register(self, plugin):

        self.plugins.append(plugin)


    def get_data(self):

        data = {}

        for plugin in self.plugins:

            data.update(
                plugin.get_data()
            )

        return data
