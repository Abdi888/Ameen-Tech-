from django.urls import include, path

from shared.api.health import HealthView

urlpatterns = [
    path("api/v1/health", HealthView.as_view(), name="health"),
    path("api/v1/", include("modules.identity.api.urls")),
    path("api/v1/", include("modules.access.api.urls")),
]

handler404 = "shared.api.errors.not_found"
handler500 = "shared.api.errors.server_error"
