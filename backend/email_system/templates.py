"""
All email templates for Marlo.
Design principles:
- Mobile-first (600px max width)
- Inline CSS only (no <style> blocks — email clients strip them)
- Big, thumb-friendly buttons
- Clear hierarchy: results → recommendations → action buttons
"""

BRAND_COLOR = "#2563EB"  # Blue
BORDER_COLOR = "#E5E7EB"
TEXT_COLOR = "#1F2937"
MUTED_COLOR = "#6B7280"

def base_template(content: str, preheader: str = "") -> str:
    """Wraps any content in the standard Marlo email shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Marlo</title>
</head>
<body style="margin:0;padding:0;background:#F9FAFB;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
{'<div style="display:none;max-height:0;overflow:hidden;">' + preheader + '</div>' if preheader else ''}
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F9FAFB;padding:24px 16px;">
  <tr><td align="center">
    <table width="100%" style="max-width:600px;background:#FFFFFF;border-radius:12px;border:1px solid {BORDER_COLOR};overflow:hidden;">
      <!-- Header -->
      <tr><td style="padding:20px 28px;border-bottom:1px solid {BORDER_COLOR};">
        <span style="font-size:18px;font-weight:700;color:{BRAND_COLOR};">Marlo</span>
        <span style="font-size:13px;color:{MUTED_COLOR};margin-left:8px;">your AI marketing assistant</span>
      </td></tr>
      <!-- Content -->
      <tr><td style="padding:28px;">
        {content}
      </td></tr>
      <!-- Footer -->
      <tr><td style="padding:20px 28px;border-top:1px solid {BORDER_COLOR};background:#F9FAFB;">
        <p style="margin:0;font-size:12px;color:{MUTED_COLOR};line-height:1.5;">
          Reply to this email anytime to talk to Marlo.<br>
          <a href="https://marlo021.ai/help" style="color:{MUTED_COLOR};">Help & FAQ</a> · 
          <a href="{{unsubscribe_url}}" style="color:{MUTED_COLOR};">Unsubscribe</a> · 
          <a href="{{preferences_url}}" style="color:{MUTED_COLOR};">Preferences</a>
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""

def approve_button(label: str, url: str, color: str = "#16A34A") -> str:
    return f"""<a href="{url}" style="display:inline-block;background:{color};color:#FFFFFF;
    text-decoration:none;font-weight:600;font-size:15px;padding:14px 28px;
    border-radius:8px;margin:4px 4px 4px 0;">{label}</a>"""

def decline_button(label: str, url: str) -> str:
    return f"""<a href="{url}" style="display:inline-block;background:#FFFFFF;color:#374151;
    text-decoration:none;font-weight:500;font-size:15px;padding:14px 28px;
    border-radius:8px;border:1px solid #D1D5DB;margin:4px 0;">{label}</a>"""

def section_divider() -> str:
    return f'<hr style="border:none;border-top:1px solid {BORDER_COLOR};margin:24px 0;">'

def metric_row(label: str, value: str, trend: str = "", positive: bool = True) -> str:
    trend_color = "#16A34A" if positive else "#DC2626"
    return f"""<tr>
      <td style="padding:8px 0;font-size:14px;color:{MUTED_COLOR};">{label}</td>
      <td style="padding:8px 0;font-size:14px;font-weight:600;color:{TEXT_COLOR};text-align:right;">{value}
        {f'<span style="color:{trend_color};font-size:12px;margin-left:4px;">{trend}</span>' if trend else ''}
      </td>
    </tr>"""

