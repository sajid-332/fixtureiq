"""
FixtureIQ Stage 8.3.1 + 8.3.2

Current-season completed-match source gate
and overall team form engine.

Rules:
- source = verified production_history.csv
- current production season only: 2026
- completed matches only
- future matches prohibited
- previous-season padding prohibited
- overall form window = latest up to 5 matches
- short windows are allowed
- result order = OLDEST_TO_NEWEST
- most recent result = RIGHTMOST

This module does NOT:
- fetch provider data
- modify Stage 7
- create current_team_form.csv
- calculate venue form
- load/execute the prediction model
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Paths
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

PRODUCTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "production"
)

CONTEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "context"
)

DEFAULT_HISTORY_FILE = (
    PRODUCTION_DIR
    / "production_history.csv"
)

DEFAULT_HISTORY_REPORT_FILE = (
    PRODUCTION_DIR
    / "production_history_report.json"
)

DEFAULT_STANDINGS_FILE = (
    CONTEXT_DIR
    / "current_standings.csv"
)

DEFAULT_STANDINGS_REPORT_FILE = (
    CONTEXT_DIR
    / "standings_report.json"
)


CURRENT_SEASON = 2026
FORM_WINDOW = 5


# ============================================================
# Errors
# ============================================================

class TeamFormSourceError(
    RuntimeError
):
    """Raised when the form source cannot be trusted."""


# ============================================================
# Column candidates
# ============================================================

COLUMN_CANDIDATES = {

    "season": [
        "season",
        "Season",
    ],

    "date": [
        "date",
        "utc_date",
        "match_date",
        "kickoff",
        "kickoff_utc",
        "datetime",
    ],

    "home_team": [
        "home_team_name",
        "home_team",
        "HomeTeam",
        "home",
    ],

    "away_team": [
        "away_team_name",
        "away_team",
        "AwayTeam",
        "away",
    ],

    "home_goals": [
        "home_goals",
        "home_score",
        "home_team_score",
        "FTHG",
        "home_goals_full_time",
    ],

    "away_goals": [
        "away_goals",
        "away_score",
        "away_team_score",
        "FTAG",
        "away_goals_full_time",
    ],

    "status": [
        "status",
        "match_status",
        "fixture_status",
    ],
}


COMPLETED_STATUSES = {
    "FINISHED",
    "FT",
    "FULL_TIME",
    "FULL TIME",
    "COMPLETED",
    "COMPLETE",
}


# ============================================================
# Helpers
# ============================================================

def sha256_file(
    path: Path,
) -> str:

    if not path.exists():

        raise TeamFormSourceError(
            f"Required artifact missing: {path}"
        )

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:

                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise TeamFormSourceError(
            f"Required JSON artifact missing: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(
            file
        )

    if not isinstance(
        payload,
        dict,
    ):

        raise TeamFormSourceError(
            f"Expected JSON object: {path}"
        )

    return payload


def normalize_key(
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

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


TEAM_ALIAS_GROUPS = [

    {
        "bournemouth",
        "afc bournemouth",
    },

    {
        "brighton",
        "brighton and hove albion",
    },

    {
        "coventry",
        "coventry city",
    },

    {
        "hull",
        "hull city",
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
        "sunderland",
        "sunderland afc",
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


def build_alias_lookup() -> dict[str, set[str]]:

    lookup = {}

    for group in TEAM_ALIAS_GROUPS:

        normalized_group = {
            normalize_key(
                value
            )
            for value in group
        }

        normalized_group.discard(
            ""
        )

        for key in normalized_group:

            lookup.setdefault(
                key,
                set(),
            ).update(
                normalized_group
            )

    return lookup


ALIAS_LOOKUP = (
    build_alias_lookup()
)


def parse_datetime_utc(
    value,
) -> datetime:

    text = str(
        value
    ).strip()

    if not text:

        raise TeamFormSourceError(
            "Blank match date encountered."
        )

    # ISO forms first.
    candidate = text

    if candidate.endswith(
        "Z"
    ):

        candidate = (
            candidate[:-1]
            + "+00:00"
        )

    try:

        parsed = datetime.fromisoformat(
            candidate
        )

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(
            timezone.utc
        )

    except ValueError:

        pass

    # Strict fallback formats only.
    formats = [

        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%d/%m/%Y",
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(
                text,
                fmt,
            )

            return parsed.replace(
                tzinfo=timezone.utc
            )

        except ValueError:

            continue

    raise TeamFormSourceError(
        f"Unsupported match date value: {text!r}"
    )


def parse_season(
    value,
) -> int:

    text = str(
        value
    ).strip()

    if not text:

        raise TeamFormSourceError(
            "Blank season value encountered."
        )

    # Examples accepted:
    # 2026
    # 2026.0
    # 2026/27
    # 2026-27
    match = re.match(
        r"^(20\d{2})",
        text,
    )

    if match:

        return int(
            match.group(
                1
            )
        )

    try:

        return int(
            float(
                text
            )
        )

    except ValueError as exc:

        raise TeamFormSourceError(
            f"Invalid season value: {text!r}"
        ) from exc


def parse_goal(
    value,
    *,
    field_name: str,
) -> int:

    text = str(
        value
    ).strip()

    if not text:

        raise TeamFormSourceError(
            f"Blank {field_name} value."
        )

    try:

        goal = int(
            float(
                text
            )
        )

    except ValueError as exc:

        raise TeamFormSourceError(
            (
                f"Invalid {field_name} value: "
                f"{value!r}"
            )
        ) from exc

    if goal < 0:

        raise TeamFormSourceError(
            f"Negative {field_name} value."
        )

    return goal


# ============================================================
# Engine
# ============================================================

class TeamFormEngine:

    def __init__(
        self,
        *,
        history_file: Path | None = None,
        history_report_file: Path | None = None,
        standings_file: Path | None = None,
        standings_report_file: Path | None = None,
        season: int = CURRENT_SEASON,
        window: int = FORM_WINDOW,
    ):

        self.history_file = (
            Path(
                history_file
            )
            if history_file is not None
            else DEFAULT_HISTORY_FILE
        )

        self.history_report_file = (
            Path(
                history_report_file
            )
            if history_report_file is not None
            else DEFAULT_HISTORY_REPORT_FILE
        )

        self.standings_file = (
            Path(
                standings_file
            )
            if standings_file is not None
            else DEFAULT_STANDINGS_FILE
        )

        self.standings_report_file = (
            Path(
                standings_report_file
            )
            if standings_report_file is not None
            else DEFAULT_STANDINGS_REPORT_FILE
        )

        self.season = int(
            season
        )

        self.window = int(
            window
        )

        if self.window <= 0:

            raise TeamFormSourceError(
                "Form window must be positive."
            )

        (
            self.team_by_key,
            self.team_by_id,
        ) = (
            self._load_current_team_registry()
        )

    # ========================================================
    # Current 20-team registry from verified Stage 8.2
    # ========================================================

    def _load_current_team_registry(
        self,
    ):

        standings_report = load_json(
            self.standings_report_file
        )

        if (
            standings_report.get(
                "status"
            )
            != "PASS"
        ):

            raise TeamFormSourceError(
                "Stage 8.2 standings report is not PASS."
            )

        if (
            standings_report.get(
                "stage_8_2_complete"
            )
            is not True
        ):

            raise TeamFormSourceError(
                "Stage 8.2 is not complete."
            )

        if (
            standings_report.get(
                "live_epl_standings_layer"
            )
            != "VERIFIED"
        ):

            raise TeamFormSourceError(
                (
                    "Live EPL standings layer "
                    "is not VERIFIED."
                )
            )

        if not self.standings_file.exists():

            raise TeamFormSourceError(
                "current_standings.csv is missing."
            )

        with self.standings_file.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.DictReader(
                file
            )

            required = {
                "team_id",
                "team_name",
            }

            fields = set(
                reader.fieldnames
                or []
            )

            if not required.issubset(
                fields
            ):

                raise TeamFormSourceError(
                    "Current standings identity schema invalid."
                )

            rows = list(
                reader
            )

        if len(
            rows
        ) != 20:

            raise TeamFormSourceError(
                (
                    "Expected 20 current EPL teams, "
                    f"found {len(rows)}."
                )
            )

        team_by_key = {}
        team_by_id = {}

        for row in rows:

            team_id = str(
                row.get(
                    "team_id",
                    ""
                )
            ).strip()

            team_name = str(
                row.get(
                    "team_name",
                    ""
                )
            ).strip()

            if (
                not team_id
                or
                not team_name
            ):

                raise TeamFormSourceError(
                    "Blank current team identity."
                )

            key = normalize_key(
                team_name
            )

            if key in team_by_key:

                raise TeamFormSourceError(
                    (
                        "Duplicate normalized current "
                        f"team name: {team_name}"
                    )
                )

            if team_id in team_by_id:

                raise TeamFormSourceError(
                    (
                        "Duplicate current team ID: "
                        f"{team_id}"
                    )
                )

            canonical = {
                "team_id":
                    team_id,

                "team_name":
                    team_name,
            }

            team_by_key[
                key
            ] = canonical

            team_by_id[
                team_id
            ] = canonical

        return (
            team_by_key,
            team_by_id,
        )

    # ========================================================
    # History schema resolution
    # ========================================================

    def _resolve_column(
        self,
        fieldnames: list[str],
        semantic_name: str,
        *,
        required: bool,
    ) -> str | None:

        candidates = COLUMN_CANDIDATES[
            semantic_name
        ]

        for candidate in candidates:

            if candidate in fieldnames:

                return candidate

        if required:

            raise TeamFormSourceError(
                (
                    "Could not resolve required history "
                    f"column {semantic_name!r}. "
                    f"Available columns: {fieldnames}"
                )
            )

        return None

    def resolve_history_schema(
        self,
    ) -> dict:

        if not self.history_file.exists():

            raise TeamFormSourceError(
                (
                    "production_history.csv is missing: "
                    f"{self.history_file}"
                )
            )

        with self.history_file.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.reader(
                file
            )

            try:

                fieldnames = next(
                    reader
                )

            except StopIteration:

                raise TeamFormSourceError(
                    "production_history.csv is empty."
                )

        schema = {

            "season":
                self._resolve_column(
                    fieldnames,
                    "season",
                    required=True,
                ),

            "date":
                self._resolve_column(
                    fieldnames,
                    "date",
                    required=True,
                ),

            "home_team":
                self._resolve_column(
                    fieldnames,
                    "home_team",
                    required=True,
                ),

            "away_team":
                self._resolve_column(
                    fieldnames,
                    "away_team",
                    required=True,
                ),

            "home_goals":
                self._resolve_column(
                    fieldnames,
                    "home_goals",
                    required=True,
                ),

            "away_goals":
                self._resolve_column(
                    fieldnames,
                    "away_goals",
                    required=True,
                ),

            "status":
                self._resolve_column(
                    fieldnames,
                    "status",
                    required=False,
                ),
        }

        return schema

    # ========================================================
    # Team resolution
    # ========================================================

    def resolve_history_team(
        self,
        value: str,
    ) -> dict:

        original_key = normalize_key(
            value
        )

        candidate_keys = [
            original_key
        ]

        for alias in sorted(
            ALIAS_LOOKUP.get(
                original_key,
                set(),
            )
        ):

            if alias not in candidate_keys:

                candidate_keys.append(
                    alias
                )

        matches = []

        for key in candidate_keys:

            canonical = (
                self.team_by_key.get(
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

        if len(
            matches
        ) == 0:

            raise TeamFormSourceError(
                (
                    "Current-season history contains "
                    "unknown team "
                    f"{value!r}. "
                    f"Candidates={candidate_keys}"
                )
            )

        if len(
            matches
        ) > 1:

            raise TeamFormSourceError(
                (
                    "Ambiguous history team mapping for "
                    f"{value!r}: {matches}"
                )
            )

        return matches[
            0
        ]

    # ========================================================
    # Stage 8.3.1 source gate
    # ========================================================

    def load_current_season_matches(
        self,
    ) -> dict:

        # Require Stage 7 production history report to exist.
        load_json(
            self.history_report_file
        )

        schema = (
            self.resolve_history_schema()
        )

        now_utc = datetime.now(
            timezone.utc
        )

        with self.history_file.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.DictReader(
                file
            )

            all_rows = list(
                reader
            )

        if not all_rows:

            raise TeamFormSourceError(
                "production_history.csv contains no rows."
            )

        current_season_source_rows = []

        for source_index, raw in enumerate(
            all_rows,
            start=1,
        ):

            row_season = parse_season(
                raw.get(
                    schema[
                        "season"
                    ]
                )
            )

            if row_season != self.season:

                continue

            current_season_source_rows.append(
                (
                    source_index,
                    raw,
                )
            )

        if not current_season_source_rows:

            raise TeamFormSourceError(
                (
                    "No production-history rows found "
                    f"for season {self.season}."
                )
            )

        matches = []

        rejected_non_completed = 0

        for (
            source_index,
            raw,
        ) in current_season_source_rows:

            # ------------------------------------------------
            # If a status field exists, enforce completion.
            # ------------------------------------------------

            if schema[
                "status"
            ] is not None:

                status = str(
                    raw.get(
                        schema[
                            "status"
                        ],
                        ""
                    )
                ).strip().upper()

                if (
                    status
                    not in COMPLETED_STATUSES
                ):

                    rejected_non_completed += 1

                    continue

            match_date = parse_datetime_utc(
                raw.get(
                    schema[
                        "date"
                    ]
                )
            )

            # ------------------------------------------------
            # production_history must never supply future form.
            # ------------------------------------------------

            if match_date > now_utc:

                raise TeamFormSourceError(
                    (
                        "Future-dated match found inside "
                        "current-season production history: "
                        f"{match_date.isoformat()}"
                    )
                )

            home = self.resolve_history_team(
                raw.get(
                    schema[
                        "home_team"
                    ]
                )
            )

            away = self.resolve_history_team(
                raw.get(
                    schema[
                        "away_team"
                    ]
                )
            )

            if (
                home[
                    "team_id"
                ]
                ==
                away[
                    "team_id"
                ]
            ):

                raise TeamFormSourceError(
                    (
                        "Home and away team resolve "
                        "to the same FixtureIQ identity."
                    )
                )

            home_goals = parse_goal(
                raw.get(
                    schema[
                        "home_goals"
                    ]
                ),
                field_name="home_goals",
            )

            away_goals = parse_goal(
                raw.get(
                    schema[
                        "away_goals"
                    ]
                ),
                field_name="away_goals",
            )

            matches.append(
                {

                    "source_row_number":
                        source_index,

                    "season":
                        self.season,

                    "date_utc":
                        match_date,

                    "home_team_id":
                        home[
                            "team_id"
                        ],

                    "home_team_name":
                        home[
                            "team_name"
                        ],

                    "away_team_id":
                        away[
                            "team_id"
                        ],

                    "away_team_name":
                        away[
                            "team_name"
                        ],

                    "home_goals":
                        home_goals,

                    "away_goals":
                        away_goals,
                }
            )

        if not matches:

            raise TeamFormSourceError(
                (
                    "No completed current-season "
                    "matches survived the source gate."
                )
            )

        # ----------------------------------------------------
        # Deterministic chronological order
        # ----------------------------------------------------

        matches.sort(
            key=lambda match: (
                match[
                    "date_utc"
                ],
                match[
                    "source_row_number"
                ],
            )
        )

        # ----------------------------------------------------
        # Reject exact duplicate match records
        # ----------------------------------------------------

        seen = set()

        for match in matches:

            key = (

                match[
                    "date_utc"
                ].isoformat(),

                match[
                    "home_team_id"
                ],

                match[
                    "away_team_id"
                ],

                match[
                    "home_goals"
                ],

                match[
                    "away_goals"
                ],
            )

            if key in seen:

                raise TeamFormSourceError(
                    (
                        "Duplicate completed current-season "
                        f"match detected: {key}"
                    )
                )

            seen.add(
                key
            )

        represented_team_ids = set()

        for match in matches:

            represented_team_ids.add(
                match[
                    "home_team_id"
                ]
            )

            represented_team_ids.add(
                match[
                    "away_team_id"
                ]
            )

        current_team_ids = set(
            self.team_by_id.keys()
        )

        unknown_ids = (
            represented_team_ids
            - current_team_ids
        )

        if unknown_ids:

            raise TeamFormSourceError(
                (
                    "Current-season history contains "
                    "non-current EPL team IDs: "
                    f"{sorted(unknown_ids)}"
                )
            )

        history_cutoff = max(
            match[
                "date_utc"
            ]
            for match in matches
        )

        return {

            "schema":
                schema,

            "history_total_rows":
                len(
                    all_rows
                ),

            "current_season_source_rows":
                len(
                    current_season_source_rows
                ),

            "completed_current_season_matches":
                len(
                    matches
                ),

            "rejected_non_completed_rows":
                rejected_non_completed,

            "history_cutoff_utc":
                history_cutoff.isoformat(),

            "matches":
                matches,
        }

    # ========================================================
    # Stage 8.3.2 overall form
    # ========================================================

    def build_overall_form(
        self,
        gated_source: dict | None = None,
    ) -> list[dict]:

        if gated_source is None:

            gated_source = (
                self.load_current_season_matches()
            )

        matches = gated_source[
            "matches"
        ]

        team_rows = []

        canonical_teams = sorted(
            self.team_by_id.values(),
            key=lambda team:
                team[
                    "team_name"
                ].casefold(),
        )

        for team in canonical_teams:

            team_id = team[
                "team_id"
            ]

            relevant = [

                match

                for match in matches

                if (
                    match[
                        "home_team_id"
                    ]
                    == team_id
                    or
                    match[
                        "away_team_id"
                    ]
                    == team_id
                )
            ]

            # Matches are already chronological.
            selected = relevant[
                -self.window:
            ]

            results = []
            wins = 0
            draws = 0
            losses = 0
            goals_for = 0
            goals_against = 0

            selected_evidence = []

            for match in selected:

                is_home = (
                    match[
                        "home_team_id"
                    ]
                    == team_id
                )

                if is_home:

                    team_goals = (
                        match[
                            "home_goals"
                        ]
                    )

                    opponent_goals = (
                        match[
                            "away_goals"
                        ]
                    )

                    opponent_id = (
                        match[
                            "away_team_id"
                        ]
                    )

                    opponent_name = (
                        match[
                            "away_team_name"
                        ]
                    )

                    venue = "HOME"

                else:

                    team_goals = (
                        match[
                            "away_goals"
                        ]
                    )

                    opponent_goals = (
                        match[
                            "home_goals"
                        ]
                    )

                    opponent_id = (
                        match[
                            "home_team_id"
                        ]
                    )

                    opponent_name = (
                        match[
                            "home_team_name"
                        ]
                    )

                    venue = "AWAY"

                if (
                    team_goals
                    >
                    opponent_goals
                ):

                    result = "W"
                    wins += 1

                elif (
                    team_goals
                    ==
                    opponent_goals
                ):

                    result = "D"
                    draws += 1

                else:

                    result = "L"
                    losses += 1

                results.append(
                    result
                )

                goals_for += (
                    team_goals
                )

                goals_against += (
                    opponent_goals
                )

                selected_evidence.append(
                    {

                        "date_utc":
                            match[
                                "date_utc"
                            ].isoformat(),

                        "venue":
                            venue,

                        "opponent_team_id":
                            opponent_id,

                        "opponent_team_name":
                            opponent_name,

                        "goals_for":
                            team_goals,

                        "goals_against":
                            opponent_goals,

                        "result":
                            result,
                    }
                )

            matches_available = len(
                selected
            )

            recent_results = "".join(
                results
            )

            recent_points = (
                3
                * wins
                + draws
            )

            goal_difference = (
                goals_for
                - goals_against
            )

            # ------------------------------------------------
            # Internal invariants
            # ------------------------------------------------

            if (
                matches_available
                !=
                wins + draws + losses
            ):

                raise TeamFormSourceError(
                    (
                        "Overall form count invariant failed "
                        f"for {team['team_name']}."
                    )
                )

            if len(
                recent_results
            ) != matches_available:

                raise TeamFormSourceError(
                    (
                        "Result-string length invariant failed "
                        f"for {team['team_name']}."
                    )
                )

            if not set(
                recent_results
            ).issubset(
                {
                    "W",
                    "D",
                    "L",
                }
            ):

                raise TeamFormSourceError(
                    (
                        "Invalid result symbol for "
                        f"{team['team_name']}."
                    )
                )

            if matches_available > self.window:

                raise TeamFormSourceError(
                    (
                        "Overall form window exceeded for "
                        f"{team['team_name']}."
                    )
                )

            team_rows.append(
                {

                    "team_id":
                        team[
                            "team_id"
                        ],

                    "team_name":
                        team[
                            "team_name"
                        ],

                    "form_matches_available":
                        matches_available,

                    "recent_results":
                        recent_results,

                    "recent_points":
                        recent_points,

                    "recent_wins":
                        wins,

                    "recent_draws":
                        draws,

                    "recent_losses":
                        losses,

                    "recent_goals_for":
                        goals_for,

                    "recent_goals_against":
                        goals_against,

                    "recent_goal_difference":
                        goal_difference,

                    "selected_matches":
                        selected_evidence,
                }
            )

        if len(
            team_rows
        ) != 20:

            raise TeamFormSourceError(
                (
                    "Overall form engine must return "
                    f"20 teams, found {len(team_rows)}."
                )
            )

        return team_rows