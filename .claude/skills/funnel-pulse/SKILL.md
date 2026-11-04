---
name: funnel-pulse
description: Twice-a-day funnel check for pdotj.co paid funnels. Pulls Meta Ads (spend, clicks, landing page views), Microsoft Clarity (sessions, scroll, dead/rage clicks, via Windsor), and GoHighLevel (qualifying pop-up answers, checkout orders, order bumps, abandoned checkouts), then explains in plain words where people drop off and what to do next. Use when asked "how's the funnel", "how are the ads doing", "run funnel pulse", or on the 9 am / 5 pm schedule.
---

# Funnel Pulse

Prathamesh's paid funnel has 4 steps. This skill counts people at each step,
finds the biggest leak, and says what to fix. Write the report at a 3rd-grade
reading level: short sentences, simple words, friendly tone. Numbers first,
then what they mean.

```
Meta ad ─► Sales page ─► Qualifying pop-up ─► Checkout (+ order bump) ─► Paid
 (Meta)    (Clarity)      (GHL "3hr Form")     (GHL orders)              (GHL)
```

## Fixed IDs (update here if the funnel changes)

| Thing | Value |
|---|---|
| Meta ad account | `574387113125115` ("pdotj", INR) |
| GHL location | `7rxmDgEXJMsPErojoFfx` |
| Pop-up form (3HROBB) | `CyZmHqBkl6Ui6hqlgNCc` ("3hr Form") on `/3houronlinebusinessbuilder-page` |
| Pop-up question field | `6e8IhdbRJNAroc684OOb` |
| Qualified answers | "2 to 5 years", "More than 5 years" → go to checkout |
| Disqualified answers | "Less than 2 Years", "I don't have a skill yet" |
| 3HROBB funnel | `GtYMbm8TlxDQY8bhVJGR`, checkout `/3hr-cp`, ₹499 main, ₹1,498 with bump |
| PES funnel | `HqPJjmagGiB5mvWuSGrH`, checkout `pdotj.co/pes` |
| Test orders to skip | `prathameshjiwatode@gmail.com` |
| Time zone | Asia/Kolkata (IST) |

Campaign → product match uses the campaign name: `3HROBB` = 3-Hour Online
Business Builder, `2OB` = Two-Offer Business Blueprint, `PES` = PES coaching.

## Time windows

- **Morning run (before ~12:00 IST):** "Yesterday" (full day) + "Last 7 days".
- **Evening run (after ~12:00 IST):** "Today so far" + "Last 7 days".

GHL dates are day-level; pass the day range to the API, then pass exact
`--since/--until` (UTC) to `crunch.py`. IST = UTC + 5:30, so IST midnight
on day D is `D-1T18:30` UTC.

## Steps

### 1. Meta Ads (Meta_Ads MCP)
`ads_get_ad_entities` on account `574387113125115`, `level=campaign`, filter
`amount_spent > 0`, once for the short window (`yesterday` or `today`) and
once for `last_7d`. Fields:
`id, name, amount_spent, impressions, cpm, ctr, link_click, cost_per_link_click, landing_page_view, lead, omni_initiated_checkout, omni_purchase, omni_purchase_values, frequency`.
Set `scheduled_task_run=true` when running from the schedule. Save each
result's JSON to the scratchpad (for example `meta_7d.json`).

If an ad set or ad needs a closer look (for example one campaign has high
spend and no sales), go one level down for that campaign only.

### 2. GHL pop-up + orders (GoHighlevel MCP)
- `get-forms-submissions` with `formId=CyZmHqBkl6Ui6hqlgNCc`, `limit=100`,
  `startAt`/`endAt` as `YYYY-MM-DD`. The result is big and gets saved to a
  file. Use that file path, don't read it by hand. Follow `meta.nextPage`.
- `list-orders` with `altType=location`, `altId=7rxmDgEXJMsPErojoFfx`,
  `limit=100`, same dates. Save the JSON to a file.

