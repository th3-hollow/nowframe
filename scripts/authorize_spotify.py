#!/usr/bin/env python3

import sys

from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


from plugins.spotify import SpotifyPlugin


def main():

    print(
        "Starting Spotify authorization..."
    )

    spotify = SpotifyPlugin()
    data = spotify.get_data()

    if not spotify.spotify_available:

        raise SystemExit(
            "Spotify authorization or API check failed."
        )

    print(
        "Spotify authorization succeeded."
    )

    if data.get("title"):

        print(
            "Current track:",
            data["title"],
            "-",
            data["artist"]
        )

    else:

        print(
            "Spotify connected. No active track."
        )


if __name__ == "__main__":

    main()
