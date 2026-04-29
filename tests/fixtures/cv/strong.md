# Maya Patel

San Francisco, CA | maya.patel@example.com | (415) 555-0142 | github.com/mpatel

## Summary

Backend engineer focused on payment infrastructure at fintech scale. Took the auth pipeline at PayCanvas from 4 nines to 5 nines while halving on-call load.

## Experience

### Senior Engineer, PayCanvas (Mar 2022 – Present)

- Drove the auth-pipeline migration from a sticky-session monolith to a stateless service mesh; reduced p99 latency from 340ms to 90ms across 12M requests/day.
- Reduced auth on-call paging volume by 54% over 6 months by instrumenting the top 8 failure modes and shipping circuit breakers for each.
- Designed and shipped the idempotency-key layer that now sits in front of 4 internal payment services; eliminated 11 duplicate-charge incidents in the first 90 days.
- Mentored 3 mid-level engineers through quarterly architecture reviews; 2 promoted to senior within 9 months.
- Owned the auth team's 24-month deprecation plan for the legacy session store; migrated 100% of traffic with zero customer-visible downtime.

### Engineer, Indigo Logistics (Aug 2019 – Feb 2022)

- Built the multi-tenant rate-limiting service that protected 38 internal APIs; absorbed a 14x traffic spike during the 2021 holiday peak with zero rate-limit-induced outages.
- Migrated 6 internal services from polling to event-driven workflows on Kafka; cut median end-to-end processing time from 11 minutes to 38 seconds.
- Refactored the order-placement state machine; reduced order-stuck-in-pending tickets from 240/week to under 20/week.
- Wrote the post-mortem template the platform org adopted as its standard; ran 9 incident reviews in 18 months.

### Engineer, Brightline Tools (Jul 2017 – Jul 2019)

- Shipped the in-app billing rewrite that took monthly revenue reconciliation from 4 days to 2 hours.
- Automated the QA test pipeline; reduced average release cycle from 11 days to 3 days.
- Launched the customer-facing API documentation site; increased self-serve API adoption by 38% in 6 months.

## Education

### B.S. Computer Science, University of Illinois Urbana-Champaign (Aug 2013 – May 2017)

- Coursework: distributed systems, compilers, databases, algorithms.
- Senior project: a fault-tolerant key-value store benchmarked against etcd; presented at the department research symposium.

## Skills

- Languages: Go, Python, TypeScript
- Infrastructure: Kubernetes, Terraform, AWS (EKS, RDS, S3, Lambda)
- Data: PostgreSQL, Kafka, Redis, ClickHouse
- Practices: incident review, on-call rotation design, mentorship

## Projects

### kvlite (open source)

- Built a 600-line embedded key-value store in Go; 1.4k GitHub stars; used as a teaching reference in 2 university courses.
