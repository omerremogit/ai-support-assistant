# Automation Matrix: What Can AI Handle?

**Project:** AI Customer Support Assistant  |  **Step 4 of 11**  |  **Version:** 1.0 (draft)

**Inputs:** request-type summary from Step 2 (`intent_summary.csv`), required actions per request
type (`kb.json`), and the business rules and policy issues from Step 3 (`02_business_rules.md`).

**Full table as data:** [`automation_matrix.csv`](automation_matrix.csv), used again in the ROI model (Step 9).

---

## 1. The four tiers

Every request type is placed in exactly one tier. A tier describes how much the AI is allowed to do
on its own, not how hard the request is.

| Tier | Name | What the AI does | Example |
|---|---|---|---|
| **A** | AI handles alone | Answers from the FAQ or walks the customer through a fix. No access to the customer's account. | "Do these jeans shrink?" |
| **B** | AI handles after verification | Confirms the customer's identity, then looks up and explains information. It changes nothing. | "When is my subscription due?" |
| **C** | AI prepares, person approves | Verifies the customer, applies the business rules and prepares the action (for example, "refund $30 to the card on file"). An agent approves it with one click. | "I want to return these boots." |
| **D** | People only during the pilot | Blocked by an open policy issue or a high fraud risk. Goes straight to an agent. | "Reset my password." |

## 2. How each request was placed

The tiers follow four questions, asked in this order. The first "yes" decides the tier.

1. **Is the request blocked by an unresolved policy issue or a high fraud risk** (Step 3, section 6)? → **D**
2. **Does it change a record or move money**, based on its required actions? → **C**
3. **Does it need the customer's account?** → **B**
4. **Otherwise** → **A**

Two policy changes from Step 3 were applied before sorting, because they're required for any
automation: card details are never collected in chat (a secure checkout or payment link is used
instead, issue 2), and every fact the AI states must come from a company system (issue 1).

## 3. Results

![Share of conversations by tier](../diagrams/automation_tiers.png)

| Tier | Request types | Share of conversations | Median conversation length |
|---|---|---|---|
| **A:** AI handles alone | 12 | 32% | 15.5 turns |
| **B:** AI handles after verification (read-only) | 6 | 12% | 24.5 turns |
| **C:** AI prepares, person approves | 31 | 44% | 23 turns |
| **D:** People only during pilot | 6 | 12% | 21.5 turns |

**Headline:** **43% of conversations (4,366 of 10,042, tiers A and B combined) could be handled end
to end by AI** without any account changes. Another **44% (tier C)** could be prepared by AI and approved by an agent,
which still saves most of the agent's time on those chats. **12%** stay with people until
specific policy problems are fixed.

**Important caveat:** these shares use the dataset's mix of requests, which is spread fairly evenly
because the dataset was built to cover every request type (Step 2). A real retailer's mix will
differ, so the ROI model treats the mix as an assumption and tests other mixes.

### What the numbers suggest

- **Tier A conversations are the shortest** (median 15.5 turns vs.
  23 for tier C). They're the safest to automate but save the least
  time per chat. Tier C chats are longer, so the time saved per chat is larger, even with a person
  approving.
- **The three most common request types in the data are account access requests**, and two of them
  (password and two-factor resets) land in tier D. For these, the better fix is a self-service reset
  link on the website, not an AI assistant.
- **Three policy issues affect half of tier C** (15 of 31 request types): shipping status taken from
  the customer (issue 5), default refund amounts (issue 6) and inconsistent identity checks
  (issue 4). Fixing those three would make tier C much safer, and low-value actions like replacement
  promo codes could later move to automatic approval.

## 4. Recommended rollout

| Phase | Tiers | Request types | Share of conversations | Condition to start |
|---|---|---|---|---|
| Pilot | A and B | 18 | 43% | Prototype passes the Step 8 test cases |
| Phase 2 | Add C | 31 more | +44% | Pilot hits its targets, and issues 4, 5 and 6 are fixed |
| Phase 3 | Review D | 6 more | +12% | Self-service resets are built, the missing guidelines are written, and Finance sets a limit for Gold credits |

## 5. Full matrix


### Tier A: AI handles alone (12 request types, 32% of conversations)

