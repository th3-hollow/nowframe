import csv
import os
import time

from datetime import date


FIELDNAMES = (
    "date",
    "total_requests",
    "successful_requests",
    "failed_requests",
    "quota_events",
    "rate_limit_events",
    "playing_responses",
    "paused_responses",
    "idle_responses",
    "unapproved_device_responses",
    "last_retry_after"
)


class SpotifyUsageTracker:

    def __init__(
        self,
        enabled,
        path,
        flush_seconds
    ):

        self.enabled = bool(
            enabled
        )

        self.path = os.path.abspath(
            os.path.expanduser(
                path
            )
        )

        self.flush_seconds = max(
            float(
                flush_seconds
            ),
            1.0
        )

        self.current_date = (
            date.today().isoformat()
        )

        self.stats = (
            self._empty_stats(
                self.current_date
            )
        )

        self.last_flush = (
            time.monotonic()
        )


        if not self.enabled:
            return


        directory = os.path.dirname(
            self.path
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True
            )


        self._load_today()


    def _empty_stats(
        self,
        day
    ):

        return {
            "date": day,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "quota_events": 0,
            "rate_limit_events": 0,
            "playing_responses": 0,
            "paused_responses": 0,
            "idle_responses": 0,
            "unapproved_device_responses": 0,
            "last_retry_after": 0
        }


    def _load_rows(self):

        if not os.path.exists(
            self.path
        ):

            return []


        try:

            with open(
                self.path,
                "r",
                newline="",
                encoding="utf-8"
            ) as file:

                return list(
                    csv.DictReader(
                        file
                    )
                )


        except Exception as error:

            print(
                "Spotify usage log read error:",
                error
            )

            return []


    def _load_today(self):

        for row in self._load_rows():

            if (
                row.get("date")
                !=
                self.current_date
            ):

                continue


            for field in FIELDNAMES[1:]:

                try:

                    self.stats[field] = int(
                        row.get(
                            field,
                            0
                        )
                        or
                        0
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    self.stats[field] = 0


            return


    def _roll_date_if_needed(self):

        today = date.today().isoformat()


        if today == self.current_date:
            return


        self.flush(
            force=True
        )

        self.current_date = today

        self.stats = (
            self._empty_stats(
                today
            )
        )


    def _increment(
        self,
        field
    ):

        self.stats[field] += 1


    def record_success(
        self,
        state
    ):

        if not self.enabled:
            return


        self._roll_date_if_needed()

        self._increment(
            "total_requests"
        )

        self._increment(
            "successful_requests"
        )


        state_field = {
            "playing": "playing_responses",
            "paused": "paused_responses",
            "idle": "idle_responses",
            "unapproved": (
                "unapproved_device_responses"
            )
        }.get(
            state
        )


        if state_field:

            self._increment(
                state_field
            )


        self.flush()


    def record_error(
        self,
        quota=False,
        rate_limit=False,
        retry_after=0
    ):

        if not self.enabled:
            return


        self._roll_date_if_needed()

        self._increment(
            "total_requests"
        )

        self._increment(
            "failed_requests"
        )


        if quota:

            self._increment(
                "quota_events"
            )


        if rate_limit:

            self._increment(
                "rate_limit_events"
            )


        try:

            parsed_retry_after = max(
                int(
                    retry_after
                ),
                0
            )

        except (
            TypeError,
            ValueError
        ):

            parsed_retry_after = 0


        if parsed_retry_after > 0:

            self.stats[
                "last_retry_after"
            ] = parsed_retry_after


        self.flush(
            force=(
                quota
                or
                rate_limit
            )
        )


    def flush(
        self,
        force=False
    ):

        if not self.enabled:
            return


        now = time.monotonic()


        if (
            not force
            and
            now - self.last_flush
            <
            self.flush_seconds
        ):

            return


        try:

            rows = self._load_rows()

            output_rows = []

            replaced = False


            for row in rows:

                if (
                    row.get("date")
                    ==
                    self.current_date
                ):

                    output_rows.append(
                        self.stats.copy()
                    )

                    replaced = True

                else:

                    output_rows.append(
                        row
                    )


            if not replaced:

                output_rows.append(
                    self.stats.copy()
                )


            temp_path = (
                self.path
                +
                ".tmp"
            )


            with open(
                temp_path,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=FIELDNAMES
                )

                writer.writeheader()

                writer.writerows(
                    output_rows
                )


            os.replace(
                temp_path,
                self.path
            )

            self.last_flush = now


        except Exception as error:

            print(
                "Spotify usage log write error:",
                error
            )