def morning_briefing_template(
    business_name: str,
    first_name: str,
    yesterday_metrics: dict,
    actions: list,
    base_url: str
) -> str:
    metrics_rows = ""
    for m in yesterday_metrics.get("highlights", []):
        metrics_rows += metric_row(
            m["label"], m["value"], m.get("trend", ""), m.get("positive", True)
        )

    results_section = f"""
    <p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 12px 0;">
      ☀️ Good morning {first_name}!
    </p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 20px 0;">
      Here's what happened yesterday and what I recommend today.
    </p>
    <p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;
       letter-spacing:0.05em;margin:0 0 8px 0;">YESTERDAY'S RESULTS</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:8px;">
      {metrics_rows}
    </table>
    """

    actions_section = ""
    if actions:
        actions_section += section_divider()
        actions_section += f"""<p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};
          text-transform:uppercase;letter-spacing:0.05em;margin:0 0 20px 0;">
          TODAY'S RECOMMENDATIONS</p>"""
        for i, action in enumerate(actions):
            approve_url = f"{base_url}/actions/approve?token={action['approve_token']}"
            decline_url = f"{base_url}/actions/decline?token={action['decline_token']}"
            actions_section += f"""
            <div style="margin-bottom:24px;">
              <p style="font-size:15px;font-weight:600;color:{TEXT_COLOR};margin:0 0 6px 0;">
                {i+1}. {action['title']}
              </p>
              <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 12px 0;line-height:1.5;">
                {action['description']}
              </p>
              {approve_button("✓ Approve", approve_url)}
              {decline_button("✗ Decline", decline_url)}
            </div>"""

    reply_hint = f"""
    {section_divider()}
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      💬 <strong>Reply to this email</strong> anytime to talk to Marlo.<br>
      "Create a post about our weekend special" · "Pause ads today" · "How much have I spent?"<br><br>
      📸 <strong>Got a product photo?</strong> Reply with the photo attached and Marlo will 
      turn it into ad-ready content for every platform.
    </p>"""

    content = results_section + actions_section + reply_hint
    return base_template(content, preheader=f"Your marketing update for {business_name}")

def onboarding_email_1(business_name: str, first_name: str, business_id: str, base_url: str) -> str:
    connect_url = f"{base_url}/integrations/connect/google?business_id={business_id}"
    skip_url = f"{base_url}/integrations/skip-google?business_id={business_id}"
    content = f"""
    <p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">
      👋 Welcome {first_name}! I'm Marlo.
    </p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      I'm your AI marketing assistant for {business_name}. Setting me up takes about 20 minutes
      across 4 quick emails. Let's start with Google.
    </p>

    <div style="background:#F0F9FF;border-radius:8px;padding:20px;margin-bottom:24px;">
      <p style="font-size:13px;font-weight:600;color:#0369A1;margin:0 0 12px 0;">
        STEP 1 OF 4 — Connect Google Ads &amp; Analytics
      </p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 12px 0;line-height:1.6;">
        This lets me manage your Google Ads campaigns and see your website traffic.
        It takes about 2 minutes — you'll sign into Google and click Allow.
      </p>

      <!-- Value prop -->
      <p style="font-size:13px;color:{TEXT_COLOR};font-weight:600;margin:0 0 8px 0;">
        Why Google Ads is worth connecting:
      </p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 12px 0;line-height:1.7;">
        ✓ Show up at the top of Google when people search for what you sell<br>
        ✓ Only pay when someone actually clicks your ad<br>
        ✓ Marlo optimizes your budget daily so every dollar works harder<br>
        ✓ See exactly what you spent and what you got in your morning email
      </p>

      <!-- Safety reassurance -->
      <div style="background:#EFF6FF;border-radius:6px;padding:10px 14px;margin-bottom:16px;">
        <p style="font-size:13px;color:#1D4ED8;margin:0;line-height:1.6;">
          🛡️ <strong>You're always in control.</strong> Marlo will never spend a dollar
          without your approval. If you don't tap Approve in your morning email,
          nothing runs — and nothing gets charged.
        </p>
      </div>

      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 16px 0;">
        <strong>What I can do:</strong> ✓ Manage Google Ads · ✓ Read Analytics · ✓ View Business Profile<br>
        <strong>What I cannot do:</strong> ✗ See your billing info · ✗ Access Gmail · ✗ Share your data
      </p>

      {approve_button("🔵 Connect Google →", connect_url, BRAND_COLOR)}
    </div>

    <!-- Don't have Google Ads yet -->
    <div style="background:#F9FAFB;border:1px solid {BORDER_COLOR};border-radius:8px;padding:16px;margin-bottom:20px;">
      <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 6px 0;">
        Don't have Google Ads yet?
      </p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 10px 0;line-height:1.5;">
        Just click the button above and sign in with your Google account.
        Google will walk you through creating a free account in about 3 minutes.<br><br>
        When asked, choose <strong>"Switch to Expert Mode"</strong> then
        <strong>"Create account without a campaign"</strong> — Marlo will set up
        your first campaign for you.
      </p>
    </div>

    <!-- Skip option -->
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      Want to start with just Instagram?
      <a href="{skip_url}" style="color:{MUTED_COLOR};font-weight:600;">Skip Google for now →</a><br>
      <span style="font-size:12px;">You can connect Google Ads anytime later by replying to any Marlo email.</span>
    </p>"""
    return base_template(content, preheader="Step 1 of 4 — Connect Google (2 minutes)")

