# Delivered 3-week misship / ghost / other

Pull of DS volume by `delivery_date` for the last 3 weeks, classified into misshipping, ghost, and other (closer vs farther to customer than assigned hub).

## How to run

```bash
python3 scripts/run_delivered_3w_misship_ghost_other.py
```

SQL: `sql/delivered_3w_misship_ghost_other.sql`

## Outputs

| File | Contents |
|------|----------|
| `output/directs/delivered_3w_misship_ghost_other.csv` | Network bucket mix |
| `output/directs/delivered_3w_misship_ghost_other.md` | Summary writeup |
| `output/directs/delivered_3w_misship_ghost_other_by_sto.csv` | By STO |
| `output/directs/delivered_3w_misship_ghost_other_by_supplier.csv` | By supplier (vol≥50) |
| `output/directs/delivered_3w_misship_ghost_other_top_hubs.csv` | Top hubs per focus bucket |
