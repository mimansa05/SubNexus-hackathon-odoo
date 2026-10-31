import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

log = logging.getLogger("subnexus.email")


def send_email(to: str, subject: str, text: str, html: str | None = None) -> None:
    """Send via SMTP; with no SMTP_HOST configured, print the message (dev mode)."""
    if not settings.SMTP_HOST:
        print(f"\n--- EMAIL (SMTP not configured) ---\nTo: {to}\nSubject: {subject}\n\n{text}\n-----------------------------------\n")
        return

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception:
        log.exception("Could not send email to %s", to)


def send_verification_email(to: str, name: str | None, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    hello = name or "there"
    text = (
        f"Hi {hello},\n\nWelcome to SubNexus. Please confirm your email address to activate your account:\n\n"
        f"{link}\n\nThis link expires in {settings.EMAIL_VERIFY_EXPIRE_HOURS} hours. "
        "If you did not sign up, you can ignore this email."
    )
    html = (
        f"<p>Hi {hello},</p><p>Welcome to SubNexus. Please confirm your email address to activate your account.</p>"
        f'<p><a href="{link}" style="background:#0d0d10;color:#fff;padding:10px 20px;border-radius:999px;text-decoration:none">Confirm email</a></p>'
        f"<p>This link expires in {settings.EMAIL_VERIFY_EXPIRE_HOURS} hours. If you did not sign up, ignore this email.</p>"
    )
    send_email(to, "Confirm your SubNexus account", text, html)