def onboarding_email_2(first_name: str, business_id: str, base_url: str, frontend_url: str = "") -> str:
    """Step 2: Connect Meta/Instagram — sent automatically after Google connects."""
    connect_url = f"{base_url}/integrations/connect/meta?business_id={business_id}"
    retry_url = f"{base_url}/integrations/connect/meta?business_id={business_id}&retry=true"
    skip_url = f"{base_url}/integrations/skip-meta?business_id={business_id}"

    # FAQ links point to frontend /help page with anchors
    faq_base = frontend_url or "https://marlo021.ai"
    faq_page_link = f"{faq_base}/help"
    faq_why_page = f"{faq_base}/help#why-facebook-page"
    faq_why_business = f"{faq_base}/help#why-business-account"
    faq_permissions = f"{faq_base}/help#meta-permissions"

    # Working Facebook Page creation link (2025)
    fb_create_page = "https://www.facebook.com/pages/create"

    content = f"""
    <p style="font-size:16px;font-weight:600;color:#16A34A;margin:0 0 4px 0;">
      ✅ Google is connected!
    </p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 28px 0;line-height:1.6;">
      Great work {first_name}. One more connection and Marlo can start posting for you.
    </p>

    <!-- MAIN CARD -->
    <div style="background:#F5F3FF;border-radius:8px;padding:20px;margin-bottom:24px;">
      <p style="font-size:13px;font-weight:600;color:#7C3AED;margin:0 0 16px 0;
         text-transform:uppercase;letter-spacing:0.05em;">
        STEP 2 OF 4 — Connect Facebook &amp; Instagram
      </p>
      <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 14px 0;">
        Before clicking connect, make sure you have these 3 things:
      </p>

      <!-- Item 1 -->
      <div style="display:flex;align-items:flex-start;margin-bottom:14px;">
        <div style="min-width:22px;height:22px;background:#7C3AED;border-radius:50%;
             color:#fff;font-size:11px;font-weight:700;text-align:center;line-height:22px;
             margin-right:12px;flex-shrink:0;">1</div>
        <div>
          <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 2px 0;">
            A Facebook account
          </p>
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.5;">
            Your personal Facebook account is fine. You'll use it to log in.
          </p>
        </div>
      </div>

      <!-- Item 2 -->
      <div style="display:flex;align-items:flex-start;margin-bottom:14px;">
        <div style="min-width:22px;height:22px;background:#7C3AED;border-radius:50%;
             color:#fff;font-size:11px;font-weight:700;text-align:center;line-height:22px;
             margin-right:12px;flex-shrink:0;">2</div>
        <div>
          <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 2px 0;">
            A Facebook Page for your business
          </p>
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 4px 0;line-height:1.5;">
            Don't have one yet?
            <a href="{fb_create_page}" style="color:#7C3AED;font-weight:600;">
              Create a free Page here</a> — just give it your business name (2 min).
          </p>
          <p style="font-size:12px;color:{MUTED_COLOR};margin:0;line-height:1.5;font-style:italic;">
            Not sure why you need this?
            <a href="{faq_why_page}" style="color:#7C3AED;">See explanation →</a>
          </p>
        </div>
      </div>

      <!-- Item 3 -->
      <div style="display:flex;align-items:flex-start;margin-bottom:20px;">
        <div style="min-width:22px;height:22px;background:#7C3AED;border-radius:50%;
             color:#fff;font-size:11px;font-weight:700;text-align:center;line-height:22px;
             margin-right:12px;flex-shrink:0;">3</div>
        <div>
          <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 2px 0;">
            Instagram set to Business account
          </p>
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 4px 0;line-height:1.6;">
            <strong>Step A — Switch to Business account:</strong><br>
            Instagram → ☰ → Settings → <strong>Account type and tools</strong> →
            <strong>Switch to Professional Account</strong> → Business.<br><br>
            <strong>Step B — Link your Instagram to Facebook (easiest on desktop):</strong><br>
            Go to <a href="https://accountscenter.facebook.com" style="color:#7C3AED;font-weight:600;">accountscenter.facebook.com</a>
            while logged into your Facebook account →
            <strong>Profiles and personal details</strong> → <strong>Add accounts</strong> →
            add your Instagram account.
          </p>
          <div style="background:#FEF9C3;border-radius:6px;padding:10px 12px;margin-top:6px;margin-bottom:6px;">
            <p style="font-size:12px;color:#854D0E;margin:0;line-height:1.5;">
              ⚠️ Log into Facebook with the account that owns your Facebook Page.
              Once your Instagram is added to that Accounts Center,
              the Facebook Page link happens automatically.
            </p>
          </div>
          <p style="font-size:12px;color:#16A34A;margin:0 0 4px 0;line-height:1.5;font-weight:600;">
            ✓ Your existing account upgrades in place — no new account, all posts and followers stay.
          </p>
          <p style="font-size:12px;color:{MUTED_COLOR};margin:0;line-height:1.5;font-style:italic;">
            Can't find the option?
            <a href="mailto:reply+{business_id}@reply.marlo021.ai?subject=Help with Instagram Business account"
               style="color:#7C3AED;">Reply and I'll walk you through it.</a>
          </p>
        </div>
      </div>

      <!-- PRE-BUTTON NOTE -->
      <div style="background:#EDE9FE;border-radius:6px;padding:12px 14px;margin-bottom:16px;">
        <p style="font-size:13px;color:#5B21B6;margin:0;line-height:1.6;">
          <strong>What happens when you click:</strong> You'll go to Facebook's official
          login page. You'll see a list of permissions — this is normal and expected.
          Select your Business Page and click <strong>Allow</strong> to finish.
          Marlo never sees your password or personal messages.
        </p>
      </div>

      {approve_button("🟣 Connect Facebook & Instagram →", connect_url, "#7C3AED")}
    </div>

    <!-- NO INSTAGRAM ESCAPE HATCH -->
    <div style="background:#F9FAFB;border:1px solid {BORDER_COLOR};border-radius:8px;
         padding:16px;margin-bottom:24px;">
      <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 6px 0;">
        Don't have Instagram yet?
      </p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 10px 0;line-height:1.5;">
        No problem — Marlo can start with just Facebook Ads and Google while you set up Instagram.
        You can connect Instagram anytime later by replying to any Marlo email.
      </p>
      <a href="{skip_url}"
         style="font-size:13px;color:{MUTED_COLOR};font-weight:600;text-decoration:none;">
        Skip Instagram for now →
      </a>
    </div>

    <!-- RETRY LINK -->
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      Already tried connecting but something went wrong?
      <a href="{retry_url}" style="color:#7C3AED;font-weight:600;">Try connecting again →</a>
    </p>

    <!-- FAQ LINKS -->
    <div style="border-top:1px solid {BORDER_COLOR};padding-top:16px;">
      <p style="font-size:12px;font-weight:600;color:{MUTED_COLOR};margin:0 0 10px 0;
         text-transform:uppercase;letter-spacing:0.05em;">Common questions</p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:2.2;">
        <a href="{faq_why_page}" style="color:#7C3AED;">
          → Why do I need a Facebook Page just for Instagram?</a><br>
        <a href="{faq_why_business}" style="color:#7C3AED;">
          → Why can't Marlo post to my personal Instagram?</a><br>
        <a href="{faq_permissions}" style="color:#7C3AED;">
          → What permissions is Marlo asking for, and why?</a><br>
        <a href="mailto:reply+{business_id}@reply.marlo021.ai?subject=Help with Step 2" style="color:#7C3AED;">
          → I'm stuck — get help</a>
      </p>
    </div>

    <p style="font-size:13px;color:{MUTED_COLOR};margin:24px 0 0 0;line-height:1.6;">
      While you set this up, I'm already reading your Google Ads history
      and researching the best keywords for your business. ⚙️
    </p>"""
    return base_template(content, preheader=f"{first_name}, Google is connected — one more step for Instagram")

