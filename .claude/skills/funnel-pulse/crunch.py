#!/usr/bin/env python3
"""Crunch GHL pop-up submissions + GHL orders (+ optional Meta campaign rows)
into funnel numbers for the funnel-pulse skill.

Usage:
  python3 -I crunch.py --forms forms.json --orders orders.json [--meta meta.json]
                       [--since 2026-11-03T00:00] [--until 2026-11-04T00:00]

Each input is the raw JSON saved from the tool call. The GHL MCP wrapper
({"success":..,"data":{..}}) and the bare API body are both accepted. Several
pages can be passed by repeating the flag. --since/--until are UTC ISO prefixes
and filter on createdAt (the API date filter is day-level only).

Prints a JSON summary to stdout. Names/emails are never printed.
"""
import argparse
import collections
import json

# ---- Config: change here if the funnel changes ---------------------------
OWNER_EMAILS = {"prathameshjiwatode@gmail.com"}  # test orders, always excluded
POPUP_QUESTION_FIELD = "6e8IhdbRJNAroc684OOb"     # "how long have you had your skill"
QUALIFIED_ANSWERS = {"2 to 5 years", "more than 5 years"}  # lower-cased
BUMP_PRICE_HINT = 999  # main ₹499 + bump ₹999 = ₹1,498 order
# ---------------------------------------------------------------------------


def load(paths, key):
    rows = []
    for p in paths or []:
        d = json.load(open(p))
        if isinstance(d, dict) and "data" in d and isinstance(d["data"], dict) and key in d["data"]:
            d = d["data"]
        if isinstance(d, dict) and "data" in d and isinstance(d["data"], dict):
            d = d["data"]
        rows.extend(d[key] if isinstance(d, dict) else d)
    return rows


def norm(s):
    return (s or "").replace("’", "'").strip().lower()


def in_window(ts, since, until):
    return (not since or ts >= since) and (not until or ts < until)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forms", action="append")
    ap.add_argument("--orders", action="append")
    ap.add_argument("--meta", action="append")
    ap.add_argument("--since")
    ap.add_argument("--until")
    a = ap.parse_args()

    subs = [s for s in load(a.forms, "submissions")
            if norm(s.get("email")) not in OWNER_EMAILS and in_window(s["createdAt"], a.since, a.until)]
    orders = [o for o in load(a.orders, "data")
              if norm(o.get("contactEmail")) not in OWNER_EMAILS and o.get("liveMode", True)
              and in_window(o["createdAt"], a.since, a.until)]

    # ---- Pop-up: one row per person, in time order ------------------------
    people = collections.OrderedDict()
    for s in sorted(subs, key=lambda x: x["createdAt"]):
        o = s.get("others", {})
        ed = o.get("eventData", {}) or {}
        utm = ed.get("url_params") or {}
        p = people.setdefault(norm(s.get("email")), {"answers": [], "sources": [], "campaigns": []})
        p["answers"].append(norm(o.get(POPUP_QUESTION_FIELD)))
        p["sources"].append(ed.get("source"))
        p["campaigns"].append(ed.get("campaign") or utm.get("utm_campaign"))

    first_answer = collections.Counter(p["answers"][0] for p in people.values())
    all_answers = collections.Counter(x for p in people.values() for x in p["answers"])
    qualified_first_try = sum(1 for p in people.values() if p["answers"][0] in QUALIFIED_ANSWERS)
    ever_qualified = {e for e, p in people.items() if any(x in QUALIFIED_ANSWERS for x in p["answers"])}
    switched = {e for e, p in people.items()
                if p["answers"][0] not in QUALIFIED_ANSWERS and e in ever_qualified}
    never_qualified = set(people) - ever_qualified
    first_touch_campaign = collections.Counter(
        next((c for c in p["campaigns"] if c), "no UTM (direct/returning)") for p in people.values())

    # ---- Orders: grouped by funnel ----------------------------------------
    funnels = collections.defaultdict(lambda: {
        "checkout_people": set(), "paid_people": set(), "paid_orders": 0, "revenue": 0,
        "bump_orders": 0, "unpaid_people": set()})
    for o in orders:
        f = funnels[o.get("sourceName") or "unknown"]
        e = norm(o.get("contactEmail"))
        f["checkout_people"].add(e)
        if o.get("paymentStatus") == "paid":
            f["paid_people"].add(e)
            f["paid_orders"] += 1
            f["revenue"] += o.get("amount", 0)
            if (o.get("totalProducts") or 1) > 1 or o.get("amount", 0) >= BUMP_PRICE_HINT:
                f["bump_orders"] += 1
        else:
            f["unpaid_people"].add(e)
    funnel_out = {}
    for name, f in funnels.items():
        abandoned = f["unpaid_people"] - f["paid_people"]
        funnel_out[name] = {
            "people_reached_checkout": len(f["checkout_people"]),
            "people_paid": len(f["paid_people"]),
            "paid_orders": f["paid_orders"],
            "revenue_inr": f["revenue"],
            "bump_orders": f["bump_orders"],
            "bump_take_rate": round(f["bump_orders"] / f["paid_orders"], 2) if f["paid_orders"] else None,
            "abandoned_checkouts_open": len(abandoned),
            "abandoned_value_inr": None,  # filled below
        }
        funnel_out[name]["abandoned_value_inr"] = sum(
            o.get("amount", 0) for o in orders
            if (o.get("sourceName") or "unknown") == name and norm(o.get("contactEmail")) in abandoned
            and o.get("paymentStatus") != "paid") if abandoned else 0

    # Pop-up people who paid in any funnel (3HROBB pop-up → checkout link)
    all_paid = {norm(o.get("contactEmail")) for o in orders if o.get("paymentStatus") == "paid"}
    all_checkout = {norm(o.get("contactEmail")) for o in orders}

    out = {
        "window": {"since": a.since, "until": a.until},
        "popup": {
            "entries": len(subs),
            "unique_people": len(people),
            "qualified_first_try": qualified_first_try,
            "ever_qualified": len(ever_qualified),
            "disqualified_then_changed_answer": len(switched),
            "switchers_who_paid": len(switched & all_paid),
            "never_qualified": len(never_qualified),
            "first_answer_counts": dict(first_answer),
            "all_answer_counts": dict(all_answers),
            "first_touch_campaign": dict(first_touch_campaign),
            "popup_people_reached_checkout": len(set(people) & all_checkout),
            "popup_people_paid": len(set(people) & all_paid),
        },
        "funnels": funnel_out,
    }

    meta = load(a.meta, "ad_entities") if a.meta else []
    if meta and isinstance(meta, str):
        meta = json.loads(meta)
    if meta:
        def num(v):
            if isinstance(v, dict):
                v = v.get("value")
            try:
                return float(str(v).rstrip("%"))
            except (TypeError, ValueError):
                return 0.0
        out["meta"] = [{
            "campaign": r.get("name"),
            "spend_inr": num(r.get("amount_spent")),
            "link_clicks": num(r.get("link_click")),
            "landing_page_views": num(r.get("landing_page_view")),
            "meta_purchases": num(r.get("omni_purchase")),
            "ctr_pct": num(r.get("ctr")),
            "cpm_inr": num(r.get("cpm")),
            "cpc_inr": num(r.get("cost_per_link_click")),
            "frequency": num(r.get("frequency")),
        } for r in meta]
        out["meta_total_spend_inr"] = round(sum(r["spend_inr"] for r in out["meta"]), 2)

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
