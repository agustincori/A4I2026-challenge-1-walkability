# Challenge 1 — Climate-Resilient Walkability

**Agents for Impact 2026**

---

## Why this one matters

Heat is the deadliest weather in America. In a typical year it kills more people than
hurricanes, floods, and tornadoes combined — and unlike those, it kills quietly, indoors and
on sidewalks, mostly among the old, the poor, and people who can't afford to run an air
conditioner.

It is also the most *unequal* hazard. Two blocks in the same city, at the same hour on the same
day, can differ by more than twenty degrees. One has tree cover and low buildings. The other is
parking lot and asphalt. The people walking those two blocks are having completely different
days, and one of them is in danger.

Cities know this in the abstract. What they don't have is a number for *this intersection*, an
argument they can put in front of a council, and someone to ask when the question changes at
4pm on a Thursday.

**A city has a small budget, a hot summer coming, and a decision to make about where to put
help.** Your job today is to build the thing that helps them make it well.

---

## First: pick a city

**This is not a universal application. It is an application for one city**, and choosing yours
is the first real decision your team makes. Everything downstream — your data, your model, your
demo, your story — lives in that city.

You do **not** have to pick the city you're sitting in.

Start here. These have the largest, best-tested datasets:

| | |
|---|---|
| **Dallas** (the default) | **Chicago** — ~49k readings |
| **New York (Manhattan/Bronx)** | **Seattle** — ~35k readings |
| **New York (Brooklyn)** | **Atlanta** — ~23k readings |
| **Los Angeles (Central)** | **Houston** — ~147k readings, the largest |

**We'd recommend staying on this list.** There are 87 cities available and Section 4 of the
notebook lists them all, but these are the ones we've tested end to end.

Then get specific, because specificity is what makes a demo land:

> *"We're the City of Dallas. It's July, we've had eleven days over 100°F, and we have
> funding for four new cooling centers plus one mobile hydration unit. We don't know where to
> put them, and the council meets in three weeks."*

That's your scenario. Write it down. Everything you build should answer to it.

---

## What you're building

**A planning assistant for a city's heat response.** Not a dashboard, and not a single query
with a chat box on it — an agent a planner can hold a working conversation with, that reaches
for real data and a real model to answer.

Your planner isn't asking one question. Over an afternoon they might ask all of these:

| What they ask | What answers it |
|---|---|
| *"We can fund three cooling centers this summer. Where should they go?"* | Your BQML model, ranked against demographics |
| *"Why is this spot so much worse than two blocks north?"* | `ML.EXPLAIN_PREDICT` attributions |
| *"How often does that area reach dangerous heat? Is it getting worse?"* | Seven years of station history |
| *"Who lives around the site we're considering — how many people, how old, how many without a car?"* | Census tract demographics |
| *"We're down to two sites. Make the case for each."* | Both, plus Gemini weighing the tradeoff |
| *"Draft the proposal I'd take to the council."* | Gemini, synthesising everything above |
| *"Did our recommendations actually reach the most vulnerable areas?"* | An equity audit of your own output |

Notice these need **different things**. Some need a prediction. Some need only a query against
history. Some need the agent to weigh a tradeoff and say why. One needs it to write prose a
human will sign their name to.

**That range is the challenge.** An agent that can only answer the first question is a model
with a chat box. An agent that handles all seven is something a planner would keep open.

### Questions that need more than we gave you

Be aware of the edges — and treat them as an opportunity, because closing one is exactly the
kind of thing that separates a team.

Our data uses **coordinates, not street names**, and **straight-line distance, not walking
routes**. So these need something extra:

| The question | What you'd need to add |
|---|---|
| *"What's at 63rd and Halsted?"* — talking in street names | Google Maps geocoding |
| *"Who's within a **10-minute walk**?"* — real walking distance | Google Maps routing / isochrones |
| *"Show me Ward 5"* — political boundaries | Your city's open data portal |
| *"Can people get there on transit?"* | Your city's GTFS feed |

We give you `no_vehicle_rate` per census tract, which tells you *who lacks a car* — that's the
right input for "if the nearest center is two miles away, who can't reach it?" It is not the
same as a walk-time isochrone. Know the difference, and say which one you used.

---

## What will set yours apart

Every team in this room building Challenge 1 gets the same data, the same model type, and the
same starting notebook. **The core is not where you win.**

Spend fifteen minutes deciding what *your* version does that nobody else's will. Some directions:

