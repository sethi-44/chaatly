from app.models import Meetup, User,MeetupParticipant
from app.schemas import MeetupResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import resend
import logging
import os

load_dotenv()

logger = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "Chaatly <onboarding@resend.dev>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8081")

def find_meetup(db, meetup_id):
    return db.query(Meetup).filter(
        Meetup.id == meetup_id
    ).first()

def find_user(db, user_id):
    return db.query(User).filter(
        User.id == user_id
    ).first()

def get_meetup_attendance(
    db: Session,
    meetup_id: int
):
    return db.query(
        MeetupParticipant
    ).filter(
        MeetupParticipant.meetup_id == meetup_id
    ).count()

def is_participant(
    db: Session,
    user_id: int,
    meetup_id: int
):
    return db.query(
        MeetupParticipant
    ).filter(
        MeetupParticipant.user_id == user_id,
        MeetupParticipant.meetup_id == meetup_id
    ).first()

def existing_user(db, user):
    return db.query(User).filter(
            or_(
                User.username == user.username,
                User.email == user.email
            )
        ).first()

def meetup_to_response(
    db: Session,
    meetup: Meetup
):
    attendee_count = get_meetup_attendance(
        db,
        meetup.id
    )

    return MeetupResponse(
        id=meetup.id,
        title=meetup.title,
        location=meetup.location,
        description=meetup.description,
        max_attendees=meetup.max_attendees,
        host=meetup.host,
        attendee_count=attendee_count,
        spots_left=meetup.max_attendees - attendee_count
    )

def send_verification_email(email: str, token: str):
    """Send a real verification email via Resend."""
    verification_url = f"{FRONTEND_URL}/verify-email?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background-color:#0D0D0F;font-family:Arial,Helvetica,sans-serif;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0D0D0F;padding:40px 20px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background-color:#1A1A1F;border-radius:16px;padding:40px;">
                        <tr>
                            <td align="center" style="padding-bottom:24px;">
                                <h1 style="margin:0;font-size:24px;font-weight:700;color:#FFFFFF;">Chaatly</h1>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding-bottom:16px;">
                                <p style="margin:0;font-size:32px;">✉️</p>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding-bottom:8px;">
                                <h2 style="margin:0;font-size:20px;font-weight:600;color:#FFFFFF;">Verify your email</h2>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding-bottom:32px;">
                                <p style="margin:0;font-size:14px;color:#8E8E9A;line-height:1.6;">
                                    Click the button below to verify your email address and activate your Chaatly account.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding-bottom:32px;">
                                <a href="{verification_url}" style="display:inline-block;padding:14px 32px;background-color:#FF6B35;color:#FFFFFF;text-decoration:none;border-radius:10px;font-size:16px;font-weight:700;">
                                    Verify Email
                                </a>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding-bottom:24px;">
                                <p style="margin:0;font-size:12px;color:#8E8E9A;line-height:1.6;">
                                    This link expires in 24 hours.<br>
                                    If you didn't create a Chaatly account, you can safely ignore this email.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="border-top:1px solid #2A2A35;padding-top:20px;">
                                <p style="margin:0;font-size:11px;color:#55555F;">
                                    If the button doesn't work, copy and paste this URL into your browser:<br>
                                    <a href="{verification_url}" style="color:#FF6B35;word-break:break-all;">{verification_url}</a>
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    params: resend.Emails.SendParams = {
        "from": SENDER_EMAIL,
        "to": [email],
        "subject": "Verify your Chaatly account",
        "html": html_content,
    }

    try:
        resend.Emails.send(params)
        logger.info(f"Verification email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {e}")
        raise

def send_password_reset_email(email: str, token: str):
    """Send a real password reset email via Resend."""
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background-color:#0D0D0F;font-family:Arial,Helvetica,sans-serif;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0D0D0F;padding:40px 20px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background-color:#1A1A1F;border-radius:16px;padding:40px;">
                        <tr>
                            <td align="center" style="padding-bottom:24px;">
                                <h1 style="margin:0;font-size:24px;font-weight:700;color:#FFFFFF;">Chaatly</h1>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding-bottom:16px;">
                                <p style="margin:0;font-size:32px;">🔑</p>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding-bottom:8px;">
                                <h2 style="margin:0;font-size:20px;font-weight:600;color:#FFFFFF;">Reset your password</h2>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding-bottom:32px;">
                                <p style="margin:0;font-size:14px;color:#8E8E9A;line-height:1.6;">
                                    We received a request to reset your Chaatly password.<br>
                                    Click the button below to choose a new one.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding-bottom:32px;">
                                <a href="{reset_url}" style="display:inline-block;padding:14px 32px;background-color:#FF6B35;color:#FFFFFF;text-decoration:none;border-radius:10px;font-size:16px;font-weight:700;">
                                    Reset Password
                                </a>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding-bottom:24px;">
                                <p style="margin:0;font-size:12px;color:#8E8E9A;line-height:1.6;">
                                    This link expires in 15 minutes.<br>
                                    If you didn't request a password reset, you can safely ignore this email.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="border-top:1px solid #2A2A35;padding-top:20px;">
                                <p style="margin:0;font-size:11px;color:#55555F;">
                                    If the button doesn't work, copy and paste this URL into your browser:<br>
                                    <a href="{reset_url}" style="color:#FF6B35;word-break:break-all;">{reset_url}</a>
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    params: resend.Emails.SendParams = {
        "from": SENDER_EMAIL,
        "to": [email],
        "subject": "Reset your Chaatly password",
        "html": html_content,
    }

    try:
        resend.Emails.send(params)
        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {e}")
        raise