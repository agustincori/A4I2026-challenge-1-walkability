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

| City | Street-level readings | |
|---|---:|---|
| **Houston** | ~147,000 | the largest campaign by far, and the slowest to load |
| **Chicago** | ~49,000 | |
| **Seattle** | ~35,000 | |
| **Atlanta** | ~23,000 | |
| **Dallas** | ~19,000 | the notebook default |
| **Los Angeles (Central)** | ~17,000 | |
| **New York (Brooklyn)** | ~15,000 | |
| **New York (Manhattan/Bronx)** | ~12,000 | |

More readings means more for your model to learn from and a slightly longer load. Fewer is not
disqualifying — Manhattan's 12,000 points still cover the borough densely, because the routes
are short. But if your team wants volume to play with, start at the top of that list.

**We'd recommend staying on this list.** There are 87 cities available and Section 4 of the
notebook lists them all, but these are the ones we've tested end to end.

Then get specific, because specificity is what makes a demo land:

> *"We're the City of Dallas. It's July, we've had eleven days over 100°F, and we have
> funding for four new cooling centers plus one mobile hydration unit. We don't know where to
> put them, and the council meets in three weeks."*

That's your scenario. Write it down. Everything you build should answer to it.

---

## Four words we use precisely

These turn up as column names later, so it's worth thirty seconds now:

| Term | What it means here |
|---|---|
| **Campaign** | One city's Heat Watch day — volunteers driving fixed routes, three one-hour windows. Your `heat_observations` table is one campaign. |
| **Traverse** | A single drive along one of those routes. Thousands of readings, one per second or so. |
| **Offset** | How much hotter a spot is **than its own city's average** on that campaign day. Not a temperature — a difference. This is what your model predicts. |
| **Track** | Which of the three decisions below your team chose to solve. Nothing to do with traverses, unhelpfully. |

---

## Then: pick a track

Heat is one problem with several different decisions attached to it, and they belong to
different people on different clocks. **Pick the one your team wants to solve.** The data and the
model are the same for all three — what changes is who's asking, what they can actually do about
it, and what a good answer looks like.

| Track | The decision | Who's asking |
|---|---|---|
| ⚡ **Today** | It's 102° tomorrow. Where do the hydration trucks, wellness checks, and extended library hours go? | Emergency management |
| 🏛️ **This budget cycle** | We can fund three permanent cooling centers. Where? | City planning, answerable to a council |
| 🌳 **This decade** | Where does tree planting or cool pavement buy the most relief per dollar? | Sustainability, urban forestry |

### What a strong version of each looks like

**⚡ Today** — the hard part isn't finding the hot blocks, it's reaching people who *can't leave*.
A strong version leans on `no_vehicle_rate` and median age, and outputs something a dispatcher
could act on in twenty minutes: a ranked list with addresses and a reason per stop. Fully
supported by the data you'll load.

**🏛️ This budget cycle** — permanence needs justification, and that's where the seven years of
station history earn their place. A location that's +8°F matters far more in a city crossing 95°F
thirty times a summer than twice. A strong version pairs the prediction with that frequency and
produces something that survives a council meeting, including what it costs and what it displaces.
Fully supported.

**🌳 This decade** — this is the one where `ML.EXPLAIN_PREDICT` does its best work, and most teams
will miss it. The attributions don't just tell you *where* it's hot, they tell you **why** — and
the feature driving the offset is the thing to change. If impervious surface dominates, that's a
pavement problem. If it's building density and land-use mix, that's a canopy and open-space
problem. **Your model can recommend the intervention, not just the location.**

One honest limit on that last track: you can identify candidates and diagnose the cause, but you
**cannot simulate the fix** — nothing in the data tells you what the offset becomes after you
plant. Say that out loud rather than implying otherwise. Judges reward it.

**Can you do more than one?** Yes, and a real planning assistant would. But three shallow tracks
lose to one that's genuinely good, and you have four and a half hours.

---

## What you're building

**A planning assistant for a city's heat response.** Not a dashboard, and not a single query
with a chat box on it — an agent a planner can hold a working conversation with, that reaches
for real data and a real model to answer.

**One afternoon, one planner.** It's 3:40 on a Tuesday in July, the forecast for Thursday is
102°F, and Dana in the city manager's office has a meeting at nine tomorrow. Everything below is
a question she asks between now and then:

