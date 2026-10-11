# Project Brief: AI Customer Support Assistant

**Author:** Mohammed Omer Ahmed  |  **Date:** October 2026  |  **Version:** 1.0 (draft)

> **Note:** This is a portfolio case study. The company, Harbor & Thread, is fictional.
> The conversation data and agent policies are real, from the public ABCD dataset.

---

## 1. Background

Harbor & Thread is a mid-size online clothing retailer. Its support team answers customer
chats about orders, shipping, returns, refunds, promo codes and account problems. Agents
must follow a written policy guide for every request. For example, they have to confirm a
customer's identity before changing an order, and only some purchases qualify for a refund.

Chat volume is growing faster than the team. Several vendors are pitching AI support
assistants, and leadership wants an independent recommendation before spending money.

## 2. Problem statement

Agents spend much of their day on repetitive requests that follow fixed policy steps.
As volume grows, customers wait longer, and hiring more agents is expensive. The company
does not know which requests an AI assistant could handle safely, how much it would save,
or how to tell whether a pilot is working.

## 3. Key business question

**Should Harbor & Thread pilot an AI assistant for customer support chats? If so, for which
types of requests, and how will it measure success?**

## 4. Objectives

1. Identify which customer requests an AI assistant could handle fully, partly (with human
   approval), or not at all.
2. Define clear, testable requirements for the assistant, based on company policy and real
   conversation data.
3. Estimate the cost, savings and break-even point of a pilot.
4. Define how the pilot's success will be measured, and test a working prototype against
   those measures.

## 5. Scope

| In scope | Out of scope |
|---|---|
| Text chat support | Phone and email support |
| The 55 request types in the dataset | Choosing a specific vendor |
| Requirements, test cases and ROI for a pilot | Production deployment |
| A small prototype using mock customer data | Connecting to real order or payment systems |
| | Staffing and HR decisions |

## 6. Stakeholders

| Role | What they care about |
|---|---|
| Head of Customer Experience (sponsor) | Faster service and lower cost per chat, without hurting customer satisfaction |
| Support agents | Fewer repetitive chats, and a clean handoff when the AI can't help |
| Support team leads | Policy compliance and quality monitoring |
| IT and Security | Customer data privacy, identity checks, system access |
| Legal and Compliance | Correct answers, telling customers they're talking to AI, liability for wrong answers |
| Finance | Cost and return on investment |
| Customers | Quick, correct answers and an easy way to reach a person |

*These roles are assumptions. In a real engagement, each would be confirmed with the
people involved.*

## 7. Data and evidence

- **Support conversations:** about 10,000 chats across 55 request types, with the actions
  agents took in each one (ABCD dataset, ASAPP Research, 2021).
- **Agent Guidelines:** the policy rules agents had to follow (included with ABCD).
- **Business assumptions:** chat volume, costs and similar figures, clearly labeled as
  assumptions (see section 11).

## 8. Approach

| Step | What happens | Output |
|---|---|---|
| 1 | Set up the project and agree on the problem | This brief |
| 2 | Explore the conversation data | Analysis notebook |
| 3 | Turn the policy guide into a list of business rules | Business rules table |
| 4 | Sort request types by how much AI could handle | Automation table |
| 5 | Map the current process for the top 3 requests | Process diagrams |
| 6 | Write the requirements | Requirements document (BRD) |
| 7 | Write user stories with acceptance criteria | User stories and Jira board |
| 8 | Define success measures and test cases | Test plan |
| 9 | Build the cost and savings model | Excel ROI model |
| 10 | Build a prototype and run the tests | Prototype and test results |
| 11 | Summarize findings and recommendation | README case study |

## 9. Success measures for the pilot (preview)

Final definitions and targets will be set in Step 8.

- **Containment rate:** share of chats the AI resolves without a human
- **Correct handoff rate:** share of chats passed to a human when they should be
- **Policy compliance rate:** share of answers that follow company policy
- **Wrong-answer rate:** share of answers that are incorrect or made up
- **Customer satisfaction (CSAT):** measured during a real pilot; not testable in the prototype

## 10. Constraints

- No access to real stakeholders, so requirements come from policy documents and data.
- The conversations were role-played by trained crowd workers, not recorded at a real
  company, so volumes and the mix of requests may differ from a live retailer.
- Chat durations may not be in the data (to be confirmed in Step 2). If they aren't,
  handle time will be an assumption.

## 11. Starting assumptions

These are placeholders for the ROI model and will be revised in Step 9.

| Assumption | Starting value |
|---|---|
| Support agents | 40 |
| Chats per month | 30,000 |
| Average time an agent spends per chat | 8 minutes |
| Agent cost per hour, including benefits | $32 |
