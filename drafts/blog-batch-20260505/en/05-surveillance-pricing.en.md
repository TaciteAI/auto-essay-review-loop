# Surveillance Pricing: When Perfect Price Discrimination Became a Checkout Flow

For a hundred years, "perfect price discrimination" was a phrase economists used to describe a limit case — a thought experiment in which a seller charges every buyer exactly what they would pay and not a cent less. In January 2025 the [Federal Trade Commission's 6(b) inquiry](https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-surveillance-pricing-study-indicates-wide-range-personal-data-used-set-individualized-consumer) confirmed it had stopped being a thought experiment. It is now a checkout flow.

## What the data actually feeds the model

The FTC found that companies use mouse movements, abandoned-cart contents, time of day, device type, location, browsing history, and demographic proxies to set individualized prices. Skin tone has been used as a pricing input. The FTC's [issue spotlight on surveillance pricing](https://www.ftc.gov/system/files/ftc_gov/pdf/sp6b-issue-spotlight.pdf) documents that the inputs are not exotic — they are standard ad-tech telemetry repurposed for the price tag.

What the textbooks call "willingness to pay" is now an estimable quantity. A model watches you hesitate over a $42 sweater, watches you check the same SKU on a competitor's site, watches you come back at 11pm after payday — and quotes you a number calibrated to extract as much of the gap between value and price as the seller can.

The classical theory was clear about the consequence: the entire consumer surplus transfers to the seller. AI is the first technology that makes the calculation tractable at population scale, in real time, on a per-session basis. The constraint that kept this in textbooks — the cost of measuring each buyer — fell away.

## The poor pay more, by design

The cyberpunk reading is exact, and the FTC has put it on the record: surveillance pricing disproportionately harms marginalized groups, because behavioral proxies for desperation, urgency, and lack of alternatives correlate sharply with race, geography, and income. The shopper with five tabs open and a credit-card balance gets a different price than the shopper who closes the window and goes to lunch.

This isn't a bug in the model. It *is* the model. The objective function is to maximize extracted surplus, and the population that can extract less surplus from is exactly the population with options. The population with no options gets the bill.

Consider the mechanics. A ride-hailing app sees your battery is at 4% and you've been refreshing for three minutes. A car-insurance quoter sees you've already declined two competitors. A buy-now-pay-later widget sees your cart abandonment history. None of these signals correlate with the cost of providing the service. All of them correlate with the seller's leverage.

## Why regulation runs years behind the capability

State legislatures noticed late. According to a [2025 review by Snell & Wilmer](https://www.swlaw.com/publication/algorithmic-pricing-under-the-antitrust-microscope-doj-and-ftc-sharpen-their-enforcement-posture/), 24 states introduced more than 50 bills regulating algorithmic pricing in 2025, and California's Attorney General opened an enforcement sweep on January 27, 2026.

That is meaningful and inadequate. Meaningful because it signals political recognition. Inadequate because the underlying capability is now general-purpose, cheap, and embedded across e-commerce, ride-hailing, insurance, lending, and increasingly healthcare and rental housing. Banning one input — say, ZIP code — does nothing to a model that can reconstruct ZIP from the seventy other features it already has.

The deeper problem is that the modern stack hides the discrimination from the buyer. The price you see is the price you see. There is no "list price" you are being given a discount or surcharge against. There is no second buyer to compare your number to. The market signal that historically disciplined sellers — *people noticing they got a worse deal* — is engineered out of the interface.

Aggressive disclosure rules would help. So would mandated reference prices, audit access for regulators, and statutory liability for race-correlated outputs regardless of intent. The Yale Law & Policy Review's [antimonopoly analysis of AI](https://yalelawandpolicy.org/antimonopoly-approach-governing-artificial-intelligence) argues for treating personalized pricing as a structural concentration problem rather than a case-by-case consumer-protection issue. That framing is closer to the scale of the thing.

## The forward question

Surveillance pricing is the cleanest demonstration available of a more general pattern: a capability that economists treated as theoretically extreme has become operationally routine, and the regulatory apparatus is calibrated to a world where it was rare. The next iteration — agents on the buyer side that negotiate against the seller's model — may flip the dynamic, or may simply produce a higher-stakes arms race on the same field.

If price itself is no longer a market signal but a per-user output, what discipline replaces it?
