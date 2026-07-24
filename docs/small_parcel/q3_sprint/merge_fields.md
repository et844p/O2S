# Q3 Sprint — Merge Fields & Conditional Blocks

Use Handlebars-style syntax for mail-merge. Conditional blocks are stripped entirely when the condition is false.

## Supplier identity

| Field | Description | Example |
|-------|-------------|---------|
| `{{Parent_Su_Name}}` | Parent supplier entity name | Acme Furniture Inc |
| `{{Parent_SUID}}` | Parent supplier ID | 12345 |
| `{{SuName}}` | Child warehouse name | Acme Furniture CA 92374 |
| `{{ChildSUID}}` | Child supplier ID | 67890 |
| `{{ChildSUName}}` | Alias for `{{SuName}}` | |
| `{{SRM_Name}}` | SRM contact | Jane Smith |
| `{{StationName}}` | FedEx station | WEST RIALTO |

## Performance metrics (L6W unless noted)

| Field | Description | Format |
|-------|-------------|--------|
| `{{IFR}}` | Baseline Induction Fill Rate | 87.3% |
| `{{L4W_IFR}}` | Last 4 weeks IFR (rolling) | 89.1% |
| `{{Label_By_7}}` | Baseline Label by 7 PM | 94.2% |
| `{{L4W_Label_By_7}}` | Last 4 weeks Label by 7 PM | 95.0% |
| `{{Wnd}}` | Fri/Sat orders shipped Sat/Sun | 73.4% |
| `{{Fri_Sat_Vol}}` | Fri/Sat order volume (L6W) | 342 |
| `{{Pct_One_Day_Late}}` | Share of late vol that is 1-day late | 62% |
| `{{Pct_Late_3Plus_Days}}` | Share of late vol 3+ days late | 18% |
| `{{Pct_Late_8AM_2PM}}` | Share of lates inducted next day 8 AM–2 PM | 24% |
| `{{Gap_Label_Induction_Pct}}` | % orders with > 1 day between label and induction | 15% |

## Settings (Stated cohorts — if applicable)

| Field | Description |
|-------|-------------|
| `{{Current_SP_LT}}` | Small parcel lead time (hours) |
| `{{Current_SP_Cutoff}}` | Cutoff time (local) |
| `{{L4W_Stated}}` | Avg calendar days order to MSBD |
| `{{O2I_Below_1_Bus_Days}}` | % inducted within 1 business day |

## Cohort metadata

| Field | Description |
|-------|-------------|
| `{{Cohort_ID}}` | Q3-A through Q3-F |
| `{{Cohort_Name}}` | Human-readable cohort name |
| `{{IFR_Sub_Cohort}}` | A, B, C, or D (late-pattern sub-code) |
| `{{Is_Constrained_Market}}` | 1 or 0 |
| `{{Is_Repeat_Target}}` | 1 if on Summer 2026 target list |
| `{{Action_Deadline}}` | August 21, 2026 |

## Conditional blocks

| Block | Include when |
|-------|--------------|
| `{{#IF_CONSTRAINED_MARKET}}...{{/IF_CONSTRAINED_MARKET}}` | `assigned_constrained_market = 1` |
| `{{#IF_NOT_CONSTRAINED_MARKET}}...{{/IF_NOT_CONSTRAINED_MARKET}}` | `assigned_constrained_market = 0` |
| `{{#IF_WEEKEND_SHIPPING}}...{{/IF_WEEKEND_SHIPPING}}` | Cohort is Q3-B, Q3-D, Q3-E, or Q3-F; or Q3-C + constrained |
| `{{#IF_NO_WEEKEND_SHIPPING}}...{{/IF_NO_WEEKEND_SHIPPING}}` | Cohort is Q3-A, or Q3-C non-constrained |
| `{{#IF_REPEAT_TARGET}}...{{/IF_REPEAT_TARGET}}` | `summer26_target = 1` |
| `{{#IF_L4W_IFR_BELOW_TARGET}}...{{/IF_L4W_IFR_BELOW_TARGET}}` | `L4W_IFR < 93%` despite baseline above |
| `{{#IF_SUB_COHORT_A}}...{{/IF_SUB_COHORT_A}}` | Late pickup 8 AM–2 PM pattern |
| `{{#IF_SUB_COHORT_B}}...{{/IF_SUB_COHORT_B}}` | 3+ day late pattern |
| `{{#IF_SUB_COHORT_C}}...{{/IF_SUB_COHORT_C}}` | Label compliance pattern |
| `{{#IF_SUB_COHORT_D}}...{{/IF_SUB_COHORT_D}}` | General handshake 1-day late |

## Subject line patterns

| Cohort | Subject |
|--------|---------|
| Q3-A – E | `ACTION REQUIRED: Q3 Dropship Performance Sprint — {{SuName}}` |
| Q3-F | `Action Required: Weekend Must-Ship-By-Date Opportunity — {{SuName}}` |

## Shared footer resources

All improvement cohorts (Q3-A through Q3-E) attach:

- Wayfair Small Parcel Dropship Guide
- Partner Home → Reports → Fulfillment Performance Diagnostics link
