# Domain context

This repo is a Claude Code **plugin marketplace** (`dp-skills`) shipping a single **plugin** (`dp`) that bundles all released skills. Skills install namespaced as `/dp:<name>`.

## Skill taxonomy

Two kinds of skills live here, and they have different shapes:

- **Output-mode skills** (`caveman`, `consult`) — change *how* the agent communicates, not what it does. They are session-persistent once invoked (active every response until the user turns them off), carry no scripts, and their SKILL.md is mostly behavioral rules plus anti-patterns. `caveman` compresses; `consult` restructures (Minto pyramid: answer first, MECE support, recommendation close).
- **Research pipelines** (`deep-research`, `quick-research`) — orchestrate subagents to fill knowledge gaps. They carry `prompts/` directories and per-skill READMEs explaining the why/architecture. `deep-research` is the multi-stage report end of the spectrum; `quick-research` is the 30-second mid-task fill.

`browse` is present in `skills/` but **unreleased** — not registered in `plugin.json` and not listed in the README.

## Adding or releasing a skill (checklist)

1. `skills/<name>/SKILL.md` — frontmatter `name` + `description` (description must include "Use when" triggers; it's the only thing the agent sees when deciding to load the skill).
2. Register the path in `.claude-plugin/plugin.json` → `skills` array.
3. Update the skill enumeration in BOTH descriptions: `plugin.json` and the plugin entry in `.claude-plugin/marketplace.json` (they are kept identical).
4. Add a `/dp:<name>` bullet to the README install section.
5. Optional: per-skill `README.md` for the why/architecture (pipelines have them; output-mode skills get one only if the design needs explaining), `EXAMPLES.md` for rendered output targets, `prompts/` for subagent prompts.

## Conventions

- Skill descriptions are written in third person, trigger-rich, under 1024 chars.
- Session-persistent skills must state their persistence rule and their off-switch phrase in SKILL.md (see caveman's "Persistence" section, consult's session-mode header).
- Local iteration: `claude --plugin-dir <repo>` + `/reload-plugins` (see README) — no marketplace re-add needed.
