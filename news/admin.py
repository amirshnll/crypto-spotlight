from django.contrib import admin
from .models import NewsCategory, NewsSource, NewsArticle, ArticleWordFilter


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")
    list_filter = ("created_at",)


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "website_url", "is_active", "last_fetch")
    list_filter = ("is_active", "categories", "created_at")
    search_fields = ("name", "website_url")
    filter_horizontal = ("categories",)


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "source",
        "is_featured",
        "is_published",
        "published_at",
        "views_count",
    )
    list_filter = ("is_featured", "is_published", "category", "source", "published_at")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("related_cryptocurrencies",)
    readonly_fields = ("views_count", "created_at", "updated_at")
    date_hierarchy = "published_at"


@admin.register(ArticleWordFilter)
class ArticleWordFilterAdmin(admin.ModelAdmin):
    list_display = ("word", "probability", "is_active")
    list_filter = ("is_active", "created_at")
    search_fields = ("word",)
    readonly_fields = ("probability",)
