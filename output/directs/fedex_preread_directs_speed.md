# FedEx Pre-Read: Directs & Customer Speed

**Meeting purpose:** FedEx is asking Wayfair to push more supplier directs. We want to pressure-test whether directs deliver the **customer speed** benefit we would need to justify that push.

**Ask of FedEx:** Help us understand where the expected O2D benefit is supposed to show up — and what would need to change operationally for directs to beat suppliers’ normal (local / SoCal) path on **O2D actual**.

**Owner / data:** Small Parcel HVE monitoring (`HVE_perf_Monitoring`), dropship only.  
**Primary window:** MSBD weeks May–Aug 2026; Memorial Day week `2026-05-24` = high-vol / constrained-origin stress; BAU = mid-Jun / mid-Jul weeks with mostly local fulfillment.

---

## 1. Bottom line (read this first)

1. **Directs shorten miles after induction** (often ~80–100 mi vs ~1,300–2,000 mi on local SoCal induct). The *routing* works.
2. **Directs do not reliably improve end-to-end customer speed (O2D actual).** On SoCal-assigned volume, directs are **~0.4d slower** than local. For suppliers who normally ship local and then directed in Memorial Day, directs were **~0.8d slower** than their own BAU local.
3. In the high-vol week itself, directs are only a **small mitigation vs same-week local** (−0.2d), not a win vs normal operations.
4. We **expect IFR to dip** when directing under constraint — that alone is not a reason to reject directs. The open question is **speed**.
5. Until we see a clear O2D actual win (or a jointly agreed network benefit that Wayfair values), **pushing suppliers harder on directs is hard to justify on customer-speed grounds.**

---

## 2. How we define a “direct” (so we are talking about the same thing)

**Candidate** (distance only):

1. Wrong hub vs assigned (`assignedhub_notequal_actualhub_flag = 1`)
2. Assigned hub ≥ 400 mi from customer
3. Assigned hub ≥ 200 mi from actual induction hub

**Exclusive buckets under candidate:**

| Bucket | Meaning |
|--------|---------|
| Misshipping | Parent has another WH in the induction state |
| Ghost warehouse | Persistent far hub (≥10% supplier vol, most weeks), no sibling WH |
| Jumbo | `direct_gain` &lt; 0.4 |
| **Direct** | Else (`direct_gain` ≥ 0.4) — this is the arm FedEx is pushing |

**Local / BAU path** in this pre-read = `non_candidate` (inducts as assigned / SoCal), same origin pool.

---

## 3. Where directs concentrate

~**40%** of classified directs originate from **West Coast** assigned hubs (almost all **CA**). Largest corridor: **West Coast → Midwest** (~8% of all directs).

SoCal assigned hubs are **~96% constrained origins** (`assigned_constrained_market = 1`). That is the right place to test “do directs help under constraint?”

| MSBD week | SoCal assigned vol | Rough direct share | Note |
|-----------|--------------------|--------------------|------|
| `2026-05-24` Memorial Day | ~255k | **High** (~136k rough / ~114k classified direct on constrained) | High-vol + directs spike; IFR dips |
| `2026-07-05` (post July 4) | ~228k | **Low** | High vol, mostly stayed local |
| BAU (e.g. `06-14`–`06-28`, `07-12`–`07-19`) | ~150–195k / wk | **Low** | Normal local fulfillment |

---

## 4. Core speed test — SoCal constrained origins

**Question:** For constrained SoCal origins, is O2D **actual** faster when suppliers build directs in a high-vol week vs (a) same-week local and (b) their own BAU local pattern?

### Table A — Period totals (constrained SoCal origin)