def onboarding_email_3(first_name: str, business_id: str, base_url: str) -> str:
    connect_url = f"{base_url}/integrations/connect/mailchimp?business_id={business_id}"
    content = f"""
    <p style="font-size:16px;font-weight:600;color:#16A34A;margin:0 0 8px 0;">
      ✅ Facebook &amp; Instagram connected!
    </p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;">
      One more connection and you're done with setup.
    </p>
    <div style="background:#FEFCE8;border-radius:8px;padding:20px;margin-bottom:24px;">
      <p style="font-size:13px;font-weight:600;color:#A16207;margin:0 0 12px 0;">
        STEP 3 OF 4 — Connect Email Marketing (Optional)
      </p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 12px 0;line-height:1.6;">
        Connect Mailchimp so Marlo can send email campaigns to your subscribers
        and track open rates and clicks.
      </p>

      <!-- Free tier callout -->
      <div style="background:#F0FDF4;border-radius:6px;padding:10px 14px;margin-bottom:16px;">
        <p style="font-size:13px;color:#15803D;margin:0;line-height:1.5;">
          💚 <strong>Mailchimp is free for your first 500 subscribers.</strong>
          No credit card needed to get started.
        </p>
      </div>

      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 16px 0;line-height:1.6;">
        Don't have a Mailchimp account yet?
        <a href="https://mailchimp.com/signup/" style="color:#D97706;font-weight:600;">
          Create a free account here</a> — it takes 2 minutes.
        Then come back to this email and click the button below.
      </p>

      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 16px 0;">
        Already have Mailchimp? Just click below to connect it.
      </p>

      {approve_button("🟡 Connect Mailchimp →", connect_url, "#D97706")}

      <p style="font-size:12px;color:{MUTED_COLOR};margin:16px 0 0 0;">
        Don't use email marketing yet?
        <a href="{base_url}/integrations/skip-mailchimp?business_id={business_id}"
           style="color:{MUTED_COLOR};font-weight:600;">Skip this step</a> —
        you can connect Mailchimp anytime later by replying to any Marlo email.
      </p>
    </div>"""
    return base_template(content, preheader="Step 3 of 4 — Connect email marketing (free for 500 subscribers)")

