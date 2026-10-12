from django.urls import path

from shared.api.health import HealthView

urlpatterns = [
    path("api/v1/health", HealthView.as_view(), name="health"),
]

handler404 = "shared.api.errors.not_found"
handler500 = "shared.api.errors.server_error"
