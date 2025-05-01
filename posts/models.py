from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from crypto.models import Cryptocurrency
from crypto_website.slugify import generate_unique_slug


class PostCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=500)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Post Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=500)
    content = models.TextField()
    promp = models.TextField(blank=True, null=True)
    category = models.ForeignKey(PostCategory, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    related_cryptocurrencies = models.ManyToManyField(Cryptocurrency)
    model = models.CharField(max_length=255)
    type = models.CharField(
        max_length=10,
        choices=[("Hourly", "Hourly"), ("Daily", "Daily"), ("Monthly", "Monthly")],
        default="Daily",
    )
    views_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)
    featured_image = models.ImageField(upload_to="posts/", blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    qr_code_url = models.CharField(max_length=255, blank=True, null=True)

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.title)

        if self.is_published and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

        # Generate QR code URL after saving
        from django.urls import reverse
        from django.conf import settings
        from .utils import generate_qr_code

        if not self.qr_code_url:
            protocol = "https" if settings.SECURE_SSL_REDIRECT else "http"
            domain = (
                settings.ALLOWED_HOSTS[0]
                if settings.ALLOWED_HOSTS
                else "localhost:8000"
            )
            url = f'{protocol}://{domain}{reverse("post_detail", args=[self.slug])}'
            self.qr_code_url = generate_qr_code(url, self.title)
            if self.qr_code_url:  # Only update if QR code was generated successfully
                Post.objects.filter(pk=self.pk).update(qr_code_url=self.qr_code_url)


class PostWordFilter(models.Model):
    word = models.CharField(max_length=255, unique=True)
    probability = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.word


class PostInteractionLog(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    interaction_type = models.CharField(
        max_length=10, choices=[("like", "Like"), ("dislike", "Dislike")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["post", "ip_address", "interaction_type"]
        indexes = [
            models.Index(fields=["ip_address", "interaction_type", "created_at"])
        ]

    def __str__(self):
        return f"{self.ip_address} - {self.interaction_type} - {self.post.title}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} - {self.post.title}"
