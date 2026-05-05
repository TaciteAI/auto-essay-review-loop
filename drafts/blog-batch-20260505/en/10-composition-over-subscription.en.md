# Composition Over Subscription: The Constellation Beats the Oracle

A 70B-parameter open-weight model on a $2,000 workstation today delivers roughly the capability you were paying $20 a month for in 2024. Three such models, specialized and orchestrated, beat one $200-a-month subscription to a single oracle. Most AI buyers have not internalized this.

The dominant consumer pattern is one chat window from one vendor that tries to do everything. The dominant enterprise pattern is the same thing with an SSO login. Both buy the wrong product. The frontier of useful AI is not bigger general models. It is small specialized models, composed.

## The economics of one giant oracle

A premium consumer subscription runs $200 a month. Enterprise seats run more. Multiply by team size and the math gets ugly — before token overage and the next pricing reset.

Training compute has grown [2 to 3x per year for eight years](https://arxiv.org/abs/2405.21015), with [big-four hyperscaler AI capex projected at up to $660 billion for 2026](https://www.cnbc.com/2026/02/06/google-microsoft-meta-amazon-ai-cash.html). That capex has to be paid back. Your subscription is the amortization schedule.

The architecture is also technically suboptimal. One model trained to do everything is, by construction, average at most things. You pay frontier prices on tasks where a 7B distilled coder, a 13B writing model, and a small vision model — each tuned for its slice — would crush the generalist on quality, latency, and cost.

## Why the constellation wins

DeepSeek shipped a frontier-tier model in late 2024 for [a reported $5.6 million in training compute](https://epoch.ai/blog/how-much-does-it-cost-to-train-frontier-ai-models), against closed-frontier rivals that cost $500 million to a billion. Llama, Mistral, Qwen, and DeepSeek are within roughly a year of closed-frontier and shrinking.

Open-weight specialization changes the unit economics of intelligence. A coding model fine-tuned on your repo beats any generalist on your codebase — it has seen your idioms, your test patterns, your private libraries. A writing model fine-tuned on your published prose preserves your voice in a way no generic chatbot can fake. A retrieval-augmented model with a local index of your documents answers questions about your work, not the open web.

The pieces compose. A small router decides which model handles which request. A local memory store keeps state. An orchestration layer sequences tool use. Remote APIs get called only when the user explicitly chooses.

This is not theoretical. It is what every team shipping AI features in production converged on after trying to scale one giant prompt to one giant model. The single-oracle pattern is fine for demos. It collapses under workload.

## The concentration argument cuts both ways

The standard worry is that the AI stack is concentrated. [Yale's antimonopoly analysis](https://yalelawandpolicy.org/antimonopoly-approach-governing-artificial-intelligence) is direct: severe concentration at multiple layers simultaneously — Nvidia for chips, three hyperscalers for cloud, a handful of labs for frontier-closed models.

That is correct at the substrate. It is wrong at the application layer if users actually compose. In a constellation architecture, the hyperscaler is one component, not the platform. Swap a frontier API call for a local 70B run and the bill drops by an order of magnitude. Swap the coding model for an updated checkpoint and nothing else changes. Orchestration, memory, and fine-tunes stay on your machine.

The entire moat the closed labs are building — context lock-in, switching costs, agent integrations — assumes you keep everything inside one vendor's walls. Composition pulls the walls down.

## What this looks like to actually use

The 2027 stack a serious user runs: a local router on a $2,000 workstation. Three to five open-weight models, each tuned to a domain. A vector index of personal documents. A persistent memory store backed up like any other file. Frontier API access for the small fraction of queries where it actually beats the local stack — billed by the token, not the seat.

Monthly cost: less than the subscription it replaces. Quality: higher. Switching cost: zero, because orchestration and memory are user-owned.

A solo lawyer with a private legal model on her own machine is not a junior associate at a firm. She is a firm. A small business with a private agent for books, marketing, and support is not paying a 30% AI tax to a hyperscaler. A community clinic running a private medical-question model is not a captive customer of a hospital chain's vendor. It is a peer.

The architectural choice the next five years lock in is not which subscription to buy. It is whether to keep buying subscriptions at all. The constellation beats the oracle. The only question is who owns yours.
