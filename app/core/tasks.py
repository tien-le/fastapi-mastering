import logging
import json
from fastapi import HTTPException
import httpx
from app.core.config_loader import settings

logger = logging.getLogger(__name__)


async def send_simple_message(
    to: str,
    subject: str,
    body: str,
    html: str | None = None
) -> dict:
    """
    Send a simple email using Mailgun's messages API.
    Raises HTTPException on any Mailgun or network error.
    """
    # Validate Mailgun configuration
    if not settings.MAILGUN_API_KEY:
        logger.error("MAILGUN_API_KEY is not configured")
        raise HTTPException(
            status_code=500,
            detail="Mailgun API key is not configured. Please set DEV_MAILGUN_API_KEY (or PROD_MAILGUN_API_KEY) in your .env file."
        )

    if not settings.MAILGUN_DOMAIN:
        logger.error("MAILGUN_DOMAIN is not configured")
        raise HTTPException(
            status_code=500,
            detail="Mailgun domain is not configured. Please set DEV_MAILGUN_DOMAIN (or PROD_MAILGUN_DOMAIN) in your .env file."
        )

    to = to or "Roger LE <le.tien.ai.dev@gmail.com>"
    subject = subject or "Good morning"
    body = (
        body
        or "Congratulations Roger LE, you just sent an email with Mailgun!"
    )

    url = f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages"
    auth = ("api", settings.MAILGUN_API_KEY)
    data = {
        "from": f"Roger LE <postmaster@{settings.MAILGUN_DOMAIN}>",
        "to": to,
        "subject": subject,
        "text": body,
        "html": html
    }
    logger.info(f"Sending email via Mailgun", extra={"to": to, "subject": subject, "body": body, "html": html})
    logger.info(f"Mailgun API key: {settings.MAILGUN_API_KEY}")
    logger.info(f"Mailgun domain: {settings.MAILGUN_DOMAIN}")
    logger.info(f"Mailgun data: {data}")

    try:
        async with httpx.AsyncClient() as client:  # default timeout of 5.0 seconds
            response = await client.post(url, auth=auth, data=data)

            # Raises httpx.HTTPStatusError if 4xx/5xx
            response.raise_for_status()

            result = response.json()
            logger.info(f"Email sent successfully via Mailgun", extra={"to": to, "message_id": result.get("id")})
            return result

    except httpx.HTTPStatusError as exc:
        # Mailgun returned an error (400/401/500 etc)
        error_text = exc.response.text
        error_message = error_text

        # Try to parse JSON error response from Mailgun
        try:
            error_json = exc.response.json()
            if isinstance(error_json, dict) and "message" in error_json:
                error_message = error_json["message"]
        except (json.JSONDecodeError, ValueError):
            # If not JSON, use the raw text
            pass

        logger.error(
            f"Mailgun API error: {exc.response.status_code} - {error_message}"
        )

        # In development, don't fail registration if email sending fails
        # This is useful for testing with Mailgun sandbox accounts
        if settings.ENV_STATE == "dev":
            logger.warning(
                f"Email sending failed in development mode. Registration will continue. "
                f"Error: {error_message}. "
                f"To fix: Add '{to}' to authorized recipients in Mailgun dashboard or upgrade your account.",
                extra={"to": to, "error": error_message, "status_code": exc.response.status_code}
            )
            # Return a mock response so the function doesn't fail
            return {
                "message": "Email sending failed (dev mode)",
                "id": "<dev-mode-skip>",
                "error": error_message
            }

        # In production/test, raise the exception
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Mailgun API error: {error_message}"
        ) from exc

    except httpx.RequestError as exc:
        # Network issues, DNS failure, timeout
        logger.error(f"Error while sending request to Mailgun: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Failed to reach Mailgun service"
        )


async def send_user_registration_email_text_body(email: str, confirmation_url: str):
    """
    Send registration confirmation email to user.

    Args:
        email: User's email address
        confirmation_url: URL for email confirmation

    Returns:
        dict: Response from Mailgun API or mock response in dev mode if sending fails
    """
    logger.info(f"Sending registration confirmation email", extra={"email": email})
    return await send_simple_message(
        to=email,
        subject="Successfully signed up",
        body= (
            f"Hi {email}! You have successfully signed up to our system."
            " Please confirm your email by clicking on the"
            f" following link: {confirmation_url}"
        )
    )

async def send_user_registration_email(email: str, confirmation_url: str):
    """
    Send registration confirmation email to user.
    """

    logger.info(
        "Sending registration confirmation email",
        extra={"email": email}
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto; padding: 20px; box-sizing: border-box;">
        <h2 style="color: #444; text-align: center;">Pleased to meet you!</h2>

        <p>Hi {email},</p>

        <p>Thanks for signing up! Please click the button below to confirm your email address.</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{confirmation_url}"
            role="button"
            aria-label="Verify your email address"
            style="
                    background-color: #4F46E5;
                    padding: 14px 24px;
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                    display: inline-block;
            ">
                Verify email address
            </a>
        </div>

        <p style="font-weight: bold;">Need help getting started?</p>
        <p>
            Check out our help page for guides, FAQs, and documentation.
            If you need anything, just reach out — we’ll reply in record time!
        </p>

        <p>⏰ <strong>Note:</strong> This confirmation link expires in <strong>20 minutes</strong>.</p>

        <p>Happy sending,<br>Team LAVIE 🚀</p>

        <hr style="margin: 40px 0; border: none; border-top: 1px solid #ddd;" />

        <p style="font-size: 12px; color: #777;">
            If you’re having trouble clicking the button above, copy and paste this URL into your browser:<br>
            <a href="{confirmation_url}" style="color: #4F46E5;">{confirmation_url}</a>
        </p>
    </div>
    """


    # Plain text fallback for clients that block HTML
    text_body = (
        f"Pleased to meet you!\n\n"
        f"Hi {email},\n\n"
        "Thanks for signing up! Confirm your email by visiting the link below:\n"
        f"{confirmation_url}\n\n"
        "Need help? Visit our help page for guides and FAQs.\n\n"
        "Happy sending!\n"
    )

    return await send_simple_message(
        to=email,
        subject="Confirm your email address",
        body=text_body,
        html=html_body,   # Make sure your send_simple_message supports html
    )

