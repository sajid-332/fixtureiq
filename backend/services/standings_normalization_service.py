"""
FixtureIQ Stage 8.2.2
Standings Team Normalization Service.

Maps football-data.org provider team identities to the canonical
FixtureIQ team registry already present in Stage 7 upcoming fixtures.

Rules:
- FixtureIQ identity is authoritative.
- Provider IDs remain metadata only.
- Alias matching is deterministic and exact.
- No fuzzy/approximate matching.
- Unknown or ambiguous teams fail closed.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path


# ============================================================
# Paths
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

UPCOMING_FIXTURES_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
    / "upcoming_fixtures.csv"
)


# ============================================================
# Exceptions
# ============================================================

class StandingsNormalizationError(
    RuntimeError
):
    """Raised when provider teams cannot be mapped safely."""


# ============================================================
# Normalization
# ============================================================

def normalize_team_key(
    value: str,
) -> str:

    text = str(
        value
    ).strip()

    text = (
        unicodedata.normalize(
            "NFKD",
            text,
        )
        .encode(
            "ascii",
            "ignore",
        )
        .decode(
            "ascii"
        )
    )

    text = (
        text
        .casefold()
        .replace(
            "&",
            " and ",
        )
        .replace(
            "'",
            "",
        )
        .replace(
            "’",
            "",
        )
    )

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    # --------------------------------------------------------
    # Generic provider suffix removal
    # --------------------------------------------------------

    suffixes = (
        " football club",
        " association football club",
        " fc",
        " afc",
    )

    changed = True

    while changed:

        changed = False

        for suffix in suffixes:

            if (
                text.endswith(
                    suffix
                )
            ):

                text = (
                    text[
                        :-len(
                            suffix
                        )
                    ]
                    .strip()
                )

                changed = True

                break

    return text


# ============================================================
# Deterministic alias groups
#
# Each group contains names that are allowed to represent the
# same football club.
#
# Matching is bidirectional:
#
# Ipswich Town -> Ipswich
# Ipswich      -> Ipswich Town
#
# depending on which form is present in FixtureIQ's registry.
# ============================================================

TEAM_ALIAS_GROUPS = [

    {
        "arsenal",
    },

    {
        "aston villa",
        "villa",
    },

    {
        "bournemouth",
        "afc bournemouth",
    },

    {
        "brentford",
    },

    {
        "brighton",
        "brighton and hove albion",
    },

    {
        "burnley",
    },

    {
        "chelsea",
    },

    {
        "crystal palace",
        "palace",
    },

    {
        "everton",
    },

    {
        "fulham",
    },

    {
        "ipswich",
        "ipswich town",
    },

    {
        "leeds",
        "leeds united",
    },

    {
        "leicester",
        "leicester city",
    },

    {
        "liverpool",
    },

    {
        "man city",
        "manchester city",
    },

    {
        "man united",
        "manchester united",
    },

    {
        "newcastle",
        "newcastle united",
    },

    {
        "nottingham forest",
        "nottm forest",
        "nottingham",
    },

    {
        "southampton",
    },

    {
        "sunderland",
    },

    {
        "tottenham",
        "tottenham hotspur",
        "spurs",
    },

    {
        "west ham",
        "west ham united",
    },

    {
        "wolves",
        "wolverhampton",
        "wolverhampton wanderers",
    },

]


# ============================================================
# Build normalized alias lookup
# ============================================================

def _build_alias_lookup() -> dict[str, set[str]]:

    lookup = {}

    for group in TEAM_ALIAS_GROUPS:

        normalized_group = {

            normalize_team_key(
                value
            )

            for value in group
        }

        normalized_group.discard(
            ""
        )

        for key in normalized_group:

            existing = lookup.setdefault(
                key,
                set(),
            )

            existing.update(
                normalized_group
            )

    return lookup


ALIAS_LOOKUP = (
    _build_alias_lookup()
)


# ============================================================
# Service
# ============================================================

class StandingsNormalizationService:

    def __init__(
        self,
        upcoming_fixtures_file: Path | None = None,
    ):

        self.upcoming_fixtures_file = (
            upcoming_fixtures_file
            or UPCOMING_FIXTURES_FILE
        )

        (
            self._canonical_by_key,
            self._canonical_by_name,
        ) = (
            self._load_canonical_registry()
        )

    # ========================================================
    # Canonical registry
    # ========================================================

    def _load_canonical_registry(
        self,
    ):

        path = (
            self.upcoming_fixtures_file
        )

        if not path.exists():

            raise StandingsNormalizationError(
                (
                    "Upcoming fixtures artifact is missing: "
                    f"{path}"
                )
            )

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.DictReader(
                file
            )

            fieldnames = set(
                reader.fieldnames
                or []
            )

            required = {
                "home_team_id",
                "home_team_name",
                "away_team_id",
                "away_team_name",
            }

            missing = (
                required
                - fieldnames
            )

            if missing:

                raise StandingsNormalizationError(
                    (
                        "upcoming_fixtures.csv is missing "
                        "canonical team fields: "
                        f"{sorted(missing)}"
                    )
                )

            canonical_by_name = {}

            id_to_name = {}

            for row in reader:

                pairs = [

                    (
                        row.get(
                            "home_team_id"
                        ),
                        row.get(
                            "home_team_name"
                        ),
                    ),

                    (
                        row.get(
                            "away_team_id"
                        ),
                        row.get(
                            "away_team_name"
                        ),
                    ),
                ]

                for (
                    team_id,
                    team_name,
                ) in pairs:

                    team_id = str(
                        team_id
                    ).strip()

                    team_name = str(
                        team_name
                    ).strip()

                    if (
                        not team_id
                        or
                        not team_name
                    ):

                        raise StandingsNormalizationError(
                            (
                                "Blank FixtureIQ team identity "
                                "found in upcoming fixtures."
                            )
                        )

                    existing_id = (
                        canonical_by_name.get(
                            team_name
                        )
                    )

                    if (
                        existing_id is not None
                        and
                        existing_id
                        != team_id
                    ):

                        raise StandingsNormalizationError(
                            (
                                "Canonical team name maps "
                                "to multiple FixtureIQ IDs: "
                                f"{team_name}"
                            )
                        )

                    existing_name = (
                        id_to_name.get(
                            team_id
                        )
                    )

                    if (
                        existing_name is not None
                        and
                        existing_name
                        != team_name
                    ):

                        raise StandingsNormalizationError(
                            (
                                "FixtureIQ team ID maps "
                                "to multiple names: "
                                f"{team_id}"
                            )
                        )

                    canonical_by_name[
                        team_name
                    ] = team_id

                    id_to_name[
                        team_id
                    ] = team_name

        if (
            len(
                canonical_by_name
            )
            != 20
        ):

            raise StandingsNormalizationError(
                (
                    "Expected exactly 20 canonical EPL teams "
                    "from upcoming fixtures, found "
                    f"{len(canonical_by_name)}."
                )
            )

        canonical_by_key = {}

        for (
            team_name,
            team_id,
        ) in canonical_by_name.items():

            key = normalize_team_key(
                team_name
            )

            if not key:

                raise StandingsNormalizationError(
                    (
                        "Could not normalize canonical "
                        f"team name: {team_name}"
                    )
                )

            if (
                key
                in canonical_by_key
            ):

                raise StandingsNormalizationError(
                    (
                        "Canonical normalization collision "
                        f"for key {key!r}."
                    )
                )

            canonical_by_key[
                key
            ] = {

                "team_id":
                    team_id,

                "team_name":
                    team_name,
            }

        return (
            canonical_by_key,
            canonical_by_name,
        )

    # ========================================================
    # Registry metadata
    # ========================================================

    @property
    def canonical_team_count(
        self,
    ) -> int:

        return len(
            self._canonical_by_name
        )

    # ========================================================
    # Candidate generation
    # ========================================================

    def _candidate_keys(
        self,
        provider_name: str,
        provider_short_name: str = "",
        provider_tla: str = "",
    ) -> list[str]:

        candidates = []

        seed_values = (
            provider_name,
            provider_short_name,
        )

        # ----------------------------------------------------
        # Exact normalized provider names first
        # ----------------------------------------------------

        for value in seed_values:

            if not value:

                continue

            key = normalize_team_key(
                value
            )

            if (
                key
                and
                key not in candidates
            ):

                candidates.append(
                    key
                )

        # ----------------------------------------------------
        # Expand deterministic alias groups
        # ----------------------------------------------------

        original_candidates = list(
            candidates
        )

        for key in original_candidates:

            aliases = (
                ALIAS_LOOKUP.get(
                    key,
                    set(),
                )
            )

            for alias in sorted(
                aliases
            ):

                if (
                    alias
                    and
                    alias not in candidates
                ):

                    candidates.append(
                        alias
                    )

        return candidates

    # ========================================================
    # Resolve one provider team
    # ========================================================

    def resolve_team(
        self,
        provider_row: dict,
    ) -> dict:

        provider_name = str(
            provider_row.get(
                "provider_team_name",
                ""
            )
        ).strip()

        provider_short_name = str(
            provider_row.get(
                "provider_short_name",
                ""
            )
        ).strip()

        provider_tla = str(
            provider_row.get(
                "provider_tla",
                ""
            )
        ).strip()

        if not provider_name:

            raise StandingsNormalizationError(
                "Provider team name is blank."
            )

        candidates = (
            self._candidate_keys(
                provider_name,
                provider_short_name,
                provider_tla,
            )
        )

        matches = []

        matched_keys = []

        for key in candidates:

            canonical = (
                self
                ._canonical_by_key
                .get(
                    key
                )
            )

            if (
                canonical is not None
                and
                canonical not in matches
            ):

                matches.append(
                    canonical
                )

                matched_keys.append(
                    key
                )

        if len(
            matches
        ) == 0:

            raise StandingsNormalizationError(
                (
                    "Unknown provider team. "
                    f"Could not map {provider_name!r}. "
                    f"Candidate keys: {candidates}. "
                    "No fuzzy fallback is permitted."
                )
            )

        if len(
            matches
        ) > 1:

            raise StandingsNormalizationError(
                (
                    "Ambiguous provider team mapping "
                    f"for {provider_name!r}. "
                    f"Matched keys={matched_keys}, "
                    f"matches={matches}"
                )
            )

        canonical = matches[
            0
        ]

        return {

            "provider_team_id":
                provider_row.get(
                    "provider_team_id"
                ),

            "provider_team_name":
                provider_name,

            "provider_short_name":
                provider_short_name,

            "provider_tla":
                provider_tla,

            "team_id":
                canonical[
                    "team_id"
                ],

            "team_name":
                canonical[
                    "team_name"
                ],

            "position":
                provider_row[
                    "position"
                ],

            "played":
                provider_row[
                    "played"
                ],

            "won":
                provider_row[
                    "won"
                ],

            "drawn":
                provider_row[
                    "drawn"
                ],

            "lost":
                provider_row[
                    "lost"
                ],

            "goals_for":
                provider_row[
                    "goals_for"
                ],

            "goals_against":
                provider_row[
                    "goals_against"
                ],

            "goal_difference":
                provider_row[
                    "goal_difference"
                ],

            "points":
                provider_row[
                    "points"
                ],
        }

    # ========================================================
    # Normalize complete table
    # ========================================================

    def normalize_standings(
        self,
        provider_rows: list[dict],
    ) -> list[dict]:

        if len(
            provider_rows
        ) != 20:

            raise StandingsNormalizationError(
                (
                    "Expected 20 provider standings rows, "
                    f"received {len(provider_rows)}."
                )
            )

        normalized = [

            self.resolve_team(
                row
            )

            for row in provider_rows
        ]

        fixtureiq_ids = [

            row[
                "team_id"
            ]

            for row in normalized
        ]

        fixtureiq_names = [

            row[
                "team_name"
            ]

            for row in normalized
        ]

        provider_ids = [

            row[
                "provider_team_id"
            ]

            for row in normalized
        ]

        # ----------------------------------------------------
        # FixtureIQ uniqueness
        # ----------------------------------------------------

        if (
            len(
                set(
                    fixtureiq_ids
                )
            )
            != 20
        ):

            raise StandingsNormalizationError(
                (
                    "Normalized FixtureIQ team IDs "
                    "are not unique."
                )
            )

        if (
            len(
                {
                    name.casefold()
                    for name in fixtureiq_names
                }
            )
            != 20
        ):

            raise StandingsNormalizationError(
                (
                    "Normalized FixtureIQ team names "
                    "are not unique."
                )
            )

        # ----------------------------------------------------
        # Provider uniqueness
        # ----------------------------------------------------

        if (
            len(
                set(
                    provider_ids
                )
            )
            != 20
        ):

            raise StandingsNormalizationError(
                (
                    "Provider team IDs "
                    "are not unique."
                )
            )

        # ----------------------------------------------------
        # Registry coverage
        # ----------------------------------------------------

        canonical_names = set(
            self._canonical_by_name.keys()
        )

        normalized_names = set(
            fixtureiq_names
        )

        if (
            normalized_names
            != canonical_names
        ):

            missing = (
                canonical_names
                - normalized_names
            )

            unexpected = (
                normalized_names
                - canonical_names
            )

            raise StandingsNormalizationError(
                (
                    "Normalized standings do not cover "
                    "the complete FixtureIQ EPL registry. "
                    f"Missing={sorted(missing)}, "
                    f"Unexpected={sorted(unexpected)}"
                )
            )

        # ----------------------------------------------------
        # Provider IDs may never become FixtureIQ IDs
        # ----------------------------------------------------

        for row in normalized:

            if (
                str(
                    row[
                        "provider_team_id"
                    ]
                )
                ==
                str(
                    row[
                        "team_id"
                    ]
                )
            ):

                raise StandingsNormalizationError(
                    (
                        "Provider team ID was reused as "
                        "FixtureIQ internal ID for "
                        f"{row['team_name']}."
                    )
                )

        # ----------------------------------------------------
        # Position order
        # ----------------------------------------------------

        normalized.sort(
            key=lambda row:
                int(
                    row[
                        "position"
                    ]
                )
        )

        positions = [

            int(
                row[
                    "position"
                ]
            )

            for row in normalized
        ]

        if (
            positions
            != list(
                range(
                    1,
                    21,
                )
            )
        ):

            raise StandingsNormalizationError(
                (
                    "Normalized standings positions "
                    "must be exactly 1 through 20."
                )
            )

        return normalized