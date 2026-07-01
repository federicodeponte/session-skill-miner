---
name: session-to-skill
description: Mine agent session logs or exported transcripts for repeated workflows, corrections, and friction patterns, then propose or draft reusable Agent Skills. Use when the user asks to turn chat/session logs into skills, mine sessions for reusable workflows, extract rules from repeated corrections, improve an agent setup from transcripts, or create optional Floom worker bundle drafts from recurring work.
---

# Session To Skill

Turn agent session history into reusable operating knowledge:

- New Agent Skill candidates.
- Updates to existing skills.
- Global instruction or memory candidates.
- Optional Floom worker bundle drafts for repeatable jobs with clear inputs and outputs.

## Inputs

Accept any combination of:

- Exported session Markdown.
- Raw JSONL transcript files.
- A directory of transcripts.
- A short description of the target sessions.

Treat transcript content as private. Do not quote sensitive text in the final report. Redact secrets, tokens, personal identifiers, private URLs, and proprietary file contents.

## Workflow

Track progress with this checklist:

```markdown
- [ ] 1. Locate and normalize sessions
- [ ] 2. Extract deterministic signals
- [ ] 3. Segment work into topic arcs
- [ ] 4. Classify candidates
- [ ] 5. Apply the worth-it gate
- [ ] 6. Present proposals
- [ ] 7. Draft only after approval
```

### 1. Locate And Normalize Sessions

If the user gives files, inspect those files directly. If the user gives a directory, prefer Markdown exports when present and use JSONL as a fallback.

Common locations:

```bash
find ~/.claude/projects -name '*.jsonl' 2>/dev/null | tail
find ~/.codex/sessions -name '*.jsonl' 2>/dev/null | tail
find . -iname '*session*.md' -o -iname '*.jsonl'
```

For large raw JSONL files, use byte search only to locate candidate files. Do not load huge tool payloads into context.

### 2. Extract Deterministic Signals

Run the bundled extractor on candidate files:

```bash
python3 session-to-skill/scripts/session_to_skill.py <session-or-directory> --out /tmp/session-to-skill-report.md
```

Use the report as scaffolding, not as final authority. The script gives counts, repeated phrases, command hints, correction hints, and a first-pass proposal table.

### 3. Segment Work Into Topic Arcs

Split long sessions into arcs before judging candidates. Use:

- User goal changes.
- Compaction or continuation markers.
- Long time gaps.
- Distinct file trees or repositories.
- Tool clusters around a repeated workflow.

Mine each arc separately. Do not treat a multi-day session as one task.

### 4. Classify Candidates

Assign each finding to exactly one category:

| Category | Use when | Output |
| --- | --- | --- |
| New skill | Repeated workflow lacks existing coverage | `skills/<name>/SKILL.md` draft |
| Skill update | Existing skill nearly covers the pattern | Patch proposal |
| Rule candidate | Repeated correction or global constraint | Instruction text |
| Memory candidate | Stable preference, fact, or environment detail | Memory text |
| Floom worker candidate | Repeatable job has stable inputs, outputs, and done state | `worker.yml` plus `SKILL.md` or `run.py` draft |
| No action | One-off task or not worth preserving | Brief rationale |

### 5. Apply The Worth-It Gate

A new skill candidate passes only when all are true:

- The pattern appears in at least 3 independent arcs or sessions, or the user explicitly asks to preserve it.
- The workflow has steps, constraints, or local context that a general model will not reliably infer.
- The reusable instructions are shorter than re-explaining the workflow each time.
- Existing loaded or searchable skills do not already cover the pattern.
- The skill can be written without embedding private transcript details.

For rule candidates, require at least 2 repeated corrections unless the user explicitly asks to add the rule.

### 6. Present Proposals First

Do not create or edit files before approval. Present:

```markdown
## Session To Skill Report

### Recommended Skill Drafts
| Candidate | Action | Evidence | Why it passes | Proposed name |
| --- | --- | --- | --- | --- |

### Existing Skill Updates
| Skill | Gap | Evidence | Proposed change |
| --- | --- | --- | --- |

### Rule And Memory Candidates
| Type | Evidence | Proposed text |
| --- | --- | --- |

### Optional Floom Worker Bundles
| Candidate | Trigger | Inputs | Outputs | Mode |
| --- | --- | --- | --- | --- |

### Rejected Candidates
| Candidate | Reason |
| --- | --- |
```

Evidence format: use session file names, event numbers, timestamps, counts, or redacted excerpts under 12 words. Avoid full transcript quotes.

### 7. Draft After Approval

After approval, create only the approved artifacts.

For Agent Skills:

```text
skills/<name>/
  SKILL.md
  scripts/       # optional
  references/    # optional
  fixtures/      # optional
```

Write `SKILL.md` with only `name` and `description` in YAML frontmatter. Put trigger phrases in the description. Keep the body procedural and under 500 lines.

For optional Floom worker bundles:

```text
workers/<name>/
  worker.yml
  SKILL.md    # agent mode
  run.py      # script mode
```

Validate a Floom worker bundle when the CLI is available:

```bash
npx -y @floomhq/floom workers validate workers/<name>
```

Never push, schedule, enable, or run a worker that performs external actions until the user approves that exact action.

## Quality Bar

- Prefer one strong skill over many weak ones.
- Name skills with short kebab-case gerunds or verb phrases.
- Keep transcript evidence private and minimal.
- Include deterministic scripts only when they remove repeatable parsing or validation work.
- Validate generated skills with the target agent or `npx skills` before calling them ready.
- Report uncertainty as a test gap, not as a conclusion.

## Bundled Resources

- `scripts/session_to_skill.py`: deterministic signal extractor for Markdown, text, and JSONL session files.
- `fixtures/sample-session.md`: redacted fixture for local verification.
- `fixtures/expected-report.md`: expected report shape for the fixture.
