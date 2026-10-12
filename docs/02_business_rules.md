# Business Rules Catalog

**Project:** AI Customer Support Assistant  |  **Step 3 of 11**  |  **Version:** 1.0 (draft)

**Source:** Harbor & Thread agent guidelines (`guidelines.json` in the ABCD dataset, which calls the
company "AcmeCorp"), checked against the required actions for each request type (`kb.json`) and the
conversation data from Step 2.

---

## 1. Purpose

This document turns the support team's policy guide into a numbered list of business rules. Each
rule is something the AI assistant must follow, or a decision it must make the same way an agent
would.

The catalog has three uses:

1. **Requirements (Step 6):** every rule becomes a requirement or a constraint in the BRD.
2. **Test cases (Step 8):** every rule with a condition ("if Gold, then...") needs a test for each branch.
3. **Risk review:** section 6 lists policy problems that must be fixed before any part of this is
   automated.

### Rule types

| Type | Meaning | Example |
|---|---|---|
| Authorization | What proof of identity is needed | Username, email and order ID |
| Eligibility | Who qualifies for what | Gold members get unlimited returns |
| Calculation | How an amount is worked out | Total refund = previous refund + new item |
| Process | Required steps or their order | Pull up the account before anything else |
| Escalation | When to involve another team or a manager | Notify the manager if the customer disputes a refund status |
| Communication | What the customer must be told | Explain the result in plain language |

Request types use the dataset's labels from Step 2 (for example `return_size`).

---

## 2. General rules

| ID | Rule | Applies to | Type |
|---|---|---|---|
| GEN-01 | Start by pulling up the customer's account using their full name or account ID. | 43 of 55 request types (all except product/store FAQs and site troubleshooting) | Process |
| GEN-02 | If the customer can't remember their username during verification, recover it (ACC-01) and then continue the original request. | Requests that use purchase validation | Process |
| GEN-03 | Explain every system result to the customer in plain language. Don't paste system output. | All | Communication |
| GEN-04 | End every conversation by asking whether the customer needs anything else. | All | Communication |

---

## 3. Identity verification rules

Four different verification methods are used depending on the request. That inconsistency is
flagged as issue 4 in section 6.

| ID | Method | What the customer must provide | Used for |
|---|---|---|---|
| ID-01 | Purchase validation | Username, email address and order ID | Refunds, returns, billing errors, shipping changes, missing items, shipping cost (`refund_*`, `return_*`, `mistimed_billing_*`, `manage`, `missing`, `cost`, `status`) |
| ID-02 | Order verification | Full name, account ID and order ID | Order issues (`status_mystery_fee`, `status_delivery_time`, `status_payment_method`, `status_quantity`, `manage_upgrade`, `manage_downgrade`, `manage_create`, `manage_cancel`), price disputes (`bad_price_*`), subscription requests (`status_active`, `status_due_amount`, `status_due_date`, `manage_pay_bill`, `manage_extension`, `manage_dispute_bill`) and shipping status (`status`, which uses ID-01 as well) |
| ID-03 | Profile change verification | The current value of the field being changed, plus any 3 of: zip code, phone number, PIN, username, password, email address, previous order ID | `manage_change_address`, `manage_change_name`, `manage_change_phone`, `manage_payment_method` |
| ID-04 | Username recovery | Any 3 of: full name, zip code, phone number, email address | `recover_username` |
| ID-05 | Password reset | Username, plus PIN or the answer to the security question | `recover_password` |
| ID-06 | Two-factor reset | Email address. If the customer doesn't know it: PIN, or the answer to "What is your mother's maiden name?" | `reset_2fa` |

---

## 4. Membership tier rules at a glance

Many decisions depend on the customer's membership level. This decision table puts them all in one
place. The detailed rules are in section 5.

