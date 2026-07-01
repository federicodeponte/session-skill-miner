# Session To Skill Signal Report

## Inputs

- `session-to-skill/fixtures/sample-session.md`

## Corpus

- Files scanned: 1
- Text events: 15
- Correction hints: 2
- Skill/rule phrase hints: 4

## Repeated Commands

- 2x `npm test`

## First-Pass Candidates

| Candidate | Evidence count | Rationale |
| --- | ---: | --- |
| `review-workflow` | 2 | Repeated `review` workflow language |
| `verify-workflow` | 2 | Repeated `verify` workflow language |
| `test-workflow` | 2 | Repeated `test` workflow language |
| `npm-workflow` | 2 | Repeated command: `npm test` |
| `correction-patterns` | 2 | Repeated correction language at sample-session.md:13, sample-session.md:25 |

## Review Notes

- Treat this as scaffolding for agent review, not a final decision.
- Require 3 independent arcs or explicit user approval before creating a new skill.
- Redact transcript details before sharing this report.
