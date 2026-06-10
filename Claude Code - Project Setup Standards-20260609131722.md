# Claude Code - Project Setup Standards

> Standard file structure, conventions, and practices for all Keytag product repos using Claude Code.
* * *

## Table of Contents

*   [Required Files Per Repo](http://#required-files-per-repo)
*   [Project Documents](http://#project-documents)
*   [1\. CLAUDE.md](http://#1-claudemd--under-200-lines-ruthlessly-pruned)
*   [2\.](http://#2-clauderules--path-scoped-instructions) [`.claude/rules/`](http://#2-clauderules--path-scoped-instructions)
*   [3\.](http://#3-claudeskills--on-demand-knowledge) [`.claude/skills/`](http://#3-claudeskills--on-demand-knowledge)
    *   [Rules vs Skills](http://#rules-vs-skills--when-to-use-which)
    *   [Splitting Large Skills](http://#when-a-skill-gets-too-large)
*   [4\.](http://#4-claudeagents--custom-subagents) [`.claude/agents/`](http://#4-claudeagents--custom-subagents)
*   [5\.](http://#5-claudesettingsjson--hooks-fast-only) [`.claude/settings.json`](http://#5-claudesettingsjson--hooks-fast-only) [— Hooks](http://#5-claudesettingsjson--hooks-fast-only)
*   [6\. Hooks vs Skills vs CI/CD](http://#6-hooks-vs-skills-vs-cicd--what-goes-where)
    *   [Decision Flowchart](http://#decision-flowchart)
    *   [PostToolUse Hooks](http://#posttooluse-hooks--every-edit-2-seconds)
    *   [Skills](http://#skills--on-demand-30-180-seconds)
    *   [CI/CD Pipeline](http://#cicd-pipeline--per-pushpr-minutes)
    *   [Quick Reference](http://#quick-reference)
*   [7\. Auto Memory](http://#7-auto-memory--let-it-work)
*   [8\. Session Discipline](http://#8-session-discipline)
*   [9\. Consistent File Naming](http://#9-consistent-file-naming)
*   [10\. What NOT to Do](http://#10-what-not-to-do)
*   [Sources](http://#sources)
* * *

## Required Files Per Repo

Every Keytag repo must have these files. The table shows what each file does, how Claude Code loads it, and the size constraint.

| File / Directory | Purpose | How Claude Loads It | Size Limit | Required |
| ---| ---| ---| ---| --- |
| `CLAUDE.md` | Core instructions: commands, architecture, conventions, gotchas | Auto-loaded every session | <200 lines | Yes |
| `DESIGN.md` | High-level design document (human-readable architecture) | Via skill (on-demand) | No limit | Yes |
| `REQUIREMENTS.md` | Scope tracking: implemented, planned, out of scope | On demand (Claude reads when asked) | Keep concise | Yes |
| `CHANGELOG.md` | What changed per release, for humans/stakeholders | On demand (Claude reads when asked) | Append-only | Yes |
| `PRODUCT_SPEC.md` | Original product requirements (startup artifact, not maintained) | Via skill (on-demand) | No limit | Yes |
| `.claude/settings.json` | Hook config (post-edit lint + format) | Always active | N/A | Yes |
| `.claude/scripts/post-edit.sh` | Lint + format on file edit (<2s) | Called by hook | N/A | Yes |
| `.claude/rules/backend.md` | Backend conventions (paths: `backend/**`) | On-demand when path matches | <100 lines each | Yes |
| `.claude/rules/frontend.md` | Frontend conventions (paths: `frontend/**` or `Frontend/**`) | On-demand when path matches | <100 lines each | Yes |
| `.claude/rules/tests.md` | Test conventions (paths: `**/tests/**`, `**/*.test.*`, `**/*.spec.*`) | On-demand when path matches | <100 lines each | Yes |
| `.claude/skills/product-spec/SKILL.md` | Wraps `PRODUCT_SPEC.md` for on-demand loading | On-demand or `/product-spec` | Wrapper only | Yes |
| `.claude/skills/pre-commit/SKILL.md` | Run related tests + type check before commit | On-demand via `/pre-commit` | N/A | Yes |
| `.claude/skills/generate-tests/SKILL.md` | Generate unit + E2E tests for new code | On-demand via `/generate-tests` | N/A | Yes |
| `.claude/skills/changelog/SKILL.md` | Generate changelog entry for current branch | On-demand via `/changelog` | N/A | Yes |
| `.github/workflows/ci.yml` | Full test suite, coverage, build, lint on push/PR | External (GitHub Actions) | N/A | Yes |

**Directory structure at a glance:**

```bash
repo/
├── CLAUDE.md                              # <200 lines, auto-loaded
├── DESIGN.md                              # Human-readable HLD
├── REQUIREMENTS.md                        # Scope checklist
├── CHANGELOG.md                           # Append-only, skill-generated
├── PRODUCT_SPEC.md                        # Startup artifact (not maintained)
├── .claude/
│   ├── settings.json                      # Hooks config
│   ├── scripts/
│   │   └── post-edit.sh                   # Lint + format (<2s)
│   ├── rules/
│   │   ├── backend.md                     # paths: ["backend/**/*.py"]
│   │   ├── frontend.md                    # paths: ["frontend/src/**/*.{ts,tsx}"]
│   │   └── tests.md                       # paths: ["**/tests/**", "**/*.test.*"]
│   ├── skills/
│   │   ├── product-spec/SKILL.md          # @../../PRODUCT_SPEC.md
│   │   ├── pre-commit/SKILL.md            # /pre-commit
│   │   ├── generate-tests/SKILL.md        # /generate-tests
│   │   └── changelog/SKILL.md             # /changelog
│   └── agents/
│       ├── code-reviewer.md               # Review changes for quality
│       └── security-reviewer.md           # OWASP top 10 checks
└── .github/
    └── workflows/
        └── ci.yml                         # Full test suite on push/PR
```

* * *

## Project Documents

Every repo has five markdown documents at the root. They serve different audiences and have different lifecycles:

| Document | Maintained By | Claude Loads It | Audience | Lifecycle |
| ---| ---| ---| ---| --- |
| `CLAUDE.md` | Human | Auto, every session | Claude | Living — prune regularly |
| `DESIGN.md` | Human | Via skill (on-demand) | Humans — stakeholders, new devs, architecture reviews | Living — update when architecture changes |
| `REQUIREMENTS.md` | Human | On demand (reads when asked) | Both — scope tracking | Living — checklist of done/planned/excluded |
| `CHANGELOG.md` | `/changelog` skill | On demand (reads when asked) | Humans — stakeholders, release notes | Append-only — generated before PR/release |
| `PRODUCT_SPEC.md` | Nobody | Via skill (on-demand) | Historical | Frozen — startup planning artifact |

### `CLAUDE.md` — For Claude

Brief architecture + commands + conventions. Claude needs this every session. See [Section 1](http://#1-claudemd--under-200-lines-ruthlessly-pruned).

### `DESIGN.md` — For Humans

The full high-level design: system diagrams, component descriptions, trade-off rationale, data flow. This exists for humans who need to understand the system — new developers, stakeholders, architecture reviews. Claude can read it via a skill when it needs the full picture, but doesn't need it every session.

`CLAUDE.md` gets a compressed ~20-line version of the architecture. `DESIGN.md` gets the complete human-readable version.

### `REQUIREMENTS.md` — Scope Tracking

A concise checklist — not a product spec. Tracks what's built, what's planned, and what's deliberately excluded:

```markdown
# Requirements

## Implemented
- [x] Bulk record assignment with due dates
- [x] Google + Microsoft SSO
- [x] CSV/JSON/PDF/Excel export

## Planned
- [ ] RBAC per-project roles
- [ ] Webhook retry dashboard

## Out of Scope
- No mobile app
- No offline mode
```

Claude doesn't need this for coding — it reads code. But it's useful when you ask "what's left to build?" or "is feature X in scope?"

### `CHANGELOG.md` — Release History

Generated by the `/changelog` skill before PR or release. Follows [Keep a Changelog](https://keepachangelog.com) format. Append-only — Claude can't corrupt existing entries.

```yaml
# .claude/skills/changelog/SKILL.md
---
name: changelog
description: Generate changelog entry for current branch
disable-model-invocation: true
---
1. Run: git log main..HEAD --oneline
2. Read the PR description if one exists
3. Categorize changes: Added / Changed / Fixed / Removed
4. Write user-facing summaries (not implementation details)
5. Append to CHANGELOG.md under a new ## [Unreleased] section
```

### `PRODUCT_SPEC.md` — Startup Artifact

The original product requirements written before coding began. **Not maintained.** Once features are built, the code is the source of truth — not a potentially-stale description of the code.

The spec stays in the repo as historical record. A skill wraps it for the rare cases Claude needs original product context:

```yaml
# .claude/skills/product-spec/SKILL.md
---
name: product-spec
description: Original product requirements and specification (pre-development planning artifact)
---
@../../PRODUCT_SPEC.md
```

### `/spec-check` — Flagging Drift (Optional)

If spec drift matters to your team, create a skill that **flags** differences without auto-rewriting:

```yaml
# .claude/skills/spec-check/SKILL.md
---
name: spec-check
description: Flag differences between product spec and current code
disable-model-invocation: true
---
1. Read git diff main...HEAD
2. Read relevant product spec skill files
3. List features/behaviors in code not reflected in spec
4. List spec requirements not yet implemented
5. Output a summary — DO NOT modify the spec files
```

This gives visibility without corrupting the planning document.
* * *

## 1\. `CLAUDE.md` — Under 200 Lines, Ruthlessly Pruned

**Location:** `./CLAUDE.md` (repo root, checked into git).

**Structure:**

```markdown
# Project Overview (2-3 sentences)

# Commands
- build, test, lint, dev server for ALL components

# Architecture (brief)
- Key relationships, service map, data flow (~20 lines)

# Conventions
- Naming, patterns, guardrails, "don't do" rules

# Gotchas
- Past bugs to avoid (1-2 lines each)
- Non-obvious constraints

# Compaction Instructions
When compacting, preserve: modified file list, test commands, architecture decisions.

# Imports
@README.md
@package.json
```

**Rules:**
*   Every line must pass: "Would removing this cause Claude to make mistakes?"
*   If Claude already does it correctly, delete the instruction.
*   Use emphasis (`IMPORTANT`, `YOU MUST`) sparingly — one per section max.
*   Add new gotchas when bugs recur; prune ones Claude handles correctly now.
* * *

## 2\. `.claude/rules/` — Path-Scoped Instructions

Split conventions by area. Only loads when Claude works with matching files.

```cpp
.claude/rules/
  backend.md          # paths: ["backend/**/*.py"]
  frontend.md         # paths: ["frontend/src/**/*.{ts,tsx}"]
  tests.md            # paths: ["**/tests/**", "**/*.test.*", "**/*.spec.*"]
  api-design.md       # paths: ["backend/app/api/**"]
  database.md         # paths: ["backend/app/models/**", "backend/app/db/**"]
```

**Rules without** **`paths`** **frontmatter** load at startup like [CLAUDE.md](http://CLAUDE.md). Only omit paths for truly global rules (e.g., architecture decisions that don't fit in [CLAUDE.md](http://CLAUDE.md)).
* * *

## 3\. `.claude/skills/` — On-Demand Knowledge

Skills load only when Claude determines they're relevant or you invoke them with `/skill-name`.

```coffeescript
.claude/skills/
  product-spec/SKILL.md       # Original product requirements
  changelog/SKILL.md          # Generate changelog entry
  fix-issue/SKILL.md          # GitHub issue → fix → PR workflow
  deployment/SKILL.md         # Deployment procedures
  pre-commit/SKILL.md         # Run tests + type check before commit
  generate-tests/SKILL.md     # Generate tests for new code
```

**Key principle:** If it's only needed for some tasks, it's a skill, not [CLAUDE.md](http://CLAUDE.md) content.

### Rules vs Skills — When to Use Which

|  | Rules (`.claude/rules/`) | Skills (`.claude/skills/`) |
| ---| ---| --- |
| How it loads | Auto-loads when Claude reads/edits files matching `paths` glob | On-demand: Claude decides it's relevant, or you invoke `/skill-name` |
| You invoke it? | No — automatic | Yes (or Claude chooses) |
| Use for | Coding conventions, patterns, guardrails scoped to code areas | Product specs, deployment procedures, repeatable workflows |
| Deciding question | "Does Claude need this every time it touches these files?" | "Does Claude only need this sometimes, for specific tasks?" |

### When a Skill Gets Too Large

**No single skill file should exceed ~500 lines.** If a skill is larger, split by domain area. Each skill is self-contained and only loads when relevant:

```coffeescript
.claude/skills/
  product-spec/SKILL.md              # Overview + data model (the core, <500 lines)
  product-auth/SKILL.md              # Auth, roles, permissions
  product-attestation/SKILL.md       # Attestation workflows, status flows
  product-integrations/SKILL.md      # Webhooks, connected apps, SSO
```

Each one needs a descriptive `description` field so Claude can decide which to load:

```yaml
---
name: product-attestation
description: Attestation workflow spec — status flows, assignment rules, delta re-load conflict logic
---
```

When you say "add a new attestation status," Claude loads `product-attestation`. When you say "fix the SSO callback," it loads `product-integrations`. The overview skill stays small.

If a single domain area is still too large, break further by layer: `product-attestation-backend/SKILL.md` and `product-attestation-frontend/SKILL.md`.
* * *

## 4\. `.claude/agents/` — Custom Subagents

Subagents run in separate context windows with their own tool permissions. Define project-specific subagents for repeated patterns:

```php
.claude/agents/
  code-reviewer.md      # Review changes for quality
  test-writer.md        # Generate tests for new code
  security-reviewer.md  # Check for OWASP top 10
```

* * *

## 5\. `.claude/settings.json` — Hooks (Fast Only)

Every repo gets a post-edit hook for lint + format. Keep `settings.json` simple; complex logic goes in scripts. **Do not run tests in hooks** — use skills or CI/CD instead.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/scripts/post-edit.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**`post-edit.sh`** **should only:** lint the changed file, auto-format, exit 2 if unfixable errors.
* * *

## 6\. Hooks vs Skills vs CI/CD — What Goes Where

Every check or automated action belongs in exactly one of the three tiers. The deciding factors are: **how fast is it?** and **does it need to run on every edit?**

### Decision Flowchart

```yaml
Does it MUST run on every single file edit?
  ├── YES → Can it complete in <2 seconds?
  │           ├── YES → PostToolUse Hook
  │           └── NO  → It's too slow for a hook. Move to Skill or CI/CD.
  └── NO  → Does the developer invoke it intentionally before a specific action?
              ├── YES → Skill (on-demand)
              └── NO  → CI/CD Pipeline (automated on push/PR)
```

### PostToolUse Hooks — Every Edit, <2 Seconds

These run automatically after every `Edit` or `Write` tool call. They must be fast and invisible.

| Action | Tool | Why Hook (not CI/CD) |
| ---| ---| --- |
| Lint single changed file | `ruff check`, `eslint` | Instant feedback — Claude fixes in same turn |
| Auto-format single file | `black`, `prettier` | Deterministic, no human judgment needed |
| Block writes to protected files | Custom script | Prevent accidental edits to migrations, lock files, `.env` |
| Validate import order | `isort`, `eslint` | Sub-second, keeps code clean as it's written |

**Do NOT put in hooks:** test runs, type checking, build verification, coverage — all too slow.

### Skills — On-Demand, 30-180 Seconds

These run only when the developer explicitly invokes them (`/skill-name`). They're for checks that matter at specific moments (before committing, after writing new code) but would be wasteful on every edit.

| Skill | Invocation | What It Does | When to Use |
| ---| ---| ---| --- |
| `/pre-commit` | Before `git commit` | Run related unit tests + type check for changed files | Every commit |
| `/generate-tests` | After writing new code | Generate unit + E2E tests for new files/functions | New features |
| `/changelog` | Before PR/release | Generate changelog entry from branch diff | Every PR |
| `/typecheck` | Before PR | Full `tsc --noEmit` or `mypy` across project | Before pushing |
| `/security-review` | Before PR for auth/data code | Subagent checks for OWASP top 10 vulnerabilities | Security-sensitive changes |
| `/run-e2e` | After UI changes | Run specific Playwright spec for changed page | Frontend changes |
| `/fix-issue` | On demand | Fetch GitHub issue, implement fix, create PR | Issue triage |
| `/spec-check` | On demand | Flag differences between spec and code | When spec drift matters |

### CI/CD Pipeline — Per Push/PR, Minutes

These run automatically on GitHub Actions (or equivalent) after every push or PR. They're the safety net — comprehensive but slow.

| Check | Tool/Command | Why CI/CD (not hook) |
| ---| ---| --- |
| Full test suite | `pytest`, `npm test`, `mvn test` | Minutes to run; blocks nothing in dev |
| Coverage enforcement | `--cov-fail-under=80` | Requires full suite to compute |
| Full build verification | `tsc + vite build`, `docker build` | 30s-5min; too slow for edit loop |
| Full lint (all files) | `ruff check .`, `eslint .` | Catches files Claude didn't touch |
| Type check (full project) | `tsc --noEmit`, `mypy .` | 10-60s; too slow for per-edit |
| Dependency audit | `npm audit`, `pip-audit` | Only needed at PR boundaries |
| Docker image build | `docker compose build` | Minutes; infra validation |
| E2E test suite | `npx playwright test` | Minutes; requires running services |
| Deploy to staging | Custom script | Only after all checks pass |

### Quick Reference

| Check | Hook | Skill | CI/CD |
| ---| ---| ---| --- |
| Lint single file | Yes |  |  |
| Format single file | Yes |  |  |
| Block protected file writes | Yes |  |  |
| Run related tests |  | Yes |  |
| Generate tests |  | Yes |  |
| Generate changelog |  | Yes |  |
| Type check (full) |  | Yes | Yes |
| Security review |  | Yes |  |
| Full test suite |  |  | Yes |
| Coverage check |  |  | Yes |
| Build verification |  |  | Yes |
| Dependency audit |  |  | Yes |
| Docker build |  |  | Yes |
| Full E2E suite |  |  | Yes |
| Deploy |  |  | Yes |

* * *

## 7\. Auto Memory — Let It Work

Don't manually maintain progress logs. Instead:
*   Enable auto memory (on by default since v2.1.59).
*   Claude writes its own notes about build commands, debugging patterns, architecture decisions.
*   Review with `/memory` periodically — edit or delete stale entries.
*   For critical learnings that must persist, add to [CLAUDE.md](http://CLAUDE.md) gotchas section.
* * *

## 8\. Session Discipline

Add to [CLAUDE.md](http://CLAUDE.md):

```markdown
# Session Management
When compacting, preserve: list of modified files, test commands and results, architecture decisions.
```

Team practice:
*   `/clear` between unrelated tasks.
*   `/compact` with focus instructions for long sessions.
*   Use subagents for codebase exploration (keeps main context clean).
*   Name sessions with `/rename` for resumability.
* * *

## 9\. Consistent File Naming

| Purpose | Standard Name | Delivery |
| ---| ---| --- |
| Claude Code instructions | `CLAUDE.md` | Auto-loaded every session |
| High-level design | `DESIGN.md` | Via skill (on-demand) |
| Requirements checklist | `REQUIREMENTS.md` | On demand (Claude reads when asked) |
| Changelog | `CHANGELOG.md` | Skill-generated, append-only |
| Product spec (frozen) | `PRODUCT_SPEC.md` | Via skill (on-demand) |
| Path-scoped rules | `.claude/rules/*.md` | Auto-loaded when path matches |
| On-demand knowledge | `.claude/skills/*/SKILL.md` | On-demand or `/skill-name` |
| Custom subagents | `.claude/agents/*.md` | When delegated to |
| Hook scripts | `.claude/scripts/*.sh` | Deterministic on every edit |
| Hook config | `.claude/settings.json` | Always active |

* * *

## 10\. What NOT to Do

*   **Don't put product specs in** [**CLAUDE.md**](http://CLAUDE.md) — they consume context every session.
*   **Don't manually maintain progress logs** — auto memory does this better.
*   **Don't write 2600-line spec files** — split into skills.
*   **Don't commit aspirational config** — only commit what actually runs.
*   **Don't put file-by-file codebase descriptions in** [**CLAUDE.md**](http://CLAUDE.md) — Claude reads code directly.
*   **Don't add emphasis to everything** — `IMPORTANT` on every rule means nothing is important.
*   **Don't use** **`.docx`** **files** — Claude Code can't read them. Use markdown.
*   **Don't skip hooks for deterministic actions** — if it must happen every time, make it a hook.
*   **Don't run tests in PostToolUse hooks** — they block every edit. Use `/pre-commit` skills or CI/CD instead.
*   **Don't use agent-type hooks for test generation** — 180s per edit kills flow. Make it a skill.
*   **Don't auto-sync the product spec** — it normalizes drift and blurs intent with implementation.
*   **Don't maintain the product spec after code exists** — the code is the source of truth.
* * *

## Sources

*   [Claude Code Memory System](https://code.claude.com/docs/en/memory) — official docs on [CLAUDE.md](http://CLAUDE.md), rules, auto memory
*   [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices) — official guidance on prompts, context, hooks, skills
*   [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide) — hook types, matchers, exit codes
*   [CLAUDE.md Best Practices (Nick Babich)](https://uxplanet.org/claude-md-best-practices-1ef4f861ce7c) — 10 sections to include
*   [Claude Code Project Structure (Nick Babich)](https://uxplanet.org/claude-code-project-structure-best-practices-5a9c3c97f121) — directory organization
*   [Claude Code Rules: Stop Stuffing Everything into One CLAUDE.md](https://medium.com/@richardhightower/claude-code-rules-stop-stuffing-everything-into-one-claude-md-0b3732bca433) — case for `.claude/rules/`
*   [50 Claude Code Tips (Builder.io)](https://www.builder.io/blog/claude-code-tips-best-practices) — practical tips
*   [7 Claude Code Best Practices for 2026 (eesel AI)](https://www.eesel.ai/blog/claude-code-best-practices) — project patterns
*   [Claude Code Hooks Tutorial (Blake Crosley)](https://blakecrosley.com/blog/claude-code-hooks-tutorial) — 5 production hooks
*   [Claude Code Hooks Mastery (GitHub)](https://github.com/disler/claude-code-hooks-mastery) — advanced hook patterns
*   [Git Worktree Isolation with Claude Code](https://medium.com/@richardhightower/git-worktree-isolation-in-claude-code-parallel-development-without-the-chaos-262e12b85cc5) — parallel development
*   [Claude Code Agent Teams Guide](https://claudefa.st/blog/guide/agents/agent-teams) — multi-session coordination
*   [Claude Code Context Buffer Management](https://claudefa.st/blog/guide/mechanics/context-buffer-management) — compaction strategy

# Anupam Claude Mapping
# Keytag Claude Standard — Design Decisions

Why we built the Claude Code setup for RebaseNow the way we did. This isn't a config dump — it's the reasoning behind every structural choice, written so the team can apply this standard to new repos, extend it confidently, and push back on it with full context.
* * *

## How We Built This

The setup process was deliberate, not ad hoc:

1. **Read the entire codebase first** — Used `/init` to have Claude read every backend file, every frontend file, every test, every config. Not summaries. The actual code.
2. **Mapped it against the Keytag standard** — Compared what existed against what the standard requires, planned exactly what to create and why, got alignment before writing a single file.
3. **Built the standard** — `CLAUDE.md`, `DESIGN.md`, `REQUIREMENTS.md`, `CHANGELOG.md`, the full `.claude/` directory with rules, skills, agents, hooks.
4. **Ran a second audit pass** — Re-read all the code against what we just created, and caught real bugs: wrong password defaults, wrong URL, missing env vars.
5. **Asked the hard "why" questions** — Why two agents and not one? Why skills and not tools? Why a 200-line cap? The answers are in the rest of this document.

The point is that this isn't configuration someone typed in 20 minutes. It's a setup that understands the actual codebase and makes decisions that hold up when the team is moving fast.
* * *

## Why Two Agents Instead of One?

The biggest failure mode for an AI agent on a complex task is **context window overflow**. A single monitoring visit capture in RebaseNow involves a 500-line schema, a previous visit record, open actions, site info, protocol references, and 15–20 back-and-forth exchanges with the CRA — all growing simultaneously. Put that in one agent and it hits the context ceiling mid-capture. It starts hallucinating field values, forgetting earlier answers, or silently dropping required fields. In a regulated clinical trial context, that's not just a bug, it's a compliance failure.

The solution is three agents with clearly separated responsibilities:

| Agent | Responsibility | Why isolated |
| ---| ---| --- |
| `capture` | Fills `/draft/visit.json` section by section | One-shot, autonomous, no user interaction. Context stays bounded. |
| `side_effects` | Creates actions, deviations, enrollments from the completed visit | Runs after save, works from final JSON only. Completely fresh context. |
| Main agent | Orchestrates, talks to the user, validates, handles signature | The only agent with the full conversation in context. |

The virtual filesystem — `/schema/`, `/context/`, `/draft/` — is the handoff mechanism. No message passing between agents, just shared files. This means you can debug any subagent in isolation by inspecting what it read and what it wrote.

**The rule for future work:** If a task needs more than ~10 file operations or more than 5 LLM turns, make it a subagent. If it's a single DB call or API operation, make it a tool.
* * *

## Why Skills Instead of More Tools?

Tools and skills look similar but solve different problems. Confusing them wastes tokens or makes the agent brittle.

**Tools** are Python `@tool` functions — single operations, always loaded, always available. Right for querying the DB, validating a record, saving a file.

**Skills** are multi-step workflows written in markdown — loaded on demand, readable by the agent before execution. Right for procedures where the agent needs to reason through a sequence of steps.

|  | Tools | Skills |
| ---| ---| --- |
| Defined in | Python | Markdown |
| Always loaded | Yes | No — on demand |
| Best for | Single operations | Multi-step procedures |
| Token cost | Low | Higher |

The `generate_pdf` skill is the canonical example: load record → render template → call WeasyPrint → store file → return URL. As a Python tool, that's a black box the agent just fires. As a skill, the agent can see exactly what it's about to do and decide whether to do it. The transparency matters.

**The rule:** If you can describe it in one sentence, it's a tool. If you need a numbered list, it's a skill.
* * *

## Why Is [CLAUDE.md](http://CLAUDE.md) Capped at 200 Lines?

[CLAUDE.md](http://CLAUDE.md) loads into **every single session**, automatically, before any work begins. We've seen repos where it grew to 2,600 lines — burning 15–20% of the context window on project setup before Claude touched a single file.

The cap enforces a discipline. Every line must pass one test: _"Would removing this cause Claude to make a real mistake?"_ If not, it doesn't belong there. Full architecture detail goes in `DESIGN.md` and loads via the `/design` skill when needed. Layer-specific conventions go in path-scoped rules. Generic practices Claude already knows. The result is that Claude starts every session with roughly 100 lines of facts it genuinely couldn't infer from reading the code — and nothing else.
* * *

## Why Path-Scoped Rules Instead of One Rules File?

When you're editing a frontend component, you don't need asyncpg patterns. When you're writing a backend tool, you don't need Next.js patterns. One big rules file means loading all of it every session regardless.

Path-scoped rules load only when Claude edits a file matching the pattern:

```css
.claude/rules/backend.md   →  backend/**/*.py
.claude/rules/frontend.md  →  frontend/src/**/*.{ts,tsx}
.claude/rules/tests.md     →  e2e/**/*.spec.ts
```

This also makes ownership clean. Backend convention changes? One engineer edits one file. No risk of a frontend change accidentally overwriting a backend rule.

**The rule:** Layer-specific conventions go in scoped rules. Universal conventions (like the `TYPE-SITE-NUMBER` ID pattern) go in [CLAUDE.md](http://CLAUDE.md).
* * *

## Why a PostToolUse Hook Instead of a Pre-Commit Hook?

Pre-commit hooks catch errors once, right before you commit. By then you've written ten files and the error is in file three. You have to stop, hunt it down, fix it, restage.

PostToolUse hooks catch errors **after every file write**, while Claude is still working in that file. The error surfaces immediately, gets fixed immediately, and never compounds.

The hard constraint is speed — the hook must finish in under 2 seconds or it blocks every edit and developers disable it. So it only does two things: `python3 -m py_compile` for Python files (~0.1s) and `next lint --file` for TypeScript (~1s). No tests, no type checking, no build. Those are too slow for a hook.
* * *

## Why Three Tiers: Hooks / Skills / CI?

Every automated check belongs in exactly one place:

*   **Must run on every file edit, invisibly** → PostToolUse hook
*   **Developer invokes it intentionally before a specific action** → Skill
*   **Runs automatically on push, can take minutes** → CI/CD

Violating the tiers creates compounding problems. Tests in hooks means every edit takes 30 seconds — developers turn hooks off and errors accumulate silently. Linting only in CI means errors surface after push and require another commit to fix. The tiers exist so that by the time code reaches CI, it's already been through fast local checks. CI is the safety net, not the first line of defence.
* * *

## Why Does PRODUCT\_SPEC.md Stay But Never Get Updated?

The spec was written before the first line of code. It captures the original product thinking — the "why" behind decisions that aren't visible in the code. Why is this not a Veeva replacement? Why no document upload? Why structured data at the point of capture instead of extraction?

Once code exists, the code is the source of truth. Maintaining the spec alongside the code creates two sources of truth that drift apart — and nobody knows which to trust. So the spec stays as a read-only historical artifact, wrapped by the `/product-spec` skill for the rare moment someone asks "why did we design it this way?" It is never updated, because the moment you start updating it, it becomes a second source of truth.
* * *

## Why Version-Controlled Review Agents?

Code review and security review happen on every feature and every PR. The things that get missed are always the same things — not because engineers are careless, but because checklists held in memory are unreliable under deadline pressure.

Putting review checklists in `.claude/agents/` means they're version-controlled alongside the code they review. When a new compliance requirement appears — a new 21 CFR Part 11 interpretation, a new OWASP finding — the agent gets updated in the same PR as the code change. Any Claude session runs the exact same checklist, not whatever the reviewer happened to remember that day.

The security reviewer specifically encodes the regulatory requirements that a generic code review misses — things like 21 CFR Part 11 §11.10(e) on audit trails, or the invariant that `record_history` is never modified or deleted. Those aren't common software engineering knowledge. They need to be written down and checked consistently.
#