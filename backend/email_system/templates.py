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
          <a href="{{unsubscribe_url}}" style="color:{MUTED_COLOR};">Unsubscribe</a> · 
          <a href="{{preferences_url}}" style="color:{MUTED_COLOR};">Preferences</a>
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""

def approve_button(label: str, url: str, color: str = "#16A34A") -> str:
    """A big thumb-friendly approve button for mobile."""
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
    """
    The daily morning briefing email.
    actions is a list of dicts with keys: title, description, approve_token, decline_token, risk_level, type
    """
    # Yesterday's results section
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

    # Actions needing approval
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
    """Step 1: Create/connect Google Ads account."""
    connect_url = f"{base_url}/integrations/connect/google?business_id={business_id}"
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
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 16px 0;line-height:1.6;">
        This lets me manage your Google Ads campaigns and see your website traffic.
        It takes about 2 minutes — you'll sign into Google and click Allow.
      </p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 16px 0;">
        <strong>What I can do:</strong> ✓ Manage Google Ads · ✓ Read Analytics · ✓ View Business Profile<br>
        <strong>What I cannot do:</strong> ✗ See your billing info · ✗ Access Gmail · ✗ Share your data
      </p>
      {approve_button("🔵 Connect Google →", connect_url, BRAND_COLOR)}
    </div>

    <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      <strong>Don't have Google Ads yet?</strong> That's fine — just click the button above,
      sign in with your Google account, and Google will walk you through creating a free account
      in about 3 minutes. When asked, choose "Switch to Expert Mode" and then
      "Create account without a campaign" — Marlo will set up your first campaign for you.<br><br>
      Need help? Just reply to this email with any questions.
    </p>"""
    return base_template(content, preheader="Step 1 of 4 — Connect Google (2 minutes)")

def onboarding_email_2(first_name: str, business_id: str, base_url: str) -> str:
    """Step 2: Connect Meta/Instagram — sent automatically after Google connects."""
    connect_url = f"{base_url}/integrations/connect/meta?business_id={business_id}"
    content = f"""
    <p style="font-size:16px;font-weight:600;color:#16A34A;margin:0 0 8px 0;">
      ✅ Google is connected!
    </p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;">
      Great work {first_name}. Now let's connect Facebook and Instagram.
    </p>

    <div style="background:#F5F3FF;border-radius:8px;padding:20px;margin-bottom:24px;">
      <p style="font-size:13px;font-weight:600;color:#7C3AED;margin:0 0 12px 0;">
        STEP 2 OF 4 — Connect Facebook &amp; Instagram
      </p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 8px 0;line-height:1.6;">
        This lets me post to Instagram, run Facebook ads, and read your audience data.
      </p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 8px 0;">
        ⚠️ Make sure your Instagram is set as a <strong>Business account</strong> first:
      </p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 8px 0;line-height:1.6;">
        On your phone: Instagram → Settings → <strong>Account type and tools</strong> → <strong>Switch to professional account</strong> → Business
      </p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 16px 0;line-height:1.6;">
        You'll also need a <strong>Facebook Page</strong> connected to your Instagram.
        <a href="https://www.facebook.com/pages/creation/" style="color:{BRAND_COLOR};">Create a free Facebook Page here</a> if you don't have one,
        then connect it in Instagram → Settings → Account → Linked Accounts.
      </p>
      {approve_button("🟣 Connect Facebook & Instagram →", connect_url, "#7C3AED")}
    </div>

    <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      While you do this step, I'm already reading your Google Ads history
      and researching the best keywords for your business. ⚙️
    </p>"""
    return base_template(content, preheader="Step 2 of 4 — Connect Instagram (2 minutes)")

def onboarding_email_3(first_name: str, business_id: str, base_url: str) -> str:
    """Step 3: Connect Mailchimp."""
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
        STEP 3 OF 4 — Connect Email Marketing
      </p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 16px 0;line-height:1.6;">
        Connect Mailchimp so I can send email campaigns to your subscribers
        and track open rates and clicks.
      </p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 16px 0;">
        Don't use Mailchimp? <a href="{base_url}/onboarding/skip-email?business_id={business_id}"
        style="color:{BRAND_COLOR};">Skip this step</a> — you can connect it later.
      </p>
      {approve_button("🟡 Connect Mailchimp →", connect_url, "#D97706")}
    </div>"""
    return base_template(content, preheader="Step 3 of 4 — Connect email (2 minutes)")

def onboarding_email_4(first_name: str, business_id: str, base_url: str) -> str:
    """Step 4: Tell Marlo about your business — reply email."""
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
    """Final onboarding email: Marlo's first plan ready for approval."""
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
        posts_html += f"""
        <div style="margin-bottom:20px;">
          <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 4px 0;">
            📸 {p.get('day', 'Monday')} — Instagram
          </p>
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
    """Sent back to user after they email a product photo."""
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
    """Monday morning weekly report."""
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
    return base_template(content, preheader=f"Your weekly marketing report")