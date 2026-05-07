---
doc-kind: convention
status: canonical
applies-to: skills/*/SKILL.md
---

# SSL Frontmatter — Scheduling · Structural · Logical

> Authoritative reference for the `ssl:` frontmatter block on every `SKILL.md`
> in this plugin. English-only by intent — this is an internal contract
> document; user-facing docs (README, CHANGELOG) remain trilingual.

## Why SSL?

A SKILL.md is not a script. It is a prompt fragment that an LLM may load —
or skip — at invocation time. The body is read lazily, often only after a
trigger fires; static analysis tools and humans both stop at the frontmatter.
That makes the frontmatter the only place where machine-checkable contracts
can live. Everything below the `---` is prose the model will paraphrase. The
frontmatter is what we can actually lint.

The `ssl:` block declares what the body would otherwise have to be re-read
to discover: when this skill should *not* run, what the run looks like step
by step, and what state on the user's disk it touches. Three layers, each
answering a different question, each addressable on its own. The names are
not decorative — they map to the **Scheduling / Structural / Logical**
framing for agent skills (cf. Schank & Abelson on scripts; recent SSL
formalism in arXiv:2604.24026), where Scheduling decides *whether*,
Structural decides *what shape*, Logical decides *what effect*.

The payoff is concrete. With SSL declared, a CI lint can refuse a SKILL.md
that claims `idempotent: true` while appending to a `*.jsonl`. A reviewer
can see the rollback contract without reading 200 lines of bash. A second
skill can be diffed against the first without an LLM round trip. The body
remains the source of truth for *how*; the frontmatter is the source of
truth for *what is touched and when*.

## The 3 layers

### Scheduling — when does this run?

Answers: under what conditions should the dispatcher *not* invoke this
skill? Triggers themselves already live in the `description:` field (where
Claude Code's skill index reads them). The Scheduling layer carries only
the **negative** signal: anti-triggers — situations where invoking this
skill would be wasteful, redundant, or actively wrong.

Schema slice:

```yaml
ssl:
  scheduling:
    anti_triggers: ["..."]
```

Worked example (from `skills/whoami/SKILL.md`):

```yaml
scheduling:
  anti_triggers:
    - "`.honne/persona.json` is fresh and no new transcript exists (use compare)"
    - "only a single axis is needed (use lexi)"
```

Each entry is a plain sentence in the user's working language. They are
hints to a future router, not regex. Two to four entries is typical; more
than six usually means the skill is overloaded and should be split.

### Structural — what shape is the run?

Answers: what are the named steps a successful run goes through, and can
the run be resumed mid-way? This mirrors the `## Step N: ...` headings in
the body — they must agree. Drift between them is a lint error.

Schema slice:

```yaml
ssl:
  structural:
    scenes: ["Step 1: ...", "Step 2: ..."]
    resumable: bool
```

Worked example (from `skills/whoami/SKILL.md`):

```yaml
structural:
  scenes:
    - "Step 1: Scope+Locale HITL"
    - "Step 2: Scan"
    - "Step 3: Rejection reframe filter"
    - "Step 4: Per-axis autonomous record"
    - "Step 5: LLM narrative synthesis"
    - "Step 6: Render persona and report"
  resumable: true
```

`resumable: true` means: if the run is interrupted between two scenes, a
later invocation can pick up from a cached intermediate file (here:
`.honne/cache/scan.json` plus per-axis caches) without redoing the prior
scenes. `resumable: false` means each invocation must run end to end —
typical for read-only skills (`compare`) and for skills whose
side-effecting steps are not individually idempotent.

### Logical — what does the run touch?

Answers: what filesystem paths and network endpoints does the body read,
write, delete, or contact? Is running the skill twice equivalent to
running it once? If not, how do you undo a run? This is the layer a
reviewer cares about most.

Schema slice:

```yaml
ssl:
  logical:
    side_effects:
      reads: ["path"]
      writes: ["path  # append" | "path  # overwrite"]
      deletes: []
      network: []
    idempotent: bool
    rollback: "..." | null
```

Worked example (from `skills/crush/SKILL.md`):

```yaml
logical:
  side_effects:
    reads:
      - ".honne/personas/*.md"
    writes: []
    deletes: []
    network: []
  idempotent: true
  rollback: null
```

`crush` is read-only — no writes, no deletes, no network. It is
trivially idempotent and needs no rollback. Compare with `whoami` which
appends to `claims.jsonl` and is therefore `idempotent: false` with a
non-null `rollback` describing how to undo the appended lines.

## Canonical schema

Copy this verbatim. Comments and trailing-space inline annotations
(`# append` / `# overwrite`) are part of the convention.

```yaml
ssl:
  scheduling:
    anti_triggers: ["..."]
  structural:
    scenes: ["Step 1: ...", "Step 2: ..."]
    resumable: bool
  logical:
    side_effects:
      reads: ["path"]
      writes: ["path  # append" | "path  # overwrite"]
      deletes: []
      network: []
    idempotent: bool
    rollback: "..." | null
```

Notes:

- `anti_triggers`, `scenes`, `reads`, `writes`, `deletes`, `network` are
  always lists (use `[]` for empty, never omit the key).
- `resumable` and `idempotent` are always present; no defaults.
- `rollback` is either a non-empty string or the literal `null`. The
  string form is read by humans, not parsed — describe the undo recipe
  in prose, including any caveats about `.gitignore`.
- Every path under `writes:` carries an inline `# append` or
  `# overwrite` comment after two spaces. This lets a reviewer (and
  any future linter) decide whether `idempotent: true` is plausible.

## Migration guide

Adding the SSL block to an existing SKILL.md:

1. **List body operations.** Walk the body top to bottom. Every command
   that touches the filesystem or network is a candidate side effect.
   Look for `bash`, `Read`, `Write`, `Edit`, `curl`, `python3 -c
   "open(...)"`, `>>`, `>`, `rm`, and any tool calls.

2. **Group into reads / writes / deletes / network.** Resolve variables
   to their literal paths where possible (`.honne/cache/scan.json`).
   When a path is templated by an environment-like variable, write it
   with `${...}` syntax (`.honne/cache/axis-${axis}.json`).

3. **Annotate each write.** For each entry under `writes:`, append two
   spaces and `# append` or `# overwrite`. Open-with-`a`, `>>`, and
   `record claim --out … .jsonl` are appends. Open-with-`w`, `>`, and
   `Write` calls that overwrite are overwrites. If a single path is
   sometimes appended and sometimes overwritten, list it twice with
   different annotations and tighten the body until that stops being
   true.

4. **Determine `idempotent`.** Run the skill twice in a clean sandbox.
   Diff the final state. If running twice produces the same final state
   (modulo timestamps), `idempotent: true`. Append-mode writes almost
   always force `idempotent: false` because the second run leaves a
   longer file than the first. Overwrite-only skills are usually
   idempotent — but check that every overwrite is deterministic given
   the same inputs.

5. **Write the rollback.** If `idempotent: false`, you owe a `rollback:`
   string. The minimum acceptable string answers two questions: which
   paths to touch, and how to identify the last run's contribution
   (typically a `RUN_ID`). Pay attention to `.gitignore` — `.honne/` is
   gitignored in this repo, so `git checkout -- .honne/...` will not
   work. Recommend `cp -r .honne .honne.bak` *before* the run instead.
   For idempotent skills, set `rollback: null`.

6. **Mirror the scenes.** Make sure every `## Step N: ...` heading in
   the body has a matching entry in `structural.scenes` and vice versa.
   Drift between this declaration and the body is a hard error — keep
   them in sync during PR review.

## Anti-patterns

- **Don't mirror `triggers:` inside `ssl.scheduling.triggers`.** Triggers
  already live in the `description:` field and Claude Code's skill
  router reads them from there. A second copy in SSL guarantees drift
  the moment you tune one and forget the other. Only `anti_triggers`
  belongs in the Scheduling layer.

- **Don't claim `idempotent: true` for any skill that appends to
  `*.jsonl`.** Appending makes the second run's final state strictly
  larger than the first run's. A reviewer will notice; declaring it
  correctly up front saves a review cycle.

- **Don't write `rollback: "git checkout -- ..."` for paths that are
  `.gitignore`d.** `.honne/` is gitignored in this repo; `git checkout`
  on a gitignored path is a no-op. Either back up with `cp` before the
  run, or describe a content-aware undo (`jq` / `grep -v $RUN_ID`).

- **Don't bury branching logic in prose.** If the body says "if X, do
  A, otherwise do B and C", every reachable scene must appear in
  `structural.scenes` as its own Step. Scenes are read as a flat list;
  hidden branches make `resumable:` impossible to verify.

- **Don't pad `anti_triggers` with vacuous entries.** A reviewer
  weights the few real risks per layer, not raw count. Filling
  `anti_triggers` with truisms ("don't run if user does not want to")
  lowers the signal density of the layer.

## Cross-references

- Worked examples in `skills/whoami/SKILL.md`, `skills/crush/SKILL.md`
- Schema gate enforced in `tests/manifest.bats`

This file is canonical. When the schema changes, update it here first
and bump the affected SKILL frontmatter blocks in the same commit.
