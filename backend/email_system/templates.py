"""
All email templates for Marlo.
Design principles:
- Mobile-first (600px max width)
- Inline CSS only (no <style> blocks — email clients strip them)
- Big, thumb-friendly buttons
- Clear hierarchy: results → recommendations → action buttons
"""

BRAND_COLOR = "#2563EB"
LIME_COLOR  = "#b8f248"
BORDER_COLOR = "#E5E7EB"
TEXT_COLOR = "#1F2937"
MUTED_COLOR = "#6B7280"


def base_template(content: str, preheader: str = "") -> str:
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
      <tr><td style="padding:20px 28px;border-bottom:1px solid {BORDER_COLOR};">
        <span style="font-size:18px;font-weight:700;color:{BRAND_COLOR};">Marlo</span>
        <span style="font-size:13px;color:{MUTED_COLOR};margin-left:8px;">your AI marketing assistant</span>
      </td></tr>
      <tr><td style="padding:28px;">
        {content}
      </td></tr>
      <tr><td style="padding:20px 28px;border-top:1px solid {BORDER_COLOR};background:#F9FAFB;">
        <p style="margin:0;font-size:12px;color:{MUTED_COLOR};line-height:1.5;">
          Reply to this email anytime to talk to Marlo.<br>
          <a href="https://marlo021.ai/help" style="color:{MUTED_COLOR};">Help &amp; FAQ</a> ·
          <a href="#" style="color:{MUTED_COLOR};">Unsubscribe</a> ·
          <a href="#" style="color:{MUTED_COLOR};">Preferences</a>
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""


def approve_button(label: str, url: str, color: str = "#16A34A") -> str:
    return (
        f'<a href="{url}" style="display:inline-block;background:{color};color:#FFFFFF;'
        f'text-decoration:none;font-weight:600;font-size:15px;padding:14px 28px;'
        f'border-radius:8px;margin:4px 4px 4px 0;">{label}</a>'
    )


def decline_button(label: str, url: str) -> str:
    return (
        f'<a href="{url}" style="display:inline-block;background:#FFFFFF;color:#374151;'
        f'text-decoration:none;font-weight:500;font-size:15px;padding:14px 28px;'
        f'border-radius:8px;border:1px solid #D1D5DB;margin:4px 0;">{label}</a>'
    )


def day_button(label: str, url: str) -> str:
    return (
        f'<a href="{url}" style="display:inline-block;background:#111111;color:{LIME_COLOR};'
        f'text-decoration:none;font-weight:600;font-size:14px;padding:12px 20px;'
        f'border-radius:8px;margin:4px 4px 4px 0;">{label}</a>'
    )


def section_divider() -> str:
    return f'<hr style="border:none;border-top:1px solid {BORDER_COLOR};margin:28px 0;">'


def metric_card(label: str, value: str, sublabel: str = "") -> str:
    sub = f'<p style="font-size:12px;color:{MUTED_COLOR};margin:4px 0 0 0;">{sublabel}</p>' if sublabel else ""
    return f"""
    <td style="padding:16px;background:#F9FAFB;border-radius:8px;border:1px solid {BORDER_COLOR};text-align:center;width:33%;">
      <p style="font-size:22px;font-weight:700;color:{TEXT_COLOR};margin:0;">{value}</p>
      <p style="font-size:12px;color:{MUTED_COLOR};margin:4px 0 0 0;">{label}</p>
      {sub}
    </td>"""


def metric_row(label: str, value: str, trend: str = "", positive: bool = True) -> str:
    trend_color = "#16A34A" if positive else "#DC2626"
    trend_html = f'<span style="color:{trend_color};font-size:12px;margin-left:4px;">{trend}</span>' if trend else ""
    return f"""<tr>
      <td style="padding:8px 0;font-size:14px;color:{MUTED_COLOR};border-bottom:1px solid {BORDER_COLOR};">{label}</td>
      <td style="padding:8px 0;font-size:14px;font-weight:600;color:{TEXT_COLOR};text-align:right;border-bottom:1px solid {BORDER_COLOR};">{value}{trend_html}</td>
    </tr>"""