- **Go deeper on one question** rather than shallow on seven. An agent that handles the siting
  question superbly beats one that half-answers everything.
- **Bring a dataset nobody else has** — your city's tree canopy, its existing cooling centers,
  311 heat complaints. (See "Bringing your own data" — check the licence first.)
- **Make the equity audit the centrepiece** instead of a footnote. It's the most interesting
  conversation available in this challenge and most teams will skip it.
- **Solve a different decision.** Cooling centers are the obvious one. Where do you plant trees
  for the best return in ten years? Which bus stops need shade first? Which blocks should get
  a cool-pavement pilot?
- **Give it a memorable face** — a map a council member could read, not a JSON blob.

Read [how you'll be judged](#how-youll-be-judged) *before* you decide. It's at the bottom, it
takes two minutes, and it will change what you build.

---

## The technology you'll use

Every team, every challenge, uses the same core stack:

| | |
|---|---|
| **ADK** (Agent Development Kit) | You build your agent in Python with ADK. This is the frame everything else hangs on. |
| **Gemini** | The reasoning model behind the agent — interpreting what the planner meant, weighing tradeoffs, drafting the proposal. |
| **BigQuery** | All the data this challenge needs lives here, and your agent queries it. |
| **A managed MCP server** | Consume at least one — don't author your own. See below. |
| **Deployed to Google Cloud** | Agent Runtime or Cloud Run, your choice. It has to actually run somewhere. |

### Choosing your MCP server

You have two good options, and you should consume one rather than writing your own:

- **BigQuery's built-in MCP server** — the quickest path if all you need is to query your tables.
- **[MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox)** — Google's open
  source MCP server for databases. It ships prebuilt tools for immediate access *and* a
  framework for defining your own, with controls like restricted access and structured queries.

**The Toolbox is generally the more flexible of the two**, and if you want your agent's database
access shaped to your own tools rather than generic queries, start there.

### And one required differentiator: **BigQuery ML**

Each of the five challenges has one required technology that makes it distinct. Yours is
BigQuery ML, and here's why it belongs in this problem rather than being bolted on.

Look back at the planner's questions. *"How often does this hit dangerous levels"* is history —
a query answers it. But *"where should the cooling centers go"* is about places **nobody has
measured**. Your data has temperature readings along the streets volunteers drove. It has
nothing for the street they didn't.

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
and the biggest risk to your team is the first hour disappearing into setup and coordination.
Spend twenty minutes on Step 0. It pays for itself twice over.

### Step 0 — Organise your team

**Pick a team lead.** One person who makes the call when you're behind — and you *will* be
behind. Deciding in advance who says "we're cutting that" is worth more than it sounds. They
don't have to be the best coder; they have to be willing to decide.

**Pick a repo owner.** Can be the same person. They create the team's repository and add
everyone to it. Everything lands in that one repo — not eight forks.

**Everyone else: create a free [GitHub](https://github.com) account now** if you don't have one,
and **send your username to the repo owner.** Do it while they're setting up. Two minutes, and
it unblocks the whole team.

**Agree your scenario and your city** (see above). Five minutes. Write it on something everyone
can see.

**Split into four lanes.** All four start immediately, in parallel.

#### Data lane — 2 to 3 people

Running the notebook takes about a minute, so that is emphatically *not* the job. This lane owns
everything between raw tables and a model the agent can call:

- **Feature engineering** — this is the real work. The loaded tables aren't model-ready. You'll
  join street readings to census tracts, compute the target (how much hotter is this spot than
  the city average?), and derive features worth learning from.
- **Train, evaluate, iterate.** Run `ML.EVALUATE`. Try feature sets. Hunt for leakage — if
  accuracy looks spectacular, something is wrong.
- **Hand the agent lane a working query.** They need the exact `ML.EXPLAIN_PREDICT` SQL their
  tool will wrap. Getting that to them early unblocks them.
- **The frequency analysis** — how often does this city cross dangerous thresholds, and is the
  trend moving?
- **The equity audit** — where did our recommendations actually land, and who lives there?
- **Decide with the team whether to bring extra data**, and if so, source it and check the licence.

#### Agent lane — 2 to 3 people

The ADK agent, its custom Python tools, the MCP server integration, and deployment to Agent
Runtime or Cloud Run. Deploy early rather than at the end — the front end needs a live endpoint.

#### Front end lane — 2 people

The face: a custom UI, Gemini Enterprise, or `adk web`. **Do not wait for a working agent.**
Build against a mocked response and swap it later. That's precisely why deployment sits in the
middle of the day rather than the end.

#### Story lane — 1 to 2 people, starting at minute zero

Not "make slides at the end." This lane owns whether anyone understands what you built.

**What you're preparing: a short pitch deck and a quick demo.** Presentation time at this event
is tight — your facilitator will give you the exact number, but plan for short. That constraint
should shape everything this lane does. **A crisp pitch with one moment that lands beats a
thorough walkthrough nobody has time to hear.**

- **The pitch deck.** Short. The problem, your city's scenario, what your agent does, what you
  found, what you'd do next. Front-load it — assume you get cut off before your last slide.
- **The demo.** Pick the one or two questions that best show what your agent can do, and
  **rehearse them.** A quick demo that works beats an ambitious one that stalls. Have a
  screenshot ready in case the live version misbehaves.
- **The Placement Recommendation** — your output artifact (see below). Something a planner would
  actually receive, not a console dump. This can carry the detail the deck has no time for.
- **The honest limitations.** Judges explicitly reward this, and one line in the deck is enough.

Time the whole thing out loud at least once before you present. Teams almost always run long.

### Your output artifact: the Placement Recommendation

Whatever else your agent does, it should be able to produce this — a ranked list of locations,
each carrying coordinates specific enough to stand on, the predicted heat risk, **why** (which
factors drove it and by how much), who lives there, and a drafted proposal a planner could take
to a council meeting.

### Step 1 — Create the team repository

**Repo owner only.**

1. At the top of this page, click the green **Use this template** button → **Create a new
   repository**. *(No button? Use **Fork** and tell a coach.)*
2. Name it after your team, choose **Public**, click **Create repository**.
3. **Settings → Collaborators** → add every teammate's GitHub username.
4. Paste the repo URL where everyone can see it.

### Step 2 — Everyone: get into Cloud Shell

**Cloud Shell is where you'll work.** It has `gcloud`, `bq`, Python, Node, git, Docker, and the
Antigravity CLI already installed. Nothing to set up on your laptop, and no admin rights needed.

1. Open [shell.cloud.google.com](https://shell.cloud.google.com), or click the terminal icon
   (**>_**) in the top right of the Google Cloud console.
2. Clone your team's repository:

   ```bash
   git clone https://github.com/YOUR-TEAM/YOUR-REPO.git
   cd YOUR-REPO
   ```

3. Open the built-in editor with `cloudshell edit .`, or click **Open Editor** in the toolbar.
   It's a full VS Code in your browser.

New to Cloud Shell? The [official guide](https://cloud.google.com/shell/docs/using-cloud-shell)
covers the basics. Your `$HOME` persists between sessions; anything outside it does not.

### Step 3 — Get into your Google Cloud project

**Your facilitator will tell you how to access your project. Follow those instructions** — they
vary by venue and they're the fastest path.

**There is one project per team.** You all share it, which is the point — you can all see the
same BigQuery tables. It also means you can overwrite each other. Agree on who creates what.

You have Owner. You don't need to create a project, set up billing, or download a key file.

### Step 4 — Load the data

**Data lane's job.** One person runs it; nobody else waits.

1. In the Google Cloud console, search for **Colab Enterprise** and open it.
2. **You'll be asked to enable some APIs. Say yes.** Then the Colab Enterprise home page shows
   *another* **Enable APIs** button at the top. Click that too. Two prompts is expected — it
   isn't an error and you haven't done anything wrong.
3. **My Notebooks** → **Import** → source **URL**, and paste this:

   ```
   https://raw.githubusercontent.com/haggman/A4I2026-challenge-1-walkability/main/notebooks/01_load_explore.ipynb
   ```

   *(If your team modifies the notebook later, get your own copy's raw URL by opening the file
   on GitHub and clicking **Raw**.)*

4. Click **Import**, open the notebook, set `CITY` at the top, and run the cells top to bottom.

It takes about a minute. **Read the text between the cells** — it explains why each step happens,
and several explanations will save you time later. The notebook ends by validating everything and
telling you plainly whether anything is wrong.

**If the notebook won't run**, there's a headless fallback in Cloud Shell:

```bash
./scripts/load.sh dallas          # --list shows every available city
```

### What you'll have

Three tables in your project, in a dataset called `a4i_climate`:

| Table | What it is |
|---|---|
| `heat_observations` | Street-level temperature readings across your city — tens of thousands of points |
| `station_daily_temps` | Seven years of daily maximums from weather stations near the city |
| `tract_demographics` | Population, age, income, and vehicle access by census tract |

---

## The data, and why we chose it

**NOAA Heat Watch** is the backbone. Volunteers drive instrumented cars along fixed routes
through a city on one hot day, logging temperature roughly once per second. It's the only public
dataset that resolves temperature differences *within* a city rather than between cities.

The others fill gaps: **GHCN-Daily** for how often the city gets hot, **EPA Smart Location** for
built environment, **ACS** for who is exposed. All public domain or CC0. Full detail is in the
notebook.

**One thing we deliberately excluded, and you should know why.** Vulnerability indices like the
NYC Heat Vulnerability Index and CDC's Social Vulnerability Index include race as a direct input
variable. We left those columns out.

Race genuinely correlates with urban heat exposure — that's well established, and formerly
redlined neighbourhoods run measurably hotter today. But the *cause* is the physical environment:
pavement, building density, missing tree cover. Those we can measure directly, and they're in
your data. Race is a cruder measurement of something we already have.

**Removing the column does not make your model unbiased.** Every proxy is still there. Which is
why the answer isn't deletion, it's checking: when you have your ranked recommendations, look at
whose neighbourhoods they landed in — as an audit of your output, never as a model input. If your
recommendations systematically miss the most vulnerable areas, that's a finding, and it's worth
more in a demo than another point of accuracy.

**Strip the variable. Audit the outcome. Say you did both.**

---

## Bringing your own data

**You're not limited to what we provide.** If your team knows a dataset that would make this
better — your city's tree canopy, cooling center locations, transit feed, 311 complaints — bring
it. Thoughtful sourcing is exactly the judgment this challenge rewards, and judges are looking
for it. This is a natural second job for the data lane once the model is training.

**Augment, don't replace.** Get the core working on the provided data *first*. "Let's find better
data" is one of the most reliable ways to lose ninety minutes and have nothing to demo.

**Check the licence before you load it.** This is a publicly branded event and winning projects
get promoted. Anything you bring has to clear the same bar we applied to ourselves:

| | |
|---|---|
| ❌ No **NonCommercial** (NC) | Winners are promoted commercially |
| ❌ No **NoDerivatives** (ND) | Building on the data is the whole point |
| ❌ No **share-alike** (ODbL, CC BY-SA) | It would encumber what *you* build |
| ❌ No **individual-level personal data** | Aggregate public statistics only |
| ❌ No **unstated licence** | No licence means no rights granted |
| ✅ Public domain, CC0, US Government works | Safe |

The trap most likely to catch you: **anything derived from OpenStreetMap is ODbL**, which is
share-alike — and OSM is the first thing most people reach for on a walkability problem. If
you're unsure, ask a coach. Thirty seconds of checking beats finding out later.

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
| **Craft & communication** | 15 | Does the short pitch land, does the quick demo work, can a non-technical person follow? |
| **Bonus — range** | **+10** | Technology breadth and ambition that *serves* the solution |

Bonus sits **on top** of the 100, so ambition can't cannibalise the core. Nail the fundamentals
and add nothing, and you can still win. Wire up five services with no coherent recommendation,
and you can't win on breadth alone.

### What "Rigor & judgment" actually means

This is the one teams under-invest in, because it's least visible in a demo. It's a quarter of
your score and the easiest place to stand out. Four concrete things:

**Data decisions you can defend.** If you brought your own dataset, do you know its licence? Why
that source and not another? Did you check whether columns were the types you assumed?

**Validation.** Did you check your tables before modelling, or assume no error meant no problem?
The notebook ships a validation section — using it, and saying what it told you, counts.

**Bias handling.** Did you keep race out of your model inputs, and did you audit where your
recommendations landed? Be ready to talk about this.

**Knowing what your model can't do.** The heat data is a single day. The campaigns were driven by
volunteers. The stations are sparse. A team that volunteers its limitations shows more skill than
one that oversells — and judges are told to reward it.

One warning worth internalising: **a model with 98% accuracy on this problem is almost certainly
broken**, not brilliant. It usually means the features contain the answer. If your model can't be
wrong, it isn't predicting anything.

---

## Getting help

Ask a coach. That's what they're there for, and whatever you're stuck on has probably already
been solved at another table.

To report a problem with the data or the notebook, run the **diagnostic cell** at the bottom of
the notebook and share what it prints. One block, everything a coach needs, beats a screenshot
every time.