def onboarding_email_4(first_name: str, business_id: str, base_url: str) -> str:
    content = f"""
    <p style="font-size:16px;font-weight:600;color:#16A34A;margin:0 0 8px 0;">
      Almost there {first_name}! One last thing.
    </p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      Just reply to this email and answer these 4 questions in plain English.
      No forms, no website — just hit reply and type your answers.
    </p>
    <div style="background:#F0FDF4;border-radius:8px;padding:20px;margin-bottom:24px;">
      <p style="font-size:13px;font-weight:600;color:#15803D;margin:0 0 16px 0;">
        STEP 4 OF 4 — Tell me about your business
      </p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 8px 0;line-height:1.8;">
        <strong>1.</strong> What does your business sell or do?<br>
        <em style="color:{MUTED_COLOR};">(e.g. "artisan sourdough bread and seasonal pastries")</em><br><br>
        <strong>2.</strong> Who are your typical customers?<br>
        <em style="color:{MUTED_COLOR};">(e.g. "Portland locals, families, food lovers aged 25–45")</em><br><br>
        <strong>3.</strong> What's your brand personality?<br>
        <em style="color:{MUTED_COLOR};">(e.g. "warm, community-focused, celebrating local ingredients")</em><br><br>
        <strong>4.</strong> Any upcoming promotions or events?<br>
        <em style="color:{MUTED_COLOR};">(e.g. "Mother's Day special May 11, new summer menu June 1")</em>
      </p>
    </div>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      Hit reply and send your answers — I'll take it from there. ✉️<br><br>
      While you reply I'm already analyzing your accounts, building your keyword strategy,
      and preparing your first week of content. ⚙️
    </p>"""
    return base_template(content, preheader="Step 4 of 4 — Just reply to this email")

