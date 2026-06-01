#!/usr/bin/env python3
"""
Portfolio Morning Briefing — Auto-Runner
Calls Claude API with the full briefing prompt, then emails via SendGrid.
"""

import os
import sys
import anthropic
import urllib.request
import urllib.error
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# ── Config from environment variables ──────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SENDGRID_API_KEY  = os.environ["SENDGRID_API_KEY"]
EMAIL_FROM        = os.environ["EMAIL_FROM"]   # must be verified in SendGrid
EMAIL_TO          = os.environ["EMAIL_TO"]

# ── Load the briefing prompt ────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(SCRIPT_DIR, "briefing_prompt.txt")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    BRIEFING_PROMPT = f.read()

# ── Call Claude ─────────────────────────────────────────────────────────────
def call_claude() -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    et_now   = datetime.now(ZoneInfo("America/New_York"))
    date_str = et_now.strftime("%A, %B %d, %Y")
    time_str = et_now.strftime("%I:%M %p ET")

    user_message = (
        f"Today is {date_str}. Current time: {time_str}.\n\n"
        "Please generate the complete Portfolio Morning Briefing using the "
        "instructions below. Follow every section, data source, and formatting "
        "rule exactly as specified.\n\n"
        + BRIEFING_PROMPT
    )

    print(f"[{time_str}] Sending request to Claude API...")

    full_response = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text in stream.text_stream:
            full_response += text
            print(text, end="", flush=True)

    print("\n\n[Done] Response received.")
    return full_response

# ── Convert Markdown → HTML ──────────────────────────────────────────────────
def markdown_to_html(md: str) -> str:
    import re

    lines     = md.split("\n")
    html_lines = []
    in_table  = False
    in_list   = False

    def inline(text):
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*',     r'<em>\1</em>', text)
        text = re.sub(r'_(.+?)_',       r'<em>\1</em>', text)
        text = re.sub(r'`(.+?)`',
            r'<code style="background:#f4f4f4;padding:1px 4px;border-radius:3px;">\1</code>', text)
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
        return text

    for line in lines:
        stripped = line.strip()

        if re.match(r'^---+$', stripped):
            if in_list:  html_lines.append("</ul>");   in_list  = False
            if in_table: html_lines.append("</table>"); in_table = False
            html_lines.append('<hr style="border:1px solid #ddd;margin:16px 0;">')
            continue

        h_match = re.match(r'^(#{1,4})\s+(.*)', stripped)
        if h_match:
            if in_list:  html_lines.append("</ul>");   in_list  = False
            if in_table: html_lines.append("</table>"); in_table = False
            level = len(h_match.group(1))
            sizes = {1:"24px", 2:"20px", 3:"17px", 4:"15px"}
            text  = inline(h_match.group(2))
            html_lines.append(
                f'<h{level} style="font-size:{sizes[level]};margin:18px 0 6px;'
                f'color:#1a1a2e;font-family:Arial,sans-serif;">{text}</h{level}>'
            )
            continue

        if stripped.startswith(">"):
            if in_list:  html_lines.append("</ul>");   in_list  = False
            if in_table: html_lines.append("</table>"); in_table = False
            text = inline(stripped.lstrip("> ").strip())
            html_lines.append(
                f'<blockquote style="border-left:4px solid #4a90d9;margin:8px 0;'
                f'padding:6px 12px;background:#f0f7ff;color:#333;font-style:italic;">'
                f'{text}</blockquote>'
            )
            continue

        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(re.match(r'^[-:]+$', c) for c in cells if c):
                continue
            if not in_table:
                html_lines.append(
                    '<table style="border-collapse:collapse;width:100%;margin:10px 0;font-size:13px;">'
                )
                in_table = True
                tag   = "th"
                style = 'style="background:#1a1a2e;color:#fff;padding:7px 10px;text-align:left;"'
            else:
                tag   = "td"
                style = 'style="padding:6px 10px;border-bottom:1px solid #eee;"'
            row = "".join(f"<{tag} {style}>{inline(c)}</{tag}>" for c in cells)
            html_lines.append(f"<tr>{row}</tr>")
            continue
        else:
            if in_table: html_lines.append("</table>"); in_table = False

        li_match = re.match(r'^[-*]\s+(.*)', stripped)
        if li_match:
            if not in_list:
                html_lines.append('<ul style="margin:6px 0;padding-left:20px;">'); in_list = True
            html_lines.append(f'<li style="margin:3px 0;">{inline(li_match.group(1))}</li>')
            continue
        else:
            if in_list: html_lines.append("</ul>"); in_list = False

        num_match = re.match(r'^\d+\.\s+(.*)', stripped)
        if num_match:
            html_lines.append(f'<p style="margin:3px 0;">• {inline(num_match.group(1))}</p>')
            continue

        if stripped == "":
            html_lines.append('<br>')
            continue

        html_lines.append(
            f'<p style="margin:5px 0;line-height:1.6;font-family:Arial,sans-serif;'
            f'font-size:14px;color:#222;">{inline(stripped)}</p>'
        )

    if in_list:  html_lines.append("</ul>")
    if in_table: html_lines.append("</table>")
    return "\n".join(html_lines)


def build_email_html(briefing_md: str, date_str: str) -> str:
    body_html = markdown_to_html(briefing_md)
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="background:#f5f5f5;margin:0;padding:20px;font-family:Arial,sans-serif;">
  <div style="max-width:860px;margin:0 auto;background:#fff;border-radius:8px;
              box-shadow:0 2px 8px rgba(0,0,0,0.1);overflow:hidden;">
    <div style="background:#1a1a2e;padding:20px 28px;">
      <h1 style="color:#fff;margin:0;font-size:22px;">📊 Portfolio Morning Briefing</h1>
      <p style="color:#aac4e8;margin:4px 0 0;font-size:14px;">{date_str}</p>
    </div>
    <div style="padding:24px 28px;">{body_html}</div>
    <div style="background:#f0f0f0;padding:14px 28px;font-size:11px;color:#888;border-top:1px solid #ddd;">
      Generated automatically by Claude · For informational purposes only · Not investment advice
    </div>
  </div>
</body>
</html>"""

# ── Send email via SendGrid ──────────────────────────────────────────────────
def send_email(subject: str, html_body: str, text_body: str):
    payload = json.dumps({
        "personalizations": [{"to": [{"email": EMAIL_TO}]}],
        "from": {"email": EMAIL_FROM},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text_body},
            {"type": "text/html",  "value": html_body},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )

    print(f"Sending email to {EMAIL_TO} via SendGrid...")
    with urllib.request.urlopen(req) as resp:
        status = resp.status
    print(f"SendGrid response: {status}")
    if status not in (200, 202):
        raise RuntimeError(f"SendGrid returned status {status}")
    print("Email sent successfully.")

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    et_now   = datetime.now(ZoneInfo("America/New_York"))
    date_str = et_now.strftime("%A, %B %d, %Y")
    subject  = f"📊 Portfolio Morning Briefing — {date_str}"

    try:
        briefing_md = call_claude()
    except Exception as e:
        print(f"ERROR calling Claude API: {e}", file=sys.stderr)
        sys.exit(1)

    html_body = build_email_html(briefing_md, date_str)

    try:
        send_email(subject, html_body, briefing_md)
    except Exception as e:
        print(f"ERROR sending email: {e}", file=sys.stderr)
        fallback_path = f"/tmp/briefing_{et_now.strftime('%Y%m%d')}.md"
        with open(fallback_path, "w") as f:
            f.write(briefing_md)
        print(f"Briefing saved locally to: {fallback_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
