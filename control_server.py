import os

from waitress import serve

from control_panel import app


def main():
    serve(
        app,
        host=os.environ.get(
            "NOWFRAME_CONTROL_HOST",
            "0.0.0.0",
        ),
        port=int(
            os.environ.get(
                "NOWFRAME_CONTROL_PORT",
                "8080",
            )
        ),
        threads=int(
            os.environ.get(
                "NOWFRAME_CONTROL_THREADS",
                "2",
            )
        ),
        channel_timeout=30,
        clear_untrusted_proxy_headers=True,
    )


if __name__ == "__main__":
    main()
