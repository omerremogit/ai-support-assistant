# Business Requirements Document (BRD)
## AI Customer Support Assistant for Harbor & Thread

| | |
|---|---|
| **Author** | Mohammed Omer Ahmed, Business Analyst |
| **Version** | 1.0 (draft for review) |
| **Date** | October 2026 |
| **Status** | Draft, not yet validated with stakeholders (see section 13) |
| **Sponsor** | Head of Customer Experience |

> Portfolio case study. Harbor & Thread is fictional. Requirements are based on real support
> conversations and agent policies from the public ABCD dataset.

---

## 1. Executive summary

Harbor & Thread's support agents handle every chat by hand, following a policy guide that is long,
inconsistent in places and not always followed. This document defines the requirements for an AI
assistant that handles part of that work.

Analysis of 10,042 support conversations across 55 request types found that:

- **43% of conversations** (tiers A and B) could be handled end to end by AI, because they need only
  FAQ answers, guided fixes or read-only account information.
- **44%** (tier C) involve refunds, returns or account changes. AI can prepare these, but a person
  should approve them.
- **12%** (tier D) should stay with people until specific policy problems are fixed.
- The current policy has **13 issues** that must be resolved before automating, including
  instructions to invent information, card numbers collected in chat, and eligibility based on
  what the customer claims instead of what the system shows.

**Recommendation:** pilot the assistant on tiers A and B (18 request types) with read-only access.
Add tier C with agent approval only after the pilot meets its targets and the blocking policy
issues are fixed.

**Supporting documents:**
[Project brief](01_project_brief.md) ·
[Data analysis](../notebooks/explore_conversations.ipynb) ·
[Business rules](02_business_rules.md) ·
[Automation matrix](03_automation_matrix.md) ·
[Process maps](04_process_maps.md)

---

## 2. Business objectives

| ID | Objective | How it's measured |
|---|---|---|
| OBJ-1 | Reduce the agent workload on routine requests | Containment rate: share of tier A and B chats resolved without an agent |
| OBJ-2 | Apply company policy the same way every time | Policy compliance rate in QA review. Today, 9% of size returns skip the eligibility check (Step 5) |
| OBJ-3 | Give customers fast, correct answers | Wrong-answer rate, response time, customer satisfaction (CSAT) |
| OBJ-4 | Reduce security and financial risk in chat support | No card numbers or passwords in transcripts; no rule-breaking payouts |
| OBJ-5 | Make an informed decision about scaling up | Pilot results compared against go/no-go criteria (section 3) |

---

## 3. Success criteria for the pilot

Draft targets. Final definitions, baselines and test methods are set in the test plan (Step 8).

| Measure | Draft target | Objective |
|---|---|---|
| Containment rate (tier A and B chats resolved by AI) | 60% or more | OBJ-1 |
| Correct handoff rate (chats passed to a person when they should be) | 95% or more | OBJ-3 |
| Policy compliance rate (QA sample) | 98% or more | OBJ-2 |
| Wrong-answer rate (incorrect or invented information) | 2% or less | OBJ-3, OBJ-4 |
| Customer satisfaction | No more than 2 points below the agent-only baseline | OBJ-3 |
| Card numbers or passwords in AI transcripts | Zero | OBJ-4 |

**Go/no-go:** after the pilot, Phase 2 starts only if all six targets are met for four weeks in a
row.

---

## 4. Scope

### 4.1 In scope

| Phase | What's included | Request types | Share of conversations |
|---|---|---|---|
| **Pilot** | Tier A: FAQs and site troubleshooting. Tier B: read-only account answers after verification | 18 | 43% |
| **Phase 2** | Tier C: refunds, returns, order and account changes, prepared by AI and approved by an agent | +31 | +44% |
| **Phase 3** | Review tier D once its blocking issues are fixed | +6 | +12% |

The full list of request types by tier is in the [automation matrix](03_automation_matrix.md).

### 4.2 Out of scope

- Phone and email support
- Choosing a vendor or technology platform
- Languages other than English (pilot)
- Rewriting the company's return, refund and membership policies. This BRD lists the decisions
  needed (section 10) but doesn't make them.
- Staffing and HR decisions

---

## 5. Stakeholders