| Request type | Category | Conversations | Rules | Issues | Why this tier |
|---|---|---|---|---|---|
| `boots` | Product and store FAQs | 281 | FAQ-01 | - | Answer comes from the product FAQ. No account access or changes. |
| `membership` | Product and store FAQs | 281 | FAQ-02 | - | Answer comes from the store FAQ. No account access or changes. |
| `pricing` | Product and store FAQs | 277 | FAQ-02 | - | Answer comes from the store FAQ. No account access or changes. |
| `policy` | Product and store FAQs | 272 | FAQ-02 | - | Answer comes from the store FAQ. No account access or changes. |
| `timing` | Product and store FAQs | 264 | FAQ-02 | - | Answer comes from the store FAQ. No account access or changes. |
| `jacket` | Product and store FAQs | 263 | FAQ-01 | - | Answer comes from the product FAQ. No account access or changes. |
| `jeans` | Product and store FAQs | 252 | FAQ-01 | - | Answer comes from the product FAQ. No account access or changes. |
| `shirt` | Product and store FAQs | 249 | FAQ-01 | - | Answer comes from the product FAQ. No account access or changes. |
| `credit_card` | Website troubleshooting | 266 | TRB-01, TRB-02, TRB-04 | 2 | Guided fixes and a report to the Website Team. The 'agent places the order' fallback is replaced by a secure checkout link (issue 2). |
| `search_results` | Website troubleshooting | 259 | TRB-01, TRB-02, TRB-04 | 2 | Guided fixes and a report to the Website Team. The 'agent places the order' fallback is replaced by a secure checkout link (issue 2). |
| `shopping_cart` | Website troubleshooting | 251 | TRB-01, TRB-02, TRB-04 | 2 | Guided fixes and a report to the Website Team. The 'agent places the order' fallback is replaced by a secure checkout link (issue 2). |
| `slow_speed` | Website troubleshooting | 250 | TRB-01, TRB-02, TRB-04 | 2 | Guided fixes and a report to the Website Team. The 'agent places the order' fallback is replaced by a secure checkout link (issue 2). |

### Tier B: AI handles after verification (read-only) (6 request types, 12% of conversations)

| Request type | Category | Conversations | Rules | Issues | Why this tier |
|---|---|---|---|---|---|
| `recover_username` | Account access | 361 | ID-04, ACC-01 | - | Verify identity, then tell the customer their username. Read-only. |
| `refund_status` | Refunds and returns | 179 | ID-01, RET-08, RET-09 | 1 | Verify, then read the refund status from the system (never pick one, issue 1). Manager escalation is a handoff; changing the refund method goes to approval. |
| `status` | Shipping | 268 | ID-01, ID-02, SHP-01 | - | Verify, then check the order against the shipping email and explain. Any fix (date, address, item, price) goes to approval. |
| `status_due_amount` | Subscription | 185 | ID-02, SUB-01 | 1 | Verify, then read subscription status, amount and due date from the system. Payment goes through a secure link. |
| `status_due_date` | Subscription | 178 | ID-02, SUB-01 | 1 | Verify, then read subscription status, amount and due date from the system. Payment goes through a secure link. |
| `status_active` | Subscription | 30 | ID-02, SUB-01 | 1 | Verify, then read subscription status, amount and due date from the system. Payment goes through a secure link. |

### Tier C: AI prepares, person approves (31 request types, 44% of conversations)

