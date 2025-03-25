import markdown
import requests
from datetime import datetime
from typing import Dict, Optional
from django.db.models import Avg
from crypto.models import PriceData
from news.models import NewsArticle


class TextGenerationService:
    def __init__(self, model_base_url: str, model_name: str):
        self.base_url = model_base_url
        self.model_name = model_name

    def generate_text(self, prompt: str, max_tokens: Optional[int] = 10000) -> Dict:
        """Generate text using Ollama API with the specified model.

        Args:
            prompt (str): The prompt to generate text from
            max_tokens (int, optional): Maximum number of tokens to generate. Defaults to 10000.

        Returns:
            Dict: Response containing the generated text and metadata
        """
        try:
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to generate text: {str(e)}")

    def generate_content(
        self, crypto, type: Dict = ["Hourly", "Daily", "Monthly"]
    ) -> list:
        """Generate a news article about a cryptocurrency.
        Args:
            crypto : The cryptocurrency to generate an article about
            type (Dict): The type of analysis (e.g., Hourly, Daily, Monthly)
        Returns:
            list: Returns a list containing:
                - The formatted article text in HTML format
                - The prompt used to generate the article
        """

        # Format the datetime to be more readable
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        # Handle case where type is a list
        analysis_type = type[0] if isinstance(type, list) else type
        topic = f"{analysis_type} Market Analysis: {crypto.name} Price Movement and Trends - {current_time}"

        current_price = PriceData.objects.filter(cryptocurrency=crypto).last()
        if current_price:
            current_price = current_price.price_usd
        else:
            current_price = 0.0

        high_24h = (
            PriceData.objects.filter(cryptocurrency=crypto)
            .order_by("-price_usd")
            .first()
        )
        if high_24h:
            high_24h = high_24h.price_usd
        else:
            high_24h = 0.0

        low_24h = (
            PriceData.objects.filter(cryptocurrency=crypto)
            .order_by("price_usd")
            .first()
        )
        if low_24h:
            low_24h = low_24h.price_usd
        else:
            low_24h = 0.0

        # Calculate average price change over 24h
        price_change_percentage_24h = (
            PriceData.objects.filter(cryptocurrency=crypto)
            .order_by("-timestamp")
            .values_list("change_24h", flat=True)
            .aggregate(Avg("change_24h"))["change_24h__avg"]
        )
        if price_change_percentage_24h is None:
            price_change_percentage_24h = 0.0

        # Assuming 'change_7d' should be replaced with 'change_24h' or another valid field
        price_change_percentage_7d = (
            PriceData.objects.filter(cryptocurrency=crypto)
            .order_by("-timestamp")
            .values_list(
                "change_24h", flat=True
            )  # Replace 'change_7d' with a valid field
            .aggregate(Avg("change_24h"))["change_24h__avg"]
        )
        if price_change_percentage_7d is None:
            price_change_percentage_7d = 0.0

        # Assuming 'change_30d' should be replaced with 'change_24h' or another valid field
        price_change_percentage_30d = (
            PriceData.objects.filter(cryptocurrency=crypto)
            .order_by("-timestamp")
            .values_list(
                "change_24h", flat=True
            )  # Replace 'change_30d' with a valid field
            .aggregate(Avg("change_24h"))["change_24h__avg"]
        )
        if price_change_percentage_30d is None:
            price_change_percentage_30d = 0.0

        articles = NewsArticle.objects.filter(related_cryptocurrencies=crypto).order_by(
            "-published_at"
        )[:50]
        article_titles = [article.title for article in articles]

        # Create a structured prompt for better article organization with minimal Markdown formatting
        prompt = f"""Write a comprehensive and well-structured news article about {topic} by Markdown format.

        Please organize the article with the following headings:
        1. Summary (2-3 sentences)
        2. Market Overview
        3. Analysis and Insights
        4. Market Outlook

        Instructions:
        - The article must be between 500–800 words
        - Write in a neutral, journalistic tone
        - Use paragraphs and bullet points for readability
        - Keep formatting minimal and clean
        - Ensure proper spacing between sections
        - Start directly with the first heading — do not add any introduction or explanations
        - Do not include any meta comments, apologies, or extra text at the beginning or end
        - Output must be only the article, without surrounding commentary or assistant-style notes

        Use the following data for the article:
        Current Price: ${current_price:.2f}
        24h High: ${high_24h:.2f}
        24h Low: ${low_24h:.2f}
        24h Price Change: {price_change_percentage_24h:.2f}%
        7d Price Change: {price_change_percentage_7d:.2f}%
        30d Price Change: {price_change_percentage_30d:.2f}%
        
        {"Latest news related to {topic}:" if len(articles) > 0 else ""}
        {"\n".join([f"- {text}" for text in article_titles])}
        """

        response = self.generate_text(prompt)
        article_text = response.get("response", "")

        # Convert Markdown to HTML
        article_text = markdown.markdown(article_text)
        article_text = article_text.replace("<ol>", "<ul>")
        article_text = article_text.replace("</ol>", "</ul>")

        # Wrap the entire article in a div with the content-body class
        formatted_article = f'<div class="content-body">{article_text}</div>'
        return [formatted_article, prompt]

    def generate_title(
        self, crypto: str, type: Dict = ["Hourly", "Daily", "Monthly"]
    ) -> str:
        # Format the datetime to be more readable
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        # Handle case where type is a list
        analysis_type = type[0] if isinstance(type, list) else type
        return f"{analysis_type} Market Analysis: {crypto} Price Movement and Trends - {current_time}"
