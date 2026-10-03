# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->

My search is a plain keyword match, so a query phrased differently from the
listings can come back empty even when a good match exists. For example, no
listing contains the word "t-shirt" — they say "tee" — so a "t-shirt" query may
find nothing, and the loop stops before the fit card. Two of the three tools
also call the model, which can fail or return nothing. 4 of 5 leaves room for
one miss like that without excusing a loop that's actually broken.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->

This path never reaches the model. `search_listings` is plain code over a fixed
data file, so an impossible query returns an empty list every time, and the
check on that empty list is a plain `if` in `run_agent`. Nothing on this path
varies from run to run, so there's no reason to accept any misses. 

---

## 3. Something about state

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->

## 3. The item search found is the item every later tool receives

For a matching query, the `id` of `session["selected_item"]` is the same as the
`id` of `session["search_results"][0]`, the `new_item` passed to
`suggest_outfit`, and the `new_item` passed to `create_fit_card` — 5 of 5 tries.


**Why this target:**

Handing the item from one tool to the next is plain Python,  nothing on that
path calls the model, so there's no run-to-run variation to allow for.


---
## 4. Something about the fit card

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->

## 4. The fit card names the item, its price and its platform

For five different matching items, run with caching off, the fit card mentions
the item, its exact price, and its platform, and is two to four sentences long
— in at least 4 of 5 tries.


**Why this target:**

The prompt asks for all three facts and gives the model their exact values, so
most cards should include them. But the model writes freely at `TEMPERATURE`
0.9, and the system prompt asks for a casual post, not a listing — so it can
round a price ("under 40 bucks") or drop the platform in favour of vibe. 4 of 5
allows one card like that. 

---

## 5. Your choice

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->

The size filter returns no false matches. For five sized queries (size S, M, L, XL, US 8), every listing returned has the requested size as a whole token. So no US 9 for "S" and no XL for "L", 5 of 5 tries. 

**Why this target:**

The filter is plain code in python, and it should give a deterministic result.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
