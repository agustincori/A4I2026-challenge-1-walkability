# Challenge 1 — Climate-Resilient Walkability

**Agents for Impact 2026** · Build an agent that tells a city planner exactly where to put a
cooling center.

---

## The challenge

Two blocks in the same city, at the same hour on the same day, can differ by more than twenty
degrees. One has tree cover and low buildings. The other is parking lot and asphalt. The people
walking those two blocks are having completely different days, and one of them is in danger.

City planners know this in the abstract. What they usually don't have is a number for *this
intersection*, and a reason they can put in front of a city council.

**Build an agent that gives them one.**

Your agent should take a question a planner would actually ask — *"we have budget for three
cooling centers in this ward, where do they go?"* — and answer it with specific locations,
predicted risk, who lives nearby, and the reasoning behind the choice.

Not "somewhere downtown." A place, with an argument.

### Your output artifact: a Placement Recommendation

A ranked list of locations with coordinates, each carrying:

- the predicted heat risk at that spot
- **why** — which features drove the prediction, and by how much
- who lives there: population, age, income, vehicle access
- a drafted proposal a planner could take to a council meeting

### Your required differentiating technology: BigQuery ML

Every challenge has one required technology. Yours is **BigQuery ML**.

You must train a model that predicts a microclimate anomaly for a location, and **your agent
must call that prediction** — not just query historical rows. A custom Python tool that runs
`ML.PREDICT`, or better `ML.EXPLAIN_PREDICT`, is the shape most teams land on.

`ML.EXPLAIN_PREDICT` matters more than it looks. It returns per-feature attributions alongside
each prediction — not just "+6.2°F" but *"+4.1 from street density, +2.8 from building age,
−0.7 from park proximity."* **That sentence is your Placement Recommendation.** Teams that treat
explanation as a reporting step at the end finish with a number and no argument.

### Also required of every team

