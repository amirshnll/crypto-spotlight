import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from posts.models import Post, PostWordFilter
from crypto.models import Cryptocurrency
from posts.services.text_similarity import TextSimilarityService
from posts.services.text_generation import TextGenerationService
from django.conf import settings
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate posts with cryptocurrency content and icons"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            type=str,
            default="Daily",
            choices=["Hourly", "Daily", "Monthly"],
            help="Frequency type of post generation",
        )

    def handle(self, *args, **options):
        try:
            success_count = self.generate_posts(options)
            self.stdout.write(
                self.style.SUCCESS(f"Successfully generated {success_count} posts")
            )
        except Exception as e:
            logger.error(f"Failed to generate posts: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Failed to generate posts: {str(e)}"))

    def generate_posts(self, options):
        # Get all available cryptocurrencies
        cryptocurrencies = Cryptocurrency.objects.all()
        if not cryptocurrencies:
            self.stdout.write(self.style.WARNING("No cryptocurrencies found"))
            return 0

        # Fetch cryptocurrency data
        call_command("fetch_crypto_data")

        success_count = 0
        # Process all cryptocurrencies
        for crypto in cryptocurrencies:
            try:
                # Generate content using TextGenerationService
                model_name = settings.MODEL_NAME
                model_base_url = settings.MODEL_BASE_URL

                if not model_base_url or not model_name:
                    raise ValueError("Model base URL or model name is not set")

                text_gen_service = TextGenerationService(
                    model_base_url=model_base_url,
                    model_name=model_name,
                )
                title = text_gen_service.generate_title(
                    crypto=crypto.name, type=options["type"]
                )
                content, promp = text_gen_service.generate_content(
                    crypto=crypto, type=options["type"]
                )

                # Find most similar category using text similarity
                text_similarity_service = TextSimilarityService()
                best_category, _ = text_similarity_service.find_similar_category(
                    title=title[:255], content=self.strip_html_tags(content)
                )

                # Create post
                post = Post(
                    title=title[:255],
                    content=content,
                    promp=promp,
                    category=best_category,
                    published_at=timezone.now(),
                    type=options["type"],
                    model=model_name,
                )

                # Set featured image from cryptocurrency icon
                if crypto.icon:
                    post.featured_image = crypto.icon

                # Check content using word filters
                should_publish = self.check_content(content)
                post.is_published = should_publish

                post.save()

                post.related_cryptocurrencies.set([crypto])

                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Generated post for {crypto.name}")
                )

            except Exception as e:
                logger.error(f"Error generating post for {crypto.name}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to generate post for {crypto.name}: {str(e)}"
                    )
                )

        return success_count

    def check_content(self, content):
        """Check if content satisfies word filters"""
        try:
            # Get all word filters
            word_filters = PostWordFilter.objects.all()

            # If no filters exist, default to publishing
            if not word_filters:
                return True

            content_lower = content.lower()

            # Check against each filter
            for word_filter in word_filters:
                if word_filter.word.lower() in content_lower:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking content filters: {str(e)}")
            return False

    def strip_html_tags(self, text):
        """Remove HTML tags from text while preserving content"""
        from html import unescape

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(text, "html.parser")

        # Get text content
        clean_text = soup.get_text(separator=" ")

        # Decode HTML entities
        clean_text = unescape(clean_text)

        # Remove extra whitespace
        clean_text = " ".join(clean_text.split())

        return clean_text
