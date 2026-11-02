from django.conf import settings

def cart_context(request):
    """Make cart data available in all templates."""
    cart = request.session.get('cart', {})
    cart_count = sum(item['quantity'] for item in cart.values())
    cart_items_list = []
    for product_id, item in cart.items():
        cart_items_list.append({
            'product_id': product_id,
            'name': item.get('name', ''),
            'brand': item.get('brand', ''),
            'price': item.get('price', 0),
            'currency': item.get('currency', 'yer'),
            'quantity': item.get('quantity', 1),
            'image_url': item.get('image_url', ''),
            'package_color': item.get('package_color', '#5c8a6e'),
            'routine_step': item.get('routine_step', 3),
            'use_time': item.get('use_time', 'both'),
            'requires_sunscreen': item.get('requires_sunscreen', False),
            'subtotal': float(item.get('price', 0)) * item.get('quantity', 1),
        })
    # Sort by routine step
    cart_items_list.sort(key=lambda x: x['routine_step'])
    cart_total = sum(item['subtotal'] for item in cart_items_list)
    wishlist = request.session.get('wishlist', [])
    return {
        'cart_count': cart_count,
        'cart_items_list': cart_items_list,
        'cart_total': cart_total,
        'wishlist_count': len(wishlist),
        'wishlist_ids': wishlist,
    }


def site_settings(request):
    """Make site-wide settings available in all templates."""
    currency = request.session.get('currency', 'yer')
    theme = request.session.get('theme', 'sage')
    currency_symbols = {'yer': 'ر.ي', 'sar': 'ر.س', 'usd': '$'}
    wa_num = getattr(settings, 'WHATSAPP_NUMBER', '967778550938')
    return {
        'site_name': 'ريمشي',
        'site_tagline': 'علم البشرة بثقة صيدلانية',
        'whatsapp_number': wa_num,
        'whatsapp_display': '778550938',
        'current_currency': currency,
        'current_currency_symbol': currency_symbols.get(currency, 'ر.ي'),
        'current_theme': theme,
        'THEMES': [
            {'id': 'sage', 'label': 'المختبر السويسري', 'color': '#5c8a6e'},
            {'id': 'rose', 'label': 'المخمل الذهبي', 'color': '#c9748a'},
            {'id': 'blue', 'label': 'المياه الحرارية', 'color': '#2563eb'},
            {'id': 'terracotta', 'label': 'الكهرمان الدافئ', 'color': '#c2845a'},
            {'id': 'dark', 'label': 'الأوبسيديان الليلي', 'color': '#1e293b'},
        ],
    }

