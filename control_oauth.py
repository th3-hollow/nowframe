import os
import secrets

from pathlib import Path
from urllib.parse import (
    parse_qs,
    urlparse,
)

from spotipy.oauth2 import SpotifyOAuth

import control_secrets as credential_store


SPOTIFY_CACHE_FILE = Path(
    os.path.expanduser(
        os.environ.get(
            "NOWFRAME_SPOTIFY_CACHE_PATH",
            "/var/lib/nowframe-control/spotify-cache",
        )
    )
)

SPOTIFY_SCOPES = (
    "user-read-playback-state",
    "user-read-currently-playing",
)


def oauth_manager():
    values = (
        credential_store
        .parse_environment_file(
            credential_store.SPOTIFY_ENV_FILE
        )
    )

    client_id = values.get(
        "SPOTIPY_CLIENT_ID",
        "",
    )

    client_secret = values.get(
        "SPOTIPY_CLIENT_SECRET",
        "",
    )

    redirect_uri = values.get(
        "SPOTIPY_REDIRECT_URI",
        "",
    )

    if not (
        client_id
        and client_secret
        and redirect_uri
    ):
        raise RuntimeError(
            "Save Spotify credentials before "
            "starting authorization."
        )

    SPOTIFY_CACHE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=list(SPOTIFY_SCOPES),
        cache_path=str(
            SPOTIFY_CACHE_FILE
        ),
        open_browser=False,
    )


def authorization_url():
    state = secrets.token_urlsafe(32)

    url = oauth_manager().get_authorize_url(
        state=state
    )

    return state, url


def callback_values(response_url):
    response_url = response_url.strip()

    if len(response_url) > 4096:
        raise ValueError(
            "Spotify callback URL is too long."
        )

    parsed = urlparse(response_url)

    if parsed.scheme not in (
        "http",
        "https",
    ):
        raise ValueError(
            "Paste the complete Spotify callback URL."
        )

    values = parse_qs(
        parsed.query,
        keep_blank_values=True,
    )

    error = values.get(
        "error",
        [""],
    )[0]

    if error:
        raise ValueError(
            "Spotify authorization was denied "
            f"or failed: {error}."
        )

    return {
        "code": values.get(
            "code",
            [""],
        )[0],
        "state": values.get(
            "state",
            [""],
        )[0],
    }


def complete_authorization(
    response_url,
    expected_state,
):
    values = callback_values(
        response_url
    )

    if not expected_state:
        raise ValueError(
            "Spotify authorization session expired. "
            "Start authorization again."
        )

    if not secrets.compare_digest(
        values["state"],
        expected_state,
    ):
        raise ValueError(
            "Spotify authorization state did not match. "
            "Start authorization again."
        )

    if not values["code"]:
        raise ValueError(
            "Spotify callback URL does not contain "
            "an authorization code."
        )

    token_info = (
        oauth_manager().get_access_token(
            code=values["code"],
            as_dict=True,
            check_cache=False,
        )
    )

    if not isinstance(
        token_info,
        dict,
    ) or not token_info.get(
        "access_token"
    ):
        raise RuntimeError(
            "Spotify did not return a valid token."
        )

    try:
        os.chmod(
            SPOTIFY_CACHE_FILE,
            0o600,
        )
    except OSError:
        pass

    return {
        "authorized": True,
        "scope": token_info.get(
            "scope",
            "",
        ),
        "refresh_token_present": bool(
            token_info.get(
                "refresh_token"
            )
        ),
    }
