from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Tuple
from news.models import NewsCategory


class TextSimilarityService:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self._update_category_vectors()

    def _update_category_vectors(self):
        """Update the TF-IDF vectors for all categories"""
        categories = NewsCategory.objects.all()
        category_texts = []
        self.categories = []

        for category in categories:
            # Combine name and description for better matching
            category_text = f"{category.name} {category.description}"
            category_texts.append(category_text)
            self.categories.append(category)

        if category_texts:
            self.category_vectors = self.vectorizer.fit_transform(category_texts)
        else:
            self.category_vectors = None

    def find_similar_category(
        self, title: str, content: str, threshold: float = 0.1
    ) -> Tuple[NewsCategory, float]:
        """
        Find the most similar category for a given title and content.
        Returns a tuple of (category, similarity_score).
        """
        default_category = NewsCategory.objects.first()
        if (
            self.category_vectors is None
            or self.category_vectors.shape[0] == 0
            or title is None
            or content is None
        ):
            return default_category, 0.0

        # Combine title and content for matching
        combined_text = f"{title} {content}"
        combined_vector = self.vectorizer.transform([combined_text])
        similarities = cosine_similarity(combined_vector, self.category_vectors)
        best_match_index = np.argmax(similarities)
        best_match_score = similarities[0, best_match_index]
        if best_match_score >= threshold:
            return self.categories[best_match_index], best_match_score

        # Return first category as fallback if no good match
        return default_category, 0.0
