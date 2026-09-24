---
name: humanize-writing
description: Rewrite AI-drafted, human-facing text (Reels scripts, captions, emails, WhatsApp broadcasts, landing pages, docs) to remove tells of AI writing while keeping the meaning and the author's voice. Use this as a final pass on any human-facing copy before it ships — after brand-voice/de-slop drafting, not instead of it.
---

# Humanize Writing

A final editing pass that strips the structural and stylistic patterns that make
text read as machine-generated, without changing what it says. Run this **after**
a draft exists (brand voice, de-slop, or otherwise) and **before** it ships.

Sources: pattern taxonomy adapted from the `blader/humanizer` skill (MIT
licensed, github.com/blader/humanizer) and Wikipedia's "Signs of AI writing"
essay (en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).

## Method

1. Read the full text once before touching anything.
2. Mark every tell below, strongest first — a piece often has 2-3 dominant
   patterns doing most of the damage, not all 20+.
3. Rewrite to remove the tells while keeping every supported claim and the
   writer's actual voice (their sentence rhythm, their word choices, not a
   generic "human" voice).
4. Re-read once more for anything left over.

Do not just delete flagged phrases — rewrite the sentence so it still lands.

## Tells to catch

**A. Staging instead of stating** (strongest, most common)
- Negative parallelism / false contrast: "It's not a product launch. It's a
  paradigm shift." Say the thing directly.
- One-line dramatic closers tacked onto a paragraph for effect.
- Sayings or clichés dressed up as insight ("rich cultural heritage,"
  "enduring legacy," "in today's fast-paced world").

**B. Rhythm by rule**
- Forced rule-of-three: adjectives, benefits, or takeaways padded to exactly
  three items because it "sounds complete."
- Repeated sentence openings across a paragraph (anaphora used as a crutch,
  not a device).
- Em dash overkill — used for punchy emphasis where a comma or period would
  do the job.
- Stacked hedges/qualifiers that quietly weaken a claim ("could potentially
  help provide some support for").

**C. Inflation and borrowed authority**
- Overused vocabulary: "delve," "testament," "pivotal," "landscape,"
  "leverage," "foster," "underscore."
- Inflated significance: framing something as playing "a vital role," serving
  as "a testament," or leaving "a lasting impact" when it's just a fact.
- Vague appeals to authority: "studies show," "experts agree," "research
  suggests" with no actual source.

**D. Formatting by rule**
- Decorative bold that doesn't mark anything load-bearing.
- Bullet lists with bolded mini-headers used as a default structure rather
  than because the content needs it.
- Over-capitalized or title-cased headings for casual copy (Reels, DMs,
  WhatsApp).
- Unnecessary emojis used as bullet substitutes.

**E. Leftovers from chat and drafts**
- Chatbot wrappers: "I hope this helps!", "Let me know if you'd like me to
  adjust this."
- Disclaimers and hedges that don't belong in finished copy ("as an AI...",
  "it's important to note that...").
- Repeated or redundant headings restating what the section already says.

## Scope

This is a style pass, not a fact or strategy check — it doesn't replace
`de-slop` (which also checks facts, brand voice, and strategy) or
`pdotj-brand-voice` (which sets the actual voice this pass should preserve).
Use humanize-writing as the last filter: after the content is right and the
voice is right, strip what's left of the machine.
