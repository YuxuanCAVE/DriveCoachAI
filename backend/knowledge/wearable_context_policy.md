---
id: wearable_context_policy
title: Optional wearable context policy
eventTypes: *
keywords: wearable, heart rate, driver state, medical, stress, fatigue
source: internal_product_policy
confidence: high
version: 2026-06-30
appliesTo: sessions with heart-rate or wearable fields, and questions about driver state
doSay: Treat heart-rate as optional context that may be reviewed next to vehicle telemetry.
doNotSay: Do not diagnose stress, fatigue, health, medical risk, alertness, or impairment from wearable data.
---
Heart-rate or wearable signals are optional driver-state context only. They can help describe when physiological activation changed near a driving event, but the coach must not infer stress, fatigue, diagnosis, health condition, or medical risk from those signals.
