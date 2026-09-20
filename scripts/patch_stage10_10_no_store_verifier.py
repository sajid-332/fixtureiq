from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

VERIFIER = (
    ROOT
    / "scripts"
    / "verify_stage10_10_1_10_10_5.py"
)


source = VERIFIER.read_text(
    encoding="utf-8"
)


old = '''    verify(
        "HTTP client uses no-store",
        (
            'cache: "no-store"'
            in
            api_sources[
                CLIENT
            ]
            or
            "cache: 'no-store'"
            in
            api_sources[
                CLIENT
            ]
        ),
    )
'''


new = '''    verify(
        "HTTP client uses no-store",
        re.search(
            r"""
            \\\\bcache
            \\\\s*
            :
            \\\\s*
            ["']
            no-store
            ["']
            """,
            api_sources[
                CLIENT
            ],
            re.VERBOSE,
        )
        is not None,
    )
'''


if old not in source:

    raise RuntimeError(
        "Expected no-store verifier block was not found."
    )


updated = source.replace(
    old,
    new,
    1,
)


VERIFIER.write_text(
    updated,
    encoding="utf-8",
)


print(
    "Stage 10.10 no-store verifier patch: APPLIED"
)