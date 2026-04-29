# Three Lessons from Shipping My First SaaS

I shipped my first paid product at 2:14am on a Tuesday in February. By Friday I had three customers, two churned, and one bug report I couldn't reproduce. Here's what the first month taught me.

## Lesson 1: The Landing Page Is the Product (For a While)

Before anyone uses your software, they read your landing page. For maybe three weeks of my launch, the landing page was the product — every conversion came from a single H1 and a 90-second demo video. The actual app could have been replaced with a Google Form and the conversion rate wouldn't have moved.

What I'd do differently: spend two days writing the landing page before I write any code. If I can't explain it on a page, the product isn't real yet.

For a deeper dive on this, [Patrick McKenzie wrote the canonical version](https://example.com/) about a decade ago and it still holds up.

## Lesson 2: The First Three Customers Are Worth a Quarter Each

I read [Paul Graham's essay on doing things that don't scale](https://example.com/) before I shipped, agreed with it, and still didn't take it seriously enough. My first three customers got a 30-minute onboarding call from me personally. One of them is still my biggest account ten months later. The other two churned, but both told me exactly why — and one of those reasons (no team-seat support) became my Q2 roadmap.

If I'd done what I planned — a polished email sequence, a help-center article, no calls — I'd have less revenue and zero qualitative signal.

### What "doesn't scale" looks like in practice

Three things, all unglamorous:

- I wrote the welcome email by hand for the first 20 signups.
- I screen-shared with anyone who asked a setup question.
- I texted (not Slacked, not emailed — texted) the two paying customers when I shipped a feature they'd asked for.

The texts had a 100% reply rate. The emails would have had maybe 30%.

## Lesson 3: My Roadmap Was Wrong (Predictably Wrong)

Before launch, my roadmap had eleven features in priority order. Six months in, I'd shipped seven of them. Of those seven, two were used heavily, two were used once and abandoned, and three were never touched by any customer.

The four I hadn't shipped? Customers asked for two of them in week one.

```python
# What my prioritization actually looked like, in pseudocode:
def what_i_built(features):
    return sorted(features, key=lambda f: my_excitement_level(f))

def what_i_should_have_built(features, customers):
    return sorted(features, key=lambda f: count_customer_requests(f, customers))
```

The lesson isn't "listen to customers" — that's a cliché and it's also wrong sometimes. The lesson is: my prior on what customers want is much weaker than I thought, and the only cure is to ship something and watch.

## What I'm Doing in Year Two

Less planning, more shipping. Smaller releases, more often. And the landing page gets rewritten before any feature ships, every time.

If you want the boring details — pricing changes, churn analysis, the spreadsheet I use to track requests — they're in [my followup post](https://example.com/).

Thanks for reading. If any of this resonates, the followup post is the next thing to read.
