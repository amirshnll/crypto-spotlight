import logging
import requests
import mimetypes
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from django.core.files.base import ContentFile
from news.models import NewsSource, NewsArticle, ArticleWordFilter
from news.services.text_similarity import TextSimilarityService
from crypto.models import Cryptocurrency

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetch news from RSS sources and filter content"

    def handle(self, *args, **options):
        try:
            self.fetch_and_process_news()
            self.stdout.write(
                self.style.SUCCESS("Successfully fetched and processed news")
            )
        except Exception as e:
            logger.error(f"Failed to fetch news: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Failed to fetch news: {str(e)}"))

    def fetch_and_process_news(self):
        """Fetch news from all active sources and process them"""
        active_sources = NewsSource.objects.filter(is_active=True)

        for source in active_sources:
            # Check if it's time to fetch again
            last_fetch = source.last_fetch
            if last_fetch is not None:
                time_since_last_fetch = (
                    timezone.now() - last_fetch
                ).total_seconds() / 60
                if time_since_last_fetch < source.fetch_frequency:
                    continue

            try:
                self.process_source_feed(source)
                source.last_fetch = timezone.now()
                source.save()
            except Exception as e:
                logger.error(f"Error processing source {source.name}: {str(e)}")
                continue

    def process_source_feed(self, source):
        """Process RSS feed for a single source using curl"""
        try:
            # Make HTTP request with timeout and custom User-Agent
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(source.feed_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse XML content
            root = ET.fromstring(response.content)

            # Handle different RSS namespaces
            namespaces = {
                "content": "http://purl.org/rss/1.0/modules/content/",
                "media": "http://search.yahoo.com/mrss/",
            }

            # Find channel items (entries)
            channel = root.find("channel")
            if channel is None:  # Handle RSS 1.0
                items = root.findall("item")
            else:  # Handle RSS 2.0
                items = channel.findall("item")

            for item in items:
                try:
                    # Extract entry data
                    title = (
                        item.find("title").text
                        if item.find("title") is not None
                        else ""
                    )
                    link = (
                        item.find("link").text if item.find("link") is not None else ""
                    )
                    description = (
                        item.find("description").text
                        if item.find("description") is not None
                        else ""
                    )

                    # Skip if article with this URL already exists
                    if NewsArticle.objects.filter(source_url=link).exists():
                        continue

                    # Extract image URL from RSS feed
                    image_url = None

                    # Try media:content tag
                    media_content = item.find("media:content", namespaces)
                    if media_content is not None and "url" in media_content.attrib:
                        image_url = media_content.attrib["url"]

                    # Try media:thumbnail tag
                    if not image_url:
                        media_thumbnail = item.find("media:thumbnail", namespaces)
                        if (
                            media_thumbnail is not None
                            and "url" in media_thumbnail.attrib
                        ):
                            image_url = media_thumbnail.attrib["url"]

                    # Try enclosure tag
                    if not image_url:
                        enclosure = item.find("enclosure")
                        if enclosure is not None and "url" in enclosure.attrib:
                            mime_type = enclosure.attrib.get("type", "")
                            if mime_type.startswith("image/"):
                                image_url = enclosure.attrib["url"]

                    # Create article
                    # Clean content
                    clean_content = (
                        self.strip_html_tags(description) if description else ""
                    )

                    # Find most similar category using text similarity
                    (
                        best_category,
                        similarity_score,
                    ) = TextSimilarityService().find_similar_category(
                        title=title[:255], content=clean_content
                    )

                    article = NewsArticle(
                        title=title[:255],
                        content=clean_content,
                        source=source,
                        source_url=link,
                        category=best_category,
                    )

                    # Download and save image if available
                    if image_url:
                        try:
                            image_response = requests.get(
                                image_url, headers=headers, timeout=10
                            )
                            image_response.raise_for_status()

                            # Check if content type is an image
                            content_type = image_response.headers.get(
                                "content-type", ""
                            )
                            if content_type.startswith("image/"):
                                # Get file extension from content type
                                ext = mimetypes.guess_extension(content_type) or ".jpg"
                                filename = f"{slugify(timezone.now().strftime('%Y%m%d-%H%M%S'))}{ext}"

                                # Save image to featured_image field
                                article.featured_image.save(
                                    filename,
                                    ContentFile(image_response.content),
                                    save=False,
                                )
                        except Exception as e:
                            logger.error(
                                f"Error downloading image from {image_url}: {str(e)}"
                            )

                    # Check content using Naive Bayes
                    should_publish = self.check_content(article.content)
                    article.is_published = should_publish

                    # Set published date if available
                    pub_date = item.find("pubDate")
                    if pub_date is not None and pub_date.text:
                        try:
                            from email.utils import parsedate_to_datetime

                            article.published_at = parsedate_to_datetime(pub_date.text)
                        except Exception:
                            article.published_at = timezone.now()
                    else:
                        article.published_at = timezone.now()

                    article.save()

                    article.related_cryptocurrencies.set(
                        self.extract_cryptocurrency_mentions(article.content)
                    )

                except Exception as e:
                    logger.error(
                        f"Error processing entry {title if title else 'Unknown'}: {str(e)}"
                    )
                    continue

        except requests.RequestException as e:
            logger.error(f"HTTP request failed for {source.feed_url}: {str(e)}")
            raise
        except ET.ParseError as e:
            logger.error(f"XML parsing failed for {source.feed_url}: {str(e)}")
            raise

    def check_content(self, content):
        """Check content using Naive Bayes algorithm"""
        try:
            # Get all active word filters
            word_filters = ArticleWordFilter.objects.filter(is_active=True)

            if not word_filters.exists():
                return True

            # Tokenize content (simple space-based tokenization)
            words = content.lower().split()

            # Calculate probability
            content_probability = 1.0
            for word in words:
                word_filter = word_filters.filter(word=word).first()
                if word_filter:
                    # Use word's probability
                    content_probability *= word_filter.probability or 0.5
                else:
                    # Use neutral probability for unknown words
                    content_probability *= 0.8

            # Threshold for publishing (can be adjusted)
            return content_probability >= 0.1

        except Exception as e:
            logger.error(f"Error in content checking: {str(e)}")
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

    def extract_cryptocurrency_mentions(self, content):
        """Extract cryptocurrencies mentioned in the content"""

        related_cryptocurrencies = []

        Cryptocurrencies = Cryptocurrency.objects.all()

        for Cryptocurrencies in Cryptocurrencies:
            if Cryptocurrencies.name.lower() in content.lower():
                related_cryptocurrencies.append(Cryptocurrencies)

        return related_cryptocurrencies
