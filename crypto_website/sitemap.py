import sys
from math import ceil
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings

from posts.models import Post, PostCategory
from crypto.models import Cryptocurrency


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return ["home", "whitepaper", "live", "about", "contact", "faq"]

    def location(self, item):
        return reverse(item)


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    limit = settings.SITEMAP_LIMIT

    def items(self):
        return Post.objects.filter(is_published=True).order_by("-published_at")

    def lastmod(self, obj):
        return obj.updated_at or obj.published_at

    def location(self, obj):
        return f"/post/{obj.slug}/"


class DynamicPostSitemap(PostSitemap):
    def __init__(self, page):
        self.page = page
        super().__init__()

    def items(self):
        start_index = (self.page - 1) * self.limit
        end_index = self.page * self.limit
        return super().items()[start_index:end_index]


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return PostCategory.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f"/category/{obj.slug}/"


class CryptoSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.6

    def items(self):
        return Cryptocurrency.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f"/crypto/{obj.slug}/"


def get_post_sitemaps():
    """Dynamically generate sitemap classes based on the number of posts"""
    if not ("runserver" in sys.argv or "runserver_plus" in sys.argv):
        return {}

    posts_count = Post.objects.filter(is_published=True).count()
    num_pages = ceil(posts_count / PostSitemap.limit)

    sitemaps = {}
    # Always include page sitemap
    sitemaps["pages"] = StaticViewSitemap
    sitemaps["categories"] = CategorySitemap
    sitemaps["cryptocurrencies"] = CryptoSitemap

    # Dynamically add post sitemaps based on the number of posts
    for page in range(1, num_pages + 1):
        sitemaps[f"posts-{page}"] = DynamicPostSitemap(page)

    return sitemaps
