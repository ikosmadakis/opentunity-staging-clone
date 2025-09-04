from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include, reverse_lazy
from django.conf import settings
from devices import views as device_views
from devices.views import activate


def _from_email():
    # Always provide a valid sender, even if env vars are missing
    return (
        getattr(settings, "DEFAULT_FROM_EMAIL", None)
        or getattr(settings, "SERVER_EMAIL", None)
        or "no-reply@bluesun.pythonanywhere.com"
    )


urlpatterns = [
    path('admin/', admin.site.urls),

    # --- Password reset (logged-out flow) ---
    # 1) Request reset (enter email)
    path(
        "accounts/password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.txt",
            subject_template_name="registration/password_reset_subject.txt",
            from_email=_from_email(),
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    # 2) “We’ve emailed you” screen
    path(
        "accounts/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    # 3) Link from email → set new password
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    # 4) Finished screen
    path(
        "accounts/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    # Keep auth URLs (login/logout, etc.) AFTER custom password-reset routes
    path('accounts/', include('django.contrib.auth.urls')),

    # --- Your app routes ---
    path('signup/', device_views.signup, name='signup'),
    path('add-device/', device_views.add_device, name='add_device'),
    path("profile/", device_views.profile, name="profile"),
    path(
        "profile/password/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change_form.html",
            success_url=reverse_lazy("password_change_done")
        ),
        name="password_change",
    ),
    path(
        "profile/password/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html"
        ),
        name="password_change_done",
    ),

    path('', device_views.dashboard, name='dashboard'),  # homepage after login
    path('device/<int:pk>/',       device_views.asset_detail, name='asset_detail'),
    path('device/<int:pk>/edit/',  device_views.asset_edit,   name='asset_edit'),
    path("activate/<uidb64>/<token>/", activate, name="activate"),
    path('', include('devices.urls')),
    path("assets/<int:pk>/delete/", device_views.asset_delete, name="asset_delete"),
    path('api/assets/<int:asset_id>/enter-api-key/', device_views.asset_api_key_entry, name='asset_api_key_entry'),
]
