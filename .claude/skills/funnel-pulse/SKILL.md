---
name: funnel-pulse
description: Twice-a-day check of the 3HROBB paid funnel (3-Hour Online Business Builder). Pulls Meta Ads (spend, outbound clicks, landing page views), Microsoft Clarity (sessions, scroll, dead/rage clicks, pop-up opens) and GoHighLevel (skill pop-up answers, checkout, paid, order bump), refreshes the "3HROBB Funnel Pulse" dashboard, and sends a short plain-words summary. Use for "how's the funnel", "how are the ads doing", "run funnel pulse", or on the 9 am / 5 pm IST schedule.
---

# Funnel Pulse (3HROBB only)

The funnel has these steps. Each run counts people at every step and
refreshes the dashboard.

```
Meta ad ─► Sales page ─► Opens pop-up ─► Skill pop-up ─► Checkout (+ bump) ─► Paid
 Meta       Meta/Clarity   Clarity         GHL form        GHL orders           GHL
```

## Rules that don't change

- **3HROBB only.** Leave PES, 2OB and every other product out of everything.
  Meta campaigns: only names containing `3HROBB`. GHL orders: only funnel
  `GtYMbm8TlxDQY8bhVJGR`.
- **Read-only.** Never pause, edit or create anything in Meta, GHL or Clarity.
  Only suggest.
- **Words to use:** "Outbound clicks" (Meta `outbound_clicks`), "Landing page
  views" (Meta `landing_page_view`), "Has a skill" / "No skill yet". Never call
  people "qualified". The pop-up exists to sort skill vs no skill.
- **Always show % next to counts.**
- No customer names, emails or phone numbers anywhere: dashboard, commits or
  messages. Counts only.
- Skip test orders from `prathameshjiwatode@gmail.com`.
- Write for a 3rd-grade reading level: short sentences, simple words.

## Fixed IDs

| Thing | Value |
|---|---|
| Meta ad account | `574387113125115` ("pdotj", INR) |
| GHL location | `7rxmDgEXJMsPErojoFfx` |
| Pop-up form | `CyZmHqBkl6Ui6hqlgNCc` ("3hr Form") on `/3houronlinebusinessbuilder-page` |
| Pop-up question field | `6e8IhdbRJNAroc684OOb` |
| No-skill answer | "I don't have a skill yet" (every other answer = has a skill) |
| Checkout | `/3hr-cp`, ₹499, ₹1,498 with order bump |
| Dashboard | https://claude.ai/artifact/VYuSVkwRofkcuFrfFcGVVH |
| Dashboard datasets | `summary`, `funnel`, `daily`, `campaigns`, `answers` |
| Time zone | Asia/Kolkata (IST) |

## Window

Always the last 7 IST days plus today so far: `START` = today − 7 days,
`END` = today (IST dates). Label: `Last 7 days · <D Mon> to <D Mon> (today so far)`.

## Steps

Keep a scratch folder (for example `$SCRATCH/run`). Save every tool answer
there as a JSON file, exactly as it came back.

### 1. Meta Ads
`ads_get_ad_entities` on `574387113125115`, `level=campaign`,
`time_increment="1"`, filter `name CONTAIN 3HROBB`, fields
`id, name, amount_spent, impressions, outbound_clicks, landing_page_view, omni_purchase, ctr, frequency`.
Call it twice: `date_preset=last_7d` and `date_preset=today`. Save as
`meta_7d.json` and `meta_today.json`. Pass `scheduled_task_run=true` on a
scheduled run.

### 2. GoHighLevel
- `get-forms-submissions`: `formId=CyZmHqBkl6Ui6hqlgNCc`, `limit=100`,
  `startAt=START`, `endAt=END+1 day` (`YYYY-MM-DD`). Big answers get saved to a
  file for you. Use that path and don't read it by hand. Follow
  `meta.nextPage`.
