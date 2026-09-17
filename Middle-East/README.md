# Middle East

Country rate pages for the Middle East region. Add a country by creating `Middle-East/<Country>.md`.

| Country | Page | Seeded rates? |
|---------|------|---------------|
| United Arab Emirates | [United-Arab-Emirates](United-Arab-Emirates.md) | ✅ 20 (19 ✅ / 1 ⚠️ / 1 ❓) |
| Israel | [Israel](Israel.md) | ✅ 17 (16 ✅ / 0 ⚠️ / 1 ❓) |
| Saudi Arabia | [Saudi-Arabia](Saudi-Arabia.md) | ✅ 19 (18 ✅ / 0 ⚠️ / 1 ❓) |
| Qatar | [Qatar](Qatar.md) | ✅ 18 (all ✅) |
| Turkey | [Turkey](Turkey.md) | ✅ 20 (all ✅) |
| Jordan | [Jordan](Jordan.md) | ✅ 13 (12 ✅ / 1 ⚠️) |
| Oman | [Oman](Oman.md) | ✅ 14 (all ✅) |
| Bahrain | [Bahrain](Bahrain.md) | ✅ 14 (all ✅) |
| Kuwait | [Kuwait](Kuwait.md) | ✅ 14 (all ✅) |

Seeded 2026-09-17 via direct provider-site fetches (Airalo, Saily, Nomad, Ubigi, Holafly, aloSIM, Maya
Mobile + local carriers where found). Jetpac and GigSky yielded no fetchable per-country pricing across
this region (site/JS-rendering issues) and were omitted rather than guessed. See the
[root README](../README.md) for the rate-row format and confidence legend, and [providers.md](../providers.md)
for provider-level traits/reputation.

## Regulatory notes (VoIP / eSIM quirks)

- **UAE**: WhatsApp/Skype voice & video calls are blocked by telecom regulation on all networks — data/eSIM messaging still works. See [United-Arab-Emirates.md](United-Arab-Emirates.md#notes).
- **Oman**: sourced but dated (2009-era) evidence of unauthorized-VoIP being treated as illegal; not confirmed as current for 2026 — see [Oman.md](Oman.md#notes).
- **Saudi Arabia**: historical VoIP restrictions were not verified this pass (search budget exhausted) — treat as unconfirmed, re-check before relying on it.
- **Turkey**: a claim that Turkey "banned" several eSIM providers (Nomad/Airalo/Saily) in July 2026 surfaced in secondary search summaries but could **not** be confirmed on any primary source fetched (eSIMRated's Turkey page only documents a 120-day IMEI-registration rule for long-stay devices, not a ban) — see [Turkey.md](Turkey.md#notes). Do not repeat the "ban" claim without a primary source.
- **Bahrain, Kuwait, Qatar, Israel, Jordan**: no sourced current VoIP/eSIM regulatory restrictions found in this research pass — absence of evidence, not confirmation of no restriction.
