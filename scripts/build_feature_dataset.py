"""
FixtureIQ Stage 7.4.1 + 7.4.2
Feature Dataset Builder.
"""

import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.features.preparation import (
    HISTORICAL_FILE,
    FEATURE_INPUT_FILE,
    load_historical_input,
    prepare_feature_input,
    save_feature_input,
)

from backend.features.historical_features import (
    FEATURE_DATASET_FILE,
    FEATURE_METADATA_FILE,
    build_historical_features,
    feature_metadata,
)


def main():

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.4.1 + 7.4.2"
    )
    print(
        "Feature Dataset Builder"
    )
    print("=" * 50)

    # ========================================================
    # Stage 7.4.1
    # ========================================================

    print(
        "\n7.4.1 Feature Input Preparation"
    )

    print(
        f"Source: {HISTORICAL_FILE}"
    )

    dataframe = load_historical_input()

    print(
        f"Historical records: "
        f"{len(dataframe)}"
    )

    prepared = prepare_feature_input(
        dataframe
    )

    print(
        f"Prepared records: "
        f"{len(prepared)}"
    )

    save_feature_input(
        prepared
    )

    print(
        f"Feature input saved:"
    )

    print(
        FEATURE_INPUT_FILE
    )

    # ========================================================
    # Stage 7.4.2
    # ========================================================

    print(
        "\n7.4.2 Time-Based Feature Construction"
    )

    features = build_historical_features(
        prepared
    )

    print(
        f"Feature records: "
        f"{len(features)}"
    )

    # --------------------------------------------------------
    # Basic verification
    # --------------------------------------------------------

    if len(features) != len(prepared):

        print(
            "Feature row count: FAIL"
        )

        sys.exit(1)

    if not features["fixture_id"].is_unique:

        print(
            "Feature fixture IDs: FAIL"
        )

        sys.exit(1)

    features.to_csv(
        FEATURE_DATASET_FILE,
        index=False,
    )

    with FEATURE_METADATA_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            feature_metadata(),
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "\nFeature dataset:"
    )

    print(
        FEATURE_DATASET_FILE
    )

    print(
        "Feature metadata:"
    )

    print(
        FEATURE_METADATA_FILE
    )

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.4.1 RESULT"
    )

    print(
        "=" * 50
    )

    print(
        "Feature input preparation: PASS"
    )

    print(
        "Time-based feature construction: PASS"
    )

    print(
        "\nSTAGE 7.4.1 + 7.4.2: PASS"
    )


if __name__ == "__main__":
    main()