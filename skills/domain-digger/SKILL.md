---
name: domain-digger
description: Generate concise .com domain name ideas based on user intent and check availability. Use when the user wants to find available domain names, brainstorm domain ideas, or check if specific domains are registered. Triggers on phrases like "find me a domain", "domain name ideas", "check domain availability", "帮我找域名", "挖掘域名".
visibility: PRIVATE
---

# Domain Digger

Generate short, intuitive .com domain names and verify availability.

## Workflow

1. **Understand intent** — Ask what the domain is for (product, blog, startup, etc.) and preferred style if not specified
2. **Generate candidates** — Create 15-25 domain ideas using patterns below
3. **Check availability** — Run `scripts/check_domain.py` to verify .com availability
4. **Present results** — Show available domains first, organized by style

## Domain Generation Patterns

### Style 1: -ology / -ify suffixes (science + action)
Pattern: [root] + ology/ify → "study of" or "make into"

Examples: Buyology, Skillify, Mindology, Evolvify

### Style 2: Short compound (word + word)
Pattern: [3-5 letter word] + [3-5 letter word]

Examples: Mindflow, Selfspark, Coreloop, Nexushub

### Style 3: AI-era synthetic
Pattern: Tech-root + evocative ending

Common roots for AI/self-evolution themes:
- self, auto, meta, Evo, neo, pro
- mind, brain, core, node, sync
- spark, flow, pulse, wave, drift

Endings: -ly, -io, -ai, -ex, -ix, -os, -us

Examples: Selfio, Evoly, Metaly, Mindai, Synex

### Style 4: Minimalist (4-6 chars total)
Pattern: Abbreviated or creative spelling

Examples: Evo.com, Mndx.com, Skil.com (often taken, try variations)

## Running Availability Check

```bash
python3 scripts/check_domain.py domain1.com domain2.com domain3.com
```

Options:
- `--quick` — DNS-only check (faster, may have false positives)
- `--json` — JSON output

## Output Format

Present results grouped by availability:

```
✅ Available:
1. evoly.com — "evolution" + "ly", AI self-improvement vibe
2. mindology.com — study of mind, memorable
3. selfspark.com — ignite personal growth

❌ Taken (for reference):
- evolve.ai — premium, expected
- mindflow.com — popular wellness term
```

## Quality Filters

Before checking, filter candidates:
- **Length**: Prefer ≤10 characters
- **Pronounceability**: Must be sayable in 2-3 syllables
- **Clarity**: Meaning should be inferable from words
- **No hyphens/numbers**: Clean .com only

## Tips

- For "self-evolving AI" themes: focus on roots like `evo`, `self`, `meta`, `auto`, `grow`
- For tools/platforms: `hub`, `lab`, `base`, `core` work well as suffixes
- Avoid trademark-heavy terms (gpt, openai, etc.)
