# Travel eSIM Rates — Reference

A structured, expandable reference of travel eSIM plan rates, organized by **region → country**.
Each country folder holds a `README.md` page listing the rates we've seen for that destination.

## Structure

```
<Region>/            e.g. Asia, Europe, Americas
  <Country>/         e.g. Japan (a folder)
    README.md        the rate list for that country
Global/              provider-level global / multi-region plans (not country-specific)
providers.md         provider-level summary (pricing model, hotspot, KYC, reputation)
```

Example: Japan lives at [`Asia/Japan/README.md`](Asia/Japan/README.md).

## How to add a rate

Append a row to the country's rate table. Keep the columns consistent:

| Provider | Plan (data / duration) | Price (USD) | $/GB | Hotspot | Confidence | Source | Seen |
|----------|------------------------|-------------|------|---------|------------|--------|------|

- **$/GB** — only for capped plans; leave `—` for unlimited.
- Add a new country by creating `<Region>/<Country>/README.md` and linking it from the region index.

## Confidence legend

- ✅ **Sourced** — figure tied to a specific page that was actually read during research.
- ⚠️ **Approx / range** — an approximate or ranged figure ("~$15–25"), or a "from" price rather than an exact plan.
- ❓ **Unverified** — flagged during research as unconfirmed (e.g. the source text was truncated before the number). Recorded for follow-up, not to be trusted yet.

## Data provenance

Seed data comes from a 3-model local-model research bake-off (2026-09-17) on the question
"best travel eSIM by price & service." **Two arms produced real, source-cited answers** and both
used web search and self-corrected figures they couldn't confirm: `qwen3.8:27b` (control) and
`qwen3.6:35b-a3b`. The seeded rates below are drawn from the `qwen3.6:35b-a3b` answer; figures it
could not tie to a fetched page were flagged and are marked ❓ here. The third arm, `command-r`,
produced no usable data (a tool-arg schema mismatch stopped its web searches from executing).

> ⚠️ **Provider-name caveat:** the research surfaced a provider it called **"HelloRoam"** carrying
> eSIMRated's *cheapest-catalog* figures. "HelloRoam" is not a confirmed major provider — it is
> likely a mis-named or conflated entry (possibly the eSIMRated house/aggregate listing). Its
> figures are recorded under Global with this caveat and should be re-verified before relying on them.

## Sources

| Tag | URL |
|-----|-----|
| eSIMRated (cheapest) | https://esimrated.com/en/best-esim/cheapest |
| eSIMRated (best) | https://esimrated.com/en/best-esim |
| Travel Vient | https://travelvient.com/tools/esim/compare/airalo-vs-holafly-vs-nomad/ |
| eSIMTips — Saily | https://esimtips.com/providers/saily |
| eSIMTips — Ubigi | https://esimtips.com/providers/ubigi |
| Maya Mobile review | https://andreondigital.com/maya-mobile-review-2026/ |
| Holafly review (Reddit consensus) | https://www.yonosim.com/en/blog/holafly-esim-review-reddit-2026 |
| aloSIM (AvailSim) | https://www.availsim.com/provider/alosim |
| Jetpac review | https://www.thetraveler.org/jetpac-review-travel-esim-plans-tested-for-2026/ |

## Regions

- [Asia](Asia/README.md) — Japan, South Korea, Thailand, Vietnam
- [Europe](Europe/README.md) — Italy, France, Spain (+ Europe-wide regional plans)
- [Americas](Americas/README.md) — United States
- [Global / multi-region plans](Global/README.md)

## See also

- [providers.md](providers.md) — provider-level summary (data policy, hotspot, activation/KYC, reputation)
