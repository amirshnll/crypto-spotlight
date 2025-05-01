from django.utils.text import slugify
from unidecode import unidecode


def generate_unique_slug(instance, value, slug_field_name="slug"):
    """
    Generate a unique slug for a model instance, supporting non-Latin characters.

    Parameters:
    - instance: The model instance.
    - value: The value to generate the slug from (e.g., name, title).
    - slug_field_name: The name of the slug field on the model (default is 'slug').

    Returns:
    - A unique slug as a string.
    """
    transliterated_value = unidecode(value)
    slug = slugify(transliterated_value)
    unique_slug = slug
    num = 1
    model_class = instance.__class__

    while model_class.objects.filter(**{slug_field_name: unique_slug}).exists():
        unique_slug = f"{slug}-{num}"
        num += 1

    return unique_slug