| Period | Path | Vol | IFR | Del rel | O2D stated | **O2D actual** | % O2D ≤5d | Mi after induction |
|--------|------|-----|-----|---------|------------|----------------|-----------|--------------------|
| Memorial Day — direct | Direct | 113,846 | 84.2% | 85.4% | 7.65 | **6.81** | 32.2% | ~82 |
| Memorial Day — local | Local | 85,134 | 84.7% | 85.9% | 7.99 | **7.01** | 50.7% | ~122 |
| BAU — local | Local | 755,445 | 90.2% | 86.6% | 6.90 | **5.99** | 46.8% | ~1,397 |
| July 5 — local (high vol, little directing) | Local | 202,191 | 88.7% | 84.7% | 7.05 | **6.20** | 44.5% | ~1,397 |

**Read of Table A**

| Compare | O2D actual Δ | Interpretation |
|---------|--------------|----------------|
| Memorial Day direct vs **same-week local** | **−0.21d** (direct faster) | Small same-week mitigation under stress |
| Memorial Day direct vs **BAU local** | **+0.82d** (direct slower) | Does not beat normal operations |
| Memorial Day local vs BAU local | **+1.02d** | Constraint / high-vol stress hurts local path |
| % ≤5d: direct vs local (Memorial Day) | 32% vs 51% | Directs less often hit fast actuals |

IFR dip on directs / high-vol is visible and **expected**; we are not using IFR as the pass/fail.

### Table B — Same suppliers, similar BAU fulfillment → then directed in Memorial Day

**Cohort:** ≥50 BAU local ops, ≤20% BAU direct share, ≥30 Memorial Day direct ops → **n = 738** suppliers.

| Metric | Result |
|--------|--------|
| Share faster than own BAU local (O2D actual) | **12.7%** (94 / 738) |
| Median O2D Δ (HV direct − BAU local) | **+0.77d** (slower) |
| Vol-weighted O2D Δ | **+0.79d** (slower) |
| Vol-weighted IFR Δ | **−7.3 pp** (dip expected) |

**Examples (high direct vol in Memorial Day)**

| Supplier | BAU local O2D act | HV direct O2D act | O2D Δ | BAU IFR → HV IFR |
|----------|-------------------|-------------------|-------|------------------|
| Devion Furniture | 7.70 | 8.86 | **+1.16** | 94% → 43% |
| Heze Starfire CA | 7.77 | 8.48 | **+0.71** | 82% → 74% |
| Aosom CA | 4.64 | 5.03 | **+0.39** | 100% → 99% |
| NFusion CA11 | 5.66 | 6.57 | **+0.91** | 84% → 82% |
| CP HomeDecor | 6.65 | 7.82 | **+1.17** | 95% → 62% |
| Kingston CA | 6.99 | 8.04 | **+1.05** | 98% → 88% |
| Safavieh CA | 3.94 | 4.86 | **+0.91** | 97% → 99% |
| CA2 (GigaCloud) | 6.31 | 6.03 | **−0.28** | 85% → 70% |

---

## 5. Broader SoCal assigned view (10w PDD) — same story

| Path | Vol | IFR | Del rel | O2D stated | **O2D actual** | % ≤5d | Mi after induction |
|------|-----|-----|---------|------------|----------------|-------|--------------------|
| Direct | 214,734 | 87.7% | 84.9% | 7.42 | **6.56** | 32.8% | ~98 |
| Local (non-candidate) | 1,532,453 | 89.5% | 85.8% | 7.00 | **6.14** | 47.0% | ~1,330 |

Direct is **+0.43d slower** on O2D actual despite ~**1,200 fewer miles** after induction.

---

## 6. Corridor check — West Coast → Midwest

Same Midwest customers; compare classified directs vs SoCal-induct non-directs.

| Period | Path | Vol | IFR | **O2D actual** | Mi after induction |
|--------|------|-----|-----|----------------|--------------------|
| Memorial Day | Midwest direct | 22,978 | 84.2% | **7.91** | ~68 |
| July 4 week | SoCal induct (non-direct) | 17,258 | 87.5% | **7.37** | ~2,000 |
| May–Aug all | Midwest direct | 72,354 | 88.1% | **7.43** | ~83 |
| May–Aug all | SoCal induct (non-direct) | 222,082 | 90.8% | **6.99** | ~1,995 |

