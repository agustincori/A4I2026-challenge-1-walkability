# Challenge 1 — Climate-Resilient Walkability

**Agents for Impact 2026**

---

## The problem

Two blocks in the same city, at the same hour on the same day, can differ by more than twenty
degrees. One has tree cover and low buildings. The other is parking lot and asphalt. The people
walking those two blocks are having completely different days, and one of them is in danger.

City planners know this in the abstract. What they don't have is a number for *this
intersection*, an argument they can put in front of a council, and someone to ask when the
question changes at 4pm on a Thursday.

## What you're building

**A planning assistant for a city's heat response.** Not a dashboard, and not a single query
with a chat box on it — an agent a planner can hold a working conversation with, that reaches
for real data and a real model to answer.

Your planner is not asking one question. Over an afternoon they might ask all of these:

> *"We have budget for three cooling centers in Ward 5. Where should they go?"*

> *"Why is 63rd and Halsted so much worse than two blocks north?"*

> *"How often does that spot actually hit dangerous levels? Is it getting worse?"*

> *"Who lives within a ten-minute walk of our proposed site, and can they get there without
> a car?"*

> *"We're choosing between these two intersections. Make the case for each."*

> *"Draft the proposal I'd take to council for the top site."*

Notice that these need **different things**. Some need a prediction. Some need only a query
against history. Some need the agent to weigh a tradeoff and say why. One needs it to write
prose a human will sign their name to.

**That range is the challenge.** An agent that can only answer the first question is a model
with a chat box. An agent that handles all six is something a planner would keep open.

### Your output artifact: a Placement Recommendation

Whatever else your agent does, it must be able to produce this — a ranked list of locations,
each carrying:

- coordinates, specific enough to stand on
- the predicted heat risk at that spot
- **why** — which factors drove it, and by how much
- who lives there: population, age, income, vehicle access
- a drafted proposal a planner could take to a council meeting

---

## The technology you'll use

Every team, every challenge, uses the same core stack:

| | |
|---|---|
| **ADK** (Agent Development Kit) | You build your agent in Python with ADK. This is the frame everything else hangs on. |
| **Gemini** | The reasoning model behind the agent — interpreting what the planner meant, weighing tradeoffs, drafting the proposal. |
| **BigQuery** | Your data store. Everything you load lives here and your agent queries it. |
| **A Google-managed MCP server** | Consume at least one. Don't author your own. |
| **Deployed to Google Cloud** | Agent Runtime or Cloud Run, your choice. It has to actually run somewhere. |

### And one required differentiator: **BigQuery ML**

Each of the five challenges has one required technology that makes it distinct. Yours is
BigQuery ML, and here's why it belongs in this problem rather than being bolted on.

Look back at the planner's questions. *"How often does this hit dangerous levels"* is history —
you can answer it with a query. But *"where should the three cooling centers go"* is about
places nobody has measured. Your data has temperature readings along the streets volunteers
drove. It has nothing for the street they didn't.

**To answer that, your agent needs a model that can predict heat risk for a location it has
never seen.** You'll train one in BigQuery ML, and your agent must **call** that prediction
through a tool — not query historical rows and describe them.

Use `ML.EXPLAIN_PREDICT` rather than `ML.PREDICT`. It returns per-feature attributions alongside
each prediction — not just "+6.2°F" but *"+4.1 from street density, +2.8 from building age,
−0.7 from park proximity."* **That sentence is the answer to "why."** Teams that treat
explanation as a reporting step at the end finish with a number and no argument.

---

## Getting started

You have **4.5 hours** and there are **8–10 of you**. That is too many people for one keyboard,
and the single biggest risk to your team is the first hour disappearing into setup and
coordination. Spend fifteen minutes on Step 0. It will pay for itself twice over.

### Step 0 — Organise your team (do this first, together)

**Pick a repo owner.** One person. They create the team's repository and add everyone else to
it. Everything the team builds lands in that one repo — not eight forks.

