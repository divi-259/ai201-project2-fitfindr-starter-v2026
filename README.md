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

**How the query is parsed:** Regex, no model call. `max_price` comes from a dollar amount after "under", "below", "less than" or "max" (e.g. `under $30` → `30.0`). `size` comes from the token after the word "size" (e.g. `size M` → `"M"`, `size US 8.5` → `"US 8.5"`). Size formats handled: `M`, `S/M`, `XXS`, `W30`, `US 8.5`. Whatever remains, with those phrases, commas and `$` signs removed, is the `description`. If no price or size is found, that field is `None` and `search_listings` skips that filter. The parsing is `_parse_query` in `agent.py`.

**The error message on an empty search:** built by `_no_results_message` in `agent.py`. It repeats what was searched for and suggests changing only the filters the user actually set, plus broader keywords. For `designer ballgown size XXS under $5`:

> No listings matched 'designer ballgown' in size XXS under $5. To find something, raise the price limit above $5, or try a different size than XXS, or use broader keywords (e.g. 'jacket' instead of a specific style).

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
