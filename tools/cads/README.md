# cads (vendored claude-ads)

Vendored from https://github.com/AgriciDaniel/claude-ads (MIT, see LICENSE).
Renamed so it can't collide with the existing pdotj skills:

- skills: `.claude/skills/cads*` (entry point `/cads`, sub-skills `cads-audit`, `cads-meta`, ...)
- agents: `.claude/agents/cads-*`
- support files (schemas, manifests, scripts): this folder. Where the skills
  say `<plugin_root>` or `control-plane/...`, that means `tools/cads/`.

Read-only by default. Originals are untouched: `humanize-writing` and the
account-level pdotj skills are not modified.
