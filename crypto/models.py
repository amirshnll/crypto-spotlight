from django.db import models
from django.utils import timezone
from crypto_spotlight.slugify import generate_unique_slug


class Cryptocurrency(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=500)
    symbol = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    whitepaper = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    market_cap = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    volume_24h = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    price_change_24h = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    icon = models.ImageField(upload_to="icons/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Cryptocurrencies"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.symbol})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)


class PriceData(models.Model):
    cryptocurrency = models.ForeignKey(
        Cryptocurrency, on_delete=models.CASCADE, related_name="price_data"
    )
    price_usd = models.DecimalField(max_digits=20, decimal_places=8)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2)
    volume_24h = models.DecimalField(max_digits=20, decimal_places=2)
    change_24h = models.DecimalField(max_digits=7, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-timestamp"]
        get_latest_by = "timestamp"

    def __str__(self):
        return f"{self.cryptocurrency.symbol} - ${self.price_usd} at {self.timestamp}"
