"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    listings = load_listings()

    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    if size:
        listings = [l for l in listings if _size_matches(size, l["size"])]

    keywords = _words(description)
    scored = []
    for listing in listings:
        score = _score(keywords, listing)
        if score > 0:
            scored.append((score, listing))

    # sorted() is stable, so ties keep the dataset's order
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "in", "of", "to", "on",
    "i", "im", "me", "my", "looking", "want", "need", "some", "something",
    "under", "size", "any", "that", "is",
}


def _tokens(text: str) -> list[str]:
    """Lowercase alphanumeric runs, keeping decimals: "US 8.5" → ["us", "8.5"]."""
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())


def _words(text: str) -> set[str]:
    """Keywords for scoring — tokens minus filler, with a trailing plural 's' dropped."""
    words = set()
    for token in _tokens(text):
        if token in _STOPWORDS:
            continue
        if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        words.add(token)
    return words


def _size_matches(wanted: str, listing_size: str) -> bool:
    """
    A size matches when every token of the requested size appears as a whole
    token in the listing's size. So "M" matches "M", "S/M" and "M/L", but not
    "W30 L30"; "S" doesn't match "US 9"; "L" doesn't match "XL".

    "One Size" listings don't match an explicit size. A user who asks for
    size S wants something labelled S, not a belt or a hat that fits anyone.
    They still show up when no size is given, because then this filter is
    skipped altogether.
    """
    have = set(_tokens(listing_size))
    want = set(_tokens(wanted))
    return bool(want) and want <= have


def _score(keywords: set[str], listing: dict) -> int:
    """
    Keyword overlap. A hit in the title, style tags or category counts 2;
    a hit only in the description, colors or brand counts 1.
    """
    strong = _words(" ".join([
        listing["title"],
        listing["category"],
        " ".join(listing["style_tags"]),
    ]))
    weak = _words(" ".join([
        listing["description"],
        " ".join(listing["colors"]),
        listing["brand"] or "",
    ]))

    score = 0
    for word in keywords:
        if word in strong:
            score += 2
        elif word in weak:
            score += 1
    return score


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    items = wardrobe.get("items") or []
    item_text = _describe_item(new_item)

    if not items:
        prompt = (
            f"Someone is thinking about buying this thrifted piece:\n{item_text}\n\n"
            "They haven't told us what else they own. Suggest one or two "
            "outfits built around this piece, using common staples (say what "
            "kind of bottoms, shoes, layers or accessories). Keep each outfit "
            "to two or three sentences."
        )
    else:
        wardrobe_text = "\n".join(_describe_wardrobe_item(w) for w in items)
        prompt = (
            f"Someone is thinking about buying this thrifted piece:\n{item_text}\n\n"
            f"Here is what they already own:\n{wardrobe_text}\n\n"
            "Suggest one or two outfits that pair the new piece with specific "
            "items from their wardrobe. Name the wardrobe pieces exactly as "
            "listed. Keep each outfit to two or three sentences."
        )

    system = (
        "You are a thrift-savvy stylist. Give concrete, wearable outfit "
        "suggestions. Only name wardrobe pieces the user actually listed."
    )
    response = generate(prompt, system=system)
    if not response.strip():
        return f"Try the {new_item['title']} with simple basics in neutral colors."
    return response


def _describe_item(item: dict) -> str:
    """One listing, as prompt text. `brand` is often None, so leave it out then."""
    lines = [
        f"- Title: {item['title']}",
        f"- Category: {item['category']}",
        f"- Colors: {', '.join(item['colors'])}",
        f"- Style: {', '.join(item['style_tags'])}",
        f"- Condition: {item['condition']}",
        f"- Description: {item['description']}",
    ]
    if item.get("brand"):
        lines.insert(1, f"- Brand: {item['brand']}")
    return "\n".join(lines)


def _describe_wardrobe_item(item: dict) -> str:
    """One wardrobe piece, as a single prompt line."""
    line = f"- {item['name']} ({item['category']}; {', '.join(item.get('colors') or [])})"
    if item.get("notes"):
        line += f", {item['notes']}"
    return line


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return (
            f"No fit card for the {new_item.get('title', 'item')}: there was no "
            "outfit suggestion to caption."
        )

    prompt = (
        f"Write a caption for a social post by someone who just bought this "
        f"thrift find and is showing off how they styled it.\n\n"
        f"Item: {new_item['title']}\n"
        f"Price: ${new_item['price']:.2f}\n"
        f"Platform: {new_item['platform']}\n"
        f"Style: {', '.join(new_item['style_tags'])}\n\n"
        f"How they're wearing it:\n{outfit}\n\n"
        "Two to four sentences. Mention the item, the price and the platform "
        "once each. Be specific about the vibe. No hashtag walls, no bullet "
        "points. Just the caption."
    )
    system = (
        "You write captions people actually post: casual, first person, a bit "
        "of personality. Never sound like a product listing."
    )
    return generate(prompt, system=system)