**Everyone else: create a free GitHub account now** at [github.com](https://github.com) if you
don't have one, and **send your username to the repo owner**. Two minutes, and it unblocks
everyone. Do it while the owner is setting up the repo.

**Split into four lanes and say out loud who is on each.** All four start now, in parallel.
Waiting for the data lane to finish is how teams lose ninety minutes.

| Lane | What they own | Roughly |
|---|---|---|
| **Data** | Run the notebook, then train the BigQuery ML model | 2–3 people |
| **Agent** | The ADK agent, its tools, the MCP server integration | 2–3 people |
| **Front end** | The face: custom UI, Gemini Enterprise, or `adk web` | 2 people |
| **Story** | The Placement Recommendation, the demo, the narrative | 1–2 people |

Two things teams consistently get wrong here. **The front end lane should not wait for a working
agent** — build against a mocked response and swap it later; that's why deployment sits in the
middle of the day rather than the end. And **the story lane should start at minute zero**, not
in the last half hour. The team that decides what it's demonstrating early builds toward it.

**Agree on one more thing before you scatter:** who makes the call when you're behind. You will
be behind. Deciding in advance who says "we're cutting that" is worth more than it sounds.

### Step 1 — Create the team repository

**Repo owner only.**

1. At the top of this page, click the green **Use this template** button, then **Create a new
   repository**.
   *(If you don't see that button, use **Fork** instead and tell a coach — it means this repo
   wasn't flagged as a template.)*
2. Name it after your team, choose **Public**, and click **Create repository**.
3. Go to **Settings → Collaborators** and add every teammate's GitHub username.
4. Paste the repo URL somewhere everyone can see it.

Everyone else: wait for that URL, then open it. Everything below happens in **your team's copy**,
not in this one.

### Step 2 — Get into your Google Cloud project

**Your facilitator will tell you how to access your project. Follow those instructions** — they
vary by venue and they are the fastest path.

**There is one Google Cloud project per team.** You all share it. That means you can all see the
same BigQuery tables, which is the point, and it also means you can all overwrite each other's
work. Agree on who is creating what.

You have Owner on that project. You do not need to create a project, set up billing, or download
a key file.

### Step 3 — Load the data

**This is the data lane's job.** One person runs it; the rest of the team doesn't wait.

**If you've used Colab Enterprise before:** import `notebooks/01_load_explore.ipynb` by URL and
run it. Skip ahead.

**If you haven't:**

1. In the Google Cloud console, search for **Colab Enterprise** and open it.
2. **You'll be asked to enable some APIs. Say yes.** Then the Colab Enterprise home page shows
   *another* **Enable APIs** button at the top. Click that too. Two separate prompts is expected
   — it isn't an error and you haven't done anything wrong.
3. Go to **My Notebooks** → **Import**, and set the source to **URL**.
4. Paste the raw URL of the notebook from your team's repository. To get it: open
   `notebooks/01_load_explore.ipynb` on GitHub, click **Raw**, and copy the address bar.
5. Click **Import**, open the notebook, and run the cells top to bottom.

It takes about a minute. **Read the text between the cells** — it explains why each step happens,
and several of those explanations will save you time later. The notebook ends by validating
everything and telling you plainly whether anything is wrong.

### What you'll have

Three tables in your project, in a dataset called `a4i_climate`:

| Table | What it is |
|---|---|
| `heat_observations` | Street-level temperature readings across your city — tens of thousands of points |
| `station_daily_temps` | Seven years of daily maximums from weather stations near the city |
| `tract_demographics` | Population, age, income, and vehicle access by census tract |

### If the notebook won't run

There's a headless fallback that reaches the same end state. In Cloud Shell:

```bash
./scripts/load.sh dallas          # or any city; --list shows them all
```

---

## The data, and why we chose it

**NOAA Heat Watch** is the backbone. Volunteers drive instrumented cars along fixed routes
through a city on one hot day, logging temperature roughly once per second. It's the only public
dataset that resolves temperature differences *within* a city rather than between cities.

The other three fill gaps: **GHCN-Daily** for how often the city gets hot, **EPA Smart Location**
for the built environment, **ACS** for who is exposed. All public domain or CC0. Full detail is
in the notebook.

**One thing we deliberately excluded, and you should know why.** Vulnerability indices like the
NYC Heat Vulnerability Index and CDC's Social Vulnerability Index include race as a direct input
variable. We left those columns out.

Race genuinely correlates with urban heat exposure — that's well established, and formerly
redlined neighbourhoods run measurably hotter today. But the *cause* is the physical environment:
pavement, building density, missing tree cover. Those we can measure directly, and they're in
your data. Race is a cruder measurement of something we already have.

**Removing the column does not make your model unbiased.** Every proxy is still there. Which is
why the answer isn't deletion, it's checking: when you have your ranked recommendations, look at
whose neighbourhoods they landed in — as an audit of your output, never as a model input. If
your recommendations systematically miss the most vulnerable areas, that's a finding, and it's
worth more in a demo than another point of accuracy.

**Strip the variable. Audit the outcome. Say you did both.**

---

## Bringing your own data

**You're not limited to what we provide.** If your team knows a dataset that would make this
better — your city's tree canopy, cooling center locations, transit ridership, 311 complaints —
bring it. Thoughtful sourcing is exactly the judgment this challenge rewards, and judges are
looking for it.

**Augment, don't replace.** Get the core working on the provided data *first*. "Let's find better
data" is one of the most reliable ways to lose ninety minutes and have nothing to demo.

**Check the license before you load it.** This is a publicly branded event and winning projects
get promoted. Anything you bring has to clear the same bar we applied to ourselves:

| | |
|---|---|
| ❌ No **NonCommercial** (NC) | Winners are promoted commercially |
| ❌ No **NoDerivatives** (ND) | Building on the data is the whole point |
| ❌ No **share-alike** (ODbL, CC BY-SA) | It would encumber what *you* build |
| ❌ No **individual-level personal data** | Aggregate public statistics only |
| ❌ No **unstated license** | No license means no rights granted |
| ✅ Public domain, CC0, US Government works | Safe |

The trap most likely to catch you: **anything derived from OpenStreetMap is ODbL**, which is
share-alike — and OSM is the first thing most people reach for on a walkability problem. If
you're unsure about a source, ask a coach. Thirty seconds of checking beats finding out later.

---

## What's in this repository

```
notebooks/01_load_explore.ipynb   The main artifact. Run this first.
scripts/load.sh                   Headless fallback if Colab is unavailable.
data/                             Seed data, if any.
agent/                            Empty. Your agent goes here.
```

`agent/` is empty on purpose. We built the on-ramp — data, loading, validation, sample queries.
We didn't build the vehicle. The design decisions in your agent are what you'll be judged on.

---

## How you'll be judged

**"Finished" is not the goalpost.** Almost nobody completes everything they set out to do in
4.5 hours — that's the design, not a failure. A team that gets three quarters of the way with
clear reasoning and honest limitations will beat a team that demos something polished and hollow.

| Dimension | Weight | The question judges are asking |
|---|---:|---|
| **Impact & insight** | 30 | Would a planner actually use this? Is the answer specific enough to act on? |
| **Technical execution** | 30 | Does it work, and is the required stack genuinely used rather than name-checked? |
| **Rigor & judgment** | 25 | Can you defend the decisions you made along the way? |
| **Craft & communication** | 15 | Can you show it, and can a non-technical person follow? |
| **Bonus — range** | **+10** | Technology breadth and ambition that *serves* the solution |

Bonus sits **on top** of the 100, so ambition can't cannibalise the core. Nail the fundamentals
and add nothing, and you can still win. Wire up five services with no coherent recommendation,
and you can't win on breadth alone.

### What "Rigor & judgment" actually means

This is the one teams under-invest in, because it's the least visible in a demo. It's worth a
quarter of your score, and it is the easiest place to stand out. Four concrete things:

**Data decisions you can defend.** If you brought your own dataset, do you know its license? Why
that source and not another? Did you check whether the columns were the types you assumed?

**Validation.** Did you check your tables before modelling, or assume that no error meant no
problem? The notebook ships a validation section — using it, and saying what it told you, counts.

**Bias handling.** Did you keep race out of your model inputs, and did you audit where your
recommendations actually landed? Be ready to talk about this. It's the most interesting
conversation available in this challenge.

**Knowing what your model can't do.** The heat data is a single day. The campaigns were driven by
volunteers. The weather stations are sparse. A team that volunteers its limitations is
demonstrating more skill than one that oversells — and judges are explicitly told to reward it.

One warning worth internalising: **a model with 98% accuracy on this problem is almost certainly
broken**, not brilliant. It usually means the features contain the answer. If your model can't
be wrong, it isn't predicting anything.

---

## Getting help

Ask a coach. That's what they're there for, and whatever you're stuck on has probably already
been solved at another table.

To report a problem with the data or the notebook, run the **diagnostic cell** at the bottom of
the notebook and share what it prints. It's one block with everything a coach needs, and it
beats a screenshot every time.
