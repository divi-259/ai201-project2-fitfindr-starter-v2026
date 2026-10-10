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
> All three tools and the planning loop are built, so that last command runs
> the whole agent: search, outfit, fit card.
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

- **What it does:** Filters the 40 mock listings by price and size, then ranks what's left by keyword overlap with the description. A keyword in the title, style tags or category scores 2; one found only in the description, colors or brand scores 1. Filler words ("looking", "for", "under") are ignored and a trailing plural "s" is dropped. Size matches on whole tokens: every token of the requested size must appear in the listing's size, so `M` matches `M`, `S/M` and `M/L`, but `S` does not match `US 9` and `L` does not match `XL`. `One Size` listings never match an explicit size request (they still appear when no size is given). *Changed in unit 4, because criterion 5 missed: the size filter used to let `One Size` match any size. See The Improvement.*
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

> **Updated in unit 4 (stretch: retry with looser constraints):** an empty search no longer stops straight away. The agent retries first without the price limit, then without the size, and stops only when an empty search has nothing left to loosen. It never changes the keywords. If a loosened search finds something, it carries on to `suggest_outfit` and sets `session["notice"]` to say what was dropped. The rule that `suggest_outfit` never sees an empty result still holds. See "Stretch: retry with looser constraints" under On the MCP move.

**Where it lives:** `agent.py::run_agent`

**Over MCP (unit 4):** `search_listings` and `suggest_outfit` are called through `call_tool` in `mcp_client.py`, which talks to `mcp_server.py`. `suggest_outfit` is the stretch move, explained under On the MCP move. `create_fit_card` is still a direct call.

**How the query is parsed:** Regex, no model call. `max_price` comes from a dollar amount after "under", "below", "less than" or "max" (e.g. `under $30` → `30.0`). `size` comes from the token after the word "size" (e.g. `size M` → `"M"`, `size US 8.5` → `"US 8.5"`). Size formats handled: `M`, `S/M`, `XXS`, `W30`, `US 8.5`. Whatever remains, with those phrases, commas and `$` signs removed, is the `description`. If no price or size is found, that field is `None` and `search_listings` skips that filter. The parsing is `_parse_query` in `agent.py`.

**The error message on an empty search:** built by `_no_results_message` in `agent.py`. It repeats what was searched for and suggests changing only the filters the user actually set, plus broader keywords. For `designer ballgown size XXS under $5`:

> No listings matched 'designer ballgown' in size XXS under $5. To find something, raise the price limit above $5, or try a different size than XXS, or use broader keywords (e.g. 'jacket' instead of a specific style).

> **Updated in unit 4 (stretch):** with retries, the agent only stops once the price and size have already been dropped, so suggesting them again would send the user down a dead end. The final message now names only the keywords:
>
> No listings matched 'designer ballgown', even after searching without the price limit and without the size. The keywords are what's missing: use broader ones (e.g. 'jacket' instead of a specific style).

**What moves through the session:** in order:
1. `query`: the user's text, set by `new_session`
2. `parsed`: `{"description", "size", "max_price"}` from the regex
3. `search_results`: the list `search_listings` returned (may be `[]`)
4. `error`: set here and the run stops, **only** if `search_results` is empty
5. `selected_item`: `search_results[0]`
6. `outfit_suggestion`: the string `suggest_outfit(selected_item, wardrobe)` returned
7. `fit_card`: the string `create_fit_card(outfit_suggestion, selected_item)` returned

`wardrobe` is set at the start and read by `suggest_outfit`. When the run stops early, `selected_item`, `outfit_suggestion` and `fit_card` stay `None`.

**Added in unit 4 (stretch):**
- `search_params`: what the last search actually used. It matches `parsed` unless a retry loosened it.
- `relaxed`: the constraints dropped on retry, in order: `"price"`, then `"size"`.
- `notice`: set when a loosened search found something, telling the user what was dropped. `app.py` prints it above "Found".

`parsed` is set once, before the loop, and never changes, so the session always holds what the user actually asked for.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Casual Y2K Denim Look**
Pair the Y2K Baby Tee — Butterfly Print with your baggy straight-leg jeans, dark wash for a classic early 2000s silhouette. Finish the look by stepping into your chunky white sneakers and slinging the black crossbody bag over your shoulder. 

