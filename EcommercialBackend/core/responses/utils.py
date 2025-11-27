from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_otp_email(user, otp_code):
    subject = 'Xác nhận tài khoản của bạn'
    html_message = render_to_string('emails/otp_email.html', {
        'user': user,
        'otp_code': otp_code,
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email

    send_mail(
        subject,
        plain_message,
        from_email,
        [to_email],
        html_message=html_message,
        fail_silently=False,
    )


# In core/responses/utils.py or wherever your email utility functions are

def send_password_reset_email(user, otp_code):
    """
    Send password reset email with OTP code to the user
    """
    subject = "Password Reset Request"
    message = f"""
    Hello {user.full_name},

    You have requested to reset your password. 
    Your password reset code is: {otp_code}

    This code will expire in 10 minutes.

    If you did not request this password reset, please ignore this email or contact support if you have concerns.

    Best regards,
    Your Application Team
    """

    # Send email using your email sending mechanism
    # Assuming you have a function like send_email that handles the actual sending
    from django.core.mail import send_mail
    from django.conf import settings

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )