# DeepSeek's $5.6M Frontier Model: What the Leak in the Moat Actually Buys You

DeepSeek shipped a frontier-tier model in late 2024 for [a reported $5.6 million in training compute](https://epoch.ai/blog/how-much-does-it-cost-to-train-frontier-ai-models). Its U.S. closed-frontier counterparts — GPT-4 at roughly $78 million, Gemini Ultra at $191 million, Llama 3.1 405B at $170 million — were trained for one to two orders of magnitude more. That spread is the most important data point in the AI economy, and it is widely misread.

## What the gap proves

The naive reading is "frontier AI is now cheap." It isn't. DeepSeek's $5.6M is the marginal training cost of one specific run, conducted by a team with prior infrastructure, prior data pipelines, prior research staff, and access to GPUs procured before export controls bit. The all-in cost is far higher than the headline. Anyone telling you a startup can replicate it for $5.6M is selling something.

What the gap *does* prove is that the assumed coupling between frontier capability and hyperscale capex was wrong. For eight years frontier compute has grown [2 to 3x per year](https://arxiv.org/abs/2405.21015), and the prevailing thesis was that capability tracked compute linearly. DeepSeek demonstrated that algorithmic and architectural efficiency can compress the cost by an order of magnitude without giving up frontier benchmark performance. That is a structural result, not a one-time arbitrage.

The implication is that the moat the hyperscalers are digging — the [$660 billion AI capex year for 2026](https://www.cnbc.com/2026/02/06/google-microsoft-meta-amazon-ai-cash.html) — does not buy what its capitalization assumes. It buys some lead. It does not buy a permanent rent.

## What the leak buys you

If you are not OpenAI, Anthropic, or Google, the DeepSeek result has three operational consequences.

First, *open-weight is now a credible production target*, not a hobbyist tier. Llama, Mistral, Qwen, and DeepSeek release weights at roughly a one-year lag behind closed frontier — and the lag is shrinking. For most production workloads — coding assistants, document QA, structured extraction, customer support, internal tools — the closed-frontier-only era is over. The right architecture choice is increasingly local-first with closed-API fallback for the narrow tasks that still need it.

Second, *the unit economics of being a model consumer flipped*. When a 70B-parameter open-weight model runs on a workstation that costs less than a year of enterprise API spend, the build-versus-buy calculation changes for every CTO who runs the numbers. The lock-in moat the labs are extending — context history, fine-tuning, prompt scaffolding — is now competing against a credible exit ramp.

Third, *China's AI sector is a structurally different problem* than the U.S. policy conversation pretends. Export controls were designed around an assumption — frontier capability requires NVIDIA H100s and the latest TSMC node — that DeepSeek partially refuted. The assumption that capability gates can be enforced at the silicon layer needs revision when the algorithmic layer is doing this much of the work.

## What it doesn't buy

The DeepSeek result is not a permission slip to claim the AI economy is decentralizing. The substrate remains concentrated. The Yale Law & Policy Review's [antimonopoly analysis of AI](https://yalelawandpolicy.org/antimonopoly-approach-governing-artificial-intelligence) catalogs the layered concentration: Nvidia for chips, three hyperscalers for cloud, a handful of labs for frontier closed models. Open-weight releases compete at the model layer; they do not compete at the chip or cloud layers. If you train a 70B model on rented H100s, you still pay rent — just to a different counterparty.

The result also does not invalidate the labor displacement thesis. Cheaper frontier capability deployed against the same task set produces the same displacement at a lower cost. Cheaper AI is not the same as more egalitarian AI. The labor share of GDP has fallen from [64% in 1974 to roughly 56% by 2024](https://news.mit.edu/2022/automation-drives-income-inequality-1121), and nothing about a more efficient training run reverses that trend. If anything, it accelerates it by lowering the capex hurdle for the next CFO who wants to thin out a department.

## The forward question

DeepSeek's $5.6M is best read as evidence about the *direction* of the cost curve, not its current level. Frontier training cost is still in the hundreds of millions for the leading-edge labs, and Amodei has openly forecast $10 billion training runs by 2028. The frontier moves up while the cost-to-replicate-last-year's-frontier moves down. Both are true.

The strategic question for everyone outside the top three labs is which curve to bet on — the rising frontier, or the falling replication cost. Most enterprise workloads are downstream of last year's frontier. Most political and labor-market effects are downstream of widespread deployment, not bleeding-edge capability. The DeepSeek trajectory says the second curve is real and accelerating. What does that imply for your stack a year from now?
