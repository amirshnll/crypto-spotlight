from django.db import models
from django.utils import timezone
from crypto.models import Cryptocurrency
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from crypto_spotlight.slugify import generate_unique_slug


class NewsCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=500)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "News Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)


class NewsSource(models.Model):
    name = models.CharField(max_length=100)
    website_url = models.URLField()
    feed_url = models.URLField()
    is_active = models.BooleanField(default=True)
    last_fetch = models.DateTimeField(null=True, blank=True)
    fetch_frequency = models.IntegerField(
        default=60, help_text="Fetch frequency in minutes"
    )
    categories = models.ManyToManyField(NewsCategory, related_name="sources")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        validator = URLValidator()
        try:
            validator(self.website_url)
            validator(self.feed_url)
        except ValidationError:
            raise ValidationError("Please enter valid URLs")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "News Sources"
        ordering = ["name"]


class NewsArticle(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=500)
    content = models.TextField()
    category = models.ForeignKey(NewsCategory, on_delete=models.CASCADE)
    related_cryptocurrencies = models.ManyToManyField(Cryptocurrency)
    source = models.ForeignKey(
        NewsSource, on_delete=models.SET_NULL, null=True, blank=True
    )
    source_url = models.URLField(blank=True)
    views_count = models.IntegerField(default=0)
    featured_image = models.ImageField(upload_to="news/", blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)

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


class ArticleWordFilter(models.Model):
    word = models.CharField(max_length=255, unique=True)
    probability = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.word
