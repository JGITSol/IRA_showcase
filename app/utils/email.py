"""Email sending utilities."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings
from app.core.logging import logger


def send_email(
    email_to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> None:
    """Send an email.
    
    Args:
        email_to: Recipient email address
        subject: Email subject
        html_content: Email HTML content
        text_content: Plain text email content (optional)
    """
    if not settings.EMAILS_ENABLED:
        logger.warning(
            "Email sending is disabled. To enable, set EMAILS_ENABLED=True"
        )
        return
    
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.EMAILS_FROM_EMAIL
    message["To"] = email_to
    
    # Attach both HTML and plain text versions
    if text_content:
        part1 = MIMEText(text_content, "plain")
        message.attach(part1)
    
    part2 = MIMEText(html_content, "html")
    message.attach(part2)
    
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        logger.info(f"Email sent to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {e}")


def send_reset_password_email(email_to: str, email: str, token: str) -> None:
    """Send password reset email.
    
    Args:
        email_to: Recipient email address
        email: User's email address
        token: Password reset token
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    
    # In production, replace with your frontend reset password URL
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    html_content = f"""
    <p>Hello,</p>
    <p>You requested a password reset for your {project_name} account.</p>
    <p>Click the link below to reset your password:</p>
    <p><a href="{reset_url}">Reset Password</a></p>
    <p>Or copy and paste this link into your browser:</p>
    <p>{reset_url}</p>
    <p>This link will expire in {settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS} hours.</p>
    <p>If you did not request a password reset, please ignore this email.</p>
    <p>Thanks,<br>
    {project_name} Team</p>
    ""
    """.format(
        reset_url=reset_url, project_name=project_name
    )
    
    text_content = f"""
    Hello,
    
    You requested a password reset for your {project_name} account.
    
    Please click on the following link to reset your password:
    {reset_url}
    
    This link will expire in {settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS} hours.
    
    If you did not request a password reset, please ignore this email.
    
    Thanks,
    {project_name} Team
    """.format(project_name=project_name)
    
    send_email(
        email_to=email_to,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )
    
    # Log the reset URL for development
    logger.info(f"Password reset URL for {email}: {reset_url}")
    
    # In development, log the token for testing
    if not settings.PRODUCTION:
        logger.info(f"Password reset token for {email}: {token}")
    
    # In production, use the actual email sending function
    send_email(
        email_to=email_to,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )


def send_new_account_email(email_to: str, username: str, token: str) -> None:
    """Send new account email.
    
    Args:
        email_to: Recipient email address
        username: User's username
        token: Account activation token
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for {username}"
    
    # In production, replace with your frontend activation URL
    activation_url = f"{settings.FRONTEND_URL}/activate?token={token}"
    
    html_content = f"""
    <p>Hello {username},</p>
    <p>Welcome to {project_name}!</p>
    <p>Your account has been created.</p>
    <p>Please click the link below to activate your account:</p>
    <p><a href="{activation_url}">Activate Account</a></p>
    <p>Or copy and paste this link into your browser:</p>
    <p>{activation_url}</p>
    <p>This link will expire in {settings.ACTIVATION_TOKEN_EXPIRE_HOURS} hours.</p>
    <p>Thanks,<br>
    {project_name} Team</p>
    ""
    """.format(
        username=username, activation_url=activation_url, project_name=project_name
    )
    
    text_content = f"""
    Hello {username},
    
    Welcome to {project_name}!
    
    Your account has been created.
    
    Please click on the following link to activate your account:
    {activation_url}
    
    This link will expire in {settings.ACTIVATION_TOKEN_EXPIRE_HOURS} hours.
    
    Thanks,
    {project_name} Team
    """.format(username=username, project_name=project_name)
    
    send_email(
        email_to=email_to,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )
