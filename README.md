# session-to-skill

Mine agent session logs for repeated workflows, corrections, and friction patterns, then turn the useful findings into reusable Agent Skills.

## Install

After this repository is published:

```bash
npx skills add <owner>/<repo> --skill session-to-skill
```

For local testing:

```bash
npx skills add . --skill session-to-skill --agent codex --copy -y
```

## What It Does

- Reads exported Markdown, plain text, or JSONL session logs.
- Extracts deterministic signals with `scripts/session_to_skill.py`.
- Guides an agent through candidate classification and a worth-it gate.
- Drafts Agent Skill artifacts after approval.
- Optionally drafts Floom worker bundles for repeatable jobs with stable inputs and outputs.

## Verification

```bash
python3 session-to-skill/scripts/session_to_skill.py session-to-skill/fixtures/sample-session.md
npx skills add . --skill session-to-skill --agent codex --copy -y
```
