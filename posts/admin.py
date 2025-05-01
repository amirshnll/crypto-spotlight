from django.contrib import admin
from .models import PostCategory, Post, PostWordFilter, PostInteractionLog, Comment


@admin.register(PostCategory)
class PostCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")
    list_filter = ("is_active", "created_at")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "author",
        "is_featured",
        "is_published",
        "published_at",
        "views_count",
        "likes_count",
        "dislikes_count",
    )
    list_filter = ("is_featured", "is_published", "category", "author", "published_at")
    search_fields = ("title", "content", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("related_cryptocurrencies",)
    readonly_fields = readonly_fields = (
        "views_count",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "published_at"


@admin.register(PostWordFilter)
class PostWordFilterAdmin(admin.ModelAdmin):
    list_display = ("word", "probability", "is_active")
    list_filter = ("is_active", "created_at")
    search_fields = ("word",)
    readonly_fields = ("probability",)


@admin.register(PostInteractionLog)
class PostInteractionLogAdmin(admin.ModelAdmin):
    list_display = ("post", "ip_address", "interaction_type", "created_at")
    list_filter = ("interaction_type", "created_at")
    search_fields = ("ip_address", "post__title")
    date_hierarchy = "created_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "name", "email", "content", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("name", "email", "content", "post__title")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