| What they ask | What answers it |
|---|---|
| *"We can fund three cooling centers this summer. Where should they go?"* | Your BQML model, ranked against demographics |
| *"Why is 4th and Marsalis so much worse than two blocks north?"* | `ML.EXPLAIN_PREDICT` attributions |
| *"How often does that area actually hit dangerous heat? Is it getting worse?"* | Seven years of station history |
| *"Who lives around that site — how many people, how old, how many without a car?"* | Census tract demographics |
| *"I'm down to two sites and have to pick one. Make the case for each."* | Both, plus Gemini weighing the tradeoff |
| *"Draft the proposal I'm taking to council in the morning."* | Gemini, synthesising everything above |
| *"Before I send it — did we actually reach the neighbourhoods that need this most?"* | An equity audit of your own output |

Notice these need **different things**. Some need a prediction. Some need only a query against
history. Some need the agent to weigh a tradeoff and say why. One needs it to write prose a
human will sign their name to.

**That range is the challenge.** An agent that can only answer the first question is a model
with a chat box. An agent that handles all seven is something a planner would keep open.

Your track shifts the specific questions — an emergency manager asks about tomorrow, a forestry
office asks about a decade. It doesn't change the shape. Some need a prediction, some need only a
query, some need the agent to weigh a tradeoff, and one needs it to write prose.

## What will set yours apart

Every team building Challenge 1 gets the same data, the same model type, and the same starting
notebook. **The core is not where you win.** Whichever track you picked, these are the levers:

- **Go deeper on one question** rather than shallow on seven. An agent that handles its track's
  central question superbly beats one that half-answers everything.
