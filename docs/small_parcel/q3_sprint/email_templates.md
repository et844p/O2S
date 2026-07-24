# Q3 Sprint — Supplier Email Templates

All improvement emails (Q3-A through Q3-E) use subject:

**`ACTION REQUIRED: Q3 Dropship Performance Sprint — {{SuName}}`**

Q3-F uses:

**`Action Required: Weekend Must-Ship-By-Date Opportunity — {{SuName}}`**

Action deadline for all improvement cohorts: **August 21, 2026**.

---

## Q3-A — Operational Issues

**Criteria:** IFR < 70% AND Label by 7 PM < 80%

**Weekend shipping:** No

---

Dear {{Parent_Su_Name}},

We are reaching out because your recent performance has fallen below our Induction Fill Rate (IFR) target of 93%. Please review your performance for the following warehouse:

**{{ChildSUID}} – {{SuName}}**

{{#IF_REPEAT_TARGET}}
We previously partnered on performance improvement during our Summer 2026 sprint. While some progress may have been made, your warehouse remains below target and requires a focused action plan before peak.
{{/IF_REPEAT_TARGET}}

### Performance summary

| Metric | Target | Baseline (L6W) | L4W |
|--------|--------|----------------|-----|
| Induction Fill Rate | 93% | {{IFR}} | {{L4W_IFR}} |
| Label by 7 PM | 97% | {{Label_By_7}} | {{L4W_Label_By_7}} |

### Metric definitions

- **Induction Fill Rate:** % of orders shipped and inducted at the local FedEx hub on or before the Must Ship By Date (MSBD)
- **Label by 7 PM:** % of orders with labels printed on or before the MSBD by 7 PM

### What we need from you

By **{{Action_Deadline}}**, please connect with your Supplier Relationship Manager ({{SRM_Name}}) to review issues contributing to shipping delays (e.g., processing disruptions, capacity constraints, carrier pickup issues).

To support this discussion:

- Review order-level data in **Partner Home → Reports → Fulfillment Performance Diagnostics**
- Share any known root causes impacting performance and come prepared with actions you are taking to improve
- Align with your local FedEx contact to ensure timely shipping and induction of Wayfair orders. If you do not have a FedEx contact, please reach out to your SRM.

### Additional insights on your performance

We've observed that not all labels are being printed by the Must Ship By Date (MSBD). For an order to ship on time, the label must be printed on or before the MSBD.

To help guide your review, please consider the following questions and provide context where applicable:

**Warehouse execution**

- How many times per day are orders being printed and labeled?
- Does this cadence align with your FedEx pickup schedule?
  - Example: If a pickup is scheduled for 4 PM, orders labeled at 6 PM would not make that trailer
- Is there a defined internal cutoff time?
  - Example: All orders placed before 11 AM will be labeled that day
- Are orders with an MSBD of the current day being prioritized for label printing?
- Do you have context on why labels are being printed late (e.g., picking, packing, staging delays)?
- Are there system or operational constraints preventing earlier label generation?
- Is there a backlog of orders carrying over day to day that is impacting performance?
  - If yes, please contact FedEx immediately to request additional capacity and ensure those orders are picked up

**Expectation:** Orders with an MSBD of the current day should have labels printed by 7 PM at the latest and be loaded onto earlier trailers (if multiple pickups occur), ensuring same-day induction.

**Next steps**

- What actions will you take to ensure labels are printed on time and orders are inducted on time?
- How can your SRM support you in this process?

### Why this matters

Improving your Induction Fill Rate will help prevent order delays and enhance the overall customer experience. It will also enable us to offer faster and more reliable delivery promises on-site, ultimately contributing to a higher badging rate.

We look forward to your continued collaboration with your SRM and engagement in regular performance reviews to drive meaningful improvements in your Dropship Fulfillment performance.

Best,
Wayfair

---

## Q3-B — Reliability: Forecasting & Constrained Markets

**Criteria:** IFR < 70%, Label by 7 PM ≥ 80%, 1-day late share > 60% of lates

**Weekend shipping:** Yes (all suppliers)

---

Dear {{Parent_Su_Name}},

We are reaching out because your recent performance has fallen below our Induction Fill Rate (IFR) target of 93%. Please review your performance for the following warehouse:

**{{ChildSUID}} – {{SuName}}**

{{#IF_REPEAT_TARGET}}
We previously partnered on performance improvement during our Summer 2026 sprint. Your warehouse remains below target and requires a renewed action plan focused on FedEx coordination and induction timing.
{{/IF_REPEAT_TARGET}}

### Performance summary

| Metric | Target | Baseline (L6W) | L4W |
|--------|--------|----------------|-----|
| Induction Fill Rate | 93% | {{IFR}} | {{L4W_IFR}} |
| Label by 7 PM | 97% | {{Label_By_7}} | {{L4W_Label_By_7}} |
| 1-day late share (of late vol) | — | {{Pct_One_Day_Late}} | — |

### What we need from you

By **{{Action_Deadline}}**, please connect with your SRM ({{SRM_Name}}) to review issues contributing to shipping delays and develop a plan to improve induction timing with FedEx.

### Additional insights on your performance

We've observed that a significant portion of late volume is being inducted one day late (typically between 8 AM–2 PM the following day), often due to handshake issues with FedEx or late trailer pickups.

{{#IF_CONSTRAINED_MARKET}}
**Constrained market context:** Your warehouse inducts into a capacity-constrained FedEx market. As peak approaches, these markets have limited ability to add ad hoc trailers and guarantee on-time inductions (before 8 AM next day). Accurate forecasting and agreed induction cutoffs with your FedEx representative are especially critical.
{{/IF_CONSTRAINED_MARKET}}

To help guide your review, please consider the following questions:

**Trailer pickup & induction timing**

- How can trailer pickups be optimized to ensure same-day induction?
- Have you aligned with FedEx on expectations for same-day induction?
  - FedEx guidance: trailers picked up before 5–7 PM are typically inducted same day
- **What is FedEx's cutoff time for same-day induction after pickup?**
- **What is the latest that FedEx will pick up a trailer and induct same day, or next day by 8 AM?**

**Forecasting & volume planning**

- Is volume being accurately forecasted and shared with FedEx?
- Are you receiving Wayfair's weekly/biweekly forecasts?
  - If not, please contact your SRM or update contacts in Partner Home
- Is your Wayfair volume being consolidated with your total volume when planning with FedEx?

**Carrier performance & escalations**

- Are trailers being picked up and unloaded on time?
- If not, what escalations have been raised with FedEx?
  - Please include examples, along with your FedEx account number (not Wayfair's) and relevant tracking numbers
  - Your SRM can assist with escalation if needed

{{#IF_WEEKEND_SHIPPING}}
### Weekend shipping opportunity

Our data shows you are currently shipping **{{Wnd}}** of orders placed on Friday and Saturday over the weekend. As peak approaches, weekend shipping can help spread volume and protect induction performance.

Please share:

- Whether you can sustain or increase weekend shipping through Q3 peak
- Any operational constraints on Saturday or Sunday fulfillment
- How weekend volume is included in your FedEx forecast
{{/IF_WEEKEND_SHIPPING}}

**Next steps**

- What actions will you take to ensure orders are inducted on time?
- How can your SRM support you in this process?

Best,
Wayfair

---

## Q3-C — Reliability: FIFO & Handshake

**Criteria:** IFR < 70%, Label by 7 PM ≥ 80%, 1-day late share ≤ 60% of lates (or label-to-induction gap > 1 day)

**Weekend shipping:** Constrained markets only

---

Dear {{Parent_Su_Name}},

We are reaching out because your recent performance has fallen below our Induction Fill Rate (IFR) target of 93%. Please review your performance for the following warehouse:

**{{ChildSUID}} – {{SuName}}**

{{#IF_REPEAT_TARGET}}
We previously partnered on performance improvement during our Summer 2026 sprint. Your warehouse remains below target and requires focused attention on warehouse execution and FedEx handshake.
{{/IF_REPEAT_TARGET}}

### Performance summary

| Metric | Target | Baseline (L6W) | L4W |
|--------|--------|----------------|-----|
| Induction Fill Rate | 93% | {{IFR}} | {{L4W_IFR}} |
| Label by 7 PM | 97% | {{Label_By_7}} | {{L4W_Label_By_7}} |
| Label-to-induction gap > 1 day | — | {{Gap_Label_Induction_Pct}} | — |

### What we need from you

By **{{Action_Deadline}}**, please connect with your SRM ({{SRM_Name}}) to review dock execution, FIFO practices, and FedEx handshake issues.

### Additional insights on your performance

We've observed that a significant portion of late volume is being inducted one day late. This is typically driven by either a handshake issue with FedEx or volume shipping one day later than expected. In some cases, labels are printed on time but induction occurs more than one calendar day later.

To help guide your review, please consider the following questions:

**Trailer pickup & induction timing**

- How can trailer pickups be optimized to ensure same-day induction?
- Have you aligned with FedEx on expectations for same-day induction?
  - FedEx guidance: trailers picked up before 5–7 PM are typically inducted same day
- What is FedEx's cutoff time for same-day induction after pickup?

**Warehouse execution & prioritization**

- Is the dock being fully cleared each day?
- Are there operational constraints impacting same-day processing?
- Is Wayfair volume being prioritized during loading?
- Is First In, First Out (FIFO) being followed consistently?
- Is Wayfair volume being loaded onto earlier trailers when multiple pickups occur?

**Forecasting & volume planning**

- Is volume being accurately forecasted and shared with FedEx?
- Are you receiving Wayfair's weekly/biweekly forecasts?
- Is your Wayfair volume being consolidated with your total volume when planning with FedEx?

**Carrier performance & escalations**

- Are trailers being picked up and dispatched on time, with minimal dwell time on the dock?
- If not, please share escalation details with your FedEx representative

{{#IF_CONSTRAINED_MARKET}}
### Weekend shipping opportunity (constrained market)

Your warehouse operates in a **constrained FedEx market** where peak capacity is limited. Our data shows you are shipping **{{Wnd}}** of Friday/Saturday orders over the weekend.

Weekend shipping may help spread volume and reduce weekday induction pressure. Please share whether you can sustain weekend fulfillment and how it is reflected in your FedEx forecast.
{{/IF_CONSTRAINED_MARKET}}

{{#IF_NOT_CONSTRAINED_MARKET}}
### Focus area

Your primary improvement lever is warehouse execution and FedEx handshake — ensuring labels translate to same-day or next-morning induction. Weekend shipping is not the primary recommendation for your market at this time.
{{/IF_NOT_CONSTRAINED_MARKET}}

**Next steps**

- What actions will you take to ensure orders are inducted on time?
- How can your SRM support you in this process?

Best,
Wayfair

---

## Q3-D — Speed & Reliability (IFR 70–90%)

**Criteria:** 70% ≤ IFR < 90%

**Weekend shipping:** Yes (all suppliers)

---

Dear {{Parent_Su_Name}},

We're reaching out to partner on sustaining and improving your Induction Fill Rate ahead of Q3 peak. Please review performance for the following warehouse:

**{{ChildSUID}} – {{SuName}}**

### Performance summary

| Metric | Target | Baseline (L6W) | L4W |
|--------|--------|----------------|-----|
| Induction Fill Rate | 93% | {{IFR}} | {{L4W_IFR}} |
| Label by 7 PM | 97% | {{Label_By_7}} | {{L4W_Label_By_7}} |
| Weekend ship rate (Fri/Sat → Sat/Sun) | — | {{Wnd}} | — |

{{#IF_L4W_IFR_BELOW_TARGET}}
While your baseline performance is within an improvement range, your last four weeks show IFR below our 93% target. Please provide insight into this recent trend as part of your action plan.
{{/IF_L4W_IFR_BELOW_TARGET}}

### What we need from you

By **{{Action_Deadline}}**, please connect with your SRM ({{SRM_Name}}) to confirm actions that will bring IFR to 93%+ and sustain it through peak.

### Improvement levers

**Weekend shipping**

Our data shows **{{Wnd}}** of your Friday and Saturday orders are currently inducted on Saturday or Sunday. Expanding weekend shipping can improve speed and protect reliability during high-volume periods.

- Can you increase or sustain weekend fulfillment through Q3?
- How is weekend volume reflected in your FedEx forecast?

**Forecasting**

- Are you receiving and acting on Wayfair's weekly/biweekly FedEx forecasts?
- Is your total volume (including non-Wayfair) consolidated when planning trailers with FedEx?

{{#IF_CONSTRAINED_MARKET}}
**Constrained market:** Your warehouse inducts into a capacity-constrained market. Accurate forecasting is essential — FedEx has limited ability to add ad hoc trailers during peak. Please confirm your forecast cadence and escalation path with your FedEx representative.
{{/IF_CONSTRAINED_MARKET}}

**Building directs and splits**

- Are there opportunities to build direct routes or split conveyable vs. non-conveyable items to improve induction timing?
- Please discuss any routing optimization opportunities with your SRM.

**Warehouse execution**

- Is FIFO being followed consistently?
- Is the dock cleared daily with Wayfair volume on earlier trailers when multiple pickups occur?

**Next steps**

- What actions will you take to reach and sustain 93% IFR?
- How can your SRM support you?

Best,
Wayfair

---

## Q3-E — Speed (IFR ≥ 90%)

**Criteria:** IFR ≥ 90%

**Weekend shipping:** Yes — primary lever for speed at peak

---

Dear {{Parent_Su_Name}},

We're reaching out because your recent Induction Fill Rate performance has been strong, and we see an opportunity to further improve customer delivery speed ahead of Q3 peak. Please review performance for the following warehouse:

**{{ChildSUID}} – {{SuName}}**

### Performance summary

| Metric | Target | Baseline (L6W) | L4W |
|--------|--------|----------------|-----|
| Induction Fill Rate | 93% | {{IFR}} | {{L4W_IFR}} |
| Weekend ship rate (Fri/Sat → Sat/Sun) | — | {{Wnd}} | — |

### What we need from you

By **{{Action_Deadline}}**, please connect with your SRM ({{SRM_Name}}) to discuss weekend shipping and peak readiness.

### Weekend shipping to protect speed and reliability

Our order-level data shows you are shipping **{{Wnd}}** of orders placed on Friday and Saturday over the weekend. Enabling or expanding weekend Must Ship By Dates (MSBDs) can provide faster customer promises and increase badging on site while protecting your strong reliability through peak.

Please share:

- Your current weekend fulfillment capability (Saturday and/or Sunday)
- Whether you can sustain or increase weekend shipping volume through Q3 peak
- Any constraints that would prevent maintaining performance with a Sunday MSBD

### FedEx forecast & peak planning

- Please confirm you are using Wayfair's weekly/biweekly forecast sends to plan trailer capacity with FedEx
- If you have not recently updated forecast contacts in Partner Home, please do so with your SRM
- Share how you plan to protect your {{IFR}} IFR as volume increases

{{#IF_CONSTRAINED_MARKET}}
**Constrained market note:** Your warehouse inducts into a capacity-constrained FedEx market. Weekend shipping and accurate forecasting are especially important to avoid weekday induction bottlenecks during peak.
{{/IF_CONSTRAINED_MARKET}}

**Next steps**

- What is your plan for weekend shipping through peak?
- How can your SRM support enablement?

Best,
Wayfair

---

## Q3-F — Weekend MSBD Enablement

**Criteria:** 24hr LT, ≥ 70% Fri/Sat weekend ship rate, IFR > 85%, Fri/Sat volume > 0

**Type:** Opportunity email (not remediation)

**Subject:** `Action Required: Weekend Must-Ship-By-Date Opportunity — {{SuName}}`

---

Hi {{Parent_Su_Name}},

We have a new opportunity to enable weekend Must Ship By Dates (MSBDs) to provide faster customer promises and increase badging on site.

Based on your recent performance, we have identified the following warehouse(s) as a potential candidate for this opportunity based on analyzing past weekend inductions or operating out of a constrained market with induction fill rate opportunities.

**{{SuName}}**

We have the ability to enable either Saturday or Sunday Must Ship By Dates (MSBDs).

Starting this week, orders placed on Friday and Saturday for this warehouse will receive a **Sunday Must Ship By Date (MSBD)**.

Our order-level data shows that you are shipping **{{Wnd}}** of orders placed on Friday and Saturday over the weekend. In addition, your recent performance has been excellent, with an Induction Fill Rate of **{{IFR}}** (the percentage of orders inducted on or before the Must Ship By Date).

This change simply aligns our system settings with your current operational performance, allowing customers to see faster and more accurate delivery promises while recognizing the level of service you are already providing.

{{#IF_CONSTRAINED_MARKET}}
**Constrained market:** Your warehouse operates in a capacity-constrained FedEx market. Weekend MSBD enablement helps distribute volume and supports reliable induction during peak. Please continue providing accurate forecasts to FedEx and leverage the weekly forecast send.
{{/IF_CONSTRAINED_MARKET}}

Please let us know if you have any questions or foresee any challenges with maintaining this level of performance. We appreciate your continued partnership and look forward to working together on this initiative.

Thank you!

---

## Appendix: Sub-cohort question blocks

Use these blocks inside Q3-A/B/C when `{{IFR_Sub_Cohort}}` matches. Insert under "Additional insights" in place of or in addition to the default block.

### `LATE_PICKUP_8_2` (Summer A equivalent)

We've observed that a significant portion of late volume is being inducted one day late (typically between 8 AM–2 PM the following day), often due to handshake issues with FedEx.

*(Use full Trailer Pickup & Warehouse Execution question sets from Q3-B/Q3-C.)*

### `EGREGIOUS_LATE` (Summer B equivalent)

We've observed that a significant portion of late volume is being inducted more than three days late. This often signals that you might be on the incorrect setup or your fulfillment and handshake with FedEx are not optimized.

**Fulfillment & order processing**

- How many business days are required to ship orders?
- How are weekend orders handled?
  - Can all orders placed on Friday, Saturday, and Sunday ship on the same day?
  - If not, when are they shipped?
- What is the latest time each day that your team prints labels and processes orders?
- Can orders placed before this cutoff ship faster than those placed after?
- Is FIFO being followed consistently?

### `LABEL_COMPLIANCE` (Summer C equivalent)

*(Use Q3-A warehouse execution block.)*

### `HANDSHAKE_1DAY` (Summer D equivalent)

We've observed that a significant portion of late volume is being inducted one day late. This is typically driven by either a handshake issue with FedEx or volume shipping one day later than expected.

*(Use Q3-C handshake question set.)*

---

## Template routing quick reference

| Cohort | Subject variant | Weekend block | Constrained-only block |
|--------|-----------------|---------------|------------------------|
| Q3-A | Improvement | Hidden | Hidden |
| Q3-B | Improvement | Always shown | Peak context paragraph |
| Q3-C | Improvement | Constrained only | Weekend section + non-constrained focus note |
| Q3-D | Improvement | Always shown | Peak context paragraph |
| Q3-E | Improvement | Always shown | Peak context paragraph |
| Q3-F | MSBD Opportunity | N/A (core topic) | Forecast reminder |
