from pathlib import Path
import json
import time

import pandas as pd
import requests


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

BULLPEN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "bullpen_appearances_2026.csv"
)

CACHE_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "play_by_play"
)


# =========================================================
# MLB API
# =========================================================

BASE_URL = (
    "https://statsapi.mlb.com/"
    "api/v1.1/game/{game_pk}/feed/live"
)


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "Loading bullpen appearances..."
    )

    bullpen = pd.read_csv(
        BULLPEN_FILE
    )

    game_pks = (
        bullpen["game_pk"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    game_pks = sorted(
        game_pks
    )

    print(
        f"Found {len(bullpen):,} "
        f"bullpen appearances."
    )

    print(
        f"Need play-by-play for "
        f"{len(game_pks):,} unique games."
    )

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    downloaded = 0
    skipped = 0
    failed = 0

    session = requests.Session()

    for number, game_pk in enumerate(
        game_pks,
        start=1,
    ):

        output_file = (
            CACHE_DIR
            / f"{game_pk}.json"
        )

        # -----------------------------------------
        # DON'T DOWNLOAD THE SAME GAME TWICE
        # -----------------------------------------

        if output_file.exists():

            skipped += 1

            print(
                f"[{number}/{len(game_pks)}] "
                f"{game_pk} cached"
            )

            continue

        url = BASE_URL.format(
            game_pk=game_pk
        )

        try:

            response = session.get(
                url,
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            # Make sure this actually looks
            # like an MLB game feed.

            if (
                "liveData" not in data
                or
                "plays" not in data[
                    "liveData"
                ]
            ):
                raise ValueError(
                    "Missing liveData/plays"
                )

            with open(
                output_file,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    data,
                    file,
                )

            downloaded += 1

            print(
                f"[{number}/{len(game_pks)}] "
                f"{game_pk} downloaded"
            )

            # Small pause so we're not
            # firing requests continuously.

            time.sleep(0.10)

        except Exception as error:

            failed += 1

            print(
                f"[{number}/{len(game_pks)}] "
                f"{game_pk} FAILED: "
                f"{error}"
            )

    print()
    print(
        "=" * 60
    )

    print(
        "PLAY-BY-PLAY DOWNLOAD COMPLETE"
    )

    print(
        "=" * 60
    )

    print(
        f"Downloaded: {downloaded:,}"
    )

    print(
        f"Already cached: {skipped:,}"
    )

    print(
        f"Failed: {failed:,}"
    )

    print(
        f"Cache folder: {CACHE_DIR}"
    )


if __name__ == "__main__":
    main()