- `list-orders`: `altType=location`, `altId=7rxmDgEXJMsPErojoFfx`,
  `limit=100`, same dates.

### 3. Microsoft Clarity (its own connector, "Microsoft Clarity")
Load its tools with ToolSearch (`clarity`). Use **Query Analytics Dashboard**
for the sales page URL (`/3houronlinebusinessbuilder-page`), last 1–3 days
(Clarity's API only goes back about 3 days). Get: sessions, average scroll
depth %, dead clicks, rage clicks, share of sessions on mobile, and, if the
pop-up tracking code is live, the custom event `popup_open` (sessions with it =
`popup_openers`, total count = `popup_opens`). Write what you got to
`clarity.json` with those key names (`sessions`, `scroll_depth_pct`,
`dead_clicks`, `rage_clicks`, `mobile_share_pct`, `popup_openers`,
`popup_opens`). Leave out any key you couldn't get. If the connector isn't
there, skip this file and say so in the summary.

Note: Clarity covers fewer days than the 7-day window. Say "last N days" when
you mention Clarity numbers.

### 4. Crunch
```bash
python3 -I .claude/skills/funnel-pulse/crunch.py \
  --forms <forms file(s)> --orders <orders file> \
  --meta meta_7d.json --meta meta_today.json [--clarity clarity.json] \
  --start START --end END --label "<label>" --out $SCRATCH/run/out
```
It drops test orders and other products, counts each person once, and writes
`summary.json`, `funnel.json`, `daily.json`, `campaigns.json` and
`answers.json`.

### 5. Refresh the dashboard
1. `ArtifactData` `list` collection `datasets` on the dashboard URL. Note each
   document's `version` and its old `source.url`.
2. Upload each of the 5 files: `Artifact` publish with `url` = dashboard,
   `asset: true`, `file_path` = the file (one call per JSON file).
3. One `ArtifactData` `batch` of 5 `update`s, each pinned with `if_version`:
   `source: {kind: "file", url: "<new /_blob/ url>", name: "<id>.json", format: "json"}`,
   `updated: {at: <UTC ISO now>, by: "Funnel Pulse run (Meta Ads + GHL + Clarity)"}`,
   `edit: {via: "claude", at: <UTC ISO now>}`.
4. Delete each old blob (`Artifact` `action: "delete"`, `url` = dashboard,
   `path` = the old 32-character id), since nothing points at it any more.
Don't change `files/index.html` on a scheduled run.

### 6. Save a snapshot
Copy `summary.json` and `funnel.json` to
`reports/funnel-pulse/snapshots/YYYY-MM-DD-am/` (or `-pm`, by IST time before
or after 12:00). Compare with the newest earlier snapshot for the summary.
Commit and push.

### 7. The summary (final message, shows on the phone)
3–5 short lines, plain words, numbers with %:
- Sales vs ad spend, and ₹ back for every ₹1.
- The biggest drop in the funnel (step → step, % kept).
- Anything that changed a lot since the last snapshot.
- One thing to do today (for example: "2 people are stuck at checkout,
  ₹998. Send them a WhatsApp.").
- The dashboard link.

Run the `humanize-writing` skill on it before sending (CLAUDE.md rule).

## Health marks (a guide, not a rule)

For a ₹499 offer from cold Meta traffic: landing page views ÷ outbound clicks
≥ 75%, pop-up fills ÷ landing page views ≥ 15%, paid ÷ checkout ≥ 50%, bump ≥
20% of buyers, frequency < 3. Under ₹1 back per ₹1 is fine for a tripwire only
if the ₹30K–50K back-end offer makes up the gap, so say that and don't panic.

Also watch:
- **Switchers:** people who said "no skill", then changed their answer to get
  through. If many of them buy, the pop-up is a speed bump, not a sorter.
- **Meta vs GHL buyers:** a big gap means pixel or CAPI tracking is off.
- **Stuck at checkout:** unpaid orders with no later paid order. These are
  worth a WhatsApp follow-up.
