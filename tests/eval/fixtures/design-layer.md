# PROJ-201 — Deliver order-confirmation webhooks with at-least-once retry

**Requirement:** When an order is placed, POST a confirmation to the customer's configured webhook
URL through the real outbound HTTP client.

**Goal:** A transient downstream failure must not drop the notification.

**Acceptance Criteria:**
- When the downstream endpoint returns `503` on the first attempt, the webhook is retried and the
  customer eventually receives exactly one confirmation.
- The retry uses exponential backoff and gives up after 5 attempts, recording the final failure.