| Situation | Gold | Silver | Bronze | Guest | Rule |
|---|---|---|---|---|---|
| Return window | Unlimited | 6 months, or has receipt, or original packaging | 90 days, or has receipt, or original packaging | 30 days, or has receipt | RET-01 |
| Extra fee that was the customer's error | Removed | Removed | Stays | Stays | ORD-01 |
| Overnight shipping upgrade | Free | $20 | $20 | $20 | ORD-04 |
| Downgrade after the order shipped | Shipping fee credited | Shipping fee credited | Shipping fee credited | Nothing | ORD-05 |
| Add an item after the order shipped | Shipped separately, no fee | Shipped separately, no fee | Not specified | Not specified | ORD-06 |
| Duplicate order after it shipped | Refund now | Refund now | Refund now | Wait for delivery, then return | ORD-07 |
| Invalid promo code (customer's error) | New code | New code | New code | No code | DSP-05 |
| Missing credit, waited less than 7 days | Credit now | No | No | No | DSP-06 |
| Charged for an item never bought (customer's error) | Credit | No | No | No | DSP-07 |
| Subscription payment extension | Always | Only if 1 day late | No | No | SUB-03 |
| Subscription bill dispute | Always refunded | Refunded if under $10 | Only if the system confirms an error | Only if the system confirms an error | SUB-04 |

---

## 5. Rules by category

### 5.1 Refunds and returns (Product Defect)

| ID | Rule | Applies to | Type |
|---|---|---|---|
| RET-01 | A return is allowed based on membership level: Gold always; Silver within 6 months, or with a receipt, or in original packaging; Bronze within 90 days, or with a receipt, or in original packaging; Guest within 30 days, or with a receipt. | `return_stain`, `return_color`, `return_size` | Eligibility |
| RET-02 | If the return isn't allowed, apologize, explain why and end the conversation. | Returns | Communication |
| RET-03 | For an approved return, collect the customer's full address so a shipping label can be created. | Returns | Process |
| RET-04 | The customer chooses how to return the item: by mail, in store or at a drop-off center. | Returns | Process |
| RET-05 | Refund options are gift card, credit to the account, paper check or the credit card on file. Gift cards and checks need a mailing address. Account credit and card refunds need the account ID. | `refund_initiate` | Process |
| RET-06 | If the customer doesn't know the refund amount, use $50. | `refund_initiate` | Calculation |
| RET-07 | When adding an item to an existing refund, record the item's brand and type. The new total is the previous refund plus the new item's price. | `refund_update` | Calculation |
| RET-08 | A refund status is one of: not started, in progress or complete. The refund was requested online, by phone or by chat. | `refund_status` | Communication |
| RET-09 | If the customer disagrees with the refund status, escalate to a manager. If they want a different refund method, update the order to change it. | `refund_status` | Escalation |

### 5.2 Order issues

| ID | Rule | Applies to | Type |
|---|---|---|---|
| ORD-01 | For an unexpected fee, check the system first. If it was the company's error, remove the fee. If it was the customer's error, Gold and Silver members still get it removed; Bronze and Guest members don't. | `status_mystery_fee` | Eligibility |
| ORD-02 | Payment methods allowed: credit card, debit card, PayPal. If the order hasn't left the warehouse yet (Order Received or In Transit), change it now. If it's Out for Delivery or Delivered, the change applies to future orders only. | `status_payment_method` | Eligibility |
| ORD-03 | If the order confirmation shows the wrong quantity, check the system. If the email was wrong, reassure the customer they were charged correctly. If the order really is wrong and hasn't shipped, refund the extra item and remove it. If it has shipped, the customer waits for delivery and then calls back to return it. | `status_quantity` | Eligibility |
| ORD-04 | Overnight shipping is only possible before the order ships. It's free for Gold members and $20 for everyone else, charged to the card on file. If the order has shipped, explain that it will likely arrive within a day anyway. | `manage_upgrade` | Eligibility, Calculation |
| ORD-05 | Delaying delivery to next week is free for everyone if the order hasn't shipped. If it has shipped, Gold, Silver and Bronze members get the shipping fee credited; Guests get nothing. | `manage_downgrade` | Eligibility |
| ORD-06 | An item can be added to an order that hasn't shipped. If the order has shipped, Gold and Silver members get the new item shipped separately with no fee. | `manage_create` | Eligibility |
| ORD-07 | For an accidental duplicate order that hasn't shipped, refund and remove the extra item. If it has shipped, Bronze, Silver and Gold members get a refund now and call back later for a return label. Guests must wait for delivery and then start a return. | `manage_cancel` | Eligibility |
| ORD-08 | A customer can ask to move delivery from morning to evening. The guideline for this request is incomplete (see issue 11). | `status_delivery_time` | Process |

### 5.3 Account access

| ID | Rule | Applies to | Type |
|---|---|---|---|
| ACC-01 | After verification (ID-04), tell the customer their username. | `recover_username` | Process |
| ACC-02 | Agents can't see existing passwords. After verification (ID-05), generate a new password and give it to the customer. | `recover_password` | Process |
| ACC-03 | For a two-factor reset, send a reset code to the email address on file, then send a link about security best practices. | `reset_2fa` | Process |

### 5.4 Website troubleshooting

| ID | Rule | Applies to | Type |
|---|---|---|---|
| TRB-01 | Offer guided fixes in any order: try again, log out and back in, check the card's expiry date (card problems), check whether the item is out of stock (cart problems), clear cookies (search problems), close other tabs or test another site (slow site). | `credit_card`, `shopping_cart`, `search_results`, `slow_speed` | Process |
| TRB-02 | Report search and speed problems to the Website Team. | `search_results`, `slow_speed` | Escalation |
| TRB-03 | If nothing works, the agent can place the order for the customer by collecting their card number and expiry date in the chat. | All troubleshooting | Process |
| TRB-04 | If nothing works and the customer doesn't want the agent to order for them, apologize and end the conversation. | All troubleshooting | Communication |

### 5.5 Account management

| ID | Rule | Applies to | Type |
|---|---|---|---|
| MAC-01 | If a customer reports an unknown service on their account, record how they heard about it (email, spouse or news) and check the system. If it's real, remove the service and refund $40. If not, explain: an email was a scam not sent by the company; anything else was a misunderstanding. | `status_service_added` | Eligibility, Calculation |
| MAC-02 | If a customer reports a missing service, check the system. If it was removed by mistake, add it back and confirm it's working. It may take a few minutes to appear. | `status_service_removed` | Process |
| MAC-03 | For missing account credit, record where the credit came from (subscription refund, previous purchase or promotional package) and check the system. If it's really missing, issue a promo code for the amount ($40 if the customer doesn't know). If it isn't missing, tell the customer to log out and back in. | `status_credit_missing` | Eligibility, Calculation |
| MAC-04 | To change profile details, the customer must give the current value and pass verification (ID-03). Formats: street address only; full first and last name; phone as (XXX) XXX-XXXX; payment method as credit card, debit card or PayPal. | `manage_change_*`, `manage_payment_method` | Authorization, Process |
| MAC-05 | Questions about free international shipping are answered with a link to the subscription FAQ. The guideline is incomplete (see issue 11). | `status_shipping_question` | Process |

### 5.6 Purchase disputes

| ID | Rule | Applies to | Type |
|---|---|---|---|
| DSP-01 | For price complaints (a competitor is cheaper, or the price was lower yesterday), verify the order and explain that prices change automatically. Offer a promo code only if the customer keeps pushing. | `bad_price_competitor`, `bad_price_yesterday` | Eligibility |
| DSP-02 | For general out-of-stock complaints, report to the Purchasing Department. Offer a promo code only if the customer is still unhappy. | `out_of_stock_general` | Escalation |
| DSP-03 | For one out-of-stock item, record the item and report it to Purchasing. If the customer is still unhappy, offer to back-order it using the card on file. | `out_of_stock_one_item` | Escalation, Process |
| DSP-04 | Promo codes last 7 days. A code older than that is out of date; a newer one that fails is invalid. | `promo_code_*` | Eligibility |
| DSP-05 | If the system confirms a promo code problem was the company's error, issue a new code. If it was the customer's error, Gold, Silver and Bronze members still get a new code; Guests don't. New codes are 20% off the next purchase. | `promo_code_*` | Eligibility |
| DSP-06 | If the customer returned an item but hasn't received credit: after more than 7 days, issue the credit. Before 7 days, only Gold members get it now. | `mistimed_billing_already_returned` | Eligibility |
| DSP-07 | If the customer was billed for something they never bought: if the system confirms a company error, issue credit. Otherwise only Gold members get credit. | `mistimed_billing_never_bought` | Eligibility |

### 5.7 Shipping

| ID | Rule | Applies to | Type |
|---|---|---|---|
| SHP-01 | For a question about a shipping email, check the system. If the order is fine, tell the customer the email was wrong. If not, fix it by changing the date, address, item or price. | `status` | Process |
| SHP-02 | Shipping changes are limited to a new address or a corrected item. | `manage` | Process |
| SHP-03 | For a missing package: if the customer has waited 7 days or less, explain it can still arrive. If they've waited a week or more, reship it to their address. | `missing` | Eligibility |
| SHP-04 | For shipping cost complaints: if the order is Order Received or In Transit, waive the fee. If it's Out for Delivery or Delivered, refund the $8 standard shipping fee. | `cost` | Eligibility, Calculation |

### 5.8 Subscription

| ID | Rule | Applies to | Type |
|---|---|---|---|
| SUB-01 | For subscription status questions, look up whether it's active, the amount due and the due date. Send an account login link and make sure the customer knows their username. Offer to take payment if it's past due. | `status_active`, `status_due_amount`, `status_due_date` | Process |
| SUB-02 | The standard subscription is $99 a year, and the customer can pay part of it. If they don't give a card, use the card on file. | `manage_pay_bill` | Calculation |
| SUB-03 | Payment extensions: Gold always; Silver only if 1 day late; Bronze and Guest never. If refused and the customer wants to escalate, take a phone number and notify the manager. | `manage_extension` | Eligibility, Escalation |
| SUB-04 | For a disputed subscription bill: Gold always gets a refund; Silver if the error is under $10; Bronze and Guest only if the system confirms an error. Refund the difference, and only if the bill was already paid. | `manage_dispute_bill` | Eligibility, Calculation |

### 5.9 Product and store questions (FAQ)

| ID | Rule | Applies to | Type |
|---|---|---|---|
| FAQ-01 | Product questions about jeans, shirts, boots and jackets come from a set of 8 standard questions per product, such as stain removal, sizing and stock. Answer from the FAQ in your own words. | `jeans`, `shirt`, `boots`, `jacket` | Communication |
| FAQ-02 | Store questions about pricing, timing, membership and policies come from a set of 4 standard questions per topic. Answer from the FAQ in your own words. | `pricing`, `timing`, `membership`, `policy` | Communication |

---

## 6. Issues to resolve before automating

Reviewing the guidelines as if they were a real company's policy surfaced the problems below. Each
one must be resolved with the business before an AI assistant follows these rules. The proposed
handling is a draft for the BRD.

> **Context:** the ABCD guidelines were written for people role-playing support agents, so some
> instructions (like "make up a reason") exist to keep the role-play going. This review treats the
> document as a real policy guide, because spotting these problems is exactly what a BA would do.

| # | Issue | Rules | Why it matters for AI | Proposed handling |
|---|---|---|---|---|
| 1 | **Instructions to invent information.** Agents are told to make up a reason for a price surge, invent an email address, pick a refund status, adjust subscription amounts so they "make sense," and accept a guessed username even if the system rejects it. | ORD-01, ACC-03, RET-08, SUB-01, GEN-02 | An AI that invents facts is the biggest risk with these tools. Companies have been held liable for wrong answers given by their chatbots. | The assistant may state only facts returned by company systems. If a value is missing, it says so or hands off to a person. |
| 2 | **Card numbers collected in chat.** Agents ask for the full card number and expiry date to place orders. | TRB-03 | Card data in chat transcripts breaks payment security standards (PCI DSS) and puts the company at risk. | The assistant never asks for card numbers. It sends a secure payment link instead. |
| 3 | **New passwords given out in chat.** | ACC-02 | Passwords stored in chat logs can be stolen. | Send a password reset link to the verified email instead. |
| 4 | **Four different identity checks, some weak.** A two-factor reset can be done with the answer to "mother's maiden name," which is often easy to find online. | ID-01 to ID-06 | Inconsistent checks are easy to exploit, and an AI can be manipulated more systematically than a person. | Define one standard check, plus a stronger check for record changes and anything involving money. |
| 5 | **Decisions based on what the customer says the shipping status is.** Agents ask the customer for the shipping status instead of looking it up. | ORD-02 to ORD-07, SHP-04 | A customer could say "not shipped yet" to get a refund or a free upgrade. | The assistant reads the shipping status from the order system and never asks the customer for it. |
| 6 | **Default amounts when the customer doesn't know.** $50 refund, $40 credit. | RET-06, MAC-03 | Paying out made-up amounts is a financial control gap, and it's easy to abuse at scale. | The assistant looks up the real amount. If it can't, it hands off to a person. |
| 7 | **Gold members are knowingly refunded twice.** The guidelines admit the company may pay twice. | DSP-06, DSP-07 | A known financial risk needs an owner and a limit. | Requires Finance sign-off and a dollar limit. Above the limit, a person approves. |
| 8 | **Discounts depend on whether the customer "keeps pushing."** | DSP-01, DSP-02 | "Pushing" isn't measurable, so the AI can't apply it consistently, and customers will learn to push. | Replace with a clear rule (for example, one code per customer per 30 days) or hand off to a person. |
| 9 | **Contradiction at exactly 7 days.** One line says "7 days or less" means wait; the next says "a week or longer" means reship. | SHP-03 | Both branches match a 7-day wait, so the assistant could do either. | Business to decide. Proposed: reship after more than 7 days. |
| 10 | **Practice differs from policy.** RET-02 says to end the conversation when a return isn't allowed. In conversation 3592, the agent offered to escalate to a manager instead. | RET-02 | If agents bend the rules, customers will expect the AI to as well, and the documented policy isn't the real one. | Define an official path for declined requests (for example, a manager callback) and apply it everywhere. |
| 11 | **Incomplete guidelines.** Delivery time changes, international shipping questions, and adding items to shipped orders for Bronze and Guest members have missing or placeholder steps. | ORD-06, ORD-08, MAC-05 | The AI can't follow a rule that doesn't exist. | Out of scope for the pilot until the policy is written. These requests go to a person. |
| 12 | **"Convince the customer."** For price complaints, agents are told to convince the customer that price changes are out of their control. | DSP-01 | The AI must stay truthful and not pressure customers. | The assistant explains the pricing policy factually and doesn't argue. |

---

## 7. Next steps

- **Step 4:** combine these rules with the Step 2 data to decide which request types AI can handle
  alone, which need a person to approve, and which stay with people only.
- **Step 6:** turn each rule and each issue in section 6 into requirements in the BRD.
- **Step 8:** write test cases for every branch of the eligibility rules, starting with the
  membership table in section 4.
