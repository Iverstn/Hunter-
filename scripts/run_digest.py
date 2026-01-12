from workers.digest import build_digest_html, build_digest_text, fetch_top_items
from workers.send_email import send_email

if __name__ == "__main__":
    items = fetch_top_items(limit=12)
    html_body = build_digest_html(items)
    text_body = build_digest_text(items)
    sent = send_email("AI Signal Radar Morning Digest", html_body, text_body)
    print("sent" if sent else "not sent")