### 3. Microsoft Clarity (Windsor MCP, connector `microsoft_clarity`)
Run `get_connectors`. If `microsoft_clarity` has no account, say in the report:
"Clarity is not connected yet, so I can't see what people do on the sales
page." Then skip this step. If it is connected: `get_fields` first, then
`get_data` for the last 1–3 days (Clarity only keeps about 3 days in its API).
Pull per-URL for the sales page and the checkout page: sessions, scroll depth,
time on page, dead clicks, rage clicks, quickbacks, and device split.
Mobile vs desktop matters most, since almost all Meta traffic is mobile.

### 4. Crunch
```bash
python3 -I .claude/skills/funnel-pulse/crunch.py \
  --forms <forms file> --orders <orders file> --meta <meta_7d file> \
  --since <UTC ISO> --until <UTC ISO>
```
Run it once per window. It removes test orders, removes duplicate people, and
counts people who changed their pop-up answer to get through.

### 5. Work out the funnel (per product, mostly 3HROBB)

| Step | Number | Rate to show |
|---|---|---|
| Ad spend | Meta `amount_spent` | — |
| Clicks | Meta `link_click` | CTR, CPC |
| Sales page views | Meta `landing_page_view` (Clarity sessions if connected) | LPV ÷ clicks |
| Pop-up filled | crunch `unique_people` | ÷ page views |
| Qualified | crunch `ever_qualified` (and `qualified_first_try`) | ÷ pop-up |
| Reached checkout | crunch funnel `people_reached_checkout` | ÷ qualified |
| Paid | crunch funnel `people_paid` | ÷ checkout |
| Order bump | `bump_orders` | ÷ paid |
| Revenue | `revenue_inr` | ROAS = revenue ÷ spend, cost per sale = spend ÷ paid |

Rough health marks for a ₹499 offer from cold Meta traffic (use as a guide,
not a rule): CTR (all) ≥ 1.5%, LPV ÷ clicks ≥ 75%, pop-up ÷ LPV ≥ 15%,
paid ÷ checkout ≥ 50%, bump take ≥ 20%, frequency < 3. Front-end ROAS under
1 is normal for a tripwire only if the ₹30K–50K back-end offer catches up, so
say that out loud and don't panic over it.

Also check:
- **Answer-switchers:** people who were disqualified and then changed their
  answer. If many of them buy, the pop-up is just a speed bump, not a filter.
- **Meta vs GHL sales gap:** Meta purchases vs GHL paid orders. A big gap
  means tracking is off (pixel/CAPI), and Meta is optimizing on bad data.
- **No-UTM entries:** people coming back without UTMs ("Direct traffic").
  Normal for returning visitors, but it hides which ad brought them.
- **Abandoned checkouts:** unpaid orders with no later paid order. Count and
  ₹ value. These people are worth a WhatsApp or email follow-up.

### 6. Write the report
Save to `reports/funnel-pulse/YYYY-MM-DD-am.md` (or `-pm.md`). Layout:

1. **The short version.** 3–5 lines: money in, money out, the one biggest
   leak, the one thing to do today.
2. **Funnel table.** The step table above, short window and 7-day side by side.
3. **Ads.** One line per campaign: spend, clicks, sales (GHL), cost per sale,
   and a simple verdict (keep / watch / pause-worthy). Never pause or change
   anything yourself. Only suggest.
4. **Sales page (Clarity).** Scroll depth, dead/rage clicks, mobile vs desktop.
5. **Pop-up.** Answers, switchers, how many disqualified people still bought.
6. **Checkout.** Paid vs abandoned, bump take rate, ₹ left on the table.
7. **What changed since last run.** Compare with the newest file in
   `reports/funnel-pulse/`.
8. **To do.** 1–3 actions, most important first.

No customer names, emails, or phone numbers in the report. Use counts only.

Per CLAUDE.md, run the `humanize-writing` skill on the report as a final pass
before saving it.

### 7. Ship it
Commit the report and push (see the scheduled prompt for the branch). End the
session with the "short version" as the final message so the phone
notification shows it.
