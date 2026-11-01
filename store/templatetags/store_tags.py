from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='svg_placeholder')
def svg_placeholder(product):
    """Render dynamic clinical SVG placeholder for a product."""
    if hasattr(product, 'get_svg_placeholder'):
        return mark_safe(product.get_svg_placeholder())
    return mark_safe('<div class="p-8 text-center text-4xl">🧴</div>')

@register.filter(name='cloudinary_thumb')
def cloudinary_thumb(product, size="200x200"):
    """Get optimized thumbnail from Cloudinary."""
    try:
        w, h = [int(x) for x in size.split('x')]
    except Exception:
        w, h = 200, 200
    if hasattr(product, 'get_optimized_cloudinary_url'):
        url = product.get_optimized_cloudinary_url(width=w, height=h)
        if url:
            return url
    if hasattr(product, 'get_image_url'):
        return product.get_image_url() or ''
    return ''

@register.filter(name='discounted_price')
def discounted_price(product, currency='yer'):
    """Calculate discounted price for a given currency."""
    if hasattr(product, 'get_discounted_price'):
        return product.get_discounted_price(currency)
    return 0

@register.filter(name='bundle_total_price')
def bundle_total_price(bundle, currency='yer'):
    """Calculate bundle total price for a given currency."""
    if hasattr(bundle, 'get_total_price'):
        return bundle.get_total_price(currency)
    return 0
