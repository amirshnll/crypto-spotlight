import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.text import slugify


def generate_qr_code(url, title):
    """Generate a QR code image for a given URL and save it to media storage.

    Args:
        url (str): The URL to encode in the QR code
        title (str): The title to use for the image filename

    Returns:
        str: The URL of the generated QR code image
    """
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Add data
        qr.add_data(url)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save image to BytesIO
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        # Generate filename
        filename = f"qr/{slugify(title)}.png"

        # Save to storage
        if not default_storage.exists(filename):
            default_storage.save(filename, ContentFile(buffer.getvalue()))

        # Return the URL
        return default_storage.url(filename)
    except Exception as e:
        print(f"Error generating QR code: {str(e)}")
        return None
