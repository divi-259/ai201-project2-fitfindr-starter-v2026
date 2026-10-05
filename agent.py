"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
        (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.
    """
    # 1. Start a session with new_session().
    session = new_session(query, wardrobe)

    # 2. Count the times round the loop, and call trace.check_iterations(count)
    #    on each one before you go again. It raises when the count passes
    #    MAX_ITERATIONS in config.py — see trace.py.
    count = 0
    while True:
        count += 1
        trace.check_iterations(count)

        # Every path through the body ends in `return session` — done, or
        # stopped early on the branch. If one doesn't, check_iterations above
        # is what catches it.

        # 3. Parse the query (regex — see README) into session["parsed"].
        session["parsed"] = _parse_query(query)
        parsed = session["parsed"]

        # 4. Search.
        session["search_results"] = search_listings(
            parsed["description"],
            size=parsed["size"],
            max_price=parsed["max_price"],
        )

        # ⚠️ THE BRANCH: nothing came back → say what to change, and stop
        # before suggest_outfit ever sees an empty result.
        if not session["search_results"]:
            session["error"] = _no_results_message(parsed)
            return session

        # 5. Choose an item — the first result is the highest-scoring one.
        session["selected_item"] = session["search_results"][0]

        # 6. Outfit, built around the item the session holds.
        session["outfit_suggestion"] = suggest_outfit(
            session["selected_item"], session["wardrobe"]
        )

        # 7. Fit card, from the outfit and the same item.
        session["fit_card"] = create_fit_card(
            session["outfit_suggestion"], session["selected_item"]
        )

        # 8. Done.
        return session

    """
    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

    • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

    • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """


# ── query parsing ─────────────────────────────────────────────────────────────

# "under $30", "below 25", "less than $40.50", "max $20"
_PRICE_RE = re.compile(
    r"\b(?:under|below|less than|max)\s*\$?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)

# "size M", "size S/M", "size XXS", "size W30", "size US 8.5"
_SIZE_RE = re.compile(
    r"\bsize\s+((?:us|w)\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?|[a-z]{1,3}(?:/[a-z]{1,3})?)\b",
    re.IGNORECASE,
)


def _parse_query(query: str) -> dict:
    """
    Pull a description, a size and a max_price out of the user's text.

    Price and size are found by regex and cut out of the query; whatever is
    left is the description. A missing price or size comes back as None, so
    search_listings skips that filter.
    """
    text = query

    max_price = None
    price_match = _PRICE_RE.search(text)
    if price_match:
        max_price = float(price_match.group(1))
        text = text[: price_match.start()] + " " + text[price_match.end():]

    size = None
    size_match = _SIZE_RE.search(text)
    if size_match:
        size = size_match.group(1)
        text = text[: size_match.start()] + " " + text[size_match.end():]

    description = " ".join(re.sub(r"[,$]", " ", text).split())
    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Say what the user could change, based on which filters they used."""
    changes = []
    if parsed["max_price"] is not None:
        changes.append(f"raise the price limit above ${parsed['max_price']:g}")
    if parsed["size"]:
        changes.append(f"try a different size than {parsed['size']}")
    changes.append("use broader keywords (e.g. 'jacket' instead of a specific style)")

    return (
        f"No listings matched '{parsed['description']}'"
        + (f" in size {parsed['size']}" if parsed["size"] else "")
        + (f" under ${parsed['max_price']:g}" if parsed["max_price"] is not None else "")
        + ". To find something, " + ", or ".join(changes) + "."
    )


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
