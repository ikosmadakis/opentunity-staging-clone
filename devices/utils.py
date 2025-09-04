from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings


def _from_addr():
    """
    Always return a valid 'from' address even if env vars are missing.
    """
    return (
        getattr(settings, "DEFAULT_FROM_EMAIL", None)
        or getattr(settings, "SERVER_EMAIL", None)
        or "no-reply@bluesun.pythonanywhere.com"
    )


def send_activation_email(request, user):
    site = get_current_site(request)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activate_url = f"https://{site.domain}/activate/{uidb64}/{token}/"

    subject = "Activate your Opentunity account"
    message = render_to_string(
        "registration/activation_email.txt",
        {
            "user": user,
            "activate_url": activate_url,
            "site_name": site.name,
        },
    )

    from_addr = _from_addr()
    try:
        send_mail(
            subject,
            message,
            from_addr,           # <-- robust sender
            [user.email],
            fail_silently=False, # raise here, then we catch
        )
    except Exception as e:
        # Don't take the signup down if email is misconfigured.
        # In staging with console backend you'll still see the email content in logs.
        print(f"WARN: activation email failed (to={user.email}, from={from_addr}): {e}")
