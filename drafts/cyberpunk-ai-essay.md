# High Tech, Low Life: How AI Builds the Cyberpunk Future We Were Warned About

The most damaging thing AI does to labor isn't the layoff. **It's that AI removes the on-ramp into expertise itself** — the lattice of junior roles that historically converted ambition into a middle-class life. Entry-level postings have [fallen ~35% since January 2023](https://fortune.com/2026/04/29/ai-agentic-entry-level-jobs-disappearing-yale-celi-sonnenfeld/). New CS graduates face 7.0% unemployment. Young software developers are off [nearly 20%](https://fortune.com/2026/04/29/ai-agentic-entry-level-jobs-disappearing-yale-celi-sonnenfeld/) since late 2022.

Bruce Sterling and William Gibson called this *high tech, low life* — neon and orbital labs over a city that can't keep the water on. The risk isn't Skynet. It's that AI quietly finishes a forty-year project: concentrate wealth at the top, hollow the middle, lock the bottom into algorithmically managed precarity with no rung up.

There is an exit. It needs both a **collective fight** — public compute, open weights, antitrust against the cloud bottleneck, data portability rules, labor protections against algorithmic management — and an **individual move**: AI you own and run yourself, instead of AI you rent from OpenAI, Google, and Anthropic. The rest of this essay walks the mechanism, then sketches what each of those exits looks like.

## Five companies own the AI substrate

Modern AI is expensive at sovereign scale.

Training GPT-4 cost around $78 million in compute, [per Epoch AI](https://epoch.ai/blog/how-much-does-it-cost-to-train-frontier-ai-models). Gemini Ultra ran an estimated $191 million. Llama 3.1 405B came in around $170 million. Costs have grown by [2 to 3x per year for eight years running](https://arxiv.org/abs/2405.21015), putting frontier training past a billion dollars by 2027. Anthropic's Dario Amodei has openly forecast $10 billion training runs by 2028.

These aren't startup numbers. They're sovereign-wealth-fund numbers. The big four cloud companies — Microsoft, Google, Amazon, Meta — are projected to spend up to [$660 billion on AI capex in 2026 alone](https://www.cnbc.com/2026/02/06/google-microsoft-meta-amazon-ai-cash.html).

The optimist's response is that the moat is leaking. DeepSeek shipped a frontier-tier model in late 2024 for a reported $5.6 million, against U.S. closed-frontier rivals at $500M–$1B. Capability is getting cheaper to produce. That is real, and it is the foundation of the exit ramp argued below.

But "cheaper" still leaves the substrate concentrated. [Yale Law & Policy Review's antimonopoly analysis](https://yalelawandpolicy.org/antimonopoly-approach-governing-artificial-intelligence) is blunt: the AI stack is severely concentrated at multiple layers — Nvidia for chips, three hyperscalers for cloud, a handful of labs for frontier models. Each layer reinforces the next.

Whoever owns the compute owns the labor surplus. If the machine that does the work is owned by five companies, the rents flow to five companies. The incumbents are not being disrupted. They are extending.

## AI hollows the middle and breaks the on-ramp

[Daron Acemoglu's research at MIT](https://news.mit.edu/2022/automation-drives-income-inequality-1121) finds that automation explains 50–70% of the rise in U.S. wage inequality from 1980 to 2016. Not globalization. Not unions falling. Automation. Wages of men without a high school degree fell 8.8% in real terms over that span as a direct result.

Acemoglu's key concept is **so-so automation** — technology just barely good enough to replace a worker but not productive enough to grow the pie. Self-checkout kiosks are the textbook case. Savings flow to capital; displaced workers compete for fewer remaining roles.

Generative AI is, for many tasks, exactly this. It can handle the junior associate's first draft, the paralegal's deposition summary, the tier-1 support ticket, the entry-level analyst's deck. It cannot yet make the senior partner ten times more productive. Headcount cuts at the bottom; bid-up at the top for the few who can wield the tool.

[Citrini Research's 2028 Global Intelligence Crisis](https://www.citriniresearch.com/p/2028gic) puts a number on the trajectory: U.S. labor's share of GDP fell from 64% in 1974 to 56% in 2024, and they project 46% by 2028 — the sharpest decline on record. They call it the *Intelligence Premium Unwind*: the historical repricing of scarce human cognition as abundant machine cognition takes its place.

The 2026 data shows the early signature. A factory worker displaced in 1985 could in principle become a data analyst by 2005. The displaced data analyst of 2026 looks at a world where "data analyst" is itself the role being eliminated, and the hiring funnel into anything cognitive starts with "we don't hire juniors anymore — the model handles that work." As [Fortune put it](https://fortune.com/2026/04/29/ai-agentic-entry-level-jobs-disappearing-yale-celi-sonnenfeld/): AI won't kill your job — it will kill the path to your first one.

This is how a society stops being mobile. Not a dramatic event. A slow, statistically invisible removal of the rungs.

## Algorithmic management: the new sharecropping

The image of low life isn't a soup line. It's a person working ten hours under fluorescent lights with a scanner that beeps every fourteen seconds and a screen that says their pace is below quota.

That image is documented. At Amazon warehouses, instructions arrive through workstation displays and barcode scanners — every scan triggers the next task and every movement is tracked. At Amazon's Manesar warehouse in India, a system called [ADAPT](https://www.medianama.com/2025/12/223-algorithms-gig-workers-india-new-study/) continuously measures productivity, with penalties for missed targets or mistakes detected on CCTV.

A 2025 Northwestern study, [Weaponizing the Workplace](https://journals.sagepub.com/doi/10.1177/23780231251318389), documented something colder: Amazon repurposed those same management tools to gauge union sympathies and push anti-union messaging during the Bessemer, Alabama campaign. *The device that tells you what to do also tells management how to break your organizing.*

This isn't AI replacing workers. It's the worse case: AI managing them. An algorithm sets the pace. A camera enforces it. A model sets the next quarter's quota from data the camera collected. The worker is a peripheral, with no manager to talk to about an unfair shift — the rule was set in code, owned by a company whose lawyers know it doesn't have to explain itself.

[Cory Doctorow's framing](https://pluralistic.net/2025/03/13/electronic-whipping/#youre-next) applies: the future of Amazon coders is the present of Amazon warehouse workers. The toolkit was built on people whose lack of bargaining power made them easy targets, and is now being ported up the org chart. Pull-request velocity dashboards. Per-keystroke productivity scores. Auto-generated performance reviews from Slack and email content. The frame on this isn't paranoia. It's the org chart.

## Surveillance pricing: charging the poor more

If you only had one mechanism to point to as proof that the gap is materializing, it would be surveillance pricing.

[The FTC's 6(b) inquiry](https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-surveillance-pricing-study-indicates-wide-range-personal-data-used-set-individualized-consumer) confirmed that companies use mouse movements, abandoned-cart contents, location, browsing history, demographic proxies, time of day, and device type to set individualized prices. Skin tone has been used as a pricing input. These features feed models that estimate a buyer's willingness to pay and quote a price calibrated to extract as much of it as possible.

Classical economics calls this *perfect price discrimination*: the entire consumer surplus — the gap between what something is worth to you and what you pay — gets transferred to the seller. AI makes this approximately tractable for the first time at scale.

The FTC notes this [disproportionately harms marginalized groups](https://www.ftc.gov/system/files/ftc_gov/pdf/sp6b-issue-spotlight.pdf), because behavioral proxies for desperation, urgency, and lack of alternatives correlate sharply with race, geography, and income. The reading is exact: the rich get a better price because the algorithm thinks they can shop around; the poor get a worse price because the algorithm has watched them fail to.

[24 states introduced more than 50 bills](https://www.swlaw.com/publication/algorithmic-pricing-under-the-antitrust-microscope-doj-and-ftc-sharpen-their-enforcement-posture/) regulating algorithmic pricing in 2025, and California's AG opened a sweep in January 2026. But the capability is now general-purpose, cheap, and embedded across e-commerce, ride-hailing, insurance, lending, and increasingly healthcare. Regulation is downstream of capability, and the capability is here.

## Why antitrust and politics will lag

The standard rebuttal — "antitrust will handle it" — fails on the timeline that matters.

The DOJ's case against Google's search monopoly took five years from filing to remedies. EU cases against the same company have run more than a decade across multiple cycles. Antitrust is *ex post* and case-by-case by design — built to address yesterday's monopoly tomorrow.

Meanwhile the AI compute stack is already concentrated, and the next cycle's monopoly is being capitalized today: Microsoft entangled with OpenAI, Amazon with Anthropic, Google with itself, every hyperscaler with Nvidia.

The political path looks worse. AI labs have the capital to lobby, the rhetorical advantage of "we are building the future," and a national-security framing — "we have to win against China" — that is genuinely true *and* aligned with their commercial interests. Too useful to break up, too critical to regulate, too entangled with state power to confront.

## Three derailers: open weights, augmenting AI, political mobilization

This story might still be wrong. Three real possibilities could break it.

### 1. Open weights collapse the compute moat faster than concentration locks in

DeepSeek's $5.6M model is the canonical example. If open-weight models keep closing the gap with closed labs, the rents at the top get competed away and AI becomes a commodity input like electricity. Plausible. Not what the capex numbers suggest, but plausible — and it's the foundation of the individual exit ramp below.

### 2. AI augments instead of replacing

Acemoglu's framework allows for shared gains when automation *augments* tasks rather than replacing them. If AI tools meaningfully raise the productivity of nurses, teachers, electricians, and small-business owners, the bottom 60% captures real gains.

The catch: current deployments skew toward replacement (call centers, copywriting, support, paralegals) because replacement shows as a clean cost line in a CFO's deck and augmentation does not. As Citrini observes, AI also tends to improve at the *same tasks humans redeploy to* — breaking the historical escape valve. This is a policy choice fighting a strong current, not a technological inevitability.

### 3. Political mobilization rebalances faster than capital concentrates

The 24 state algorithmic-pricing bills, the FTC's surveillance-pricing study, the [growing labor research on algorithmic management](https://arxiv.org/html/2508.09438v1), the live Google antitrust remedies — these are real. They are not yet at the scale of the problem, but movements precede legislation.

None of these is on autopilot. All require active political and economic choices currently being out-spent, out-lobbied, and out-paced.

## The equilibrium, in plain language

A handful of firms control the substrate the next decade's productive economy runs on. They charge what they like for it because there is no alternative.

Productivity gains flow to capital because labor's share has been falling for forty years and AI accelerates the trend. Entry-level work is automated first, eliminating the on-ramp before the next generation can reach it. The work that remains is mediated by algorithms that set the pace, score the worker, and resist organization. The prices the bottom pays are individually optimized to extract more than the prices the top pays for the same goods.

Antitrust runs ten years behind the capability. Politics runs five years behind antitrust.

The neon is not the threat. The neon is the cover story.

## The collective exit: public compute, open weights, antitrust, labor power

The cyberpunk equilibrium is built on a few firms owning the model that everyone else has to rent by the token. The collective exit has to invert that property at the level of policy.

The fights worth having most:

- **Public compute and open-weight model funding.** National AI labs in the public-utility sense — building, training, and releasing weights for general use — not "national champions" entrenching the same private incumbents.
- **Antitrust against the GPU and cloud bottleneck.** The chokepoint isn't the model anymore; it's whose data centers it runs in. Three providers should not be the answer.
- **Data portability and right-to-export rules.** A user moving off a closed API should be able to take their context, fine-tunes, and chat history with them — the way they take an email archive when they switch providers.
- **Labor protections against algorithmic management.** Audit rights for the algorithms that score workers, transparency requirements for pace-setting and discipline systems, organizing protections that explicitly cover algorithmically mediated workplaces.
- **Regulation of surveillance pricing.** The 24-state bill wave is the right direction; what's missing is a federal floor.

These aren't exotic. They're the digital-era versions of fights already fought, and largely won, for electricity, telephony, and the early internet — *before* those technologies got captured.

## The individual exit: own the machine

The collective fight will take years. While it runs, there is something an individual can do this year. **Whether AI is something a person owns or something a person rents from OpenAI, Google, and Anthropic is the most important architectural choice the next decade will make on a per-user basis.**

It comes down to three properties.

**Weights run on hardware you control.** A model running locally is one whose telemetry doesn't leave your house, whose pricing doesn't depend on a third party's quarterly earnings, and whose availability cannot be revoked because you said something a content policy doesn't like. Open-weight models — Llama, Mistral, Qwen, DeepSeek — are now within roughly a year of frontier-closed performance. A 70B-parameter model on a $2,000 desktop today is roughly the capability you were paying $20/month for in 2024.

A working stack today: a desktop with one or two consumer GPUs running [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai), a personal vector database holding your documents and notes, and a local agent layer that escalates to a remote API only when you explicitly approve. A few thousand dollars one-time, then ~$50/month in electricity for unlimited inference.

**Your context belongs to you, not to a vendor.** The deepest moat the closed labs are building isn't the model — it's the accumulated context: every chat, every document, every preference, every workflow, sitting on their servers, locked in by switching costs. Personal AI inverts this: the memory store is on your machine, the fine-tunes are yours, your *agent* is a local artifact you can back up, version, port, and delete. Anything less is sharecropping with extra steps.

**Composition over subscription.** A small set of specialized open-weight models — coding, writing, vision — orchestrated locally, augmented by a personal knowledge base you control, talking to remote APIs only when you choose to and only with the data you choose to send. Harder than typing into chat.openai.com. Also the only architecture that doesn't end with one company sitting between you and your own thoughts.

This is not a Luddite position. The cyberpunk failure mode is *too few people benefit from too much capability*. Personal AI bets that the same capability, distributed and owned by individuals, produces a fundamentally different political economy:

- A solo lawyer with a private legal model on her own machine is not a junior associate — she is a firm.
- A community clinic running a private medical-question model is not a captive customer — it is a peer.
- A small business with a private agent that handles its books and support is not paying a 30% AI tax to a hyperscaler — it is keeping that margin and competing.

Personal AI doesn't fix mass labor displacement on its own. The collective fight has to do that. But it's the move available right now to anyone who would rather not be a tenant in someone else's intelligence.

The choice the next five years lock in is not "AI or no AI." That ship has sailed. It's whether AI ends up like the public road — universally available, mostly neutral, occasionally taxed — or like a private feudal estate, with a few lords renting access to peasants by the query.

The exit ramp is to own the machine. The collective fight is to make sure the road stays open for everyone.

---

## Sources

- [AI won't kill your job — it will kill the path to your first one — Fortune](https://fortune.com/2026/04/29/ai-agentic-entry-level-jobs-disappearing-yale-celi-sonnenfeld/)
- [Tech AI spending approaches $700 billion in 2026 — CNBC](https://www.cnbc.com/2026/02/06/google-microsoft-meta-amazon-ai-cash.html)
- [How much does it cost to train frontier AI models? — Epoch AI](https://epoch.ai/blog/how-much-does-it-cost-to-train-frontier-ai-models)
- [The rising costs of training frontier AI models (arXiv 2405.21015)](https://arxiv.org/abs/2405.21015)
- [An Antimonopoly Approach to Governing Artificial Intelligence — Yale Law & Policy Review](https://yalelawandpolicy.org/antimonopoly-approach-governing-artificial-intelligence)
- [Study: Automation drives income inequality — MIT News](https://news.mit.edu/2022/automation-drives-income-inequality-1121)
- [The 2028 Global Intelligence Crisis — Citrini Research](https://www.citriniresearch.com/p/2028gic)
- [Weaponizing the Workplace: How Algorithmic Management Shaped Amazon's Antiunion Campaign — Sage Journals](https://journals.sagepub.com/doi/10.1177/23780231251318389)
- [Fulfillment of the Work Games: Warehouse Workers' Experiences with Algorithmic Management (arXiv)](https://arxiv.org/html/2508.09438v1)
- [Algorithms Decide How Gig Workers Work In India — Medianama](https://www.medianama.com/2025/12/223-algorithms-gig-workers-india-new-study/)
- [The future of Amazon coders is the present of Amazon warehouse workers — Cory Doctorow / Pluralistic](https://pluralistic.net/2025/03/13/electronic-whipping/#youre-next)
- [FTC Surveillance Pricing Study — Federal Trade Commission](https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-surveillance-pricing-study-indicates-wide-range-personal-data-used-set-individualized-consumer)
- [Issue Spotlight: The Rise of Surveillance Pricing — FTC](https://www.ftc.gov/system/files/ftc_gov/pdf/sp6b-issue-spotlight.pdf)
- [Algorithmic Pricing Under the Antitrust Microscope — Snell & Wilmer](https://www.swlaw.com/publication/algorithmic-pricing-under-the-antitrust-microscope-doj-and-ftc-sharpen-their-enforcement-posture/)