def weekly_cadence_diagram() -> str:
    """Chevron diagram showing the weekly cadence."""
    cell_style = "padding:10px 6px;text-align:center;vertical-align:middle;"
    arrow_style = f"font-size:18px;color:#D1D5DB;padding:0 2px;vertical-align:middle;"
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;border-collapse:collapse;">
      <tr>
        <td style="{cell_style}width:22%;">
          <div style="background:#111111;border-radius:8px;padding:10px 6px;text-align:center;">
            <p style="font-size:11px;font-weight:700;color:{LIME_COLOR};margin:0 0 2px 0;">DAY 1</p>
            <p style="font-size:10px;color:#888;margin:0;line-height:1.3;">Kickoff +<br>first post</p>
          </div>
        </td>
        <td style="{arrow_style}">›</td>
        <td style="{cell_style}width:22%;">
          <div style="background:#F9FAFB;border:1px solid {BORDER_COLOR};border-radius:8px;padding:10px 6px;text-align:center;">
            <p style="font-size:11px;font-weight:700;color:{TEXT_COLOR};margin:0 0 2px 0;">DAYS 2–8</p>
            <p style="font-size:10px;color:{MUTED_COLOR};margin:0;line-height:1.3;">Post approvals<br>any day of week</p>
          </div>
        </td>
        <td style="{arrow_style}">›</td>
        <td style="{cell_style}width:22%;">
          <div style="background:#F9FAFB;border:1px solid {BORDER_COLOR};border-radius:8px;padding:10px 6px;text-align:center;">
            <p style="font-size:11px;font-weight:700;color:{TEXT_COLOR};margin:0 0 2px 0;">DAY 7</p>
            <p style="font-size:10px;color:{MUTED_COLOR};margin:0;line-height:1.3;">Analytics +<br>next week strategy</p>
          </div>
        </td>
        <td style="{arrow_style}">›</td>
        <td style="{cell_style}width:22%;">
          <div style="background:#111111;border-radius:8px;padding:10px 6px;text-align:center;">
            <p style="font-size:11px;font-weight:700;color:{LIME_COLOR};margin:0 0 2px 0;">DAY 8</p>
            <p style="font-size:10px;color:#888;margin:0;line-height:1.3;">= Next cycle's<br>Day 1</p>
          </div>
        </td>
      </tr>
    </table>"""


# ─── ONBOARDING EMAILS ────────────────────────────────────────────────────────

def onboarding_email_1(business_name: str, first_name: str, business_id: str, base_url: str) -> str:
    connect_url = f"{base_url}/integrations/connect/google?business_id={business_id}"
    skip_url = f"{base_url}/integrations/skip-google?business_id={business_id}"
    content = f"""
    <p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">👋 Welcome {first_name}! I'm Marlo.</p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      I'm your AI marketing assistant for {business_name}. Setting me up takes about 20 minutes across 4 quick emails. Let's start with Google.
    </p>
    <div style="background:#F0F9FF;border-radius:8px;padding:20px;margin-bottom:24px;">
      <p style="font-size:13px;font-weight:600;color:#0369A1;margin:0 0 12px 0;">STEP 1 OF 4 — Connect Google Ads &amp; Analytics</p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 12px 0;line-height:1.6;">
        This lets me manage your Google Ads campaigns and see your website traffic. It takes about 2 minutes.
      </p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 12px 0;line-height:1.7;">
        ✓ Show up at the top of Google when people search for what you sell<br>
        ✓ Only pay when someone actually clicks your ad<br>
        ✓ Marlo optimizes your budget daily so every dollar works harder
      </p>
      <div style="background:#EFF6FF;border-radius:6px;padding:10px 14px;margin-bottom:16px;">
        <p style="font-size:13px;color:#1D4ED8;margin:0;line-height:1.6;">
          🛡️ <strong>You're always in control.</strong> Marlo will never spend a dollar without your approval.
        </p>
      </div>
      {approve_button("🔵 Connect Google →", connect_url, BRAND_COLOR)}
    </div>
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      Want to start with just Instagram? <a href="{skip_url}" style="color:{MUTED_COLOR};font-weight:600;">Skip Google for now →</a>
    </p>"""
    return base_template(content, preheader="Step 1 of 4 — Connect Google (2 minutes)")


def onboarding_email_2(first_name: str, business_id: str, base_url: str, frontend_url: str = "", skipped_google: bool = False) -> str:
    connect_url = f"{base_url}/integrations/connect/meta?business_id={business_id}"
    skip_url = f"{base_url}/integrations/skip-meta?business_id={business_id}"

    top_message = (
        f'<p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 4px 0;">No problem — let\'s connect Instagram next!</p>'
        f'<p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 28px 0;line-height:1.6;">You can always connect Google Ads later by replying to any Marlo email.</p>'
    ) if skipped_google else (
        f'<p style="font-size:16px;font-weight:600;color:#16A34A;margin:0 0 4px 0;">✅ Google is connected!</p>'
        f'<p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 28px 0;line-height:1.6;">Great work {first_name}. One more connection and Marlo can start posting for you.</p>'
    )

    content = top_message + f"""
    <div style="background:#F5F3FF;border-radius:8px;padding:20px;margin-bottom:24px;">
      <p style="font-size:13px;font-weight:600;color:#7C3AED;margin:0 0 16px 0;">STEP 2 OF 4 — Connect Facebook &amp; Instagram</p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 16px 0;line-height:1.6;">
        Before clicking connect, make sure you have:<br><br>
        <strong>1.</strong> A Facebook account<br>
        <strong>2.</strong> A Facebook Page for your business — <a href="https://www.facebook.com/pages/create" style="color:#7C3AED;">create one free here</a><br>
        <strong>3.</strong> Instagram set to Business account and linked to your Facebook Page via
        <a href="https://accountscenter.facebook.com" style="color:#7C3AED;">accountscenter.facebook.com</a>
      </p>
      {approve_button("🟣 Connect Facebook & Instagram →", connect_url, "#7C3AED")}
    </div>
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      Don't have Instagram yet? <a href="{skip_url}" style="color:{MUTED_COLOR};font-weight:600;">Skip Instagram for now →</a>
    </p>"""
    preheader = "Skipped Google — let's connect Instagram next" if skipped_google else f"{first_name}, Google is connected — one more step"
    return base_template(content, preheader=preheader)


def onboarding_email_3(first_name: str, business_id: str, base_url: str, skipped_meta: bool = False) -> str:
    connect_url = f"{base_url}/integrations/connect/mailchimp?business_id={business_id}"
    skip_url = f"{base_url}/integrations/skip-mailchimp?business_id={business_id}"

    top_message = (
        f'<p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">No worries — you can connect Instagram anytime later.</p>'
        f'<p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;">One more optional connection and setup is complete.</p>'
    ) if skipped_meta else (
        f'<p style="font-size:16px;font-weight:600;color:#16A34A;margin:0 0 8px 0;">✅ Facebook &amp; Instagram connected!</p>'
        f'<p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;">One more connection and you\'re done with setup.</p>'
    )

    content = top_message + f"""
    <div style="background:#FEFCE8;border-radius:8px;padding:20px;margin-bottom:24px;">
      <p style="font-size:13px;font-weight:600;color:#A16207;margin:0 0 12px 0;">STEP 3 OF 4 — Connect Email Marketing (Optional)</p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 12px 0;line-height:1.6;">
        Connect Mailchimp so Marlo can send email campaigns to your subscribers and track open rates.
      </p>
      {approve_button("🟡 Connect Mailchimp →", connect_url, "#D97706")}
      <p style="font-size:12px;color:{MUTED_COLOR};margin:16px 0 0 0;">
        Don't use email marketing? <a href="{skip_url}" style="color:{MUTED_COLOR};font-weight:600;">Skip this step →</a>
      </p>
    </div>"""
    return base_template(content, preheader="Step 3 of 4 — Connect email marketing (optional)")


def onboarding_email_4(first_name: str, business_id: str, base_url: str, is_reminder: bool = False) -> str:
    if is_reminder:
        top_section = f"""
    <p style="font-size:16px;font-weight:600;color:#D97706;margin:0 0 8px 0;">⏰ Just checking in, {first_name}!</p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 16px 0;line-height:1.6;">
      Marlo is ready to build your first marketing plan — I'm just waiting on a quick description of your business.
    </p>
    <div style="background:#FEF9C3;border-radius:8px;padding:14px 16px;margin-bottom:20px;">
      <p style="font-size:13px;color:#854D0E;margin:0;line-height:1.6;">
        ⚠️ <strong>Without your answers, Marlo can't generate personalised content.</strong> Your posts and ads will stay on hold until you reply.
      </p>
    </div>"""
    else:
        top_section = f"""
    <p style="font-size:16px;font-weight:600;color:#16A34A;margin:0 0 8px 0;">Almost there {first_name}! One last thing.</p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 16px 0;line-height:1.6;">
      Just reply to this email and answer these 4 quick questions. No forms, no website — just hit reply and type your answers.
    </p>
    <div style="background:#FEF9C3;border-radius:8px;padding:14px 16px;margin-bottom:20px;">
      <p style="font-size:13px;color:#854D0E;margin:0;line-height:1.6;">
        ⚠️ <strong>Marlo won't be able to generate your first week of content until you reply.</strong> This takes 2 minutes and unlocks everything.
      </p>
    </div>"""

    content = top_section + f"""
    <div style="background:#F0FDF4;border-radius:8px;padding:20px;margin-bottom:24px;">
      <p style="font-size:13px;font-weight:600;color:#15803D;margin:0 0 16px 0;">STEP 4 OF 4 — Tell me about your business</p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 8px 0;line-height:2.0;">
        <strong>1.</strong> What does your business sell or do?<br>
        <em style="color:{MUTED_COLOR};">(e.g. "artisan sourdough bread and seasonal pastries")</em>
      </p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 8px 0;line-height:2.0;">
        <strong>2.</strong> Who are your typical customers?<br>
        <em style="color:{MUTED_COLOR};">(e.g. "Portland locals, families, food lovers aged 25–45")</em>
      </p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 8px 0;line-height:2.0;">
        <strong>3.</strong> What's your brand personality?<br>
        <em style="color:{MUTED_COLOR};">(e.g. "warm, community-focused, celebrating local ingredients")</em>
      </p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0;line-height:2.0;">
        <strong>4.</strong> Any upcoming promotions or events?<br>
        <em style="color:{MUTED_COLOR};">(e.g. "Mother's Day special May 11, new summer menu June 1")</em>
      </p>
    </div>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      Hit reply and send your answers — I'll take it from there. ✉️
    </p>"""
    preheader = "Marlo is waiting — reply to unlock your first marketing plan" if is_reminder else "Step 4 of 4 — Reply to unlock your first week of content"
    return base_template(content, preheader=preheader)


# ─── ONBOARDING COMPLETE ─────────────────────────────────────────────────────

def onboarding_complete_template(first_name: str, business_name: str) -> str:
    content = f"""
    <p style="font-size:16px;font-weight:600;color:#16A34A;margin:0 0 8px 0;">🎉 Setup complete, {first_name}!</p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 20px 0;line-height:1.6;">
      Marlo has everything it needs to get started on {business_name}'s marketing. Your first content plan is being prepared right now.
    </p>
    <div style="background:#F0FDF4;border-radius:8px;padding:20px;margin-bottom:24px;">
      <p style="font-size:13px;font-weight:600;color:#15803D;margin:0 0 12px 0;">What happens next</p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 8px 0;line-height:1.8;">
        ✅ Marlo is generating your first week of content<br>
        ✅ You'll receive a detailed kickoff email shortly<br>
        ✅ The kickoff email explains your content strategy, posting schedule, and how approvals work<br>
        ✅ Nothing goes live until you approve it
      </p>
    </div>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      Check your inbox — your kickoff email is on its way. 🚀
    </p>"""
    return base_template(content, preheader="Setup complete — your first content plan is being prepared")


# ─── FIRST KICKOFF EMAIL ──────────────────────────────────────────────────────

def first_kickoff_template(
    first_name: str,
    business_name: str,
    business_id: str,
    first_post: dict,
    first_post_day: str,
    first_approve_token: str,
    first_decline_token: str,
    google_campaign: dict,
    ads_approve_token: str,
    ads_decline_token: str,
    posting_schedule: list,
    strategy_summary: str,
    image_guide: list,
    base_url: str,
) -> str:
    # Day picker buttons
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_buttons_html = ""
    for day in days_of_week:
        url = f"{base_url}/settings/kickoff-day?business_id={business_id}&day={day}"
        is_current = day == first_post_day
        bg = LIME_COLOR if is_current else "#F3F4F6"
        color = "#111111" if is_current else MUTED_COLOR
        day_buttons_html += (
            f'<a href="{url}" style="display:inline-block;background:{bg};color:{color};'
            f'text-decoration:none;font-weight:600;font-size:13px;padding:10px 16px;'
            f'border-radius:8px;margin:4px 4px 4px 0;border:1px solid {BORDER_COLOR};">{day}</a>'
        )

    schedule_html = " → ".join([f'<strong>{d}</strong>' for d in posting_schedule])

    image_guide_html = ""
    for item in image_guide:
        image_guide_html += f"""
        <div style="background:#F9FAFB;border-radius:6px;padding:12px 16px;margin-bottom:8px;border-left:3px solid {LIME_COLOR};">
          <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 4px 0;">{item.get('day')}</p>
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.5;">{item.get('description', '')}</p>
        </div>"""

    post_params = first_post or {}
    caption = post_params.get("caption", "")
    hashtags = post_params.get("hashtags", [])
    image_url = post_params.get("image_url")
    platform = post_params.get("platform", "instagram").title()
    approve_url = f"{base_url}/actions/approve?token={first_approve_token}"
    decline_url = f"{base_url}/actions/decline?token={first_decline_token}"

    image_html = (
        f'<img src="{image_url}" alt="Post image" style="width:100%;border-radius:8px;margin-bottom:12px;display:block;" />'
        if image_url else
        f'<div style="background:#F3F4F6;border:2px dashed #D1D5DB;border-radius:8px;padding:20px;text-align:center;margin-bottom:12px;">'
        f'<p style="font-size:13px;color:{MUTED_COLOR};margin:0;">📷 Marlo will generate an image when you approve</p></div>'
    )

    hashtags_html = (
        f'<p style="font-size:12px;color:#9CA3AF;margin:8px 0 16px 0;">{" ".join(hashtags[:10])}</p>'
        if hashtags else ""
    )

    ads_html = ""
    if google_campaign:
        keywords = google_campaign.get("keywords", [])
        kw_list = ", ".join([k.get("keyword", k) if isinstance(k, dict) else k for k in keywords[:5]])
        ads_approve_url = f"{base_url}/actions/approve?token={ads_approve_token}"
        ads_decline_url = f"{base_url}/actions/decline?token={ads_decline_token}"
        ads_html = f"""
        {section_divider()}
        <p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;letter-spacing:0.08em;margin:0 0 12px 0;">Your Google Ads Campaign</p>
        <div style="background:#F8FAFC;border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid {BORDER_COLOR};">
          <p style="font-size:15px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">{google_campaign.get('campaign_name', 'Search Campaign')}</p>
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 4px 0;line-height:1.6;"><strong>Keywords:</strong> {kw_list}</p>
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 4px 0;line-height:1.6;"><strong>Budget:</strong> ${google_campaign.get('daily_budget', 0):.2f}/day</p>
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 16px 0;line-height:1.6;"><strong>Goal:</strong> {google_campaign.get('campaign_goal', '')}</p>
          {approve_button("✓ Approve Campaign", ads_approve_url)}
          {decline_button("✗ Skip for now", ads_decline_url)}
        </div>"""

    content = f"""
    <p style="font-size:17px;font-weight:700;color:{TEXT_COLOR};margin:0 0 8px 0;">🚀 Welcome to Marlo, {first_name}!</p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      Your setup is complete and I've built {business_name}'s first content plan. Here's everything you need to know about how Marlo works — this is the only time I'll explain the full system.
    </p>

    {section_divider()}

    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 12px 0;">📅 How your weekly cycle works</p>

    {weekly_cadence_diagram()}

    <div style="background:#F9FAFB;border-radius:8px;padding:20px;margin-bottom:20px;border:1px solid {BORDER_COLOR};">
      <p style="font-size:13px;color:{TEXT_COLOR};margin:0 0 12px 0;line-height:1.8;">
        <strong>Day 1 (your kickoff day)</strong> — Every week you'll get this email with:<br>
        &nbsp;&nbsp;• Last week's performance summary<br>
        &nbsp;&nbsp;• This week's content strategy<br>
        &nbsp;&nbsp;• Image guide (what photos will make each post stronger)<br>
        &nbsp;&nbsp;• First post of the week ready for approval
      </p>
      <p style="font-size:13px;color:{TEXT_COLOR};margin:0 0 12px 0;line-height:1.8;">
        <strong>Days 2–8</strong> — The day before each scheduled post, you'll get an approval email. Tap Approve → it posts at your preferred time. Don't tap → it expires automatically. Posts can fall on any day of the week including weekends. Day 8 rolls into the next cycle's Day 1.
      </p>
      <p style="font-size:13px;color:{TEXT_COLOR};margin:0 0 12px 0;line-height:1.8;">
        <strong>Day 7</strong> — You'll get a detailed analytics email covering reach, engagement, audience insights, and strategy recommendations for next week. Reply with feedback before your next kickoff.
      </p>
      <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
        💬 You can reply to <em>any</em> Marlo email to make changes, request revisions, or ask questions.
      </p>
    </div>

    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 12px 0;">✅ How approvals work</p>
    <div style="background:#F0F9FF;border-radius:8px;padding:16px 20px;margin-bottom:20px;">
      <p style="font-size:13px;color:#0369A1;margin:0;line-height:1.9;">
        ✓ Tap <strong>Approve</strong> → post goes live at your scheduled time<br>
        ✗ Tap <strong>Skip</strong> → nothing happens, post is cancelled<br>
        ✏️ <strong>Reply with changes</strong> → Marlo rewrites and sends a new version<br>
        📷 <strong>Reply with a photo</strong> → replaces the AI-generated image<br>
        🕐 <strong>Don't respond</strong> → post expires automatically (no action needed)
      </p>
    </div>

    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">📆 Choose your kickoff day</p>
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 12px 0;line-height:1.6;">
      Your kickoff day is when you receive the weekly plan. Currently set to <strong>{first_post_day}</strong>. Change it anytime:
    </p>
    <div style="margin-bottom:24px;">{day_buttons_html}</div>

    {section_divider()}

    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">🧠 This week's content strategy</p>
    <div style="background:#F9FAFB;border-radius:8px;padding:16px 20px;margin-bottom:20px;border-left:3px solid {BRAND_COLOR};">
      <p style="font-size:13px;color:{TEXT_COLOR};margin:0;line-height:1.7;">{strategy_summary}</p>
    </div>

    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">📅 This week's posting schedule</p>
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 20px 0;line-height:1.6;">{schedule_html}</p>

    {f'''<p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">📸 Image guide — photos that will make your posts stronger</p>
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 12px 0;line-height:1.6;">
      Marlo generates images automatically, but your real photos always perform better. Here's what to shoot this week:
    </p>
    {image_guide_html}
    {section_divider()}''' if image_guide_html else section_divider()}

    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 12px 0;">📸 {platform} · {first_post_day} — ready for your approval</p>
    <div style="background:#FFFFFF;border:1px solid {BORDER_COLOR};border-radius:12px;padding:20px;margin-bottom:16px;">
      {image_html}
      <p style="font-size:14px;color:{TEXT_COLOR};line-height:1.7;margin:0 0 4px 0;">{caption}</p>
      {hashtags_html}
      <div style="background:#F9FAFB;border-radius:6px;padding:10px 12px;margin-bottom:16px;">
        <p style="font-size:12px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
          ✏️ <strong>Want changes?</strong> Reply: <em>"Change {first_post_day} post: [your instruction]"</em><br>
          📷 <strong>Have a photo?</strong> Reply with the photo attached and it'll replace the image above.
        </p>
      </div>
      {approve_button(f"✓ Approve {first_post_day} post", approve_url)}
      {decline_button("✗ Skip", decline_url)}
    </div>

    {ads_html}

    {section_divider()}
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.8;">
      You can reply to this email anytime to adjust your posting schedule, kickoff day, or ask Marlo anything.
    </p>"""

    return base_template(content, preheader="Welcome to Marlo — your first content plan is ready")


# ─── WEEKLY KICKOFF EMAIL ─────────────────────────────────────────────────────

def weekly_kickoff_template(
    first_name: str,
    business_name: str,
    business_id: str,
    first_post: dict,
    first_post_day: str,
    first_approve_token: str,
    first_decline_token: str,
    google_campaign: dict,
    ads_approve_token: str,
    ads_decline_token: str,
    posting_schedule: list,
    strategy_summary: str,
    image_guide: list,
    last_week_stats: dict,
    base_url: str,
) -> str:
    approved = last_week_stats.get("approved", 0)
    skipped  = last_week_stats.get("skipped", 0)
    expired  = last_week_stats.get("expired", 0)

    stats_html = f"""
    <table width="100%" cellpadding="8" cellspacing="0" style="margin-bottom:24px;">
      <tr>
        {metric_card("Posts published", str(approved))}
        <td style="width:2%;"></td>
        {metric_card("Skipped", str(skipped))}
        <td style="width:2%;"></td>
        {metric_card("Expired", str(expired), "no response")}
      </tr>
    </table>"""

    schedule_html = " → ".join([f'<strong>{d}</strong>' for d in posting_schedule])

    image_guide_html = ""
    for item in image_guide:
        image_guide_html += f"""
        <div style="background:#F9FAFB;border-radius:6px;padding:12px 16px;margin-bottom:8px;border-left:3px solid {LIME_COLOR};">
          <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 4px 0;">{item.get('day')}</p>
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.5;">{item.get('description', '')}</p>
        </div>"""

    post_params = first_post or {}
    caption = post_params.get("caption", "")
    hashtags = post_params.get("hashtags", [])
    image_url = post_params.get("image_url")
    platform = post_params.get("platform", "instagram").title()
    approve_url = f"{base_url}/actions/approve?token={first_approve_token}"
    decline_url = f"{base_url}/actions/decline?token={first_decline_token}"

    image_html = (
        f'<img src="{image_url}" alt="Post image" style="width:100%;border-radius:8px;margin-bottom:12px;display:block;" />'
        if image_url else
        f'<div style="background:#F3F4F6;border:2px dashed #D1D5DB;border-radius:8px;padding:20px;text-align:center;margin-bottom:12px;">'
        f'<p style="font-size:13px;color:{MUTED_COLOR};margin:0;">📷 Marlo will generate an image when you approve</p></div>'
    )

    hashtags_html = (
        f'<p style="font-size:12px;color:#9CA3AF;margin:8px 0 16px 0;">{" ".join(hashtags[:10])}</p>'
        if hashtags else ""
    )

    ads_html = ""
    if google_campaign:
        keywords = google_campaign.get("keywords", [])
        kw_list = ", ".join([k.get("keyword", k) if isinstance(k, dict) else k for k in keywords[:5]])
        ads_approve_url = f"{base_url}/actions/approve?token={ads_approve_token}"
        ads_decline_url = f"{base_url}/actions/decline?token={ads_decline_token}"
        ads_html = f"""
        {section_divider()}
        <p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;letter-spacing:0.08em;margin:0 0 12px 0;">Google Ads Campaign</p>
        <div style="background:#F8FAFC;border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid {BORDER_COLOR};">
          <p style="font-size:15px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">{google_campaign.get('campaign_name', 'Search Campaign')}</p>
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 4px 0;"><strong>Keywords:</strong> {kw_list}</p>
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 16px 0;"><strong>Budget:</strong> ${google_campaign.get('daily_budget', 0):.2f}/day</p>
          {approve_button("✓ Approve Campaign", ads_approve_url)}
          {decline_button("✗ Skip for now", ads_decline_url)}
        </div>"""

    content = f"""
    <p style="font-size:17px;font-weight:700;color:{TEXT_COLOR};margin:0 0 8px 0;">📅 Your week ahead, {first_name}</p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      Here's last week's summary, this week's strategy, and your first post ready to approve.
    </p>

    <p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;letter-spacing:0.05em;margin:0 0 12px 0;">Last week</p>
    {stats_html}

    {section_divider()}

    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">🧠 This week's strategy</p>
    <div style="background:#F9FAFB;border-radius:8px;padding:16px 20px;margin-bottom:20px;border-left:3px solid {BRAND_COLOR};">
      <p style="font-size:13px;color:{TEXT_COLOR};margin:0;line-height:1.7;">{strategy_summary}</p>
    </div>

    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">📅 This week's schedule</p>
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 20px 0;">{schedule_html}</p>

    {f'''<p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">📸 Image guide</p>
    {image_guide_html}
    {section_divider()}''' if image_guide_html else section_divider()}

    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 12px 0;">📸 {platform} · {first_post_day}</p>
    <div style="background:#FFFFFF;border:1px solid {BORDER_COLOR};border-radius:12px;padding:20px;margin-bottom:16px;">
      {image_html}
      <p style="font-size:14px;color:{TEXT_COLOR};line-height:1.7;margin:0 0 4px 0;">{caption}</p>
      {hashtags_html}
      <div style="background:#F9FAFB;border-radius:6px;padding:10px 12px;margin-bottom:16px;">
        <p style="font-size:12px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
          ✏️ <strong>Want changes?</strong> Reply: <em>"Change {first_post_day} post: [your instruction]"</em><br>
          📷 <strong>Have a photo?</strong> Reply with the photo attached.
        </p>
      </div>
      {approve_button(f"✓ Approve {first_post_day} post", approve_url)}
      {decline_button("✗ Skip", decline_url)}
    </div>

    {ads_html}"""

    return base_template(content, preheader=f"Your week ahead — {first_post_day}'s post is ready to approve")


# ─── POST APPROVAL EMAIL ─────────────────────────────────────────────────────

def post_approval_template(
    first_name: str,
    post: dict,
    scheduled_day: str,
    approve_token: str,
    decline_token: str,
    base_url: str,
) -> str:
    caption = post.get("caption", "")
    hashtags = post.get("hashtags", [])
    image_url = post.get("image_url")
    platform = post.get("platform", "instagram").title()
    approve_url = f"{base_url}/actions/approve?token={approve_token}"
    decline_url = f"{base_url}/actions/decline?token={decline_token}"

    image_html = (
        f'<img src="{image_url}" alt="Post image" style="width:100%;border-radius:8px;margin-bottom:12px;display:block;" />'
        if image_url else
        f'<div style="background:#F3F4F6;border:2px dashed #D1D5DB;border-radius:8px;padding:20px;text-align:center;margin-bottom:12px;">'
        f'<p style="font-size:13px;color:{MUTED_COLOR};margin:0;">📷 Marlo will generate an image when you approve</p></div>'
    )

    hashtags_html = (
        f'<p style="font-size:12px;color:#9CA3AF;margin:8px 0 16px 0;">{" ".join(hashtags[:10])}</p>'
        if hashtags else ""
    )

    content = f"""
    <p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">📅 Tomorrow is {scheduled_day}, {first_name}</p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      Here's your {scheduled_day} post. Approve it today and it'll go live tomorrow morning.
    </p>
    <div style="background:#FFFFFF;border:1px solid {BORDER_COLOR};border-radius:12px;padding:20px;margin-bottom:16px;">
      <p style="font-size:12px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;letter-spacing:0.08em;margin:0 0 16px 0;">
        📸 {platform} · {scheduled_day}
      </p>
      {image_html}
      <p style="font-size:14px;color:{TEXT_COLOR};line-height:1.7;margin:0 0 4px 0;">{caption}</p>
      {hashtags_html}
      <div style="background:#F9FAFB;border-radius:6px;padding:10px 12px;margin-bottom:16px;">
        <p style="font-size:12px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
          ✏️ <strong>Want changes?</strong> Reply: <em>"Change {scheduled_day} post: [your instruction]"</em><br>
          📷 <strong>Have a photo?</strong> Reply with the photo attached.
        </p>
      </div>
      {approve_button(f"✓ Approve {scheduled_day} post", approve_url)}
      {decline_button("✗ Skip", decline_url)}
    </div>
    <p style="font-size:12px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      If you don't respond, this post will expire automatically. No action needed to skip.
    </p>"""

    return base_template(content, preheader=f"Tomorrow is {scheduled_day} — approve your post now")


# ─── WEEKLY ANALYTICS EMAIL ───────────────────────────────────────────────────

def weekly_analytics_template(
    first_name: str,
    business_name: str,
    insights: dict,
) -> str:
    raw = insights.get("_raw", {})
    posting = raw.get("posting_stats", {})
    instagram = raw.get("instagram", {})
    google = raw.get("google_ads", {})

    week_start = insights.get("week_start", "")
    week_end   = insights.get("week_end", "")

    reach = instagram.get("total_reach") or google.get("total_impressions") or 0
    clicks = google.get("total_clicks", 0)
    approved = posting.get("approved", 0)

    metrics_html = f"""
    <table width="100%" cellpadding="8" cellspacing="0" style="margin-bottom:24px;">
      <tr>
        {metric_card("People reached", f"{reach:,}" if reach else "—")}
        <td style="width:2%;"></td>
        {metric_card("Posts published", str(approved))}
        <td style="width:2%;"></td>
        {metric_card("Ad clicks", str(clicks) if clicks else "—")}
      </tr>
    </table>"""

    audience_items = insights.get("audience_insights", [])
    audience_html = "".join([
        f'<li style="margin-bottom:10px;font-size:14px;color:{TEXT_COLOR};line-height:1.6;">{item}</li>'
        for item in audience_items
    ])

    content_perf = insights.get("content_performance", {})
    content_html = ""
    if content_perf.get("best_performing_content"):
        content_html += f"""
        <div style="background:#F0FDF4;border-radius:6px;padding:12px 16px;margin-bottom:8px;">
          <p style="font-size:12px;font-weight:600;color:#15803D;margin:0 0 4px 0;">✅ What worked</p>
          <p style="font-size:13px;color:{TEXT_COLOR};margin:0;line-height:1.5;">{content_perf['best_performing_content']}</p>
        </div>"""
    if content_perf.get("worst_performing_content"):
        content_html += f"""
        <div style="background:#FEF2F2;border-radius:6px;padding:12px 16px;margin-bottom:8px;">
          <p style="font-size:12px;font-weight:600;color:#DC2626;margin:0 0 4px 0;">⚠️ What to improve</p>
          <p style="font-size:13px;color:{TEXT_COLOR};margin:0;line-height:1.5;">{content_perf['worst_performing_content']}</p>
        </div>"""
    if content_perf.get("engagement_pattern"):
        content_html += f"""
        <div style="background:#EFF6FF;border-radius:6px;padding:12px 16px;margin-bottom:8px;">
          <p style="font-size:12px;font-weight:600;color:#1D4ED8;margin:0 0 4px 0;">📊 Engagement pattern</p>
          <p style="font-size:13px;color:{TEXT_COLOR};margin:0;line-height:1.5;">{content_perf['engagement_pattern']}</p>
        </div>"""

    kw_items = insights.get("keyword_insights", [])
    kw_html = "".join([
        f'<li style="margin-bottom:10px;font-size:14px;color:{TEXT_COLOR};line-height:1.6;">{item}</li>'
        for item in kw_items
    ])

    strategy_items = insights.get("next_week_strategy", [])
    strategy_html = "".join([
        f'<div style="background:#F9FAFB;border-radius:6px;padding:12px 16px;margin-bottom:8px;border-left:3px solid {LIME_COLOR};">'
        f'<p style="font-size:13px;color:{TEXT_COLOR};margin:0;line-height:1.5;">{item}</p></div>'
        for item in strategy_items
    ])

    content = f"""
    <p style="font-size:17px;font-weight:700;color:{TEXT_COLOR};margin:0 0 8px 0;">📊 Weekly results for {business_name}</p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      {week_start} – {week_end} · Your full performance breakdown
    </p>
    {metrics_html}
    <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 24px 0;line-height:1.7;background:#F9FAFB;padding:16px;border-radius:8px;">
      {insights.get('performance_summary', '')}
    </p>
    {section_divider()}
    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 12px 0;">👥 Audience insights</p>
    <ul style="padding-left:20px;margin:0 0 24px 0;">{audience_html}</ul>
    {section_divider()}
    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 12px 0;">📸 Content performance</p>
    {content_html}
    {f'''{section_divider()}
    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 12px 0;">🔍 Keyword insights</p>
    <ul style="padding-left:20px;margin:0 0 24px 0;">{kw_html}</ul>''' if kw_html else ''}
    {section_divider()}
    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">💰 Budget</p>
    <p style="font-size:14px;color:{TEXT_COLOR};margin:0 0 24px 0;line-height:1.6;background:#FFFBEB;padding:14px;border-radius:8px;border-left:3px solid #F59E0B;">
      {insights.get('budget_recommendation', '')}
    </p>
    {section_divider()}
    <p style="font-size:14px;font-weight:600;color:{TEXT_COLOR};margin:0 0 12px 0;">🎯 Next week's strategy</p>
    {strategy_html}
    <div style="background:#F0F9FF;border-radius:8px;padding:16px;margin-top:24px;">
      <p style="font-size:13px;font-weight:600;color:#0369A1;margin:0 0 6px 0;">👀 One thing to watch next week</p>
      <p style="font-size:14px;color:{TEXT_COLOR};margin:0;line-height:1.6;">{insights.get('one_thing_to_watch', '')}</p>
    </div>
    {section_divider()}
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.6;">
      Reply to this email with any feedback or strategy adjustments before your next kickoff. Marlo reads every reply. 💬
    </p>"""

    return base_template(content, preheader=f"Your weekly results — {week_start} to {week_end}")


# ─── REMAINING TEMPLATES ──────────────────────────────────────────────────────

def morning_briefing_template(
    business_name: str,
    first_name: str,
    yesterday_metrics: dict,
    actions: list,
    base_url: str
) -> str:
    metrics_rows = ""
    for m in yesterday_metrics.get("highlights", []):
        metrics_rows += metric_row(m["label"], m["value"], m.get("trend", ""), m.get("positive", True))

    results_section = f"""
    <p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 12px 0;">☀️ Good morning {first_name}!</p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 20px 0;">Here's what happened yesterday and what I recommend today.</p>
    <p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;letter-spacing:0.05em;margin:0 0 8px 0;">YESTERDAY'S RESULTS</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:8px;">{metrics_rows}</table>"""

    actions_section = ""
    if actions:
        actions_section += section_divider()
        actions_section += f'<p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;letter-spacing:0.05em;margin:0 0 20px 0;">TODAY\'S RECOMMENDATIONS</p>'
        for i, action in enumerate(actions):
            approve_url = f"{base_url}/actions/approve?token={action['approve_token']}"
            decline_url = f"{base_url}/actions/decline?token={action['decline_token']}"
            actions_section += f"""
            <div style="margin-bottom:24px;">
              <p style="font-size:15px;font-weight:600;color:{TEXT_COLOR};margin:0 0 6px 0;">{i+1}. {action['title']}</p>
              <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 12px 0;line-height:1.5;">{action['description']}</p>
              {approve_button("✓ Approve", approve_url)}
              {decline_button("✗ Decline", decline_url)}
            </div>"""

    content = results_section + actions_section
    return base_template(content, preheader=f"Your marketing update for {business_name}")


def photo_response_template(first_name: str, original_caption: str,
                              platform_previews: list, base_url: str) -> str:
    previews_html = ""
    for p in platform_previews:
        image_html = ""
        if p.get("image_url"):
            image_html = f'<img src="{p["image_url"]}" alt="{p["platform_label"]}" style="width:100%;max-width:400px;border-radius:8px;margin-bottom:10px;display:block;" />'
        previews_html += f"""
        <div style="margin-bottom:24px;padding-bottom:24px;border-bottom:1px solid {BORDER_COLOR};">
          <p style="font-size:13px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">📱 {p['platform_label']}</p>
          {image_html}
          <p style="font-size:13px;color:{MUTED_COLOR};margin:0 0 10px 0;font-style:italic;">Caption: "{p['caption'][:120]}..."</p>
          {approve_button(f"✓ Post to {p['platform_label']}", p['approve_url'])}
        </div>"""

    content = f"""
    <p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">📸 Got your photo, {first_name}!</p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">
      I've enhanced it and prepared versions for each platform. Approve any you'd like to post.
    </p>
    {previews_html}
    <p style="font-size:13px;color:{MUTED_COLOR};margin:16px 0 0 0;">Want to edit a caption? Reply: "Edit Instagram caption: [your new text]"</p>"""
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
    <p style="font-size:16px;font-weight:600;color:{TEXT_COLOR};margin:0 0 8px 0;">📊 Your weekly report, {first_name}</p>
    <p style="font-size:14px;color:{MUTED_COLOR};margin:0 0 24px 0;line-height:1.6;">{summary}</p>
    <p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;letter-spacing:0.05em;margin:0 0 12px 0;">KEY INSIGHTS</p>
    <ul style="padding-left:20px;margin:0 0 24px 0;">{insights_html}</ul>
    {section_divider()}
    <p style="font-size:13px;font-weight:600;color:{MUTED_COLOR};text-transform:uppercase;letter-spacing:0.05em;margin:0 0 12px 0;">NEXT WEEK'S PRIORITIES</p>
    <ul style="padding-left:20px;margin:0 0 24px 0;">{recs_html}</ul>
    <p style="font-size:13px;color:{MUTED_COLOR};margin:0;line-height:1.6;">Reply with any questions about this report, or tell me what to focus on next week.</p>"""
    return base_template(content, preheader="Your weekly marketing report")