| Stakeholder | Interest | R | A | C | I |
|---|---|---|---|---|---|
| Head of Customer Experience (sponsor) | Faster service and lower cost without hurting satisfaction | | ✓ | | |
| Business Analyst | Requirements, traceability, test plan | ✓ | | | |
| Support team leads | Policy compliance, quality review, approval workflow | | | ✓ | |
| Support agents | Fewer repetitive chats, clean handoffs, usable approval tool | | | ✓ | |
| IT and Security | System access, identity checks, data protection | ✓ | | ✓ | |
| Legal and Compliance | AI disclosure, liability, data retention | | | ✓ | |
| Finance | Refund limits, ROI | | | ✓ | |
| Customers | Quick, correct answers and an easy way to reach a person | | | | ✓ |

R = responsible, A = accountable, C = consulted, I = informed. Roles are assumptions until
validated (section 13).

---

## 6. Current state

The full analysis is in the [process maps](04_process_maps.md). Key findings:

- **Every chat is handled entirely by an agent**, including product questions that come from a
  fixed list of 8 FAQs per product.
- **Customers repeat themselves.** A size return asks the customer for information 6 separate times
  and runs a median of 29 turns, the longest of any request type.
- **Identity checks are inconsistent.** There are 4 different methods, and asking about a
  subscription requires an unrelated order ID.
- **Policy isn't applied consistently.** 9% of size returns were created without checking
  eligibility, and agents offer escalations that aren't in the written policy.
- **Customers are trusted on key facts.** Agents ask customers for their membership level and
  shipping status instead of checking the system.

---

## 7. Assumptions, constraints and dependencies

| Type | ID | Statement |
|---|---|---|
| Assumption | AS-1 | The conversation data reflects how agents work, but not the real mix of requests. The ROI model tests different mixes. |
| Assumption | AS-2 | Order, account and subscription systems can provide read access to the assistant (an API or equivalent). |
| Assumption | AS-3 | Volume and cost figures are the placeholders in the [project brief](01_project_brief.md), section 11. |
| Constraint | CO-1 | Requirements are based on documents and data. They haven't yet been validated with stakeholders. |
| Constraint | CO-2 | The pilot gives the assistant read-only access. No record can be changed by AI in the pilot. |
| Constraint | CO-3 | Chat duration isn't in the data, so handle time is an assumption. |
| Dependency | DE-1 | A secure payment and checkout link service (issue 2) must exist before the pilot. |
| Dependency | DE-2 | An approval tool for agents must exist before Phase 2. |
| Dependency | DE-3 | Policy decisions in section 10 must be made before the phase that needs them. |

---

## 8. Functional requirements

