# Network bucket summary — last 10 weeks PDD, DS

- **Network volume:** 7,728,808 ops
- **Candidate volume:** 1,061,480 (13.7% of network)
- **Network IFR:** 89.1% → ~841,599 late-order equivalents
- **Network delivery_rel:** 85.5% → ~1,124,411 delivery-miss equivalents
- Candidates are 13.7% of volume but **16.4%** of late orders and **17.6%** of delivery misses

## Attribution formulas

- Late orders = `vol × (1 − IFR)`
- Delivery misses = `vol × (1 − delivery_rel)`
- `% of all late/del misses` = bucket’s share of those network totals
- CTC-style impact = `(% network vol) × late_orders` (same shape as CTC)

| Bucket | Vol | % network | IFR | vs net (pp) | Late orders | % of all late | Del rel | vs net (pp) | Del misses | % of all del misses |
|--------|-----|-----------|-----|-------------|-------------|---------------|---------|-------------|---------|---------------------|
| direct | 581,541 | 7.5% | 88.0% | -1.1 | 69,597 | 8.3% | 85.1% | -0.4 | 86,723 | 7.7% |
| jumbo | 192,398 | 2.5% | 83.2% | -5.9 | 32,358 | 3.8% | 77.5% | -8.0 | 43,336 | 3.9% |
| ghost_warehouse | 106,954 | 1.4% | 88.6% | -0.5 | 12,150 | 1.4% | 80.7% | -4.7 | 20,616 | 1.8% |
| misshipping | 180,587 | 2.3% | 86.8% | -2.3 | 23,759 | 2.8% | 74.0% | -11.5 | 47,027 | 4.2% |
| non_candidate | 6,667,328 | 86.3% | 89.4% | +0.3 | 703,735 | 83.6% | 86.1% | +0.6 | 926,709 | 82.4% |

## Among candidates only

| Bucket | % cand vol | IFR | % cand late | Del rel | % cand del misses |
|--------|------------|-----|-------------|---------|-------------------|
| direct | 54.8% | 88.0% | 50.5% | 85.1% | 43.9% |
| jumbo | 18.1% | 83.2% | 23.5% | 77.5% | 21.9% |
| ghost_warehouse | 10.1% | 88.6% | 8.8% | 80.7% | 10.4% |
| misshipping | 17.0% | 86.8% | 17.2% | 74.0% | 23.8% |

## Meeting takeaways

1. **Jumbo** is the weakest IFR bucket at **83.2%** (-5.9 pp vs network) and weak del rel (**77.5%**).
2. **Misshipping** has the worst delivery_rel among candidate buckets (**74.0%**, -11.5 pp) — sibling-state shipping is hurting reliability more than IFR.
3. **Direct** is large (7.5% of network / 55% of candidates) with IFR **88.0%** — most candidate late orders sit here because of volume (50% of candidate lates).
4. **Ghost** is small (1.4% of network) with IFR near network (**88.6%**) but softer del rel (**80.7%**). Still a compliance/address issue more than an IFR sink.
5. Most misses are still **non_candidate** (84% of late orders) simply because it’s 86% of volume — candidates over-index slightly on misses relative to volume.