def onboarding_email_5_ready(first_name: str, campaigns: list, posts: list,
                               approve_all_url: str, base_url: str) -> str:
    campaigns_html = ""
    for c in campaigns[:1]:
        campaigns_html += f"""
        <div style="background:#F8FAFC;border-radius:8px;padding:16px;margin-bottom:12px;
             border:1px solid {BORDER_COLOR};">
          <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 4px 0;">
            📊 {c.get('name', 'Google Search Campaign')}
          </p>
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 12px 0;line-height:1.5;">
            Keywords: {', '.join(c.get('keywords', [])[:4])}<br>
            Budget: ${c.get('daily_budget', 8)}/day · Est. {c.get('est_clicks', '40–60')} clicks/day
          </p>
          {approve_button("✓ Approve Campaign", c.get('approve_url', '#'))}
          {decline_button("✗ Skip", c.get('decline_url', '#'))}
        </div>"""

    posts_html = ""
    for p in posts[:3]:
        image_html = ""
        if p.get("image_url"):
            image_html = f"""<img src="{p['image_url']}" alt="Post image"
                style="width:100%;max-width:400px;border-radius:8px;margin-bottom:10px;display:block;" />"""
        posts_html += f"""
        <div style="margin-bottom:24px;padding-bottom:24px;border-bottom:1px solid {BORDER_COLOR};">
          <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">
            📸 {p.get('day', 'This week')} — Instagram
          </p>
          {image_html}
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 8px 0;font-style:italic;">
            "{p.get('caption_preview', '')[:100]}..."
          </p>
          {approve_button("✓ Approve", p.get('approve_url', '#'))}
          {decline_button("✗ Skip", p.get('decline_url', '#'))}
        </div>"""

    content = f"""
    <p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">
      🚀 {first_name}, everything is ready!
    </p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      I've analyzed your accounts and built your first marketing plan.
      Review and approve what looks good — skip anything you want to change later.
    </p>
    <p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;
       letter-spacing:0.05em;margin:0 0 12px 0;">YOUR FIRST GOOGLE ADS CAMPAIGN</p>
    {campaigns_html}
    {section_divider()}
    <p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;
       letter-spacing:0.05em;margin:0 0 12px 0;">THIS WEEK'S INSTAGRAM POSTS</p>
    {posts_html}
    {section_divider()}
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      🎉 Starting tomorrow at 8am, you'll get your first daily briefing.<br>
      From then on — just open your morning email and tap approve. That's it.
    </p>"""
    return base_template(content, preheader="Your first marketing plan is ready — please review")

def photo_response_template(first_name: str, original_caption: str,
                              platform_previews: list, base_url: str) -> str:
    previews_html = ""
    for p in platform_previews:
        image_html = ""
        if p.get("image_url"):
            image_html = f"""<img src="{p['image_url']}" alt="{p['platform_label']}"
                style="width:100%;max-width:400px;border-radius:8px;margin-bottom:10px;display:block;" />"""
        previews_html += f"""
        <div style="margin-bottom:24px;padding-bottom:24px;border-bottom:1px solid {BORDER_COLOR};">
          <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">
            📱 {p['platform_label']}
          </p>
          {image_html}
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 10px 0;font-style:italic;">
            Caption: "{p['caption'][:120]}..."
          </p>
          {approve_button(f"✓ Post to {p['platform_label']}", p['approve_url'])}
        </div>"""

    content = f"""
    <p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">
      📸 Got your photo, {first_name}!
    </p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      I've enhanced it and prepared versions for each platform with captions
      written in your brand voice. Approve any you'd like to post.
    </p>
    {previews_html}
    <p style="font-size:13px;color:{MUTED_COLOR};margin:16px 0 0 0;">
      Want to edit a caption? Just reply: "Edit Instagram caption: [your new text]"
    </p>"""
    return base_template(content, preheader="Your photo is ready to post — approve below")

def weekly_report_template(first_name: str, report_data: dict) -> str:
    summary = report_data.get("summary", "")
    insights = report_data.get("insights", [])
    recommendations = report_data.get("recommendations", [])

    insights_html = "".join([
        f'<li style="margin-bottom:8px;font-size:14px;color:{TEXT_COLOR};line-height:1.5;">{i}</li>'
        for i in insights[:4]
    ])
    recs_html = "".join([
        f'<li style="margin-bottom:8px;font-size:14px;color:{TEXT_COLOR};line-height:1.5;">{r}</li>'
        for r in recommendations[:3]
    ])

    content = f"""
    <p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">
      📊 Your weekly report, {first_name}
    </p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      {summary}
    </p>
    <p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;
       letter-spacing:0.05em;margin:0 0 12px 0;">KEY INSIGHTS</p>
    <ul style="padding-left:20px;margin:0 0 24px 0;">{insights_html}</ul>
    {section_divider()}
    <p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;
       letter-spacing:0.05em;margin:0 0 12px 0;">NEXT WEEK'S PRIORITIES</p>
    <ul style="padding-left:20px;margin:0 0 24px 0;">{recs_html}</ul>
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      Reply with any questions about this report, or tell me what to focus on next week.
    </p>"""
    return base_template(content, preheader="Your weekly marketing report")