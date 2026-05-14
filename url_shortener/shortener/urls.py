from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from links.views import LinkViewSet

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("links.urls")),
    path(
        "s/<str:short_code>",
        LinkViewSet.as_view({"get": "redirect_to_original"}),
        name="redirect_no_slash",
    ),
    path(
        "s/<str:short_code>/",
        LinkViewSet.as_view({"get": "redirect_to_original"}),
        name="redirect",
    ),
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
]