| Request type | Category | Conversations | Rules | Issues | Why this tier |
|---|---|---|---|---|---|
| `status_service_removed` | Account management | 153 | MAC-02 | - | Changes the account: adds a service back. |
| `status_service_added` | Account management | 129 | MAC-01 | - | Removes a service and refunds $40. |
| `status_credit_missing` | Account management | 114 | MAC-03 | 6 | Issues credit as a promo code. The amount must come from the system (issue 6). |
| `manage_change_address` | Account management | 51 | ID-03, MAC-04 | 4 | Changes personal details, a common route to account takeover. Needs the stronger identity check (issue 4). |
| `manage_change_name` | Account management | 51 | ID-03, MAC-04 | 4 | Changes personal details, a common route to account takeover. Needs the stronger identity check (issue 4). |
| `manage_change_phone` | Account management | 48 | ID-03, MAC-04 | 4 | Changes personal details, a common route to account takeover. Needs the stronger identity check (issue 4). |
| `manage_payment_method` | Account management | 36 | ID-03, MAC-04 | 4 | Changes personal details, a common route to account takeover. Needs the stronger identity check (issue 4). |
| `status_quantity` | Order issues | 135 | ID-02, ORD-03 | 5 | May refund and remove an item. |
| `status_payment_method` | Order issues | 134 | ID-02, ORD-02 | 5 | Changes the order. Shipping status must come from the system (issue 5). |
| `manage_create` | Order issues | 134 | ID-02, ORD-06 | 5, 11, 13 | Places a purchase. Bronze and Guest members with shipped orders have no written rule, so those go to a person (issue 11). |
| `status_mystery_fee` | Order issues | 130 | ID-02, ORD-01 | 1, 5, 13 | Removes a fee (money). No made-up reasons when a fee stays (issue 1). |
| `manage_cancel` | Order issues | 125 | ID-02, ORD-07 | 5, 13 | Refunds and removes an item. |
| `manage_downgrade` | Order issues | 123 | ID-02, ORD-05 | 5, 13 | Changes the order or credits the shipping fee. |
| `manage_upgrade` | Order issues | 117 | ID-02, ORD-04 | 5, 13 | Changes the order and may charge $20. |
| `bad_price_competitor` | Purchase disputes | 149 | ID-02, DSP-01 | 8, 12 | AI explains the pricing policy factually (issue 12). A person decides on any promo code, which removes the 'keeps pushing' judgment (issue 8). |
| `out_of_stock_general` | Purchase disputes | 140 | DSP-02 | 8 | AI reports to Purchasing. A person decides on any promo code (issue 8). |
| `bad_price_yesterday` | Purchase disputes | 139 | ID-02, DSP-01 | 8, 12 | AI explains the pricing policy factually (issue 12). A person decides on any promo code, which removes the 'keeps pushing' judgment (issue 8). |
| `promo_code_invalid` | Purchase disputes | 133 | DSP-04, DSP-05 | 13 | Issues a 20% code. Low value, so a candidate for automatic approval after the pilot. |
| `out_of_stock_one_item` | Purchase disputes | 127 | DSP-03 | - | AI reports to Purchasing. A back-order is a purchase, so it needs approval. |
| `promo_code_out_of_date` | Purchase disputes | 112 | DSP-04, DSP-05 | 13 | Issues a 20% code. Low value, so a candidate for automatic approval after the pilot. |
| `return_size` | Refunds and returns | 191 | ID-01, RET-01 to RET-04 | 10, 13 | AI can check eligibility from the membership table, but it creates a return. Declined returns need an official escalation path (issue 10). |
| `return_color` | Refunds and returns | 180 | ID-01, RET-01 to RET-04 | 10, 13 | AI can check eligibility from the membership table, but it creates a return. Declined returns need an official escalation path (issue 10). |
| `refund_update` | Refunds and returns | 177 | ID-01, RET-07 | - | Moves money: the refund total changes. |
| `refund_initiate` | Refunds and returns | 176 | ID-01, RET-05, RET-06 | 6 | Moves money. The amount must come from the order, not a $50 default (issue 6). |
| `return_stain` | Refunds and returns | 167 | ID-01, RET-01 to RET-04 | 10, 13 | AI can check eligibility from the membership table, but it creates a return. Declined returns need an official escalation path (issue 10). |
| `missing` | Shipping | 261 | ID-01, SHP-03 | 9 | May reship an order. The 7-day rule contradicts itself (issue 9). |
| `manage` | Shipping | 248 | ID-01, SHP-02 | 5 | Changes the shipping address or item. |
| `cost` | Shipping | 243 | ID-01, SHP-04 | 5 | Waives a fee or refunds $8. |
| `manage_dispute_bill` | Subscription | 190 | ID-02, SUB-04 | 13 | Moves money: refunds part of a bill. |
| `manage_extension` | Subscription | 165 | ID-02, SUB-03 | 13 | Changes the subscription. |
| `manage_pay_bill` | Subscription | 162 | ID-02, SUB-02 | 2 | Takes a payment. Must use a secure payment link, not card details in chat (issue 2). |

### Tier D: People only during pilot (6 request types, 12% of conversations)

| Request type | Category | Conversations | Rules | Issues | Why this tier |
|---|---|---|---|---|---|
| `reset_2fa` | Account access | 351 | ID-05, ID-06, ACC-02, ACC-03 | 3, 4 | Account-takeover risk: weak checks (maiden name) and passwords shared in chat. Better fixed with a self-service reset link than with AI. |
| `recover_password` | Account access | 336 | ID-05, ID-06, ACC-02, ACC-03 | 3, 4 | Account-takeover risk: weak checks (maiden name) and passwords shared in chat. Better fixed with a self-service reset link than with AI. |
| `status_shipping_question` | Account management | 131 | MAC-05 | 11 | The guideline is incomplete, so there's no rule to follow. |
| `status_delivery_time` | Order issues | 142 | ORD-08 | 11 | The guideline is incomplete, so there's no rule to follow. |
| `mistimed_billing_never_bought` | Purchase disputes | 139 | ID-01, DSP-06, DSP-07 | 7, 13 | The company knowingly risks paying twice for Gold members. Stays with people until Finance sets a limit. |
| `mistimed_billing_already_returned` | Purchase disputes | 137 | ID-01, DSP-06, DSP-07 | 7, 13 | The company knowingly risks paying twice for Gold members. Stays with people until Finance sets a limit. |

---

## 6. Next steps

- **Step 5:** map the current process for three request types, one each from tiers A, B and C, to
  show where the AI fits into each one.
- **Step 6:** turn the tiers into requirements, for example "The assistant must not change any
  record without agent approval (tier C)."
- **Step 9:** use `automation_matrix.csv` to estimate how many chats the AI could take on.