July 4 SoCal long-haul to Midwest still beats Memorial Day directs on O2D actual (**7.37 vs 7.91**). Full-window: directs **+0.44d slower**.

---

## 7. Network context (not the speed case, but useful)

Last 10w PDD, DS — candidates are 13.7% of volume but slightly over-index on misses. Classified **direct** is ~7.5% of network:

| Bucket | % network | IFR | Del rel | Note |
|--------|-----------|-----|---------|------|
| Direct | 7.5% | 88.0% | 85.1% | Large; IFR ~−1 pp vs network |
| Jumbo | 2.5% | 83.2% | 77.5% | Weakest IFR |
| Ghost | 1.4% | 88.6% | 80.7% | Compliance / undeclared location |
| Misshipping | 2.3% | 86.8% | 74.0% | Worst del rel |
| Non-candidate | 86.3% | 89.4% | 86.1% | Baseline |

Speed case for “push more directs” is **not** supported by IFR/del alone either — but our primary objection is **O2D actual**.

---

## 8. What we think is happening

```text
Direct path:     [order] → longer / harder induction into far hub → short last mile → customer
Local path:      [order] → familiar SoCal induction → long linehaul → customer

Miles after scan:   Direct wins by a lot
Time to customer:   Local often still wins (induction friction > transit savings)
```

Directs look like a **FedEx network / last-mile / constrained-hub relief** play. They are **not** currently showing up as a **supplier → customer speed** win in HVE O2D actual.

---

## 9. Discussion questions for FedEx

1. **Where should we see the O2D benefit?** Same origin, same dest, O2D actual — if not there, what metric should Wayfair use to green-light a supplier push?
2. **Induction SLA on directs:** What scan-by / tender expectations exist when a supplier skips the assigned SoCal hub? Can FedEx commit to induction parity with local?
3. **When directs *do* help:** Are there lanes, package profiles, or days-of-week where FedEx expects O2D actual to beat local by ≥0.5d? We can validate those next.
4. **Constrained-origin relief vs customer speed:** If the value is hub relief (not O2D), can we quantify that jointly so Wayfair isn’t selling “faster delivery” to suppliers/customers?
5. **Operational failure modes:** Ghost hubs / address issues (e.g. persistent far CA annex) and misshipping muddy “direct” volume — how do we keep a clean directs program?

---

## 10. Proposed Wayfair position (for alignment)

- **Open to directs** where we can show O2D actual ≤ BAU local (or a jointly agreed network KPI).
- **Not ready to broadly push** suppliers on directs based on miles/`direct_gain` alone.
- **Next step:** Pick 1–2 pilot lanes + supplier set with FedEx; pre-commit success = O2D actual lift vs own BAU local in a high-vol week, with IFR dip tolerance agreed up front.

---

## Appendix — Definitions & sources

| Term | Definition |
|------|------------|
| O2D actual | Days order → delivery (`o2d_actual`) — primary speed metric |
| O2D stated | Promised O2D at order (`o2d_stated`) |
| IFR | `AVG(inducted_on_time_or_early)` — expected to dip under directs / peak |
| Del rel | Delivered on/before promise (`delivery_rel`) |
| Local | `non_candidate` on SoCal constrained assigned origin |
| Direct | Classified direct bucket (gain ≥ 0.4) |
| BAU weeks | `2026-06-14, 06-21, 06-28, 07-12, 07-19` |
| High-vol week | `2026-05-24` (Memorial Day) |
| Table | `` `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` `` |
| Scope | `fulfillment_type = 'DS'` |

**Detail artifacts (repo):**  
`output/directs/socal_constrained_directs_o2d_verdict.xlsx` · `wc_midwest_direct_vs_socal_compare.xlsx` · `socal_o2d_by_bucket.xlsx` · `fedex_meeting_network_bucket_summary.xlsx`