**Outfit 2: Layered Streetwear Style**
Tuck the Y2K Baby Tee — Butterfly Print into your wide-leg khaki trousers, secured with the brown leather belt. Layer your vintage black denim jacket on top and lace up your black combat boots to add an edgy contrast to the cute butterfly graphic.

  Fit card: scored this little butterfly baby tee on depop for just 18 bucks and I'm obsessed. figured it was too cute not to style a couple ways, so I'm currently torn between throwing it on with baggy denim and chunky sneaks or edging it up with wide-leg trousers and a black denim jacket.

2 model calls this session, 577 prompt + 197 output tokens
```

**The same command on a query nothing matches**, which stops before any model call:

```
$ python app.py ask 'designer ballgown size XXS under $5'

  No listings matched 'designer ballgown' in size XXS under $5. To find something, raise the price limit above $5, or try a different size than XXS, or use broader keywords (e.g. 'jacket' instead of a specific style).

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_012', 'title': 'Oversized Crewneck Sweatshirt — Vintage Navy', 'description': 'Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.', 'category': 'tops', 'style_tags': ['vintage', 'basics', 'oversized', 'classic'], 'size': 'XL (fits oversized)', 'condition': 'good', 'price': 20.0, 'colors': ['navy'], 'brand': None, 'platform': 'thredUp'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
**Outfit 1: Effortless Streetwear**
Pair the Vintage Levi's 501 Jeans with the white ribbed tank top tucked in, cinched with the brown leather belt. Throw the oversized grey crewneck sweatshirt over your shoulders and finish the look with the chunky white sneakers and the black crossbody bag. 

**Outfit 2: Edgy Casual**
Style the Vintage Levi's 501 Jeans with the black cropped zip hoodie layered underneath the vintage black denim jacket for a cool double-denim moment. Ground the outfit with the black combat boots and carry your essentials in the black crossbody bag.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these vintage Levi's 501s on depop for $38 and I am never taking them off. Paired them with crisp white sneakers for that effortlessly cool 90s dad vibe. Honestly the wash on these is just too good.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1: writing the three tools**

- *What I asked for:* I asked Claude to write all three tool functions in tools.py after helping me understand what each tool does.
- *What came back:* It came up with fully formed methods taking care of edge cases.
- *What I changed:* I made sure the code was functional, and tested each function.

**Moment 2: formatting the write-up, and understanding how the code works**

