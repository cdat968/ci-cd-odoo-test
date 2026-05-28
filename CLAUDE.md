# Claude Code Instructions — qa-system

## Harness Workflow

This project uses the Harness system. Every implementation task must go through
the harness workflow below. Do NOT skip steps.

### Before Implementation

When the user confirms any implementation task (any phrasing: "triển khai đi",
"sửa đi", "làm đi", "confirm", "proceed", etc.):

**Step 1 — Present classification to user. Wait for confirmation before writing anything.**

Present the following in a clear block:

```
Story: [new US-XXX] or [existing US-XXX — "<title>"]
  Reason: [why this work fits / doesn't fit an existing story contract]

Type: [change-request | spec-slice | maintenance-request | ...]
  Reason: [why]

Risk flags:
  - [flag name] — [specific reason this work touches this flag]
  - [flag name] — [specific reason]
  (only list flags that actually apply, with reasoning)

Flag count: N → Lane: [tiny | normal | high-risk]
  Hard gates triggered: [list or "none"]
```

**Step 2 — Wait for user to confirm or correct the classification.**

**Step 3 — After user confirms:**
- If new story: create story file at `docs/stories/epics/E01-qa-bug-system/US-XXX-title.md`
- Run `scripts/bin/harness-cli intake --type ... --summary ... --lane ... --flags ... --story ...`
- Run `scripts/bin/harness-cli story add --id ... --title ... --lane ... --contract ... --notes ...`
- If architecture changes: run `scripts/bin/harness-cli decision add --id ... --title ... --notes ...`
- Then proceed with implementation

### After Implementation

- Run `scripts/bin/harness-cli story update --id US-XXX --status implemented`
- Run `scripts/bin/harness-cli trace --summary "..." --outcome completed`
- Update story file: add Evidence section with what was implemented

### Flag Reference (from docs/FEATURE_INTAKE.md)

| Flag | Applies when touching |
|---|---|
| auth | login, logout, sessions, JWT, password |
| authorization | roles, permissions, tenant scope |
| data-model | schema, migration, new fields, deletion |
| audit-security | logs, privacy, sensitive data |
| external-systems | cloud services, SDKs, webhooks, queues |
| public-contracts | API shape, response envelope |
| cross-platform | desktop/mobile/browser split |
| existing-behavior | already-implemented or tested behavior changes |
| weak-proof | unclear or missing tests around affected area |
| multi-domain | more than one product domain changes |

Lane rules:
- 0-1 flags → tiny or normal
- 2-3 flags → normal (stronger validation)
- 4+ flags → high-risk
- Any hard gate (auth, authorization, data-loss, audit-security) → high-risk

### Tiny Lane Exception

Tiny tasks (1 flag max, narrow edit) may skip story file creation.
Still record intake + trace after.

### Harness CLI Location

```bash
scripts/bin/harness-cli <command>
# Must be run from /Users/macos/Desktop/WorkSpace/qa-system
```
