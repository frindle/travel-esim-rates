# Provider Summary

Provider-level facts that don't belong on any single country page (data policy, hotspot, activation/KYC, reputation).
Country pages carry the **rates**; this page carries the **traits**. All ✅ figures are tied to a fetched source (see [README](README.md#sources)).

| Provider | Pricing model | Data policy | Hotspot | Activation / KYC | Reputation (Trustpilot) | Notes |
|----------|---------------|-------------|---------|------------------|--------------------------|-------|
| **Airalo** | Per-GB capped + Eurolink unlimited Europe | Hard cap, top-up on existing eSIM, data expires at plan end; **14-day** refund (shortest) | ✅ all plans | Instant QR, smoothest iOS install, no ID | ~4.7 | 200+ countries — widest catalog |
| **Saily (NordVPN)** | Per-GB capped + unlimited (FUP) | Unlimited = 5 GB/day full speed then 1 Mbps (transparent); 30-day refund | ✅ all plans, no daily cap | Instant QR, no ID | ~4.4 | Resolves to strongest local carrier (Docomo/AIS/T-Mobile/TIM) |
| **Nomad** | Per-GB capped + some unlimited (Japan, HK) | Capped buckets, top-up, 30-day refund | ✅ all plans | Instant QR, app-based | ~4.2 | Best value/GB in APAC; smaller catalog |
| **Ubigi** | Per-GB capped + unlimited (FUP) + monthly/annual subscriptions | Reusable eSIM across destinations, global top-up, 30-day refund; Smartstart (plan starts on arrival) | ✅ all plans (data-only, no voice/SMS) | Reusable profile, no ID | ~4.0 | Full MVNO = cleaner routing; best for long stays / monthly billing |
| **Maya Mobile** | Global unlimited flat-rate tiers only | "Unlimited" w/ daily fair-use; install-once; 30-day refund (unactivated) | ✅ included, no advertised cap | One-time install, programmable start date, no ID | 4.6 (12k+ reviews) | 250+ partners / 165+ countries; newer track record |
| **Holafly** | Unlimited-only day-passes | FUP throttling (not hard-capped); **no top-up** — rebuy when expired | ⚠️ **many plans BLOCK hotspot** (esp. Europe/Asia) — #1 complaint | Instant QR, no ID | ~4.6 (91k+ reviews) | Largest review base; unlimited caveats + hotspot blocks |
| **aloSIM** | Per-GB capped + unlimited (2 GB/day FUP) | Top-up, 30-day refund | ✅ all plans | Instant QR, free intl number via Hushed | ~4.1 | AvailSim: actual catalog ~11 countries vs "200+" marketing claim |
| **Jetpac** | Per-GB capped + regional/global bundles + some unlimited (FUP) | Top-up on many plans; refund varies | ⚠️ varies by plan — check first | Instant QR (iOS+Android), no ID | ~4.7 (3,500+ reviews) | Free key-app access when data runs out; some regional coverage gaps; some "Unlimited/30d" prices seen far above other providers ($265+) — verify before buying |
| **GigSky** | Per-GB capped, some larger bundles | Top-up varies, refund policy varies | ❓ often unconfirmed — many country pages don't disclose | Instant QR, no ID | ~4.3 (6,600+ reviews; regional Trustpilot pages 4.1–4.3) | Country pages are frequently JS-rendered and don't return plan data on a plain fetch — confirm pricing directly on-site |
| **"HelloRoam"** ❓ | Per-GB only | Hard cap, top-up near-universal, 180-day refund | ✅ all plans | Instant QR, 63-language support | ~4.9 | ⚠️ **Unconfirmed provider name** — likely mis-named/aggregate eSIMRated listing; re-verify |
| **StaffTraveler** | Single flat global tier structure only (no per-country/per-region pricing) | Hard cap (100 MB–50 GB), no throttling before cap, top-up in-app, 365-day validity | ✅ all plans (explicit tethering support) | Instant QR/app activation, no verified account or ID required | ❓ not found (no Trustpilot page located; no refund policy stated on-site) | Airline-crew-focused; same 5 price tiers ($0.99–$119) confirmed identical across its Turkey/US/China/Europe pages and its own pricing page — 168+ country coverage on one SKU |

## Ranked picks (from the seed research)

- **(a) Cheapest for light data use:** budget per-GB providers (~$0.80–1.14/GB at the 10 GB tier per eSIMRated cheapest catalog).
- **(b) Best value, 1–2 week trip:** **Saily** — resolves to strong primary carriers, transparent 5 GB/day-then-1 Mbps FUP, hotspot on all plans.
- **(c) Heavy use / hotspot / global multi-country:** **Maya Mobile** (global unlimited, hotspot included) or **Nomad** (best value/GB with full hotspot).

## Avoid / caveats

- **Holafly** — "unlimited" is throttled and many plans block hotspot; no top-up. Read plan details.
- **aloSIM** — catalog far smaller than marketed; higher per-GB on capped plans.
- **"HelloRoam"** — treat as unverified until the provider identity is confirmed.
