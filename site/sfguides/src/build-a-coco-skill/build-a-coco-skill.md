author: Gilberto Hernandez, James Cha-Earley, Snowflake CoCo
id: build-a-coco-skill
summary: Learn how to use the built-in Skill Development skill in CoCo to build, install, and run your own custom skill – no coding required.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
language: en

# Build Your First CoCo Skill
<!-- ------------------------ -->
## Overview

CoCo is Snowflake's AI coding assistant. Out of the box it can query your data, write SQL, and explore your account, and more. One of its key capabilities is also being able to teach it new, repeatable workflows through **skills**.

A skill is a small Markdown file that tells CoCo how to complete a specific task. Skills allow you to turn tasks that have a known and repeatable structure into something CoCo does consistently every time. Once you add a skill, it shows up in either CoCo's skill picker (`$skill-name`) or command picker (`/skill-name`) where anyone on your team can invoke it.

You don't have to write a CoCo skill manually because CoCo ships with a built-in skill called **Skill Development** (`skill-development`) that interviews you and writes the skill on your behalf.

In this guide, you'll play the role of a **marketer at Peak Outfitters**, a fictional outdoor-gear company. Your marketing team wants everyone – even non-technical team members – to be able to draft launch emails and slide outlines that follow the company's brand voice and style guidelines. Instead of asking everyone to memorize the style guide, you'll build a reusable **brand-content** skill that does it for them.

### What You'll Learn
- What a CoCo skill is and what it's made of
- How to tell when a task is actually worth turning into a skill
- The two ways to start a skill – from an idea, or by capturing work you just did
- How to use the built-in **Skill Development** skill to create a new skill
- Where skills live and how CoCo discovers them
- How to install, run, and iterate on your own skill

### What You'll Need
- Access to **CoCo** – see the [CoCo Skills documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop/skills) for how to get started
- A working directory (project folder) open in CoCo where you can create files
- No prior coding experience – everything here is in plain English and Markdown

### What You'll Build
- A custom **`brand-content`** skill that drafts on-brand marketing copy
- A supporting **brand guidelines** reference file the skill reads on demand
- A working skill you can invoke from CoCo's `/` picker

<!-- ------------------------ -->
## What Is a Skill?

Before building a skill, it helps to understand what CoCo is actually reading. A skill is a folder containing a **SKILL.md** file. That file has two parts:

**1. Frontmatter** – a small block at the top (between `---` fences) with two fields:

```yaml
---
name: brand-content
description: "Draft on-brand marketing copy... Use whenever the user wants to write marketing content, a launch email, or a slide outline. Triggers: brand content, marketing copy, launch email, announcement, deck outline."
---
```

Here's what the frontmatter does:

- **`name`** – the skill's identifier, in `kebab-case` (lowercase words joined by hyphens).

- **`description`** – the most important field. This is how CoCo decides when to use the skill. A good description says **what** the skill does, **when** to use it, and lists **trigger** words that should activate it.

