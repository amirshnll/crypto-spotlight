from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap, index as sitemap_index
from django.views.generic.base import TemplateView
from . import views
from .sitemap import get_post_sitemaps

# Get dynamically generated sitemaps based on post count
sitemaps = get_post_sitemaps()

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("", views.home, name="home"),
        path("whitepaper/", views.whitepaper, name="whitepaper"),
        path("about/", views.about, name="about"),
        path("contact/", views.contact, name="contact"),
        path("faq/", views.faq, name="faq"),
        path("live/", views.live, name="live"),
        path("donate/", views.donate, name="donate"),

        path("rss/", views.rss_feed, name="rss_feed"),

        path("post/<slug:slug>/", views.post_detail, name="post_detail"),
        path("category/<slug:slug>/", views.category_posts, name="category_posts"),
        path("crypto/<slug:slug>/", views.crypto_posts, name="crypto_posts"),

        path("post/like/<slug:slug>/", views.like_post, name="like_post"),
        path("post/dislike/<slug:slug>/", views.dislike_post, name="dislike_post"),
        path("submit_contact/", views.submit_contact, name="submit_contact"),
        path("submit_comment/<slug:slug>/", views.submit_comment, name="submit_comment"),

        path("short/", views.short_url, name="short_url"),

        path(
            "sitemaps.xml",
            sitemap_index,
            {"sitemaps": sitemaps},
            name="django.contrib.sitemaps.views.index",
        ),
        path(
            "sitemap-<section>.xml",
            sitemap,
            {"sitemaps": sitemaps},
            name="django.contrib.sitemaps.views.sitemap",
        ),
        path(
            "robots.txt",
            TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
            name="robots_txt",
        ),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
