#!/usr/bin/env python3
"""Turn raw Meta + GHL tool answers into the 3HROBB Funnel Pulse numbers.

Usage:
  python3 -I crunch.py --forms F.json [--forms F2.json] --orders O.json \
      --meta M.json [--meta M2.json] [--clarity C.json] \
      --start 2026-10-28 --end 2026-11-04 --label "28 Oct - 4 Nov (to 10:15 IST)" \
      --out DIR

Inputs are the tool answers saved as files (the GHL MCP wrapper or the bare API
body are both fine; repeat a flag for more pages). Meta files are
ads_get_ad_entities answers at level=campaign with time_increment="1" so each
row has date_start. --start/--end are IST calendar days, both included.

Writes summary.json, funnel.json, daily.json, campaigns.json, answers.json to
--out (the dashboard's data files) and prints summary.json. No names, emails or
phone numbers ever leave this script.
"""
import argparse
import collections
import datetime as dt
import json
import os

# ---- Config: change here if the funnel changes ---------------------------
OWNER_EMAILS = {"prathameshjiwatode@gmail.com"}      # test orders/entries, always skipped
FUNNEL_ID = "GtYMbm8TlxDQY8bhVJGR"                    # 1. 3HROBB: DP Funnel
CAMPAIGN_MATCH = "3HROBB"                              # only Meta campaigns with this in the name
POPUP_FIELD = "6e8IhdbRJNAroc684OOb"                   # "how long have you had your skill"
NO_SKILL_ANSWERS = {"i don't have a skill yet"}        # every other answer = has a skill
ANSWER_ORDER = ["More than 5 years", "2 to 5 years", "Less than 2 years", "I don't have a skill yet"]
BUMP_MIN_AMOUNT = 999                                  # ₹499 main, ₹1,498 with bump
IST = dt.timedelta(hours=5, minutes=30)
# ---------------------------------------------------------------------------


def unwrap(d, key):
    for _ in range(4):
        if isinstance(d, dict) and isinstance(d.get(key), (list, str)):
            v = d[key]
            return json.loads(v) if isinstance(v, str) else v
        if isinstance(d, dict) and "data" in d:
            d = d["data"]
    return d if isinstance(d, list) else []


def load(paths, key):
    rows = []
    for p in paths or []:
        rows.extend(unwrap(json.load(open(p)), key))
    return rows


def norm(s):
    return (s or "").replace("’", "'").strip().lower()


def ist_day(iso):
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (t + IST).date().isoformat()


