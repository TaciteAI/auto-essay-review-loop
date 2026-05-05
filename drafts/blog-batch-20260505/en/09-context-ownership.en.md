# Context Ownership: The Real Moat Isn't the Model

The most valuable artifact OpenAI owns is not GPT. It is the chat history of three hundred million people who can't take it with them when they leave.

The compute moat gets the press. GPT-4 training cost [around $78 million](https://epoch.ai/blog/how-much-does-it-cost-to-train-frontier-ai-models). Gemini Ultra ran $191 million. Big-four hyperscaler AI capex for 2026 is projected at [up to $660 billion](https://www.cnbc.com/2026/02/06/google-microsoft-meta-amazon-ai-cash.html). Real numbers, wrong moat.

The moat that matters is the one users dig themselves, every day, by typing into a chat box that does not let them export.

## Capability is commoditizing; context is not

DeepSeek shipped a frontier-tier model in late 2024 for [a reported $5.6 million in training compute](https://epoch.ai/blog/how-much-does-it-cost-to-train-frontier-ai-models), benchmarked against closed-frontier rivals that cost $500 million to a billion. Open-weight models — Llama, Mistral, Qwen, DeepSeek — are within roughly a year of closed-frontier performance and shrinking. A 70B-parameter model on a $2,000 box today is roughly the capability you were paying $20 a month for in 2024.

If raw capability is the moat, the moat leaks.

The closed labs are quietly switching moats. The new defensive line is not weights. It is the accumulated context: every chat, every document, every inferred preference, every workflow built around its quirks. That context lives on their servers, trains their next model, and hardens your switching cost.

Try this: export your full ChatGPT history — with attachments, semantic memory, custom instructions — in a format another vendor can ingest tomorrow. You cannot. The button does not exist. That is not an oversight. That is the moat.

## Switching costs masquerading as features

Persistent memory. Project workspaces. Custom GPTs. Connected apps. Each is sold as a productivity feature. Each is a deeper hook into a single vendor.

Enterprise software learned this play in the 1990s. Data in their schema, workflows in their UI, integrations in their marketplace. Migration cost grows linearly with usage until it exceeds whatever the next vendor could save you. The result is captive renewal at whatever price the incumbent can defend.

AI vendors run a sharper version. Your context is not just data — it is the substrate the model conditions on to feel like *yours*. The longer you use it, the more it knows your codebase, your prose voice, your client list. A clean migration means handing all of that to a competitor who doesn't yet know you. So you don't migrate.

[Yale's antimonopoly analysis of AI](https://yalelawandpolicy.org/antimonopoly-approach-governing-artificial-intelligence) names the pattern: concentration is reinforced layer-by-layer, each layer locking the user into the next. Chat history is the user-facing layer. It is also the one regulators have not touched.

## What ownership actually requires

Right-to-export is necessary and not sufficient. A JSON dump with embeddings stripped and tool-call traces lost is not portability. It is a graveyard.

Real ownership has a short, hard spec. Memory store on hardware the user controls. Fine-tunes as local files the user can back up, version, and delete. The agent — the thing that knows what you are working on and how you write — sits as a file on your machine, not a row in someone's database. Remote APIs get called only when the user explicitly chooses, with only the data they explicitly send.

A 70B-parameter open-weight model on a $2,000 workstation makes this architecturally feasible for the first time. Capability is no longer the bottleneck. Discipline is. The default path — paste everything into a hosted chat, accept memory-on, sign the terms — is sharecropping with extra steps, and it compounds.

[Cory Doctorow has been blunt](https://pluralistic.net/2025/03/13/electronic-whipping/#youre-next): the lock-in patterns built on Amazon warehouse workers are now being ported to white-collar tools. The keyboard inherits the scanner.

Policy can help. Mandated portability with embedding-grade fidelity. Antitrust treatment of the GPU and cloud bottlenecks that funnel everyone onto three providers. Right-to-repair-style protections against vendors disabling local AI through firmware. These are the digital-era versions of fights already fought, and largely won, for telephony and the early internet — before those technologies got captured.

The decade's architectural choice is not which chatbot to use. It is whether the chat history that compounds into your second brain lives on your machine or on theirs. Whoever owns the context owns the user. Who owns yours?