**Priority** (MoSCoW for the phase listed): **M** = must, **S** = should, **C** = could.
**Source** links each requirement to its evidence: business rules (RET-01), policy issues (#5),
or findings from Steps 2, 4 and 5.

### 8.1 Understanding and routing requests

| ID | Requirement | Priority | Phase | Source |
|---|---|---|---|---|
| FR-01 | The assistant must identify the customer's request type from their messages, across all 55 request types. | M | Pilot | Step 2: 55 request types |
| FR-02 | The assistant must route each request by its tier: tiers A and B handled by AI, tier C prepared for approval, tier D handed to an agent. | M | Pilot | Step 4 |
| FR-03 | If a request changes tier during a chat (for example, a subscription question becomes a payment change), the assistant must follow the higher tier's path. | M | Pilot | Step 5: 10% of `status_due_date` chats end in a change |
| FR-04 | The assistant should handle more than one request in a chat, each under its own tier. | S | Pilot | Step 5: 4% of `jeans` chats have two questions; GEN-02 |
| FR-05 | If the request type is still unclear after two clarifying questions, the assistant must hand off to an agent. | M | Pilot | Risk R1 |

### 8.2 Identity verification

| ID | Requirement | Priority | Phase | Source |
|---|---|---|---|---|
| FR-06 | The assistant must verify the customer's identity before revealing or changing any account information. | M | Pilot | ID-01 to ID-06, GEN-01 |
| FR-07 | The assistant must use one standard verification method for read-only requests and ask for all details in a single message. | M | Pilot | #4; Step 5: identity asked in two rounds |
| FR-08 | Before any record change or money movement, the assistant must use a stronger check, such as a one-time code sent to the email or phone on file. | M | Phase 2 | #4, ID-03 |
| FR-09 | Security questions (such as mother's maiden name) must never be the only verification. | M | Pilot | #4, ID-06 |
| FR-10 | After 3 failed verification attempts, the assistant must stop and hand off, without saying which detail was wrong. | M | Pilot | Risk R2 |
| FR-11 | The assistant must never ask the customer for information the system already holds: membership level, shipping status, address or purchase date. | M | Pilot | #5, #13; Step 5 pain points ⚠2 and ⚠5 |

### 8.3 Answers and troubleshooting (tier A)

| ID | Requirement | Priority | Phase | Source |
|---|---|---|---|---|
| FR-12 | The assistant must answer product and store questions only from approved FAQ content. | M | Pilot | FAQ-01, FAQ-02 |
| FR-13 | If a question isn't covered by the FAQ, the assistant must say so and offer an agent. It must never guess. | M | Pilot | #1; Step 5: 23% of `jeans` chats didn't use a stored answer |
| FR-14 | The assistant must explain answers and system results in plain language, not paste raw system text. | M | Pilot | GEN-03 |
| FR-15 | The assistant must guide customers through the approved fixes for the 4 website problems, and report search and speed problems to the Website Team. | M | Pilot | TRB-01, TRB-02 |
| FR-16 | When troubleshooting fails, the assistant must offer a secure checkout link instead of taking the order in chat. | M | Pilot | TRB-03, #2 |
| FR-17 | The support operations team should be able to update FAQ content without a code change. | S | Pilot | Step 5 pain point ⚠3 |

### 8.4 Account information (tier B)

| ID | Requirement | Priority | Phase | Source |
|---|---|---|---|---|
| FR-18 | After verification, the assistant must look up and explain usernames, refund status, subscription status (active, amount due, due date) and shipping status. | M | Pilot | Step 4: 6 tier B request types |
| FR-19 | The assistant must state only values returned by company systems. If a value is missing or looks wrong, it must say so and hand off. It must never adjust or invent a value. | M | Pilot | #1, SUB-01, RET-08 |
| FR-20 | Payments must go through a secure payment link, never through details typed into the chat. | M | Pilot | #2, SUB-01; Step 5: 23% of `status_due_date` chats took payment in chat |
| FR-21 | The assistant could offer the account login link so customers can check for themselves next time. | C | Pilot | SUB-01 |

### 8.5 Actions with agent approval (tier C)

| ID | Requirement | Priority | Phase | Source |
|---|---|---|---|---|
| FR-22 | The assistant must decide eligibility by applying the business rules to system data (membership level, dates, shipping status, order history). | M | Phase 2 | Business rules catalog, sections 4 and 5 |
| FR-23 | For every tier C request, the assistant must prepare a proposed action showing the customer, the action, the amount, the rule applied and the data used. | M | Phase 2 | Step 5: future returns process |
| FR-24 | The assistant must never complete a tier C action without agent approval. | M | Phase 2 | Step 4 |
| FR-25 | Every amount must come from the order or account. Default amounts are not allowed. | M | Phase 2 | #6, RET-06, MAC-03 |
| FR-26 | If no written rule covers the situation, the assistant must hand off. | M | Pilot | #11 |
| FR-27 | When a request is declined, the assistant must explain the reason based on the rule, stay polite, and not change the outcome because the customer pushes back. | M | Pilot | RET-02, #10; conversation 3592 |
| FR-28 | Promo codes and discounts must be approved by an agent until the business sets a clear rule. | M | Phase 2 | #8, DSP-01, DSP-02 |
| FR-29 | Credits that risk paying a Gold member twice must go to an agent. | M | Phase 2 | #7, DSP-06, DSP-07 |

### 8.6 Handoff and escalation

| ID | Requirement | Priority | Phase | Source |
|---|---|---|---|---|
| FR-30 | A customer must be able to ask for a person at any time, and the assistant must hand off right away. | M | Pilot | Brief: stakeholder "Customers" |
| FR-31 | Every handoff must include a summary: request type, verification status, what was tried, and the customer's own words, so the customer doesn't have to repeat themselves. | M | Pilot | Step 5: handoff branches; customers repeat information today |
| FR-32 | Tier D requests must be handed off as soon as they're identified. | M | Pilot | Step 4: tier D |
| FR-33 | Declined requests must follow one official escalation path (for example, a manager callback), the same for every request type. | M | Pilot | #10 |
| FR-34 | For callbacks, the assistant should confirm the phone number on file rather than collect a new one. | S | Pilot | Step 2: `enter-details` captures phone numbers; privacy |
| FR-35 | Outside support hours, the assistant should create a ticket and tell the customer when to expect a reply. | S | Pilot | AS-3 |

### 8.7 Agent tools

| ID | Requirement | Priority | Phase | Source |
|---|---|---|---|---|
| FR-36 | Agents must see each proposed action with its evidence and the rule used, and be able to approve, reject or edit it in one step. | M | Phase 2 | Step 5: "one approval click" |
| FR-37 | Agents should give a reason code when rejecting a proposed action, so rules can be improved. | S | Phase 2 | Risk R5 |
| FR-38 | When taking over a chat, agents must see the full conversation with the AI. | M | Pilot | FR-31 |

### 8.8 Monitoring and reporting

| ID | Requirement | Priority | Phase | Source |
|---|---|---|---|---|
| FR-39 | Every conversation must be logged with its request type, tier, outcome (resolved by AI or by an agent), handoff reason, actions and approvals. | M | Pilot | Section 3 |
| FR-40 | A dashboard must show the six success measures in section 3, updated daily. | M | Pilot | Section 3 |
| FR-41 | Customers should get a one-question satisfaction survey at the end of each chat. | S | Pilot | OBJ-3 |
| FR-42 | Team leads must review a weekly sample of AI conversations for policy compliance and correctness. | M | Pilot | OBJ-2; stakeholder "Support team leads" |

---

## 9. Non-functional requirements

| ID | Category | Requirement | Priority | Source |
|---|---|---|---|---|
| NFR-01 | Transparency | The assistant must tell customers at the start of the chat that they're talking to an AI. | M | Brief: Legal and Compliance |
| NFR-02 | Accuracy | The assistant must not invent facts. Wrong-answer rate must be 2% or less (section 3). | M | #1 |
| NFR-03 | Security | The assistant must never request or store full card numbers. Any card number typed by a customer must be masked in transcripts. | M | #2, PCI DSS |
| NFR-04 | Security | Passwords must never be sent in chat. Resets use a link to the verified email. | M | #3 |
| NFR-05 | Privacy | Personal data (phone numbers, addresses, emails) must be masked in logs, with access limited by role. | M | Step 2: `enter-details` captures personal data |
| NFR-06 | Security | In the pilot, the assistant gets read-only system access. In Phase 2, it can write only through approved actions. | M | CO-2 |
| NFR-07 | Consistency | Eligibility decisions must be made by fixed business rules, not by the AI model's judgment, so the same facts always give the same result. The AI model handles the conversation. | M | Step 5: 9% of returns skipped the eligibility check |
| NFR-08 | Robustness | Customer messages must not be able to change the rules, the tier or the assistant's instructions (for example, "ignore your rules" or repeated pleading). | M | #4, #8; Step 5 example conversation |
| NFR-09 | Tone | Replies must be polite, short and factual. The assistant must not argue or pressure customers. | S | #12 |
| NFR-10 | Performance | 95% of AI replies within 5 seconds. | S | OBJ-3 |
| NFR-11 | Availability | 99.5% during support hours. If the assistant is down, chats go straight to agents. | S | OBJ-3 |
| NFR-12 | Accessibility | The chat interface must meet WCAG 2.1 AA. | M | Brief: Legal and Compliance |
| NFR-13 | Auditability | Conversations, decisions and approvals must be kept for the period Legal sets (proposed: 1 year). | M | FR-39 |
| NFR-14 | Language | English only in the pilot. | M | Section 4.2 |

---

## 10. Policy decisions needed

These are the 13 issues from the [business rules catalog](02_business_rules.md), section 6. Each
needs a decision from its owner before the phase listed.

| Issue | Decision needed | Owner | Needed before | Requirements |
|---|---|---|---|---|
| #1 | Confirm that company systems are the only source of facts | Head of CX, IT | Pilot | FR-13, FR-19, NFR-02 |
| #2 | Provide secure payment and checkout links | IT, Finance | Pilot | FR-16, FR-20, NFR-03 |
| #3 | Replace in-chat passwords with self-service reset links | IT Security | Phase 3 | NFR-04 |
| #4 | Approve one standard identity check and one stronger check | IT Security | Pilot (standard), Phase 2 (stronger) | FR-07 to FR-10 |
| #5 | Make shipping status available from the system | IT | Phase 2 | FR-11, FR-22 |
| #6 | Remove default refund and credit amounts | Finance | Phase 2 | FR-25 |
| #7 | Set a limit for Gold member credits that risk double payment | Finance | Phase 3 | FR-29 |
| #8 | Replace "if the customer keeps pushing" with a clear promo code rule | Head of CX, Finance | Phase 2 | FR-28 |
| #9 | Resolve the 7-day contradiction for missing packages | Support operations | Phase 2 | FR-22 |
| #10 | Define one official escalation path for declined requests | Head of CX | Pilot | FR-27, FR-33 |
| #11 | Write the missing guidelines | Support operations | Phase 3 | FR-26 |
| #12 | Approve a factual explanation of dynamic pricing | Head of CX, Legal | Phase 2 | NFR-09 |
| #13 | Make membership level available from the system | IT | Phase 2 | FR-11, FR-22 |

---

## 11. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | The assistant gives a wrong or invented answer | Medium | High | FR-13, FR-19, NFR-02; weekly QA review (FR-42); wrong-answer target |
| R2 | Someone takes over an account through the chat | Low | High | FR-06 to FR-10, NFR-04; read-only access in the pilot |
| R3 | Customers talk the assistant into breaking policy | Medium | Medium | FR-27, NFR-07, NFR-08; manipulation test cases in Step 8 |
| R4 | Customers dislike the assistant and satisfaction drops | Medium | Medium | FR-30, FR-31; CSAT go/no-go target |
| R5 | Agents approve proposed actions without checking them | Medium | Medium | FR-36, FR-37; QA sampling of approvals |
| R6 | The real request mix differs from the dataset, so savings are lower | High | Medium | Measure the real mix in the pilot; ROI scenarios (Step 9) |
| R7 | Systems aren't ready for the assistant to connect to | Medium | Medium | The pilot needs read access only (AS-2) |
| R8 | Legal exposure from AI answers | Low | High | NFR-01, NFR-13; Legal review before launch |

---

## 12. Traceability

Every policy issue and every rule category is covered by at least one requirement.

| Source | Covered by |
|---|---|
| Issues #1 to #13 | See section 10, last column |
| General rules (GEN-01 to GEN-04) | FR-04, FR-06, FR-14, NFR-09 |
| Identity rules (ID-01 to ID-06) | FR-06 to FR-10 |
| Membership table and eligibility rules (RET, ORD, MAC, DSP, SHP, SUB) | FR-22 to FR-29 |
| Account access rules (ACC-01 to ACC-03) | FR-18, NFR-04, tier D (FR-32) |
| Troubleshooting rules (TRB-01 to TRB-04) | FR-15, FR-16 |
| FAQ rules (FAQ-01, FAQ-02) | FR-12, FR-13, FR-17 |
| Step 5 pain points | FR-07, FR-11, FR-13, FR-20, FR-31, NFR-07 |

User stories (Step 7) and test cases (Step 8) will each reference the requirement IDs above.

---

## 13. Stakeholder validation plan

These requirements were built from documents and data, without stakeholder interviews. Before
sign-off, each group would be asked to confirm the parts that affect them.

| Stakeholder | What to validate | Example questions |
|---|---|---|
| Head of CX | Objectives, scope, pilot targets, escalation path | Are the success targets realistic? Is a manager callback the right escalation path for declined requests? |
| Team leads and agents | Process maps, pain points, approval workflow | Do the maps match how you work? What would make approving an AI's proposed action quick and safe? |
| IT and Security | Identity checks, system access, data masking | Can systems provide membership level and shipping status? Which stronger check is practical? |
| Finance | Refund rules, limits, ROI assumptions | What limit should apply to Gold member credits? Are the cost assumptions reasonable? |
| Legal and Compliance | AI disclosure, data retention, liability | What retention period applies? Does the disclosure wording meet our obligations? |

---

## 14. Glossary

| Term | Meaning |
|---|---|
| Request type | What the customer wants, such as `return_size`. There are 55. |
| Tier | How much the AI may do on its own: A (alone), B (after verification, read-only), C (prepare for approval), D (people only). |
| Containment rate | The share of chats resolved by the AI without an agent. |
| Handoff | Passing a chat from the AI to an agent. |
| Stronger check | Extra identity verification for risky actions, such as a one-time code. |
| PCI DSS | The security standard for handling payment card data. |
| CSAT | Customer satisfaction score from a post-chat survey. |

---

## 15. Approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Head of Customer Experience (sponsor) | | | |
| IT and Security | | | |
| Finance | | | |
| Legal and Compliance | | | |
