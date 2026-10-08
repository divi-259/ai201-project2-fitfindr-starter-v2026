"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
    {
        # Criterion 3 — state. A normal matching query; what's checked is the
        # item id in the trace: select_item, suggest_outfit and create_fit_card
        # must all show the same id as the search's top result.
        "name": "state: same item through every tool",
        "query": "denim jacket size M",
        "wardrobe": "example",
        "criterion": 3,
    },
    # Criterion 4 — the fit card, across FIVE DIFFERENT items. run_eval runs
    # each scenario five times; score try 1 of each item as that item's try.
    # Each query below selects a different top listing (checked with
    # search_listings directly).
    {
        # → lst_001 Vintage Levi's 501 Jeans — Medium Wash
        "name": "fit card: item 1 (Levi's jeans)",
        "query": "vintage levis jeans under $50",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # → lst_008 Knit Cardigan — Chunky Brown
        "name": "fit card: item 2 (cardigan)",
        "query": "cardigan under $40",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # → lst_013 90s Silk Slip Dress — Floral, Midi Length
        "name": "fit card: item 3 (slip dress)",
        "query": "slip dress",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # → lst_011 Low-Rise Cargo Pants — Khaki
        "name": "fit card: item 4 (cargo pants)",
        "query": "cargo pants under $30",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # → lst_004 90s Track Jacket — Navy/White Stripe
        "name": "fit card: item 5 (track jacket)",
        "query": "track jacket",
        "wardrobe": "example",
        "criterion": 4,
    },
    # Criterion 5 — the size filter, one scenario per size. Broad "vintage"
    # queries pull in many sizes, so a loose filter would show up here. The
    # search trace step prints every returned size; each must contain the
    # requested size as a whole token (no XL for L, no US 9 for S).
    #
    # Scoring rule, decided before the run: a "One Size" listing does NOT
    # contain the requested size, so a try that returns one is a FAIL. The
    # search lets One Size through on purpose — if that costs the criterion,
    # it's a finding to diagnose, not a reason to reword the criterion.
    {
        "name": "size filter: S",
        "query": "vintage size S",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        "name": "size filter: M",
        "query": "vintage size M",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        "name": "size filter: L",
        "query": "vintage size L",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        "name": "size filter: XL",
        "query": "vintage size XL",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        "name": "size filter: US 8",
        "query": "sneakers size US 8",
        "wardrobe": "example",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
