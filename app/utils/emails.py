import resend

from app.config.settings import settings

resend.api_key = settings.RESEND_API_KEY




def send_reset_email(
    email: str,
    reset_link: str
):
    resend.Emails.send({
        "from": "AssetIQ <onboarding@resend.dev>",
        "to": [email],
        "subject": "Reset Your Password",
        "html": f"""
        <h2>Password Reset</h2>

        <p>
            Click below to reset your password.
        </p>

        <a href="{reset_link}">
            Reset Password
        </a>

        <p>
            This link expires in 15 minutes.
        </p>
        """
    })