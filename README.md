# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr is a thrift-shopping assistant. A user describes the piece they want in plain language, optionally with a size and a price ceiling (for example, "vintage graphic tee under $30, size M"). The agent searches the secondhand listings for the best match, then suggests one or two outfits that pair it with clothes already in the user's wardrobe (or gives general styling advice if the wardrobe is empty), and writes a short, shareable "fit card" caption that names the item, its price, and its platform. If no listing matches, the agent stops before styling anything and tells the user what to change, such as raising the price limit, trying a different size, or broadening the description.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the 40 mock listings by price and size, then ranks what's left by keyword overlap with the description. A keyword in the title, style tags or category scores 2; one found only in the description, colors or brand scores 1. Filler words ("looking", "for", "under") are ignored and a trailing plural "s" is dropped. Size matches on whole tokens: every token of the requested size must appear in the listing's size, so `M` matches `M`, `S/M` and `M/L`, but `S` does not match `US 9` and `L` does not match `XL`. `One Size` listings match any size.
- **Inputs:** <!-- name and type each: `max_price` (float), not "a price" -->
  - `description` (str): keywords for what the user wants, e.g. `"vintage graphic tee"`
  - `size` (str | None): size to filter by, case-insensitive; `None` skips size filtering
  - `max_price` (float | None): price ceiling, inclusive; `None` skips price filtering
- **Returns:** `list[dict]`: up to `SEARCH_RESULT_LIMIT` (10) listing dicts, highest score first (ties keep dataset order). Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None) and `platform`.
- **When it has nothing:** Returns an empty list `[]`, not `None` and not an exception, when no listing passes the filters with a score above zero. The loop branches on this: it sets `session["error"]` and stops before `suggest_outfit`.

### `suggest_outfit`

- **What it does:** Asks the model, through `generate()`, for one or two outfits built around the thrifted item. If the wardrobe has items, the prompt lists them and asks for combinations that name pieces the user already owns. If it's empty, the prompt asks for general styling ideas for the item instead.
- **Inputs:**
  - `new_item` (dict): one listing dict from `search_listings`, the item being considered (uses `title`, `category`, `style_tags`, `colors`, `description`; `brand` may be `None`)
  - `wardrobe` (dict): a wardrobe dict with an `items` key holding a list of wardrobe item dicts; the list may be empty
- **Returns:** `str`: a non-empty block of outfit suggestions. Each suggestion names the pieces it combines, drawn from the user's wardrobe when there is one.
- **When it has nothing:** With an empty wardrobe (`wardrobe["items"] == []`) it returns general styling advice for the item, not `""` and not an exception. If the model can't be reached, `generate()` raises `ModelUnavailable`, which the loop handles.

### `create_fit_card`

- **What it does:** Asks the model, through `generate()`, for a short caption someone would actually post about the find. It should read like a real post, not a product description: specific about the vibe, and mentioning the item, its price and its platform once each.
- **Inputs:**
  - `outfit` (str): the outfit suggestion string returned by `suggest_outfit`
  - `new_item` (dict): the same listing dict passed to `suggest_outfit` (uses `title`, `price`, `platform`)
- **Returns:** `str`: a caption of two to four sentences. Different inputs produce different captions
- **When it has nothing:** If `outfit` is empty or only whitespace, it skips the model call and returns a descriptive message saying there was no outfit to caption, rather than raising. If the model can't be reached, `generate()` raises `ModelUnavailable`, which the loop handles.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that tells the user what to change (raise the price limit, drop or change the size, or use broader keywords), and return the session without calling `suggest_outfit` or `create_fit_card`. Otherwise, take the first (highest-scoring) result as `session["selected_item"]` and go on to `suggest_outfit`, then `create_fit_card`. Every pass round the loop first calls `trace.check_iterations(count)`, which raises once the count passes `MAX_ITERATIONS` (10).

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, no model call. `max_price` comes from a dollar amount after "under", "below", "less than" or "max" (e.g. `under $30` → `30.0`). `size` comes from the token after the word "size" (e.g. `size M` → `"M"`, `size US 8.5` → `"US 8.5"`). Whatever remains, with those phrases removed, is the `description`. If no price or size is found, that field is `None` and `search_listings` skips that filter.

**What moves through the session:** in order:
1. `query`: the user's text, set by `new_session`
2. `parsed`: `{"description", "size", "max_price"}` from the regex
3. `search_results`: the list `search_listings` returned (may be `[]`)
4. `error`: set here and the run stops, **only** if `search_results` is empty
5. `selected_item`: `search_results[0]`
6. `outfit_suggestion`: the string `suggest_outfit(selected_item, wardrobe)` returned
7. `fit_card`: the string `create_fit_card(outfit_suggestion, selected_item)` returned

`wardrobe` is set at the start and read by `suggest_outfit`. When the run stops early, `selected_item`, `outfit_suggestion` and `fit_card` stay `None`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```

```
$ python -c "from tools import suggest_outfit; ..."

```

```
$ python -c "from tools import create_fit_card; ..."

```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
