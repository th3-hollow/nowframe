import pytest

import control_oauth as oauth


class FakeOAuth:
    def __init__(self):
        self.received_state = None
        self.received_code = None

    def get_authorize_url(self, state=None):
        self.received_state = state

        return (
            "https://accounts.spotify.com/authorize"
            f"?state={state}"
        )

    def get_access_token(
        self,
        code=None,
        as_dict=True,
        check_cache=True,
    ):
        self.received_code = code

        return {
            "access_token": "private-access-token",
            "refresh_token": "private-refresh-token",
            "scope": (
                "user-read-playback-state "
                "user-read-currently-playing"
            ),
        }


def test_authorization_url_contains_state(
    monkeypatch,
):
    fake = FakeOAuth()

    monkeypatch.setattr(
        oauth,
        "oauth_manager",
        lambda: fake,
    )

    state, url = oauth.authorization_url()

    assert len(state) >= 32
    assert fake.received_state == state
    assert state in url


def test_callback_values():
    values = oauth.callback_values(
        "http://127.0.0.1:8888/callback"
        "?code=spotify-code&state=session-state"
    )

    assert values == {
        "code": "spotify-code",
        "state": "session-state",
    }


def test_callback_denial_is_rejected():
    with pytest.raises(
        ValueError,
        match="denied",
    ):
        oauth.callback_values(
            "http://127.0.0.1:8888/callback"
            "?error=access_denied"
        )


def test_mismatched_state_is_rejected(
    monkeypatch,
):
    fake = FakeOAuth()

    monkeypatch.setattr(
        oauth,
        "oauth_manager",
        lambda: fake,
    )

    with pytest.raises(
        ValueError,
        match="did not match",
    ):
        oauth.complete_authorization(
            "http://127.0.0.1:8888/callback"
            "?code=spotify-code&state=wrong",
            "expected",
        )

    assert fake.received_code is None


def test_successful_authorization_hides_tokens(
    monkeypatch,
    tmp_path,
):
    fake = FakeOAuth()
    cache = tmp_path / "spotify-cache"
    cache.write_text(
        "{}",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        oauth,
        "SPOTIFY_CACHE_FILE",
        cache,
    )

    monkeypatch.setattr(
        oauth,
        "oauth_manager",
        lambda: fake,
    )

    result = oauth.complete_authorization(
        "http://127.0.0.1:8888/callback"
        "?code=spotify-code&state=expected",
        "expected",
    )

    assert fake.received_code == "spotify-code"
    assert result["authorized"] is True
    assert result[
        "refresh_token_present"
    ] is True
    assert "private-access-token" not in str(result)
    assert "private-refresh-token" not in str(result)
