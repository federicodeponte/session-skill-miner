# session-skill-miner

Mine agent session logs for repeated workflows, corrections, and friction patterns, then turn the useful findings into reusable Agent Skills.

## Install

After this repository is published:

```bash
npx skills add <owner>/<repo> --skill session-skill-miner
```

For local testing:

```bash
npx skills add . --skill session-skill-miner --agent codex --copy -y
```

## What It Does

- Reads exported Markdown, plain text, or JSONL session logs.
- Extracts deterministic signals with `scripts/session_skill_miner.py`.
- Guides an agent through candidate classification and a worth-it gate.
- Drafts Agent Skill artifacts after approval.
- Optionally drafts Floom agent-worker specifications for repeatable jobs with stable inputs and outputs.

## Verification

```bash
python3 -m unittest discover -s tests
python3 session-skill-miner/scripts/session_skill_miner.py session-skill-miner/fixtures/sample-session.md
npx skills add . --skill session-skill-miner --agent codex --copy -y
```
