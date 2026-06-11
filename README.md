![banner](assets/banner.jpg)

# Agent Skills

## Install

This repo is a Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) (`dp-skills`) that ships one plugin (`dp`) bundling all skills below.

```
/plugin marketplace add tumultousRamen/skills
/plugin install dp@dp-skills
```

Skills are namespaced under the plugin name once installed:

- `/dp:deep-research` — multi-stage research pipeline with span-grounded citations
- `/dp:quick-research` — mid-task knowledge-gap fills (subagent does a tight search+fetch loop, returns a question-shaped answer)
- `/dp:caveman` — anti-slop framing for agent reasoning
- `/dp:consult` — McKinsey-style answer-first responses (Minto pyramid: verdict first, MECE reasons under action titles, recommendation + next steps + risks)

To pin to a specific commit or tag, append `@<ref>` to the marketplace add (e.g. `tumultousRamen/skills@v0.1.0`). To share with a team via `.claude/settings.json`, see the [`extraKnownMarketplaces`](https://code.claude.com/docs/en/settings#plugin-settings) settings reference.

### Local development

While iterating on the skills, load the plugin directly from a local checkout — no marketplace dance:

```
claude --plugin-dir /path/to/this/repo
```

Run `/reload-plugins` after edits to pick up changes without restarting.