- **Bring a dataset nobody else has.** Your city's tree canopy, its existing cooling centers, 311
  heat complaints. See [Bringing your own data](#bringing-your-own-data) for what would unlock
  what, and check the licence first.
- **Make the equity audit the centrepiece** instead of a footnote — checking whether your
  recommendations actually reached the neighbourhoods that need them most. It's the most
  interesting conversation available in this challenge and most teams will skip it.
  ([What that means, concretely](#what-auditing-the-outcome-actually-means).) It lands hardest on
  the decade track, where the question becomes whether your plan reverses a century of
  disinvestment or repeats it.
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
| **At least one custom Python tool** | Yours, not configuration. See below for why. |
| **Deployed to Google Cloud** | Agent Runtime or Cloud Run, your choice. It has to actually run somewhere. |

### One more thing already installed for you

**Antigravity CLI (`agy`)** is pre-installed in Cloud Shell — a terminal coding agent that reads
your codebase, proposes edits, and runs commands. Google would like you to try it. It is not
required and nothing here depends on it, but it's free and it's already there. Details and
examples are in [Step 3](#step-3--everyone-get-into-cloud-shell).

### Choosing your MCP server

You have two good options, and you should consume one rather than writing your own:

- **BigQuery's built-in MCP server** — the quickest path if all you need is to query your tables.
- **[MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox)** — Google's open
  source MCP server for databases. It ships prebuilt tools for immediate access *and* a
  framework for defining your own, with controls like restricted access and structured queries.

**The Toolbox is generally the more flexible of the two**, and if you want your agent's database
access shaped to your own tools rather than generic queries, start there.

### Why we also require a custom Python tool

Fair question, since MCP Toolbox lets you define a tool as parameterised SQL — you could run the
prediction through MCP and write no Python at all.

**That's true of the query. It isn't true of the work around it.** Turning "somewhere on the
south side" into a bounding box is judgment. `ML.EXPLAIN_PREDICT` hands you attributions as a
nested structure, and turning that into *"impervious surface contributed +4.2°"* is code.
Assembling a Placement Recommendation from four sources, deciding what to do when the model has
no answer for a location — none of that is a single SQL call.

So: **let the search itself be a Toolbox tool if you like.** The custom tool exists for the
reasoning around it, which is the part a rulebook can't express and the part you'll be judged on.

> **Hint worth taking:** run the Toolbox as a container on **Cloud Run with minimum instances
> set to 1**. Cloud Run scales to zero by default, which means the first request after an idle
> period pays a cold start — and the first request after an idle period is usually the one you
> make on stage. Pinning one warm instance costs very little for a day and removes an entire
> class of demo failure.

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

**Agree your city, your track, and your scenario** (see above). Ten minutes, and it is the most
valuable ten minutes of the day — everything downstream answers to it. Write it on something
everyone can see.

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
  ([Explained below](#what-auditing-the-outcome-actually-means).)
- **Decide with the team whether to bring extra data**, and if so, source it and check the licence.

#### Agent lane — 2 to 3 people

- **Prompt engineering.** Expect this to be the hardest part, and budget for it. Your system
  instruction has to teach the agent who it's talking to, when to reach for which tool, what to
  do with a vague question, and — importantly — **when to refuse.** An agent that confidently
  answers something it has no data for is worse than one that says "I can't tell you that."
- **Custom Python tools.** At least one is required. The obvious one wraps your BQML prediction,
  so the agent can ask about a location nobody measured.
- **Decide what goes through MCP and what needs a custom tool.** Generic "query my tables" access
  is a good fit for the managed MCP server. Anything with shape to it — a ranked siting query, an
  explanation call — usually wants a purpose-built tool. **This is your main coordination point
  with the data lane**: they own the SQL, you own the wrapper. Ask them for it early.
- **Deploy early, not at the end.** Agent Runtime or Cloud Run. The front end lane is blocked on
  a live endpoint, and deployment always takes longer than you think.
- **Test with the real questions.** Take the seven planner questions above and actually ask them.
  You'll find the gaps faster than by reasoning about them.
- **Decide what failure looks like.** What does your agent say when the model has no prediction
  for a location, or the planner asks about a city you didn't load? Judges notice this.

#### Front end lane — 2 people

You have three routes. **Pick deliberately and be ready to say why** — the choice tells judges
something about who you think the user is.

| Option | Strength | Trade-off |
|---|---|---|
| **`adk web`** | Free. Built in. Works the moment your agent does. **Everyone starts here.** | It is visibly a developer tool. Fine as a demo, weak as a product story. |
| **Gemini Enterprise** | A polished interface with almost no front-end code. Free trial available, and an agent already deployed to Agent Runtime can be surfaced through it. | Serves **internal** users, not the public. |
| **Custom web UI** | Full control. A map a council member could actually read beats a chat log. | The most work by far. Scope it small. |

**Every team starts on `adk web`** — that's not a choice, it's just what's in front of you. The
real question is whether you *finish* there. Staying is a legitimate decision if you spent the
time elsewhere and can say so. "It was already there" is the weakest available defence of it.

The Gemini Enterprise trade-off is worth thinking about rather than working around. It's built
for people *inside* an organisation — which, for a tool whose users are city planners and
emergency management staff, is arguably exactly right. **Say that on purpose.** "We chose an
internal-facing interface because our user is a city employee, not a resident" is a good answer.
Discovering the limitation on stage is not.

- **Do not wait for a working agent.** Mock the response, build against it, swap later. That is
  precisely why deployment sits in the middle of the day rather than at the end.
- **Whatever you build, the demo runs on it.** Test it on the machine you'll actually present
  from, before you need it.

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

### Step 2 — Get into your Google Cloud project

**Your facilitator will tell you how to access your project. Follow those instructions** — they
vary by venue and they're the fastest path.

**There is one project per team.** You all share it, which is the point — you can all see the
same BigQuery tables. It also means you can overwrite each other. Agree on who creates what.

You have Owner. You don't need to create a project, set up billing, or download a key file.

### Step 3 — Everyone: get into Cloud Shell

**Cloud Shell is where you'll work.** It has `gcloud`, `bq`, Python, Node, git, Docker, and the
Antigravity CLI already installed. Nothing to set up on your laptop, and no admin rights needed.

1. In the Google Cloud console — the one your facilitator just got you into — click the
   **terminal icon (`>_`) in the top right**. Use that icon rather than a bookmark or a typed
   address: it opens Cloud Shell attached to *this* project, in *this* browser session. Typing a
   URL can land you in a different window signed in as a different account, which is a confusing
   twenty minutes nobody needs.

2. Clone your team's repository:

   ```bash
   git clone https://github.com/YOUR-TEAM/YOUR-REPO.git
   ```

3. Open the whole repo in the editor:

   ```bash
   cloudshell workspace .
   ```

   That opens your cloned folder as a workspace in the Cloud Shell Editor — the same thing as
   **File → Open Folder** in VS Code, which is essentially what the editor is. You get a file
   tree, a real editor, and a terminal in the same browser tab.

#### One repo, one branch per lane

Eight to ten people committing to `main` will collide, and merge conflicts at minute 200 are a
genuinely bad way to lose a demo. Nobody needs their own fork — just take a branch:

```bash
git checkout -b data        # or agent, frontend, story
```

Work on your lane's branch. Merge into `main` when you have something the other lanes need —
the data lane's `ML.EXPLAIN_PREDICT` query is the obvious example, and the agent lane is blocked
until they get it. Merging early and often beats one heroic merge at the end.

New to any of this? Both guides open in a new tab:
<a href="https://cloud.google.com/shell/docs/using-cloud-shell" target="_blank" rel="noopener noreferrer">Using Cloud Shell</a>
·
<a href="https://cloud.google.com/shell/docs/editor-overview" target="_blank" rel="noopener noreferrer">Cloud Shell Editor overview</a>

One thing worth knowing: your `$HOME` directory persists between sessions. Anything outside it
does not — so keep your work in the cloned repo.

#### Optional but encouraged: the Antigravity CLI

**`agy` is already installed in Cloud Shell.** You run zero setup commands — just type it.

Google would like you to try it. It is **not a requirement**, and nothing in this challenge
depends on it, so don't lose time fighting it if it isn't helping. But it's a genuinely capable
terminal coding agent: it reads your codebase, proposes edits with your permission, and runs
commands for you.

```bash
agy
```

Then talk to it in plain language. Places it tends to earn its keep in a hackathon:

- **Agent lane** — scaffolding ADK boilerplate, wiring a custom tool around a query, drafting a
  Cloud Run deploy. The tedious parts you already know how to do.
- **Data lane** — drafting BigQuery SQL against tables you just loaded, or restructuring a query
  you've already written.
- **Anyone, stuck** — paste an error and ask what's wrong. Faster than a search, and it can see
  your actual code.

A couple of built-ins worth knowing: `/diff` shows you pending changes before you accept them,
and `/permissions` controls what it's allowed to do on its own. Review before you accept — it's
fast, which is exactly why it's worth reading what it did.

<a href="https://antigravity.google/docs/cli/install" target="_blank" rel="noopener noreferrer">Docs</a>
·
<a href="https://github.com/google-antigravity/antigravity-cli" target="_blank" rel="noopener noreferrer">GitHub</a>
·
<a href="https://codelabs.developers.google.com/antigravity-cli-hands-on" target="_blank" rel="noopener noreferrer">Hands-on codelab</a>

### Step 4 — Load the data

**Data lane's job.** One person runs it; nobody else waits.

1. In the Google Cloud console, search for **Colab Enterprise** and open it.
2. **You'll be asked to enable some APIs. Say yes.** Then the Colab Enterprise home page shows
   *another* **Enable APIs** button at the top. Click that too. Two prompts is expected — it
   isn't an error and you haven't done anything wrong.
3. **My Notebooks** → **Import** → source **URL**, and paste this:

   ```
   https://raw.githubusercontent.com/haggman/A4I2026-challenge-1-walkability/main/notebooks/c1_01_load_explore.ipynb
   ```

   *(If your team modifies the notebook later, get your own copy's raw URL by opening the file
   on GitHub and clicking **Raw**.)*

4. Click **Import**, open the notebook, set `CITY` at the top, and run the cells top to bottom.

It takes about a minute. **Read the text between the cells** — it explains why each step happens,
and several explanations will save you time later. The notebook ends by validating everything and
telling you plainly whether anything is wrong.

**If the notebook won't run**, there's a headless fallback. From the root of your cloned repo
in Cloud Shell:

```bash
bash scripts/load.sh dallas
```

```bash
bash scripts/load.sh --list       # every city we've published
```

Invoke it with `bash` rather than `./scripts/load.sh` — that way it doesn't matter whether the
file arrived with its executable bit set, which depends on how your repo was created.

It's safe to run more than once. Every table is fully replaced rather than appended to, so if
you cancel it halfway through, or you're not sure whether it finished, just run it again.

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

### What "auditing the outcome" actually means

We keep saying this, so here is exactly what it is. It's three steps and about twenty minutes.

1. **Produce your recommendations.** Say your agent's top ten sites.
2. **Look up who lives there.** Find the census tract each site falls in, and pull its
   demographics from `tract_demographics` — median income, poverty rate, share of households
   without a car, median age.
3. **Compare that to the city as a whole.** Are your recommended tracts poorer than the city
   average, or richer? Older or younger? More or less likely to be without a vehicle?

Then say the answer out loud: **did our recommendations land in the neighbourhoods that need
them most, or in the ones that happened to be easiest to model?**

Both answers are worth having. If your sites skew toward high-poverty, low-vehicle-access,
older-resident tracts, you have evidence your model is finding real vulnerability — say so, with
the numbers. If they skew the other way, you've found something more interesting: your features
may be capturing where it's *hot* without capturing where heat *hurts*. That's a genuine finding
about your own work, and presenting it honestly will land better with judges than a slide
claiming everything worked.

This is also where race belongs, and only here. You can compare the racial composition of your
recommended tracts against the city — as a **check on your output**, after the fact. That's a
completely different act from feeding race into the model, and it's the one that actually tells
you something.

---

## Bringing your own data

**You're not limited to what we provide.** Thoughtful sourcing is exactly the judgment this
challenge rewards, and judges are looking for it. This is a natural second job for the data lane
once the model is training.

### What would unlock what

Our data uses **coordinates, not street names**, and **straight-line distance, not walking
routes**. That's not a flaw to work around so much as a list of things a team can go and fix —
and closing one of these is precisely the kind of move that separates a demo.

| What you can't currently ask | What would unlock it | Matters most to |
|---|---|---|
| *"What's at 63rd and Halsted?"* — talking in street names | Google Maps geocoding | every track |
| *"Who's within a **10-minute walk**?"* — real walking distance | Google Maps routing / isochrones | Today, This budget cycle |
| *"Can people get there on transit?"* | Your city's GTFS feed | Today |
| *"Show me Ward 5"* — political boundaries | Your city's open data portal | This budget cycle |
| *"How much canopy is there now?"* | Your city's tree inventory — NYC's is already in BigQuery at `bigquery-public-data.new_york_trees.tree_census_2015` | This decade |
| *"Which blocks are mostly pavement?"* | An impervious-surface layer, if your city publishes one | This decade |

One distinction worth getting right: we give you `no_vehicle_rate` per census tract, which tells
you *who lacks a car*. That's the right input for "if the nearest center is two miles away, who
can't reach it?" It is **not** a walk-time isochrone. Know which one you used, and say so.

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
notebooks/c1_01_load_explore.ipynb   The main artifact. Run this first.
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
| **Craft & communication** | 15 | Does the short pitch land, does the quick demo work, and can you justify your interface choice? |
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

**Bias handling.** Did you keep race out of your model inputs, and did you run the
[equity audit](#what-auditing-the-outcome-actually-means) on your output? Be ready to talk about
this, and bring the numbers rather than the intention.

**Knowing what your model can't do.** The heat data is a single day. The campaigns were driven by
volunteers. The stations are sparse. A team that volunteers its limitations shows more skill than
one that oversells — and judges are told to reward it.

One warning worth internalising: **a model with 98% accuracy on this problem is almost certainly
broken**, not brilliant. It usually means the features contain the answer. If your model can't be
wrong, it isn't predicting anything.

And a general note, because this challenge asks you to choose more than it asks you to follow
instructions — which city, which track, which interface, what to cut when you're behind. **None
of those have a single right answer and judges are not checking them against a key.** They're
asking whether you chose on purpose and can say why. "We picked Gemini Enterprise because our
user is a city employee" is a strong answer; "we used `adk web` because it was there" is a weaker
one for the same work.

---


## Getting help

Ask a coach. That's what they're there for, and whatever you're stuck on has probably already
been solved at another table.

To report a problem with the data or the notebook, run the **diagnostic cell** at the bottom of
the notebook and share what it prints. One block, everything a coach needs, beats a screenshot
every time.
