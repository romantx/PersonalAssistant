import imaplib
import smtplib
from email.message import EmailMessage
import email
from email.header import decode_header
from langchain_core.tools import tool
from config import settings

def _get_imap_connection(provider: str):
    if provider.lower() == "gmail":
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(settings.gmail_email, settings.gmail_app_password)
        return mail
    elif provider.lower() == "proton":
        mail = imaplib.IMAP4(settings.imap_host, settings.imap_port)
        mail.starttls()
        mail.login(settings.proton_email, settings.proton_password)
        return mail
    raise ValueError("Invalid provider. Use 'gmail' or 'proton'")

def _get_smtp_connection(provider: str):
    if provider.lower() == "gmail":
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(settings.gmail_email, settings.gmail_app_password)
        return server
    elif provider.lower() == "proton":
        server = smtplib.SMTP(settings.imap_host, settings.smtp_port)
        server.starttls()
        server.login(settings.proton_email, settings.proton_password)
        return server
    raise ValueError("Invalid provider. Use 'gmail' or 'proton'")

@tool
def read_emails(provider: str, limit: int = 5) -> str:
    """Reads the most recent emails from the specified provider ('gmail' or 'proton')."""
    try:
        mail = _get_imap_connection(provider)
        mail.select("inbox")
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            return "Failed to search inbox."
            
        email_ids = messages[0].split()
        if not email_ids:
            return "Inbox is empty."
            
        latest_ids = email_ids[-limit:]
        
        output = []
        for e_id in reversed(latest_ids):
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    from_ = msg.get("From")
                    output.append(f"From: {from_}\nSubject: {subject}\n---")
                    
        mail.logout()
        return "\n".join(output) if output else "No readable emails found."
    except Exception as e:
        return f"Error reading emails from {provider}: {str(e)}"

@tool
def send_email(provider: str, to: str, subject: str, body: str) -> str:
    """Sends an email using the specified provider ('gmail' or 'proton')."""
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["To"] = to
        
        if provider.lower() == "gmail":
            msg["From"] = settings.gmail_email
        else:
            msg["From"] = settings.proton_email
            
        server = _get_smtp_connection(provider)
        server.send_message(msg)
        server.quit()
        return f"Email successfully sent via {provider} to {to}"
    except Exception as e:
        return f"Error sending email via {provider}: {str(e)}"
