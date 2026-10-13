from django.urls import path

from modules.identity.api.views import (
    ChangePasswordView,
    CurrentUserView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
)

urlpatterns = [
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("auth/me", CurrentUserView.as_view(), name="auth-me"),
    path("auth/password/change", ChangePasswordView.as_view(), name="auth-password-change"),
    path("auth/password/reset", PasswordResetView.as_view(), name="auth-password-reset"),
    path(
        "auth/password/reset/confirm",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
]
