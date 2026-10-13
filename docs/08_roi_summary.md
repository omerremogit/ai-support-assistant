# ROI Summary

**Project:** AI Customer Support Assistant  |  **Step 9 of 11**  |  **Version:** 1.1 (prototype results added)

**Full model:** [`roi/roi_model.xlsx`](../roi/roi_model.xlsx). GitHub can't show Excel files, so
the key results are summarized here. Every number below comes from the workbook's formulas, and
every assumption is listed on its Inputs sheet.

---

## 1. The question

What does chat support cost today, what would the AI assistant cost, and what share of chats must
the AI resolve before it pays for itself?

## 2. Key assumptions

| Assumption | Expected value | Source |
|---|---|---|
| Chats per month | 30,000 | Project brief (placeholder) |
| Agent handle time per chat | 8 minutes | Project brief (the dataset has no durations) |
| Agent cost per hour, including benefits | $32 | Project brief (placeholder) |
| Request mix by tier | A 31.5%, B 12.0%, C 44.2%, D 12.3% | Automation matrix (dataset mix) |
| Containment rate for tiers A and B | 60% | Pilot target (test plan) |
| Tier C chats prepared by AI | 70% | Assumption |
| Agent time to approve a tier C chat | 2 minutes | Assumption |
| AI costs | $0.10 usage per chat, plus $0.99 per resolved or prepared chat, plus $2,500 a month fixed | Assumption based on per-resolution vendor pricing |
| One-time cost | $120,000 pilot, plus $80,000 for Phase 2 | Assumption |

Today, chats take **4,000 agent hours a month**, costing **$128,000**.

## 3. Results

| | Worst | Expected | Best |
|---|---|---|---|
| **Pilot** (tiers A and B): net annual benefit | $40,744 | **$229,245** | $358,347 |
| Pilot: payback period | 47.1 months | **6.3 months** | 3.0 months |
| Pilot: break-even containment rate | 30.6% | **15.3%** | 9.9% |
| **Phase 2** (adds tier C): net annual benefit | $91,148 | **$475,483** | $725,901 |
| Phase 2: payback period | 35.5 months | **5.0 months** | 2.5 months |
| Phase 2: share of agent chat workload removed | 28.4% | **49.3%** | 63.1% |

## 4. What this means

- **The pilot breaks even once the AI resolves about 15% of tier A and B chats**, far below the 60%
  target. To also pay back its one-time cost within a year, it needs about **39%**.
- **The worst case is a warning.** With 40% containment, higher vendor fees and higher
  implementation costs, the pilot takes about four years to pay back. That supports the BRD's
  go/no-go rule: expand only after the pilot proves its numbers.
- **Phase 2 doubles the benefit.** Tier C chats are long, so even with an agent approving each one,
  the time saved per chat is large. At the expected values, the assistant removes about half of the
  agents' chat workload, roughly 14 full-time equivalents of capacity.
- **Vendor pricing matters more than expected.** In the expected case, per-chat vendor fees are the
  largest running cost. The Sensitivity sheet shows how the result changes with the fee and with
  the request mix.

## 5. Limitations

- The request mix comes from a dataset built to cover every request type evenly, so a real
  retailer's mix will differ (BRD risk R6). The Sensitivity sheet tests mixes from 25% to 65%
  tier A and B.
- Handle time, costs and vendor fees are placeholders to confirm with Finance.
- Handed-off chats are assumed to take the full handle time, so savings are conservative.
- The prototype can't measure real containment, because that needs real customers (see section 6).

## 6. What the prototype changed

The prototype's routing test (TC-36, 521 real conversations) gives two numbers that affect the model:

- **88.4% of tier A and B chats reached the AI** (153 of 173). The AI can only resolve chats that
  reach it, so this caps containment. The expected 60% and the best case of 75% both stay below the
  cap, so the savings estimates hold. The workbook now checks this automatically (Inputs, row 36).
- **14.4% of chats that need a person reached the AI first** (50 of 348). In the pilot these chats
  still end with an agent, because the AI is read-only and hands off as soon as a change is
  requested. The cost is a few extra messages for the customer and a small AI usage cost, not
  agent time, so the model's numbers don't change. The customer experience impact is the real
  concern, and it's why routing has to improve before the pilot (see the README).