- *What I asked for:* I asked Claude to format README sections (Tool Inventory, Planning Loop, Sample Run) and to refine the criteria and their whys in `criteria.md`. I also asked how to run each tool and check its results, so I could understand what the code was actually doing.
- *What came back:*
It formatted and the files, and helped me brainstorm the criteria.md 
- *What I changed:*
I updated my criterias after the suggestions from the claude to make it more robust.

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
| 1. A matching query completes all three tools | 4 of 5 | FAIL | FAIL | FAIL | PASS | FAIL | MISSED (1/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item search found is the item every later tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the item, its price and its platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. The size filter returns no false matches | 5 of 5 | FAIL | FAIL | FAIL | FAIL | PASS | MISSED (1/5) |

Source: `results/run_2026-10-07_1723_before.md`, produced by `run_eval.py::main` (5 tries per scenario, caching off, temperature 0.9). The scenarios are in `scenarios.py`.

How each row's tries map to scenarios:
- **Criteria 1–3:** one scenario each, run 5 times.
- **Criterion 4:** the five tries are five different items: Levi's jeans (`lst_001`), cardigan (`lst_008`), slip dress (`lst_013`), cargo pants (`lst_011`) and track jacket (`lst_004`). Each column is try 1 of that item's scenario.
- **Criterion 5:** the five tries are five sizes, in order S, M, L, XL and US 8. Each column is try 1 of that size's scenario. The search doesn't call the model, so all 5 tries of each size returned identical results.

All 14 crashed tries in this run, across every scenario, raised the same error:

```
ModelUnavailable: Couldn't reach the model: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}
```

Diagnostic run, not one of the five: **empty wardrobe** (`denim jacket under $50`, empty wardrobe) completed 2 of 5 tries, and the other 3 crashed with the 503 above. Both completed tries returned general styling advice instead of crashing or returning `""`.

**Real output from one try**, pasted as text, naming the file and function
that produced it. Criterion 1, try 4, from `run_eval.py::main` running `agent.py::run_agent`:

```
- stopped early: no
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Outfit suggestion:
**Outfit 1: Y2K Casual Streetwear**
Pair the Y2K Baby Tee — Butterfly Print with your Baggy straight-leg jeans, dark wash for that classic early 2000s contrast between fitted and loose. Layer your Vintage black denim jacket over top and finish with the Chunky white sneakers.

**Outfit 2: Sporty Layered Look**
Style the Y2K Baby Tee — Butterfly Print underneath your Black cropped zip hoodie left open for a casual layered effect, paired with your Baggy straight-leg jeans, dark wash. Complete the outfit with your Black combat boots and the Black crossbody bag.

Fit card:
Found this cute lil butterfly baby tee on depop for $18 and haven't taken it off since. Swung it with baggy dark wash denim and sneakers for that lazy 2000s streetwear vibe, but I'm lowkey obsessed with how it looks under an unzipped hoodie with combat boots too. Such a good little find.

Trace:
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    top id=lst_002
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    id=lst_002; results found → top match, continuing to suggest_outfit
[4] suggest_outfit
      in:  item id=lst_002 'Y2K Baby Tee — Butterfly Print', wardrobe_items=10
      out: **Outfit 1: Y2K Casual Streetwear** Pair the Y2K Baby Tee — Butterfly Print with your Baggy straight-leg jeans…
[5] create_fit_card
      in:  item id=lst_002 'Y2K Baby Tee — Butterfly Print', outfit=<from suggest_outfit>
      out: Found this cute lil butterfly baby tee on depop for $18 and haven't taken it off since. Swung it with baggy da…
```

And try 1 of the same criterion, which crashed:

```
ModelUnavailable: Couldn't reach the model: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}
```

Criterion 5, size S (identical in all 5 tries):

```
[2] search_listings (via MCP)
      in:  {'description': 'vintage', 'size': 'S', 'max_price': None}
      →    top id=lst_002; sizes returned: ['S/M', 'S', 'One Size (adjustable)', 'One Size', 'S', 'One Size']
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
| 1 | A matching query completes all three tools | 4 of 5 | MISSED (1/5) | Only try 4 reached step 5 (`create_fit_card`) and returned a fit card. Tries 1, 2, 3 and 5 crashed with `ModelUnavailable` (503) and returned no fit card, so they count as FAIL. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | In all 5 tries, the trace ended at step 3 (`branch`) with no `suggest_outfit` step, `selected_item` was `(none)`, and the message named all three things to change: price, size and keywords. |
| 3 | The item search found is the item every later tool receives | 5 of 5 | MET (5/5) | In all 5 tries, the search's top result, `select_item`, `suggest_outfit` and `create_fit_card` all showed the same id, `lst_004`. |
| 4 | The fit card names the item, its price and its platform | 4 of 5 | MET (5/5) | For each of the five items, the try-1 card named the item, gave the exact listing price ($38, $35, $30, $27, $45), named the platform (Depop or Poshmark), and was 3 sentences long. One judgment call: the cardigan card says "chunky brown knit" rather than "cardigan". I counted that as naming the item because the words come from its title (`Knit Cardigan — Chunky Brown`). Counted strictly, this row is still MET at 4/5. |
| 5 | The size filter returns no false matches | 5 of 5 | MISSED (1/5) | S, M, L and XL each returned at least one `One Size` listing, which doesn't contain the requested size, so those tries FAIL under the rule I set in `scenarios.py` before the run. US 8 returned only `US 8`, so it PASSES. Apart from `One Size`, every result matched on a whole token: no XL for L, no US 9 for S. |

**Diagnoses**

**Criterion 1, MISSED 1/5.**
- **Where:** the model, plus the loop's lack of handling for it.
- **Mechanism:** Gemini (`gemini-3.5-flash-lite`) returned `503 UNAVAILABLE — This model is currently experiencing high demand`. `generate()` raised `ModelUnavailable`, and `agent.py::run_agent` neither retries nor catches it, so one failed model call crashed the whole run with no fit card.
- **The pattern:** all 14 crashes in the run, across 5 scenarios, are this same 503. That's one problem, not 14.
- **Why it isn't the loop's logic:** the earlier run of this same scenario (`results/run_2026-10-07_1646_before.md`) completed 5 of 5 with no crashes, and the one try here that reached the model completed normally. The loop works when the model answers. It has no defence when the model is briefly overloaded, which is a transient failure that a retry would usually get past.

**Criterion 5, MISSED 1/5.**
- **Where:** the `search_listings` tool (`tools.py`).
- **Mechanism:** the size filter treats a `One Size` listing as matching every requested size. This was on purpose, and the Tool Inventory said so at the time ("`One Size` listings match any size"). Broad `vintage` queries pull in accessories sized `One Size` or `One Size (adjustable)` (a braided belt, a bucket hat and a shoulder bag), so they pass the filter for S, M, L and XL. US 8 passed only because the `sneakers` query didn't match any `One Size` listing.
- **Why it's consistent:** this is plain code with no model involved, so all 5 tries of each size returned identical results. The filter itself is correct on whole tokens. The conflict is between the rule that `One Size` fits all and the criterion's "every listing has the requested size".

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
python app.py ask 'vintage graphic tee under $30'         


[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    results found → top match, continuing to suggest_outfit
[4] suggest_outfit
      in:  item='Y2K Baby Tee — Butterfly Print', wardrobe_items=10
      out: **Outfit 1: Casual Y2K Denim Look** Pair the Y2K Baby Tee — Butterfly Print with your Baggy straight-leg jeans…
[5] create_fit_card
      in:  item='Y2K Baby Tee — Butterfly Print', outfit=<from suggest_outfit>
      out: scored this little butterfly print baby tee on depop for $18 and I’m literally never taking it off. worn it tw…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Casual Y2K Denim Look**
Pair the Y2K Baby Tee — Butterfly Print with your Baggy straight-leg jeans, dark wash. Complete the outfit by slipping on the Chunky white sneakers and wearing the Black crossbody bag. 

**Outfit 2: Layered Streetwear Style**
Style the Y2K Baby Tee — Butterfly Print underneath the Vintage black denim jacket, paired with your Baggy straight-leg jeans, dark wash. Finish the look with the Black combat boots for an effortless edge.

  Fit card: scored this little butterfly print baby tee on depop for $18 and I’m literally never taking it off. worn it twice already—first with baggy dark wash denim and chunky sneakers for pure y2k nostalgia, and then layered under an oversized black jacket with combat boots when I want it a little more grunge. honestly the easiest $18 I’ve ever spent.
```

**Empty search**

```
python app.py ask 'yellow car under $30'         


[1] parse_query
      in:  yellow car under $30
      out: {'description': 'yellow car', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'yellow car', 'size': None, 'max_price': 30.0}
      out: [] (empty)
[3] branch
      →    search empty → stopping before suggest_outfit

  No listings matched 'yellow car' under $30. To find something, raise the price limit above $30, or use broader keywords (e.g. 'jacket' instead of a specific style).

0 model calls this session


```

**On the MCP move:** <!-- what changed in your code, and whether anything behaved differently afterwards. If the rewire didn't work, say exactly where it  broke — the error text and the last thing that worked. That earns the point in full. -->

### Stretch: a second tool moved onto MCP, `suggest_outfit`

`suggest_outfit` is now also registered in `mcp_server.py` and called over MCP. It's the first tool on the server that calls the model.

### Stretch: retry with looser constraints

Before this change, an empty search stopped the run straight away. Now `agent.py::run_agent` retries with looser constraints, using the `while` loop that until now only ever ran once:

1. Search with everything the user gave: keywords, size and price.
2. If that comes back empty and there was a price limit, drop the price limit and search again.
3. If it's still empty and there was a size, drop the size and search again.
4. If it's still empty with nothing left to loosen, stop before `suggest_outfit` with a message, as before.



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** the size rule in `search_listings`, specifically `_size_matches` in `tools.py`. Before, a listing sized `One Size` matched every requested size. Now a `One Size` listing never matches an explicit size request. It still appears when the query gives no size, because the size filter is skipped then. The search behaviour changed because criterion 5 failed. The criterion itself is unchanged in `criteria.md`, with the same wording and the same 5 of 5 target, and the after-run is measured against it.

**Which failure it was meant to fix:** criterion 5, "the size filter returns no false matches", which MISSED at 1/5 in the before-run. The diagnosis pointed at the tool rather than the model: S, M, L and XL each returned `One Size` accessories (a braided belt, a bucket hat and a shoulder bag), and only US 8 came back clean. The filter is plain code, so the miss was the same in every try. That makes it a rule to change, not randomness to retry around. Checked directly after the change, the same queries return only matching sizes. For example, `vintage size S` now returns `S/M`, `S` and `S`, where before it also returned three `One Size` listings.

Not part of the improvement: alongside it I also added a `ModelUnavailable` handler to `agent.py::run_agent`, which is one of the required failure modes. It turns a model error such as a bad key or a 503 into a message in `session["error"]` instead of a crash. It doesn't retry, so it can't turn a criterion 1 FAIL into a PASS. Any criterion 1 change in the after-run comes from Gemini's load at the time, not from this.

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item search found is the item every later tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the item, its price and its platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. The size filter returns no false matches | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Source: `results/run_2026-10-07_1905_after.md`, produced by `run_eval.py::main` (5 tries per scenario, caching off, temperature 0.9). It used the same scenarios as the before-run, with tries mapped the same way: criterion 4 is try 1 of each of the five items, and criterion 5 is try 1 of S, M, L, XL and US 8. No try crashed and none hit a 503. The empty-wardrobe diagnostic completed 5 of 5, each with general styling advice.

Criterion 5, the row the improvement targeted. Every returned size now contains the requested size, and the result was identical in all 5 tries of each size:

```
vintage size S      before: ['S/M', 'S', 'One Size (adjustable)', 'One Size', 'S', 'One Size']
                    after:  ['S/M', 'S', 'S']
vintage size M      before: ['S/M', 'M', 'M', 'One Size (adjustable)', 'M/L', 'M', 'M', 'M', 'M', 'M']
                    after:  ['S/M', 'M', 'M', 'M/L', 'M', 'M', 'M', 'M', 'M', 'M']
vintage size L      before: ['L', 'L', 'One Size (adjustable)', 'L', 'M/L', 'L', 'One Size', 'One Size']
                    after:  ['L', 'L', 'L', 'M/L', 'L']
vintage size XL     before: ['XL (oversized)', 'XL (fits oversized)', 'One Size (adjustable)', 'XL', 'One Size', 'One Size']
                    after:  ['XL (oversized)', 'XL (fits oversized)', 'XL']
sneakers size US 8  before: ['US 8']
                    after:  ['US 8']
```

Criterion 4, try 1 of each item. Every card names the item, its exact price and its platform in 2 to 3 sentences:

```
Levi's jeans  ($38, depop):     scored these vintage levi's 501s on depop for $38 and i’m obsessed with how they fit. …
cardigan      ($35, depop):     Scored this chunky brown knit cardigan on Depop for $35 and honestly haven't taken it off since. …
slip dress    ($30, depop):     scored this 90s floral silk slip dress on depop for just $30 and honestly I’m never taking it off. …
cargo pants   ($27, poshmark):  Scored these low-rise khaki cargos on Poshmark for $27 and honestly they're doing all the heavy lifting. …
track jacket  ($45, poshmark):  Scored this navy and white 90s track jacket on Poshmark for $45 and I'm obsessed. …
```

**Did it help, and how do I know:**

**For criterion 5, yes: it went from MISSED (1/5) to MET (5/5).**
- **What changed in the output:** before the fix, the S, M, L and XL queries each returned `One Size` accessories. After it, every returned size contains the requested size as a whole token. The table above shows it query by query.
- **Why the change caused it:** the search is plain code with no model involved, and the queries, data and scoring rule were the same in both runs. The size rule was the only thing that changed between them.
- **Nothing else broke:** sized results that were correct before are still returned, such as `S/M` for S and `M/L` for L. US 8 is unchanged. Criterion 3's scenario (`denim jacket size M`) returned the same four sizes as before.

**Criterion 1 also went from MISSED (1/5) to MET (5/5), but the improvement didn't cause that.**
- **Why it changed:** every before-run failure on criterion 1 was a Gemini `503 UNAVAILABLE` (high demand). The after-run had no 503s, so every try reached the model and finished.
- **Why it isn't the improvement:** the size fix doesn't affect this query, which has no size. The `ModelUnavailable` handler can only turn a crash into an error message, which still scores FAIL.


---

## What's Still Broken

Every criterion was MET in the after-run, but two weaknesses are still there:

- **Criterion 1 depends on Gemini being available.** The before-run showed that a burst of 503s can take it down to 1/5. The `ModelUnavailable` handler now turns those failures into a readable message instead of a crash, but it doesn't retry, so on a busy day criterion 1 would miss again.

- **Criterion 4's "names the item" is a judgment call.** In the before-run, the cardigan card said "chunky brown knit" without the word "cardigan", and I counted it as a pass. A stricter check, such as requiring the item's category word in the card, would make the criterion scorable without judgment.

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
