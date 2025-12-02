import aiosmtplib
from email.message import EmailMessage
from fastapi import BackgroundTasks
from app.config import settings
import logging

# Configure logger
logger = logging.getLogger(__name__)

async def send_email_async(
    to: str,
    subject: str,
    body: str
) -> None:
    """
    Send an email asynchronously using SMTP.
    Uses credentials from settings.
    """
    message = EmailMessage()
    message["From"] = settings.SMTP_USER
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
        )
        logger.info(f"✅ Email sent to {to} | Subject: {subject}")
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to}: {str(e)}")
        raise RuntimeError(f"Email delivery failed: {str(e)}")

def send_otp_email(
    background_tasks: BackgroundTasks,
    email: str,
    otp: str
) -> None:
    """
    Send OTP email to admin during registration.
    """
    subject = "🔐 Your Admin Account Verification OTP"
    body = (
        f"Hello,\n\n"
        f"Your OTP for admin account verification is: {otp}\n\n"
        f"This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"Best regards,\nSchool Management System"
    )
    background_tasks.add_task(send_email_async, email, subject, body)

def send_verification_email(
    background_tasks: BackgroundTasks,
    email: str,
    token: str
) -> None:
    """
    Send email verification link to student during registration.
    """
    verification_link = f"http://localhost:8000/api/users/verification?token={token}"
    subject = "📧 Please Verify Your Student Account"
    body = (
        f"Hello,\n\n"
        f"Thank you for registering! Please verify your student account by clicking the link below:\n\n"
        f"{verification_link}\n\n"
        f"This link will expire in 24 hours.\n\n"
        f"If you did not create this account, please ignore this email.\n\n"
        f"Best regards,\nSchool Management System"
    )
    background_tasks.add_task(send_email_async, email, subject, body)

def send_password_set_email(
    background_tasks: BackgroundTasks,
    email: str,
    token: str
) -> None:
    """
    Send password setup email to teacher (created by admin).
    """
    password_link = f"http://localhost:8000/api/users/password-reset/confirm?token={token}"
    subject = "🧑‍🏫 Set Your Teacher Account Password"
    body = (
        f"Hello,\n\n"
        f"An administrator has created a teacher account for you.\n\n"
        f"Please set your password by clicking the link below:\n\n"
        f"{password_link}\n\n"
        f"This link will expire in 1 hour.\n\n"
        f"Best regards,\nSchool Management System"
    )
    background_tasks.add_task(send_email_async, email, subject, body)

def send_password_reset_email(
    background_tasks: BackgroundTasks,
    email: str,
    token: str
) -> None:
    """
    Send password reset email (for students/teachers).
    """
    reset_link = f"http://localhost:8000/api/users/password-reset/confirm?token={token}"
    subject = "🔒 Password Reset Request"
    body = (
        f"Hello,\n\n"
        f"We received a request to reset your password.\n\n"
        f"Click the link below to set a new password:\n\n"
        f"{reset_link}\n\n"
        f"This link will expire in 1 hour.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"Best regards,\nSchool Management System"
    )
    background_tasks.add_task(send_email_async, email, subject, body)