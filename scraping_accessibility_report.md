# Accessibility Testing: Top 20 Nigerian News Sites

In light of your project to automate data scraping for a security incident tracker, I tested the top 20 Nigerian news websites using `curl`. 

Automated scripts, like the Python AI pipeline described in `Step 3.md` and `Step 5.md`, can often be blocked by Cloudflare's "Are you a robot?" checks (returning an HTTP 403 Forbidden). Here are the results to help you determine which sources are reliable for automated extraction.

> [!WARNING]  
> The **Blocked** sites currently have strict Cloudflare anti-bot checks (HTTP 403). Scraping them automatically via simple scripts will fail unless you use advanced headless browsers or residential proxies.

## 🔴 Blocked by Anti-Bot Checks (Not Recommended for Scraping)
These sites returned an HTTP 403 Forbidden with Cloudflare headers when requested via curl:
- **Vanguard** (`https://www.vanguardngr.com/`)
- **The Guardian** (`https://guardian.ng/`)
- **Leadership** (`https://leadership.ng/`)
- **Nairaland** (`https://www.nairaland.com/`)
- **Tribune Online** (`https://tribuneonlineng.com/`)

## 🟢 Accessible (Recommended for Scraping)
These sites returned a successful HTTP 200 response. Most sit behind Cloudflare but do not currently enforce aggressive JavaScript/Captcha challenges against simple curl requests. 

**No Cloudflare detected (Direct access):**
- **Legit.ng** (`https://www.legit.ng/`)
- **ThisDay Live** (`https://www.thisdaylive.com/`)
- **Arise News** (`https://www.arise.tv/`)

**Cloudflare present but did not block the request:**
- **Punch** (`https://punchng.com/`)
- **Premium Times** (`https://www.premiumtimesng.com/`)
- **Daily Post** (`https://dailypost.ng/`)
- **Pulse Nigeria** (`https://www.pulse.ng/`)
- **Sahara Reporters** (`https://saharareporters.com/`)
- **Channels Television** (`https://www.channelstv.com/`)
- **Linda Ikeji's Blog** (`https://lindaikejisblog.com/`)
- **Information Nigeria** (`https://www.informationng.com/`)
- **Naijaloaded** (`https://www.naijaloaded.com.ng/`)
- **BusinessDay** (`https://businessday.ng/`)
- **The Cable** (`https://www.thecable.ng/`)
- **Daily Trust** (`https://dailytrust.com/`)

> [!TIP]
> For the data pipeline you are building, focus your `google-genai` searches on the **accessible sites** (e.g., using search operators like `site:punchng.com OR site:premiumtimesng.com`). This ensures your backend won't break due to Cloudflare when it attempts to scrape article text.
