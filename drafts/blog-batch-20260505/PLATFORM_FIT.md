# Platform-fit notes for the 20-blog batch

All drafts are written as 500–800 word blog posts in plain markdown so they
port across any of the six target platforms with minimal rework. Below is the
recipe per platform — how to adapt each draft when posting.

## LinkedIn (long-post format)

- Paste the full markdown body. LinkedIn renders bold and links inline.
- LinkedIn collapses paragraph breaks above ~1,300 chars into a "see more"
  fold. Make sure the H1 title + first paragraph + first H2 fit above that
  line — these drafts are written to do that.
- Strip the literal `# H1` header line; promote it into the LinkedIn post
  title field. Same for the `## H2`s — re-render as bold lines or leave as
  body, depending on the deck's house style.
- LinkedIn clamps URLs but does open-graph preview the first link. Put the
  most reputable / shareable source link first.
- Suggested cadence: 2–3 posts/week from this batch. Don't dump all 20.

## X (Twitter, ≤280 chars)

- Each draft has a load-bearing opening sentence. That's the hook tweet.
- For threads: H1 = tweet 1, each H2 + first paragraph = a follow-up tweet,
  with a single source link in tweet 2 or the final tweet.
- Strip all markdown. Strip `[anchor](url)` to plain `url` (X auto-shortens).
- One hashtag max if any. The drafts have none — that's intentional; you
  may add one (`#AI`, `#economics`) when posting if your audience expects it.
- For pure single-tweet pulls: the H1 + the last sentence of the post is
  often a shippable two-line tweet (claim + sting).

## Facebook

- Treat as a softer LinkedIn. Paste the body, including H2s as bolded lines.
- FB favors visuals — pair with one chart or one screenshot pulled from the
  source articles (FTC release, BLS data, etc.). Caption it with the post's
  most-quoted line.
- Avoid the academic register if your FB audience is family/friends; for a
  professional FB page these drafts are fine as-is.

## WeChat (公众号)

- Paste the Chinese version (`cn/`) into 公众号 后台 编辑器.
- Title: use the Chinese H1, optionally append a 副标题 (subtitle) like
  "AI 时代的劳动经济观察"  to anchor the column.
- Add a 头图 (cover image) — neutral data viz works best. The 公众号
  algorithm prefers original images.
- 公众号 truncates at the Chinese-character equivalent of ~3 screens; first
  H2 must arrive before that. Drafts are written to do this.
- One post per day max if you want sustained reach; spacing matters more
  than batching.

## Redbook (小红书)

- Redbook is image-first. Treat the Chinese draft as the script for a
  4–8 image carousel:
  - Image 1 = title card with the H1 line.
  - Image 2–N = each H2 becomes a card; the body under that H2 is the
    caption text.
  - Final image = the closing question or forward-looking sentence.
- Caption text below the carousel: the first 1–2 sentences of the draft +
  3–5 hashtags (Redbook expects hashtags; the drafts intentionally don't
  include any so you can add platform-native ones at post time).
- Tone-shift note: Redbook reads younger and more lifestyle-y than the
  drafts. You may need to soften the polemical edges with a 笔记式 voice
  ("最近在想...", "刚看到一组数据...") before the body lands.

## Sina blog (新浪博客)

- Paste the Chinese draft directly. Sina's editor preserves H1/H2 markdown
  fine.
- Sina's audience skews older / professional and rewards data density —
  these drafts are a natural fit.
- Add 3–5 标签 (tags) at post time: 人工智能 / 劳动经济 / 货币政策 /
  反垄断 / 科技股 — pick what matches the draft's argument.
- Sina rewards series. Posting all 20 over 4–6 weeks as a numbered series
  ("AI 与劳动者 #01 – 算力护城河") is more durable than one-off posts.

## Cross-platform discipline

- **Don't post the same draft to all six on the same day.** Same content
  on the same day reads as automation, not authorship.
- **Lead the X thread with the LinkedIn post's last paragraph.** Different
  audiences want different opens; the last paragraph is usually the most
  quotable.
- **Localize numerical examples.** US-dollar figures land on LinkedIn/X.
  For WeChat/Redbook/Sina, the CN drafts already supplement with comparable
  domestic context (上海/北京 房价, 银联/支付宝/微信支付, 字节/阿里/腾讯).
- **Each draft has at least one quotable line.** Identify it before posting
  and make it the post's pull-quote / OG image text / first tweet.

## Posting-order suggestion (8-week run)

Pair one cyberpunk-side topic with one 2028-GIC-side topic each week so
the running thread alternates between mechanism (cyberpunk) and consequence
(GIC):

| Week | Mon (cyberpunk) | Thu (2028-GIC) |
|------|-----------------|----------------|
| 1 | 01-compute-moat | 11-displacement-spiral |
| 2 | 02-on-ramp-collapse | 12-ghost-gdp |
| 3 | 03-so-so-automation | 13-friction-elimination |
| 4 | 04-algorithmic-management | 14-top10-spending-collapse |
| 5 | 05-surveillance-pricing | 15-daisy-chain |
| 6 | 06-antitrust-lag | 16-2028-mortgage-crisis |
| 7 | 07-personal-ai-exit-ramp | 17-interchange-pressure |
| 8 | 08-deepseek-trajectory | 18-zendesk-template |
| 9 | 09-context-ownership | 19-revenue-paradox |
| 10 | 10-composition-over-subscription | 20-labor-share-46 |

(Or compress to 5 weeks at 2 posts/week with the same pairing.)
