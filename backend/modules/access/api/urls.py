from django.urls import path

from modules.access.api.views import (
    ActivateUserView,
    DeactivateUserView,
    RoleCollectionView,
    UserCollectionView,
    UserDetailView,
    UserRoleView,
)

urlpatterns = [
    path("users", UserCollectionView.as_view(), name="users"),
    path("users/<uuid:user_id>", UserDetailView.as_view(), name="user-detail"),
    path("users/<uuid:user_id>/activate", ActivateUserView.as_view(), name="user-activate"),
    path("users/<uuid:user_id>/deactivate", DeactivateUserView.as_view(), name="user-deactivate"),
    path("users/<uuid:user_id>/roles", UserRoleView.as_view(), name="user-roles"),
    path("roles", RoleCollectionView.as_view(), name="roles"),
]