def num(v):
    if isinstance(v, dict):
        v = v.get("value")
    try:
        return float(str(v).rstrip("%"))
    except (TypeError, ValueError):
        return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forms", action="append", default=[])
    ap.add_argument("--orders", action="append", default=[])
    ap.add_argument("--meta", action="append", default=[])
    ap.add_argument("--clarity", help="optional JSON: {\"sessions\":n, \"popup_opens\":n, \"popup_openers\":n, \"scroll_depth_pct\":n, \"dead_clicks\":n, \"rage_clicks\":n, \"mobile_share_pct\":n}")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    days = []
    d = dt.date.fromisoformat(a.start)
    while d <= dt.date.fromisoformat(a.end):
        days.append(d.isoformat())
        d += dt.timedelta(days=1)
    inside = set(days)

    # ---- Meta ------------------------------------------------------------
    seen = set()
    meta = []
    for r in load(a.meta, "ad_entities"):
        if CAMPAIGN_MATCH.lower() not in (r.get("name") or "").lower():
            continue
        key = (r.get("id"), r.get("date_start"))
        if key in seen or r.get("date_start") not in inside:
            continue
        seen.add(key)
        meta.append(r)

    # ---- GHL pop-up --------------------------------------------------------
    people = {}
    entries_by_answer = collections.Counter()
    for s in sorted(load(a.forms, "submissions"), key=lambda x: x["createdAt"]):
        e = norm(s.get("email"))
        if e in OWNER_EMAILS or ist_day(s["createdAt"]) not in inside:
            continue
        o = s.get("others", {})
        ed = o.get("eventData") or {}
        ans = (o.get(POPUP_FIELD) or "").replace("’", "'").strip()
        entries_by_answer[norm(ans)] += 1
        p = people.setdefault(e, {"day": ist_day(s["createdAt"]), "answers": [], "campaign": None})
        p["answers"].append(norm(ans))
        p["campaign"] = p["campaign"] or ed.get("campaign") or (ed.get("url_params") or {}).get("utm_campaign")

    def has_skill(x):
        return x not in NO_SKILL_ANSWERS

    # ---- GHL orders (3HROBB funnel only) -----------------------------------
    orders = [o for o in load(a.orders, "data")
              if o.get("sourceId") == FUNNEL_ID and norm(o.get("contactEmail")) not in OWNER_EMAILS
              and o.get("liveMode", True) and ist_day(o["createdAt"]) in inside]
    checkout, paid, unpaid = set(), {}, collections.defaultdict(int)
    bump_orders = revenue = 0
    paid_by_day = collections.Counter()
    revenue_by_day = collections.Counter()
    for o in orders:
        e = norm(o.get("contactEmail"))
        checkout.add(e)
        if o.get("paymentStatus") == "paid":
            paid[e] = paid.get(e, 0) + 1
            revenue += o.get("amount", 0)
            paid_by_day[ist_day(o["createdAt"])] += 1
            revenue_by_day[ist_day(o["createdAt"])] += o.get("amount", 0)
            if (o.get("totalProducts") or 1) > 1 or o.get("amount", 0) >= BUMP_MIN_AMOUNT:
                bump_orders += 1
        else:
            unpaid[e] = max(unpaid[e], o.get("amount", 0))
    abandoned = {e: v for e, v in unpaid.items() if e not in paid}
    paid_orders = sum(paid.values())

    skill_people = {e for e, p in people.items() if any(has_skill(x) for x in p["answers"])}
    skill_first = {e for e, p in people.items() if has_skill(p["answers"][0])}
    switchers = skill_people - skill_first
    blocked = set(people) - skill_people

    # ---- Clarity (optional) -------------------------------------------------
    clarity = json.load(open(a.clarity)) if a.clarity else {}

    spend = sum(num(r.get("amount_spent")) for r in meta)
    impressions = sum(num(r.get("impressions")) for r in meta)
    clicks = sum(num(r.get("outbound_clicks")) for r in meta)
    lpv = sum(num(r.get("landing_page_view")) for r in meta)
    meta_purchases = sum(num(r.get("omni_purchase")) for r in meta)
    now = dt.datetime.now(dt.timezone.utc)

    summary = [{
        "window": a.label,
        "updated_ist": (now + IST).strftime("%-d %b, %-I:%M %p IST"),
        "spend": round(spend, 2),
        "revenue": revenue,
        "paid_people": len(paid),
        "paid_orders": paid_orders,
        "meta_purchases": int(meta_purchases),
        "abandoned_people": len(abandoned),
        "abandoned_value": sum(abandoned.values()),
        "bump_orders": bump_orders,
        "popup_people": len(people),
        "popup_entries": sum(entries_by_answer.values()),
        "skill_first_try": len(skill_first),
        "switched_to_skill": len(switchers),
        "switchers_paid": len(switchers & set(paid)),
        "no_skill_blocked": len(blocked),
        "popup_opens": clarity.get("popup_opens"),
        "popup_openers": clarity.get("popup_openers"),
        "clarity_sessions": clarity.get("sessions"),
        "scroll_depth_pct": clarity.get("scroll_depth_pct"),
        "dead_clicks": clarity.get("dead_clicks"),
        "rage_clicks": clarity.get("rage_clicks"),
        "mobile_share_pct": clarity.get("mobile_share_pct"),
    }]

    funnel = [
        {"order": 1, "step": "Outbound clicks", "people": int(clicks), "source": "Meta"},
        {"order": 2, "step": "Landing page views", "people": int(lpv), "source": "Meta"},
        {"order": 3, "step": "Opened the pop-up", "people": clarity.get("popup_openers"), "source": "Clarity"},
        {"order": 4, "step": "Filled the pop-up", "people": len(people), "source": "GHL"},
        {"order": 5, "step": "Said they have a skill", "people": len(skill_people), "source": "GHL"},
        {"order": 6, "step": "Reached checkout", "people": len(checkout), "source": "GHL"},
        {"order": 7, "step": "Paid", "people": len(paid), "source": "GHL"},
        {"order": 8, "step": "Took the order bump", "people": bump_orders, "source": "GHL"},
    ]

    by_day = collections.defaultdict(lambda: {"spend": 0.0, "clicks": 0, "lpv": 0})
    for r in meta:
        b = by_day[r["date_start"]]
        b["spend"] += num(r.get("amount_spent"))
        b["clicks"] += int(num(r.get("outbound_clicks")))
        b["lpv"] += int(num(r.get("landing_page_view")))
    popup_by_day = collections.Counter(p["day"] for p in people.values())
    daily = [{"day": d_, "spend": round(by_day[d_]["spend"], 2), "clicks": by_day[d_]["clicks"],
              "lpv": by_day[d_]["lpv"], "popup_people": popup_by_day[d_],
              "paid": paid_by_day[d_], "revenue": revenue_by_day[d_]} for d_ in days]

    camp = collections.defaultdict(lambda: {"spend": 0.0, "impressions": 0, "clicks": 0, "lpv": 0, "meta_purchases": 0})
    for r in meta:
        c = camp[r.get("name")]
        c["spend"] += num(r.get("amount_spent"))
        c["impressions"] += int(num(r.get("impressions")))
        c["clicks"] += int(num(r.get("outbound_clicks")))
        c["lpv"] += int(num(r.get("landing_page_view")))
        c["meta_purchases"] += int(num(r.get("omni_purchase")))
    camp_people = collections.Counter(p["campaign"] or "No ad tag (came back later)" for p in people.values())
    camp_paid = collections.Counter(people[e]["campaign"] or "No ad tag (came back later)" for e in paid if e in people)
    names = sorted(set(camp) | set(camp_people), key=lambda n: -camp[n]["spend"] if n in camp else 1)
    campaigns = [{"campaign": n, "spend": round(camp[n]["spend"], 2) if n in camp else 0,
                  "impressions": camp[n]["impressions"] if n in camp else 0,
                  "clicks": camp[n]["clicks"] if n in camp else 0,
                  "lpv": camp[n]["lpv"] if n in camp else 0,
                  "meta_purchases": camp[n]["meta_purchases"] if n in camp else 0,
                  "popup_people": camp_people[n], "paid": camp_paid[n]} for n in names]

    first = collections.Counter(p["answers"][0] for p in people.values())
    answers = [{"answer": ans, "skill": "No skill yet" if norm(ans) in NO_SKILL_ANSWERS else "Has a skill",
                "first_answer_people": first[norm(ans)], "all_entries": entries_by_answer[norm(ans)]}
               for ans in ANSWER_ORDER]

    os.makedirs(a.out, exist_ok=True)
    for name, rows in [("summary", summary), ("funnel", funnel), ("daily", daily),
                       ("campaigns", campaigns), ("answers", answers)]:
        with open(os.path.join(a.out, name + ".json"), "w") as f:
            json.dump(rows, f, indent=1, ensure_ascii=False)
    print(json.dumps(summary[0], indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