**2. Body** – plain Markdown that teaches CoCo how to do the task. The [Create your own skill](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop/skills#create-your-own-skill) documentation describes the structure, but the common sections are:

- `## Workflow` – the step-by-step instructions CoCo follows.
- `## Stopping Points` – where CoCo should pause and check in with you.
- `## Output` – what the skill produces when it's done.

That's it! A skill is just a description of a job, formatted as a Markdown text file that is written so CoCo can follow it. You don't have to write this file yourself – the Skill Development skill will do it for you.

Before we build one, it's worth understanding: when is a skill actually worth creating?

<!-- ------------------------ -->
## When Should You Build a Skill?

Before you build anything, it's good practice to check whether a relevant skill already exists. CoCo ships with a large library of built-in skills, and your team may have published more – so search first using the built-in `/find-skill` skill:

```bash
/find-skill is there a skill for drafting on-brand marketing content?
```

CoCo will search the catalog and lists anything that matches, ready to install in one step. In our case nothing fits our use case, so we'll build one.

Note that not every task will deserve a skill. Building one for the wrong thing just adds clutter to your `/` picker. The signal to watch for is repetition with structure: you catch yourself doing the same kind of task more than once – the same rough steps, the same shape – just with different inputs each time. This could be things like drafting a launch email every quarter, standing up a new data pipeline the same way each time, running the same checks before you ship a change. Those are skills waiting to happen. A true one-off, or something open-ended and creative with no repeatable shape, usually isn't worth capturing as a skill.

Here are a couple of important things to keep in mind when building a skill:

- **Clearly define the outcome.** Be clear about what "done" actually looks like, because that's the artifact your skill has to produce every time. 

- **Capture as many steps as possible before you build.** Even a rough list of what you do, in order, is enough, and it means the skill encodes the workflow you actually follow instead of a guess at it.

Once you've spotted a good candidate, there are a couple of ways to turn it into a skill:

- You already have the idea in your head: e.g., "I want a skill that drafts on-brand launch emails." That's the path we'll walk through next.

- Or you just finished work with CoCo and want to keep it: e.g., "Make a skill out of what we just did today." We'll come back to that one later, but it's a useful approach.

<!-- ------------------------ -->
## Invoke the Skill Development Skill

This guide uses the `skill-development` skill to build a single skill – the same create-from-scratch workflow works in the CoCo CLI and CoCo Desktop. In the Snowsight UI, you create a skill with **+ Create Skill** instead. (CoCo Desktop also bundles a `plugin-creator` skill, but that scaffolds a whole **plugin** – a container that packages one or more skills for sharing – which is more than you need for a single skill.) Either way you end up with a **SKILL.md** in your skills folder, and everything after this step works identically. The **Use Your Skill in CoCo Desktop, the CLI, and Snowsight** section below covers the differences.

CoCo includes a built-in skill called **Skill Development** whose entire job is to help you build other skills. Let's start it.

In the CoCo prompt, type `/` to open the skill picker, then choose **skill-development** (or type `$skill-development`). Tell CoCo what you want to build:

```bash
$skill-development I want to create a new skill that drafts on-brand
marketing content for my team.
```

The Skill Development skill recognizes this as a **create** request and begins interviewing you. It will ask for the essentials of your new skill:

- **Name** – a short `kebab-case` name
- **Purpose** – what problem the skill solves
- **Triggers** – words or phrases that should activate it
- **Tools/Scripts** – any scripts or APIs it needs (we don't need any here)

You should see CoCo ask you to confirm these details before it writes anything. This is a deliberate checkpoint – the skill pauses so you can correct course before any files are created.

<!-- ------------------------ -->
## Describe Your Skill

Answer CoCo's questions with the details for our **`brand-content`** skill. You can paste something like this:

```bash
Name: brand-content

Purpose: Draft marketing copy – product announcement emails and slide
outlines – that follows Peak Outfitters' brand voice and style guidelines,
so anyone can produce on-brand content without memorizing the style guide.

Triggers: brand content, marketing copy, launch email, announcement,
deck outline, slide outline, on-brand, style guide

Tools/Scripts: none – the skill should read a brand guidelines file and
write the copy directly.
```

A note on **triggers**: list the everyday phrases your teammates would actually type, not just the obvious ones. A good description casts a wide net – "launch email" and "announcement" should both trigger `brand-content`, even if a user never types the word "brand."

CoCo will confirm your requirements, then propose a **structure** for the skill and pause again for your approval. For our case it will suggest a single **SKILL.md** plus a small **references** file to hold the brand guidelines – content that the skill only needs to load when it's actually drafting. Approve the structure to continue.

<!-- ------------------------ -->
## Review the Generated Skill

Once you approve the structure, CoCo writes the skill. It creates a **SKILL.md** similar to this:

```markdown
---
name: brand-content
description: "Draft on-brand marketing copy – product announcement emails and slide outlines – that follows Peak Outfitters' brand voice and style guidelines. Use whenever the user wants to write marketing content, a launch email, an announcement, or a slide/deck outline. Triggers: brand content, marketing copy, launch email, announcement, deck outline, slide outline, on-brand, style guide."
---

# Brand Content

## Setup
**Load** `references/brand-guidelines.md` before drafting.

## Workflow

### Step 1: Gather the brief
Ask for content type, product/topic, audience, and key points.
**⚠️ STOP**: Confirm the brief before drafting.

### Step 2: Draft against the guidelines
Apply the voice, terminology, structure, and CTA rules from the guidelines file.

### Step 3: Present with a compliance note
Return the draft plus a short "Brand check" list of the rules applied.
**⚠️ STOP**: Final review with the user.

## Stopping Points
- ✋ Step 1: Brief confirmed
- ✋ Step 3: Final review

## Output
An on-brand email or slide outline, plus a brand-compliance checklist.
```

Here's what this skill does:

- The **description** is written to trigger on many everyday phrases, so teammates don't have to know it exists to benefit from it.

- The **Setup** section points to a separate **references/brand-guidelines.md** file. Keeping the guidelines in their own file means CoCo only loads them when it's actually drafting – and Marketing can update the brand rules without touching the workflow.

- The **⚠️ STOP** checkpoints make CoCo pause so that a human confirms the brief and the final copy before anything ships.

Next, create the guidelines file that the skill relies on. Ask CoCo to add **references/brand-guidelines.md** next to the **SKILL.md**, with your team's actual voice, terminology, structure rules, and calls to action. A short version of this file could look like this:

```markdown
# Peak Outfitters – Brand Voice & Style Guidelines

## Voice
- Confident, not boastful. Plainspoken. Outdoors-forward.

## Approved terminology
- Use "gear" (not "equipment"), "adventurers" (not "users").

## Structure rules
- Lead with the customer benefit, then the feature.
- Emails: one clear ask. Slide outlines: max 6 slides.

## Approved brand hook
- "The outdoors doesn't wait – and neither do we."

## Calls to action
- Email: "Shop the collection." Slides: close with a "Get outside" slide.
```

Keep this reference file short. It's loaded into CoCo's context on demand, so trimming it to the rules that matter keeps the skill fast and focused.

<!-- ------------------------ -->
## Install and Run Your Skill

Skills live in a **skills** folder that CoCo watches. When you let CoCo write the skill, it places the files there for you – a **brand-content/** folder containing your **SKILL.md** and the **references/brand-guidelines.md** file. The exact folder depends on which surface you're using (for example, **.cortex/skills/** in the CLI, or **.snowflake/cortex/skills/** in CoCo Desktop and the Snowsight UI) – the **Use Your Skill in CoCo Desktop, the CLI, and Snowsight** section below has the full breakdown.

There's no separate skill registration step. The skill becomes available the next time you open the `/` picker.

Let's use it. Open the `/` picker, choose **brand-content**, and give it a brief:

```bash
/brand-content Draft a launch email to existing customers announcing our
new three-season waterproof shell. Emphasize that it stays dry in multi-day
storms and packs down small.
```

Here's what you should see:

- CoCo first confirms the brief (content type, product, audience, key points) and waits for your OK – that's the Step 1 stopping point doing its job.

- It then drafts an email that opens with the approved brand hook, leads with the customer benefit, uses your approved terminology, and closes with "Shop the collection."

- Finally it shows a short **Brand check** list of the rules it applied, so you can confirm the copy is on-brand before sending.

You've just turned your brand guidelines into a repeatable workflow that anyone on the team can run – without reading the style guide.

<!-- ------------------------ -->
## Use Your Skill in CoCo Desktop, the CLI, and Snowsight

CoCo comes in three places: the **Desktop** app, the **CLI**, and inside **Snowsight** in your browser. The `brand-content` skill you just built works the same in all three – you invoke it by typing `/` – but where skills live and how you create and share them differs a little by surface.

| | CoCo Desktop | CoCo CLI | Snowsight UI |
|---|---|---|---|
| **Where skills live** | Project **.snowflake/cortex/skills/** plus any local folders you register; config in **~/.snowflake/cortex/skills.json** | Project **.cortex/skills/** or global **~/.snowflake/cortex/skills/** (shares **skills.json** with Desktop) | The workspace's **.snowflake/cortex/skills/** (workspace-scoped only) |
| **Create a skill** | The `skill-development` skill for a single skill (or `plugin-creator` to scaffold a full plugin), or register a folder via **Agent Settings → Skills → Add Local Skill** | The bundled `skill-development` skill, or add a **SKILL.md** under **.cortex/skills/** yourself | **+ Create Skill**, or **Upload Skill File(s)** / **Upload Skill Folder(s)** |
| **Invoke a skill** | Type `/` in chat, or let CoCo auto-match it from your prompt | Type `/` or `$skill-name`; run `/skill list` to see what's available | Type `/` in the message box |
| **Share with your team** | Publish to a Snowflake stage or the Skills Catalog, or add from GitHub | `cortex skill publish --to-stage`, a Git repo, or the Snowflake catalog | Share through the Horizon Catalog with the `share-skill` skill; teammates find it with `find-skill` |

A few things worth knowing:

- **Desktop and the CLI share the same config.** Both read **~/.snowflake/cortex/skills.json**, so a skill you add on one shows up on the other automatically.

- **Snowsight skills are workspace-scoped.** A personal skill you create in a Snowsight workspace is only available in that workspace – it won't follow you elsewhere.

- **How you start a skill varies a bit.** The `skill-development` create workflow builds a single skill on both the CLI and Desktop; in Snowsight you use **+ Create Skill**. CoCo Desktop's `plugin-creator` is the step up from there – it packages one or more skills into a shareable plugin. Whatever you use, you end up with a **SKILL.md** in a skills folder, invoked the same way everywhere.

<!-- ------------------------ -->
## Share Skills With Your Team

A skill that lives only on your machine only helps you. If everyone builds their own version, you're back to five slightly different launch emails. The fix is to publish it to the **Skills Catalog**, Snowflake's governed registry for skills. Once it's there, teammates find and install the same version, with access controlled by Snowflake roles.

How you publish depends on your surface:

- **CoCo Desktop** – select the skill in **Agent Settings → Skills** and choose **Publish to Skills Catalog**.
- **Snowsight** – run the `share-skill` skill, which gives you a share link to hand out.
- **CoCo CLI** – run `cortex skill publish` to push the skill to a Snowflake stage or the catalog.

However you publish, teammates then discover it with `find-skill` (or by pasting a share link) and install it in one step – so everyone runs the same `brand-content` skill.

### Package Related Skills as a Plugin

As your toolkit grows – say `brand-content`, a launch-checklist skill, and a competitor-scan skill – you don't have to share them one at a time. A **plugin** is the container that bundles related skills (and optionally hooks or MCP servers) into a single installable unit. On CoCo Desktop, ask the `plugin-creator` skill to package them:

```bash
/plugin-creator package my marketing skills into a plugin
```

Now a teammate installs the whole toolkit in one step instead of hunting for each piece.

<!-- ------------------------ -->
## Scale Your Skill

The skill you built is a single **SKILL.md** plus one reference file – and for most tasks, that's all you'll ever need. As your skills take on bigger jobs, two patterns help them grow without becoming slow or unwieldy. 

**References – offload the detail.** You already used this pattern. Keep the instructions in **SKILL.md** and move bulky or frequently-changing detail into a **references/** file that CoCo loads only when it's needed. Your brand guidelines are a perfect example: the workflow rarely changes, but the guidelines do – and Marketing can update **brand-guidelines.md** without ever touching the workflow. Reach for a reference file when content is long, or when someone other than the skill's author owns it.

**Sub-skills – split by branch.** When a single skill starts covering clearly separate jobs, split it. Imagine your `brand-content` skill grew to handle emails, slide decks, and social posts. Instead of one long file, you'd use a small "router" **SKILL.md** that detects which job the user wants, plus a sub-folder for each branch. CoCo loads only the branch that matches the request, so the other two never take up context.

The guiding principle: CoCo shares a limited context window across your whole conversation, so a lean, focused skill is a faster and more reliable skill. Start simple, and only add structure when the skill actually needs it.

Here's how the same skill could look as it grows:

```bash
# Simple – one file
brand-content/
└── SKILL.md

# With a reference – detail loaded on demand
brand-content/
├── SKILL.md
└── references/
    └── brand-guidelines.md

# With sub-skills – one branch loaded at a time
brand-content/
├── SKILL.md            # router: detects email vs. deck vs. social
├── email/
│   └── SKILL.md
├── slide-deck/
│   └── SKILL.md
└── social-post/
    └── SKILL.md
```

A quick point of guidance: reach for a reference file when the detail is bulky or owned by someone else, and reach for sub-skills when the skill has clearly separate jobs. 

The Skill Development skill can set up either structure for you – just describe what you want. For the structural specifics, see the [Create your own skill](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop/skills#create-your-own-skill) documentation.

<!-- ------------------------ -->
## Capture a Skill From Work You've Already Done

Some of the best skills don't start as ideas at all – they start as work you just finished. Say you spent this morning with CoCo drafting Peak Outfitters' spring launch email: you pasted in the brief, went back and forth on the hook, tightened the call to action, and landed on something you're happy with. Next quarter you'll do the whole thing again from scratch – unless you capture it now, while the workflow is still fresh.

So instead of describing a new skill, point CoCo at the session you just had:

```bash
$skill-development can you make a skill from what we just did today?
```

CoCo reads back through the conversation, works out the repeatable workflow underneath it, and drafts a **SKILL.md** that generalizes the specifics – turning "this quarter's spring email" into "any launch email" – pausing at the same review checkpoints you saw earlier. The difference from building an idea from scratch is that you've already proven the workflow works, so you're not guessing at the steps; you're just saving the ones you already ran. That's what makes this so useful: the next time the task comes around, it's one command.

This is worth keeping in the back of your mind as you work. Any time you finish something with CoCo and think "I'll be doing this again," that's a good cue to capture it as a skill.

<!-- ------------------------ -->
## Iterate on Your Skill

Skills are living documents. As your needs grow, the Skill Development skill can help you improve them, too. Invoke `$skill-development` again and describe what you want:

- **Review it** – ask CoCo to review your skill against best practices and suggest fixes (for example, "audit my brand-content skill").

- **Refactor it** – if a single skill grows too large or starts covering several distinct jobs, ask CoCo to split it into smaller, focused pieces.

- **Add capabilities** – extend the workflow (for example, add a "social post" content type) by describing the change and letting CoCo update the **SKILL.md**.

<!-- ------------------------ -->
## Build a skill for Anything

This guide walked through one skill end to end – the mechanics of what a skill is made of, the best practices for when and how to build one, and how to use and design skills across CoCo Desktop, the CLI, and Snowsight. We kept the example deliberately simple and aimed it at non-technical teammates, but that's just one shape a skill can take. You can build a skill for almost anything you do repeatedly, and the same mechanics apply.

Here are a few ideas by role:

- **Data analysts** – a skill that turns a set of tables into a validated Cortex Analyst semantic view following your naming conventions; one that answers ad-hoc questions using only your team's approved metric definitions; or a "profile this table" skill that returns row counts, null rates, and distributions in a standard format.

- **Data engineers** – a skill that stands up a new pipeline (dynamic tables or dbt) in your project's layering and naming standard; a pre-release data-quality check that runs your usual freshness, row-count, and null tests; or an impact-analysis skill that traces downstream lineage before you rename or drop a column.

- **ML engineers** – a skill that builds features and registers a model following your MLOps conventions; a standardized batch-inference scorer that writes results consistently; or a document-intelligence skill that turns a stage of PDFs into a structured table.

- **App builders** – a skill that scaffolds a Streamlit in Snowflake app with your team's layout, auth, and theming; a Native App starter that follows your packaging conventions; or a "deploy to SPCS" skill that applies your standard configuration.

### Start From What's Already Built In

You don't always have to start from scratch. CoCo ships with a large library of built-in skills spanning warehouses, dynamic tables, dbt, Iceberg, semantic views, dashboards, Cortex Agents, machine learning, document intelligence, data quality, lineage, governance, sharing, and cost management. Before you build, check whether one already covers what you need – and reading existing skills is one of the best ways to learn to write your own.

To browse what's available:

- **CLI** – run `/skill list`, or use the `find-skill` skill to search by description.
- **Desktop** – open **Agent Settings → Skills** and look at the **Packaged Skills** section; **Browse Skills Catalog** shows skills shared across your org.
- **Snowsight** – type `/` in the message box to see the built-in skills available on any page.

For the full catalog, see the [CoCo CLI bundled skills](https://docs.snowflake.com/en/user-guide/cortex-code/bundled-skills) reference.

<!-- ------------------------ -->
## Clean Up

If you only built this skill to follow along, you can remove it. Delete the skill folder CoCo created – the **brand-content/** directory and everything inside it. Once it's gone, it will no longer appear in the `/` picker.

<!-- ------------------------ -->
## Conclusion And Resources

You built a working CoCo skill without writing a single line of code. By using the built-in **Skill Development** skill, you described what you wanted in plain English, reviewed what CoCo generated at each checkpoint, and ended up with a reusable `brand-content` skill your whole team can run from the `/` picker.

This same pattern works for almost any repeatable task – onboarding checklists, code-review conventions, data-request intake, release notes. If your team does it more than once, you can turn it into a skill.

### What You Learned
- A skill is a **SKILL.md** file with frontmatter (`name` + `description`) and a workflow body
- The `description` field, with good trigger words, is what makes CoCo actually use your skill
- The **Skill Development** skill interviews you and writes the skill for you, pausing at checkpoints
- Reference files (like brand guidelines) keep skills focused and let non-technical owners maintain them
- Skills are discovered automatically from the **skills** folder – no registration, just the `/` picker

### Related Resources
- [CoCo Skills documentation (Desktop)](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop/skills)
- [Create your own skill](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop/skills#create-your-own-skill)
- [CoCo CLI skills (extensibility)](https://docs.snowflake.com/en/user-guide/cortex-code/extensibility)
- [CoCo CLI bundled skills](https://docs.snowflake.com/en/user-guide/cortex-code/bundled-skills)
- [Skills and plugins in Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight/skills-and-plugins)
- [Building AI Agents with Cortex Code and Cowork](https://www.snowflake.com/en/developers/guides/building-ai-agents-with-cortex-code-and-cowork/)