BigQuery · ADK · Gemini · a Google-managed MCP server (consume one, don't author one) · deployed
to Google Cloud

---

## Getting started

You have **4.5 hours**. The single biggest risk to your team is losing the first ninety minutes
to setup. We have removed as much of that as we can — the data is sourced, the licensing is
checked, and the load process is written and tested.

### Step 1 — Get this repository

**If you've used GitHub before:** click **Use this template** at the top of this page to create
your own copy. Don't fork it; a template copy is independent and cleaner for a team.

**If you've never used GitHub:**

1. You need a free account at [github.com](https://github.com). If you don't have one, make one
   now — it takes two minutes.
2. At the top of this page, click the green **Use this template** button, then **Create a new
   repository**.
3. Give it a name (your team name is fine), choose **Public**, and click **Create repository**.
4. You now have your own copy. Everything below happens in *your* copy, not this one.

Only one person on the team needs to do this. Everyone else works from that copy.

### Step 2 — Open the notebook in Colab Enterprise

Your Google Cloud project is already created for you. You have Owner on it. You do not need to
create a project, set up billing, or download a key file.

**If you've used Colab Enterprise before:** import
`notebooks/01_load_explore.ipynb` by URL and run it. Skip to Step 3.

**If you haven't:**

1. In the Google Cloud console, search for **Colab Enterprise** and open it.
2. **You will be asked to enable some APIs. Say yes.** Then the Colab Enterprise home page will
   show *another* **Enable APIs** button at the top. Click that too. Two separate prompts is
   expected — it is not an error and you have not done anything wrong.
3. Go to **My Notebooks** → **Import**.
4. Set the source to **URL**.
5. Paste the raw URL of the notebook from your repository. To get it: open
   `notebooks/01_load_explore.ipynb` in GitHub, click the **Raw** button, and copy the address
   from your browser's address bar.
6. Click **Import**, then open the notebook and run the cells top to bottom.

It takes about a minute to run. **Read the text between the cells** — it explains why each step
happens, and several of those explanations will save you time later.

### Step 3 — What you'll have

Four tables in your own BigQuery project, in a dataset called `a4i_climate`:

| Table | What it is |
|---|---|
| `heat_observations` | Street-level temperature readings across your city — tens of thousands of points |
| `station_daily_temps` | Seven years of daily maximums from weather stations near the city |
| `tract_demographics` | Population, age, income, and vehicle access by census tract |

The notebook ends by validating all of them and telling you whether anything is wrong.

### If the notebook won't run

There's a headless fallback that reaches the same end state:

```bash
./scripts/load.sh chicago
```

Run it in Cloud Shell. It rebuilds every table from a pre-staged snapshot. See
`scripts/README.md` for options and the list of available cities.

---

## The data, and why we chose it

**NOAA Heat Watch** is the backbone. Volunteers drive instrumented cars along fixed routes
through a city on one hot day, logging temperature roughly once per second. It is the only
public dataset that resolves temperature differences *within* a city rather than between cities.

The other three sources fill gaps: **GHCN-Daily** for how often the city gets hot,
**EPA Smart Location** for built environment, **ACS** for who is exposed.

Every one is public domain or CC0. Full licensing detail is in the notebook.

**One dataset we deliberately excluded, and you should know why.** Vulnerability indices like
the NYC Heat Vulnerability Index and CDC's Social Vulnerability Index include race as a direct
input variable. We left those columns out.

Race genuinely correlates with urban heat exposure — that's well established, and redlined
neighborhoods run measurably hotter today. But the *cause* is the physical environment:
pavement, building density, missing tree cover. Those we can measure directly, and they're in
your data. Race is a cruder measurement of something we already have.

**Removing the column does not make your model unbiased.** Every proxy is still there. That's
why the answer is to check your output: when you have your ranked recommendations, look at
whose neighbourhoods they landed in. As an audit, never as a model input. If your
recommendations systematically miss the most vulnerable areas, that is a finding — and it's
worth more in a demo than another point of accuracy.

**Strip the variable. Audit the outcome. Say you did both.**

---

## Bringing your own data

**You are not limited to what we provide.** If your team knows a dataset that would make this
better — your city's tree canopy, cooling center locations, transit ridership, 311 complaints —
bring it. Teams that source thoughtfully are demonstrating exactly the judgment this challenge
is meant to reward, and judges are looking for it.

Two pieces of advice before you do.

**Augment, don't replace.** Get the core path working on the provided data first, *then* add.
"Let's find better data" is one of the most reliable ways to lose ninety minutes and have
nothing to demo. The foundation is standing; build on it.

**Check the license before you load it.** This is a publicly branded event and winning projects
get promoted. Anything you bring has to clear the same bar we applied to ourselves:

| Rule | Why |
|---|---|
| ❌ No **NonCommercial** (NC) licenses | Winners are promoted commercially |
| ❌ No **NoDerivatives** (ND) licenses | Building on the data is the whole point |
| ❌ No **share-alike** (ODbL, CC BY-SA) | It would encumber what *you* build |
| ❌ No **individual-level personal data** | Aggregate public statistics only |
| ❌ No **unstated license** | No license means no rights granted |
| ✅ Public domain, CC0, US Government works | Safe |

The trap most likely to catch you: **anything derived from OpenStreetMap is ODbL**, which is
share-alike. OSM is the first thing most people reach for on a walkability problem. Be careful.

If you're unsure about a source, ask a coach. Thirty seconds of checking beats finding out
afterward.

---

## What's in this repository

```
notebooks/01_load_explore.ipynb   The main artifact. Run this first.
scripts/load.sh                   Headless fallback if Colab is unavailable.
data/                             Seed data, if any.
agent/                            Empty. Your agent goes here.
```

`agent/` is empty on purpose. We built the on-ramp — data, loading, validation, sample queries.
We did not build the vehicle. The design decisions in your agent are what you'll be judged on.

---

## How you'll be judged

Judging rewards **progress and judgment**, not just a finished product. A team that gets three
quarters of the way with clear thinking and honest limitations will beat a team that demos
something polished and hollow.

Four dimensions, plus bonus points for range:

| Dimension | Weight |
|---|---|
| Impact & insight — does this actually help a planner? | 30 |
| Technical execution — does it work, and is the required stack really used? | 30 |
| Judgment — data sourcing, licensing, handling of bias, honest limitations | 25 |
| Craft & communication — the demo, the story, the artifact | 15 |
| **Bonus** — technology range, ambition, stretch goals | up to +10 |

The full rubric, including what judges are told to look for in this specific challenge, is in
the judging guide.

---

## Getting help

Ask a coach. Seriously — that's what they're there for, and the thing you're stuck on has
probably already been solved at another table.

If you need to report a problem with the data or the notebook, run the **diagnostic cell** at
the bottom of the notebook and share what it prints. It's one block containing everything a
coach needs, and it beats a screenshot every time.
