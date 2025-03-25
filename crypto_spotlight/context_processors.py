from django.conf import settings


def website_name(requests):
    return {
        "WEBSITE_NAME": getattr(settings, "WEBSITE_NAME", ""),
    }


def website_domain(requests):
    return {
        "WEBSITE_DOMAIN": getattr(settings, "WEBSITE_DOMAIN", ""),
    }


def website_twitter(requests):
    return {
        "WEBSITE_TWITTER": getattr(settings, "WEBSITE_TWITTER", "https://x.com/"),
    }


def website_linkedin(requests):
    return {
        "WEBSITE_LINKEDIN": getattr(
            settings, "WEBSITE_LINKEDIN", "https://linkedin.com"
        ),
    }


def model_name(requests):
    return {
        "MODEL_NAME": getattr(settings, "MODEL_NAME", ""),
    }
