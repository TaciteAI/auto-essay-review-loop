---
marp: true
title: Why our checkout broke (and what we did about it)
---

# Checkout broke for 4% of users on Black Friday

Subtitle: a postmortem and the three changes that fixed it

<!-- Open with the impact number. The audience cares about the dollar figure first; the technical detail comes later. Spend 30 seconds here. -->

---

## Agenda

- The incident in numbers
- What we thought was wrong
- What was actually wrong
- The three fixes
- What we changed about how we work

<!-- Walk the agenda fast. Don't read it; preview only. -->

---

## $1.2M of revenue stalled in 90 minutes

- Cart-to-purchase conversion fell from 31% to 18%
- Affected only mobile Safari users on iOS 17.4
- We did not get paged for the first 47 minutes

<!-- The numbers do the work. Pause on the 47 minutes — that's the most embarrassing one. -->

---

## We blamed Stripe first

- Latency on /v1/charges spiked at the same minute
- We rolled back our deploy thinking it was us
- Both turned out to be coincidence
- Real lesson: correlated timing is not causation

<!-- Confess fast. The audience trusts you more after you admit you got it wrong. -->

---

## The actual cause was a Safari iOS 17.4 ITP change

- Apple shipped an Intelligent Tracking Prevention update overnight
- Our session cookie's SameSite attribute became a hard reject
- We discovered it via a single Sentry breadcrumb at minute 71

<!-- Show the breadcrumb on screen if Wi-Fi cooperates; otherwise describe it. -->

---

## Fix 1: cookies migrated to SameSite=Lax with a Secure flag

- Took 4 hours to ship; required a session-store migration
- Restored 80% of lost conversion within 2 hours of deploy
- Code change was 12 lines; the deploy gate took the rest

<!-- 12 lines. That's the line that gets the laugh. Pause for it. -->

---

## Fix 2: synthetic checkout monitor that actually checks Safari

- Old monitor only ran on headless Chrome, missed all Safari issues
- New monitor runs every 5 minutes against real iOS Simulator
- Pages on-call within 90 seconds of conversion drop

<!-- This is the slide an exec might quote later. Make sure it's crisp. -->

---

## Fix 3: revenue-loss alerting tied to dollar amount, not error rate

- Old alert: 5xx error rate > 0.5% for 5 minutes
- New alert: revenue/min drops 30% below trailing-90-min average
- Catches silent failures that don't throw 5xx errors

<!-- This is the slide engineering teams should steal. Open-source the spec on the blog. -->

---

## We changed three things about how we work

- All synthetic monitors must include the top-3 user platforms
- Postmortem actions go on the on-call rotation, not "someone's roadmap"
- We now track $/min as a first-class metric in Grafana

<!-- The cultural fixes matter more than the code fixes. Land this slide. -->

---

## Takeaways

- Correlation is not causation, even on the dashboard
- Browser ITP changes are silent killers; treat Safari as a tier-1 platform
- Tie alerts to revenue, not error codes

<!-- One sentence per bullet when delivered live. Don't read the slide. -->

---

## Questions

<!-- Open the floor. Have answers ready for: "what did Stripe say later?" and "why no pre-prod canary?" -->
