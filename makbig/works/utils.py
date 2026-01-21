from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def compress_image(image):
    img=Image.open(image)
    img=img.convert('RGB')

    buffer=BytesIO()
    img.save(buffer,format='JPEG', quality=60, optimize=True)

    return ContentFile(buffer.getvalue(),image.name)