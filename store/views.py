import json
import urllib.parse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count
from django.conf import settings
from django.template.loader import render_to_string
from .models import (
    Product, SkinType, SkinConcern, ActiveIngredient,
    IngredientConflict, IngredientSynergy, RoutineBundle, Order, OrderItem
)


# ─── Currency helpers ────────────────────────────────────────────────────────

CURRENCY_SYMBOLS = {'yer': 'ر.ي', 'sar': 'ر.س', 'usd': '$'}

def get_currency(request):
    return request.session.get('currency', 'yer')


# ─── 1. Home Page ────────────────────────────────────────────────────────────

def home(request):
    currency = get_currency(request)
    featured = Product.objects.filter(is_available=True, badge='featured')[:6]
    bestsellers = Product.objects.filter(is_available=True, badge='bestseller')[:6]
    new_arrivals = Product.objects.filter(is_available=True, badge='new')[:4]
    bundles = RoutineBundle.objects.filter(is_active=True).prefetch_related('products')[:3]
    skin_types = SkinType.objects.all()
    skin_concerns = SkinConcern.objects.all().order_by('display_order')
    steps = [
        (1, 'غسول منظف', '🧴', 'صباحي ومسائي'),
        (2, 'تونر وموازنة', '💦', 'صباحي ومسائي'),
        (3, 'سيروم وعلاج مركز', '💊', 'صباحي أو مسائي'),
        (4, 'مرطب ومجدد للحاجز', '🥛', 'صباحي ومسائي'),
        (5, 'واقي شمس', '☀️', 'صباحاً فقط'),
        (6, 'عناية خاصة / ماسك', '🎭', 'أسبوعياً'),
    ]
    context = {
        'featured_products': featured,
        'bestsellers': bestsellers,
        'new_arrivals': new_arrivals,
        'bundles': bundles,
        'skin_types': skin_types,
        'skin_concerns': skin_concerns,
        'steps': steps,
        'currency': currency,
        'page_title': 'ريمشي — علم البشرة بثقة صيدلانية',
    }
    return render(request, 'store/home.html', context)


# ─── 2. Products List + HTMX Filter ─────────────────────────────────────────

def products(request):
    currency = get_currency(request)
    all_products = Product.objects.filter(is_available=True).prefetch_related(
        'skin_types', 'skin_concerns', 'active_ingredients'
    )

    # Filters
    skin_type_slug = request.GET.get('skin_type', '')
    concern_slug = request.GET.get('concern', '')
    ingredient_slug = request.GET.get('ingredient', '')
    step = request.GET.get('step', '')
    use_time = request.GET.get('use_time', '')
    safe_pregnancy = request.GET.get('safe_pregnancy', '')
    fragrance_free = request.GET.get('fragrance_free', '')
    q = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'step')

    if skin_type_slug:
        all_products = all_products.filter(skin_types__slug=skin_type_slug)
    if concern_slug:
        all_products = all_products.filter(skin_concerns__slug=concern_slug)
    if ingredient_slug:
        all_products = all_products.filter(active_ingredients__slug=ingredient_slug)
    if step:
        all_products = all_products.filter(routine_step=step)
    if use_time:
        all_products = all_products.filter(use_time__in=[use_time, 'both'])
    if safe_pregnancy == '1':
        all_products = all_products.filter(safe_pregnancy=True)
    if fragrance_free == '1':
        all_products = all_products.filter(fragrance_free=True)
    if q:
        all_products = all_products.filter(
            Q(name__icontains=q) | Q(brand__icontains=q) |
            Q(short_description__icontains=q) |
            Q(active_ingredients__name_ar__icontains=q) |
            Q(active_ingredients__name_en__icontains=q)
        )

    if sort_by == 'price_asc':
        all_products = all_products.order_by('price_yer')
    elif sort_by == 'price_desc':
        all_products = all_products.order_by('-price_yer')
    elif sort_by == 'hydration':
        all_products = all_products.order_by('-hydration_level')
    else:
        all_products = all_products.order_by('routine_step', 'name')

    all_products = all_products.distinct()

    # HTMX partial response
    if request.headers.get('HX-Request'):
        html = render_to_string(
            'store/partials/product_grid.html',
            {'products': all_products, 'currency': currency},
            request=request
        )
        return HttpResponse(html)

    context = {
        'products': all_products,
        'skin_types': SkinType.objects.all(),
        'skin_concerns': SkinConcern.objects.all().order_by('display_order'),
        'active_ingredients': ActiveIngredient.objects.all().order_by('name_ar'),
        'currency': currency,
        'selected_skin_type': skin_type_slug,
        'selected_concern': concern_slug,
        'selected_step': step,
        'selected_use_time': use_time,
        'selected_safe_pregnancy': safe_pregnancy,
        'selected_fragrance_free': fragrance_free,
        'search_q': q,
        'sort_by': sort_by,
        'product_count': all_products.count(),
        'page_title': 'جميع المنتجات',
    }
    return render(request, 'store/products.html', context)


# ─── 3. Product Detail ───────────────────────────────────────────────────────

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    currency = get_currency(request)
    related = product.pairs_well_with.filter(is_available=True)[:4]
    same_brand = Product.objects.filter(brand=product.brand, is_available=True).exclude(pk=product.pk)[:4]

    # Ingredient conflict check with cart
    cart = request.session.get('cart', {})
    cart_ingredient_ids = []
    for item in cart.values():
        cart_ingredient_ids.extend(item.get('ingredient_ids', []))

    product_ingredient_ids = list(product.active_ingredients.values_list('id', flat=True))
    conflicts_in_cart = []
    synergies_in_cart = []

    if cart_ingredient_ids and product_ingredient_ids:
        for ing_id in product_ingredient_ids:
            for cart_ing_id in cart_ingredient_ids:
                try:
                    ing_a = ActiveIngredient.objects.get(id=ing_id)
                    ing_b = ActiveIngredient.objects.get(id=cart_ing_id)
                    conflict = ing_a.get_conflict_with(ing_b)
                    if conflict:
                        conflicts_in_cart.append(conflict)
                    synergy = ing_a.get_synergy_with(ing_b)
                    if synergy:
                        synergies_in_cart.append(synergy)
                except ActiveIngredient.DoesNotExist:
                    pass

    context = {
        'product': product,
        'currency': currency,
        'related_products': related,
        'same_brand_products': same_brand,
        'conflicts_in_cart': conflicts_in_cart[:3],
        'synergies_in_cart': synergies_in_cart[:3],
        'page_title': f'{product.name} — {product.brand}',
        'price': product.get_discounted_price(currency),
        'original_price': product.get_price(currency),
    }
    return render(request, 'store/product_detail.html', context)


# ─── 4. Cart Operations ──────────────────────────────────────────────────────

@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    currency = get_currency(request)
    cart = request.session.get('cart', {})
    key = str(product_id)
    ingredient_ids = list(product.active_ingredients.values_list('id', flat=True))

    if key in cart:
        cart[key]['quantity'] += 1
    else:
        cart[key] = {
            'product_id': product_id,
            'name': product.name,
            'brand': product.brand,
            'price': float(product.get_discounted_price(currency)),
            'currency': currency,
            'quantity': 1,
            'image_url': product.get_image_url() or '',
            'package_color': product.package_color,
            'routine_step': product.routine_step,
            'use_time': product.use_time,
            'requires_sunscreen': product.requires_sunscreen,
            'ingredient_ids': ingredient_ids,
            'slug': product.slug,
        }
    request.session['cart'] = cart
    request.session.modified = True

    # Smart cart analysis
    analysis = _analyze_cart(cart)

    if request.headers.get('HX-Request'):
        html = render_to_string('store/partials/cart_drawer.html', {
            'cart_items_list': _get_cart_list(cart),
            'cart_total': sum(i['subtotal'] for i in _get_cart_list(cart)),
            'cart_count': sum(i['quantity'] for i in cart.values()),
            'currency': currency,
            'cart_analysis': analysis,
        }, request=request)
        response = HttpResponse(html)
        response['HX-Trigger'] = json.dumps({
            'cartUpdated': {'count': sum(i['quantity'] for i in cart.values())},
            'showToast': {'message': f'تمت إضافة {product.name} للسلة ✅', 'type': 'success'}
        })
        return response

    return redirect('store:product_detail', slug=product.slug)


@require_POST
def cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    request.session.modified = True
    currency = get_currency(request)
    analysis = _analyze_cart(cart)

    if request.headers.get('HX-Request'):
        html = render_to_string('store/partials/cart_drawer.html', {
            'cart_items_list': _get_cart_list(cart),
            'cart_total': sum(i['subtotal'] for i in _get_cart_list(cart)),
            'cart_count': sum(i['quantity'] for i in cart.values()),
            'currency': currency,
            'cart_analysis': analysis,
        }, request=request)
        response = HttpResponse(html)
        response['HX-Trigger'] = json.dumps({
            'cartUpdated': {'count': sum(i['quantity'] for i in cart.values())},
        })
        return response
    return redirect('store:cart')


def cart_view(request):
    cart = request.session.get('cart', {})
    currency = get_currency(request)
    cart_list = _get_cart_list(cart)
    analysis = _analyze_cart(cart)
    return render(request, 'store/cart.html', {
        'cart_items_list': cart_list,
        'cart_total': sum(i['subtotal'] for i in cart_list),
        'currency': currency,
        'cart_analysis': analysis,
        'page_title': 'سلة المشتريات الذكية',
    })


def _get_cart_list(cart):
    items = []
    for product_id, item in cart.items():
        items.append({**item, 'subtotal': float(item['price']) * item['quantity']})
    items.sort(key=lambda x: x.get('routine_step', 99))
    return items


def _analyze_cart(cart):
    """Smart cart analysis: conflicts, missing sunscreen, gift bar."""
    analysis = {'conflicts': [], 'missing_sunscreen': False, 'gift_threshold': 0}
    if not cart:
        return analysis

    # Check for missing sunscreen
    has_exfoliant = False
    has_sunscreen = False
    total_qty = sum(i['quantity'] for i in cart.values())

    for item in cart.values():
        if item.get('requires_sunscreen'):
            has_exfoliant = True
        if item.get('routine_step') == 5:
            has_sunscreen = True

    if has_exfoliant and not has_sunscreen:
        analysis['missing_sunscreen'] = True

    # Check ingredient conflicts
    items_list = list(cart.values())
    ingredient_id_map = {}
    for item in items_list:
        for ing_id in item.get('ingredient_ids', []):
            ingredient_id_map.setdefault(ing_id, []).append(item['name'])

    checked_pairs = set()
    for i, item_a in enumerate(items_list):
        for item_b in items_list[i+1:]:
            for ing_a_id in item_a.get('ingredient_ids', []):
                for ing_b_id in item_b.get('ingredient_ids', []):
                    pair = tuple(sorted([ing_a_id, ing_b_id]))
                    if pair in checked_pairs:
                        continue
                    checked_pairs.add(pair)
                    try:
                        ing_a = ActiveIngredient.objects.get(id=ing_a_id)
                        conflict = IngredientConflict.objects.filter(
                            Q(ingredient_a_id=ing_a_id, ingredient_b_id=ing_b_id) |
                            Q(ingredient_a_id=ing_b_id, ingredient_b_id=ing_a_id)
                        ).first()
                        if conflict:
                            analysis['conflicts'].append({
                                'product_a': item_a['name'],
                                'product_b': item_b['name'],
                                'reason': conflict.reason[:120],
                                'safe_usage': conflict.safe_usage[:150],
                            })
                    except ActiveIngredient.DoesNotExist:
                        pass

    # Gift bar (gamification)
    if total_qty >= 4:
        analysis['gift_threshold'] = 100
    else:
        analysis['gift_threshold'] = int((total_qty / 4) * 100)

    return analysis


# ─── 5. Currency Switcher ────────────────────────────────────────────────────

@require_POST
def set_currency(request):
    currency = request.POST.get('currency', 'yer')
    if currency not in ['yer', 'sar', 'usd']:
        currency = 'yer'
    request.session['currency'] = currency
    request.session.modified = True
    if request.headers.get('HX-Request'):
        response = HttpResponse('')
        response['HX-Refresh'] = 'true'
        return response
    return redirect(request.META.get('HTTP_REFERER', '/'))


# ─── 6. Theme Switcher ───────────────────────────────────────────────────────

@require_POST
def set_theme(request):
    theme = request.POST.get('theme', 'sage')
    if theme not in ['sage', 'rose', 'blue', 'terracotta', 'dark']:
        theme = 'sage'
    request.session['theme'] = theme
    request.session.modified = True
    response = HttpResponse('')
    response['HX-Trigger'] = json.dumps({'themeChanged': theme})
    return response


# ─── 7. Facial Zone Mapper ───────────────────────────────────────────────────

def face_mapper(request):
    zone = request.GET.get('zone', '')
    concern_slug = request.GET.get('concern', '')
    currency = get_currency(request)

    zone_concerns = SkinConcern.objects.all()
    if zone:
        zone_concerns = zone_concerns.filter(face_zone=zone)

    products_qs = Product.objects.filter(is_available=True)
    if concern_slug:
        products_qs = products_qs.filter(skin_concerns__slug=concern_slug)
    elif zone:
        products_qs = products_qs.filter(skin_concerns__face_zone=zone)
    products_qs = products_qs.distinct()[:12]

    if request.headers.get('HX-Request'):
        html = render_to_string('store/partials/face_mapper_results.html', {
            'zone': zone,
            'zone_concerns': zone_concerns,
            'products': products_qs,
            'currency': currency,
        }, request=request)
        return HttpResponse(html)

    return render(request, 'store/face_mapper.html', {
        'zone_concerns': zone_concerns,
        'skin_concerns': SkinConcern.objects.all().order_by('display_order'),
        'products': products_qs,
        'currency': currency,
        'page_title': 'خريطة الوجه التفاعلية',
    })


# ─── 8. Skin Consultant (5-Step Quiz) ────────────────────────────────────────

def skin_consultant(request):
    step = int(request.GET.get('step', 1))
    skin_types = SkinType.objects.all()
    concerns = SkinConcern.objects.all().order_by('display_order')
    context = {
        'step': step,
        'skin_types': skin_types,
        'concerns': concerns,
        'page_title': 'المستشار الصيدلاني التفاعلي',
    }
    return render(request, 'store/consultant.html', context)


def consultant_result(request):
    """Generate personalized prescription based on quiz answers."""
    currency = get_currency(request)
    skin_type_slug = request.GET.get('skin_type', '')
    primary_concern = request.GET.get('primary_concern', '')
    secondary_concern = request.GET.get('secondary_concern', '')
    sensitivity = request.GET.get('sensitivity', 'medium')
    safe_pregnancy = request.GET.get('safe_pregnancy', '0') == '1'

    products_qs = Product.objects.filter(is_available=True)

    if skin_type_slug:
        products_qs = products_qs.filter(skin_types__slug=skin_type_slug)
    if primary_concern:
        products_qs = products_qs.filter(skin_concerns__slug=primary_concern)
    if safe_pregnancy:
        products_qs = products_qs.filter(safe_pregnancy=True)
    if sensitivity == 'high':
        products_qs = products_qs.filter(sensitivity_safety__gte=75)

    products_qs = products_qs.distinct().order_by('routine_step')

    # Build prescription: one product per routine step
    prescription = {}
    for p in products_qs:
        step = p.routine_step
        if step not in prescription:
            prescription[step] = p

    prescription_list = [prescription[k] for k in sorted(prescription.keys())]

    if request.headers.get('HX-Request'):
        html = render_to_string('store/partials/prescription.html', {
            'prescription': prescription_list,
            'currency': currency,
            'skin_type_slug': skin_type_slug,
            'primary_concern': primary_concern,
        }, request=request)
        return HttpResponse(html)

    return render(request, 'store/prescription.html', {
        'prescription': prescription_list,
        'currency': currency,
        'page_title': 'وصفتك الطبية الرقمية',
    })


# ─── 9. Skin Cycling Generator ───────────────────────────────────────────────

def skin_cycling(request):
    currency = get_currency(request)
    cart = request.session.get('cart', {})
    cart_list = _get_cart_list(cart)

    # Categorize products in cart
    exfoliants = [i for i in cart_list if i.get('routine_step') == 3 and any(
        kw in i.get('name', '').lower() for kw in ['acid', 'aha', 'bha', 'glycolic', 'salicyl', 'exfol']
    )]
    retinoids = [i for i in cart_list if any(
        kw in i.get('name', '').lower() for kw in ['retinol', 'retin', 'retinal']
    )]
    moisturizers = [i for i in cart_list if i.get('routine_step') == 4]
    cleansers = [i for i in cart_list if i.get('routine_step') == 1]

    # Get products for cycling from DB if cart is empty
    if not cart:
        cleansers_db = Product.objects.filter(routine_step=1, is_available=True)[:1]
        exfoliants_db = Product.objects.filter(routine_step=3, exfoliation_power__gte=40, is_available=True)[:1]
        retinoids_db = Product.objects.filter(name__icontains='retinol', is_available=True)[:1]
        moisturizers_db = Product.objects.filter(routine_step=4, is_available=True)[:2]
    else:
        cleansers_db = moisturizers_db = exfoliants_db = retinoids_db = []

    context = {
        'exfoliants': exfoliants,
        'retinoids': retinoids,
        'moisturizers': moisturizers,
        'cleansers': cleansers,
        'cart_list': cart_list,
        'currency': currency,
        'page_title': 'مولّد جدول التدوير الليلي للبشرة',
        'has_cart': bool(cart),
    }
    return render(request, 'store/skin_cycling.html', context)


# ─── 10. Compatibility Checker Lab ───────────────────────────────────────────

def compatibility_lab(request):
    currency = get_currency(request)
    products_all = Product.objects.filter(is_available=True).order_by('brand', 'name')
    context = {
        'products': products_all,
        'currency': currency,
        'page_title': 'مختبر فحص التوافق الكيميائي',
    }
    return render(request, 'store/compatibility_lab.html', context)


def check_compatibility(request):
    """HTMX: check compatibility between selected products."""
    product_ids = request.GET.getlist('products')
    if len(product_ids) < 2:
        return HttpResponse('<p class="text-amber-600 text-center py-4">يرجى اختيار منتجين على الأقل للفحص.</p>')

    products_selected = Product.objects.filter(id__in=product_ids).prefetch_related('active_ingredients')

    # Gather all ingredient pairs
    conflicts = []
    synergies = []
    all_ingredients = {}
    for p in products_selected:
        for ing in p.active_ingredients.all():
            all_ingredients.setdefault(ing.id, {'ingredient': ing, 'products': []})
            all_ingredients[ing.id]['products'].append(p.name)

    ing_ids = list(all_ingredients.keys())
    checked = set()
    for i, id_a in enumerate(ing_ids):
        for id_b in ing_ids[i+1:]:
            pair = tuple(sorted([id_a, id_b]))
            if pair in checked:
                continue
            checked.add(pair)
            conflict = IngredientConflict.objects.filter(
                Q(ingredient_a_id=id_a, ingredient_b_id=id_b) |
                Q(ingredient_a_id=id_b, ingredient_b_id=id_a)
            ).select_related('ingredient_a', 'ingredient_b').first()
            if conflict:
                conflicts.append(conflict)
            synergy = IngredientSynergy.objects.filter(
                Q(ingredient_a_id=id_a, ingredient_b_id=id_b) |
                Q(ingredient_a_id=id_b, ingredient_b_id=id_a)
            ).select_related('ingredient_a', 'ingredient_b').first()
            if synergy:
                synergies.append(synergy)

    html = render_to_string('store/partials/compatibility_result.html', {
        'products': products_selected,
        'conflicts': conflicts,
        'synergies': synergies,
        'is_safe': len(conflicts) == 0,
    }, request=request)
    return HttpResponse(html)


# ─── 11. INCI Decoder ────────────────────────────────────────────────────────

def inci_decoder(request):
    product_id = request.GET.get('product_id', '')
    inci_text = request.GET.get('inci_text', '')
    decoded = []

    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            inci_text = product.inci_list
        except Product.DoesNotExist:
            pass

    if inci_text:
        ingredients_db = {i.name_en.lower(): i for i in ActiveIngredient.objects.all()}
        parts = [p.strip() for p in inci_text.replace('\n', ',').split(',') if p.strip()]
        for part in parts:
            match = ingredients_db.get(part.lower())
            if match:
                decoded.append({'name': part, 'info': match, 'type': 'known'})
            elif any(kw in part.lower() for kw in ['acid', 'retinol', 'vitamin', 'niacin', 'hyaluron']):
                decoded.append({'name': part, 'info': None, 'type': 'active'})
            elif any(kw in part.lower() for kw in ['fragrance', 'parfum', 'alcohol denat']):
                decoded.append({'name': part, 'info': None, 'type': 'caution'})
            else:
                decoded.append({'name': part, 'info': None, 'type': 'neutral'})

    if request.headers.get('HX-Request'):
        html = render_to_string('store/partials/inci_result.html', {
            'decoded': decoded,
            'inci_text': inci_text,
        }, request=request)
        return HttpResponse(html)

    products_with_inci = Product.objects.filter(is_available=True).exclude(inci_list='')
    return render(request, 'store/inci_decoder.html', {
        'products_with_inci': products_with_inci,
        'decoded': decoded,
        'inci_text': inci_text,
        'page_title': 'محلل قائمة المكونات INCI',
    })


# ─── 12. Product Comparator ──────────────────────────────────────────────────

def compare(request):
    currency = get_currency(request)
    product_ids = request.GET.getlist('products')[:3]
    selected = Product.objects.filter(id__in=product_ids, is_available=True).prefetch_related(
        'skin_types', 'skin_concerns', 'active_ingredients'
    ) if product_ids else []
    all_products = Product.objects.filter(is_available=True).order_by('brand', 'name')
    return render(request, 'store/compare.html', {
        'selected_products': selected,
        'all_products': all_products,
        'currency': currency,
        'page_title': 'جدول المقارنة التفصيلي',
    })


# ─── 13. Checkout & WhatsApp Invoice ────────────────────────────────────────

def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('store:cart')
    currency = get_currency(request)
    cart_list = _get_cart_list(cart)
    cart_total = sum(i['subtotal'] for i in cart_list)
    analysis = _analyze_cart(cart)

    if request.method == 'POST':
        # Save order
        order = Order.objects.create(
            customer_name=request.POST.get('customer_name', ''),
            whatsapp=request.POST.get('whatsapp', ''),
            city=request.POST.get('city', ''),
            address=request.POST.get('address', ''),
            skin_notes=request.POST.get('skin_notes', ''),
            payment_method=request.POST.get('payment_method', 'cod'),
            currency=currency,
            total_amount=cart_total,
            notes=request.POST.get('notes', ''),
            status='pending',
        )

        morning_items = []
        evening_items = []

        for item in cart_list:
            try:
                product = Product.objects.get(id=item['product_id'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item['quantity'],
                    unit_price=item['price'],
                    currency=currency,
                )
                use_time = item.get('use_time', 'both')
                if use_time in ['morning', 'both']:
                    morning_items.append(item)
                if use_time in ['evening', 'both']:
                    evening_items.append(item)
            except Product.DoesNotExist:
                pass

        # Clear cart
        request.session['cart'] = {}
        request.session.modified = True

        # Build WhatsApp message
        wa_msg = _build_whatsapp_message(order, cart_list, morning_items, evening_items, currency)
        wa_number = getattr(settings, 'WHATSAPP_NUMBER', '967778550938')
        wa_url = f'https://wa.me/{wa_number}?text={urllib.parse.quote(wa_msg)}'

        return render(request, 'store/order_success.html', {
            'order': order,
            'cart_list': cart_list,
            'wa_url': wa_url,
            'morning_items': morning_items,
            'evening_items': evening_items,
            'currency': currency,
            'page_title': 'تم تأكيد طلبك!',
        })

    return render(request, 'store/checkout.html', {
        'cart_list': cart_list,
        'cart_total': cart_total,
        'currency': currency,
        'cart_analysis': analysis,
        'page_title': 'إتمام الطلب',
    })


def _build_whatsapp_message(order, cart_list, morning_items, evening_items, currency):
    symbols = {'yer': 'ر.ي', 'sar': 'ر.س', 'usd': '$'}
    sym = symbols.get(currency, 'ر.ي')
    lines = [
        '🌿 *طلب جديد — متجر ريمشي الطبي* 🌿',
        '━━━━━━━━━━━━━━━━━',
        f'👤 *الاسم:* {order.customer_name}',
        f'📱 *الواتساب:* {order.whatsapp}',
        f'📍 *المدينة:* {order.city}',
        f'🏠 *العنوان:* {order.address}',
        f'💳 *طريقة الدفع:* {order.get_payment_method_display()}',
        '━━━━━━━━━━━━━━━━━',
        '🛒 *الأصناف المطلوبة:*',
    ]
    for item in cart_list:
        lines.append(f'  • {item["brand"]} — {item["name"]} × {item["quantity"]} = {item["subtotal"]:,.0f} {sym}')

    lines += [
        '━━━━━━━━━━━━━━━━━',
        f'💰 *الإجمالي: {order.total_amount:,.0f} {sym}*',
        '━━━━━━━━━━━━━━━━━',
        '💊 *دليل استخدام منتجاتك (خدمة مجانية من ريمشي):*',
        '',
        '☀️ *الروتين الصباحي:*',
    ]
    for i, item in enumerate(morning_items, 1):
        lines.append(f'  {i}. {item["name"]}')

    lines += ['', '🌙 *الروتين المسائي:*']
    for i, item in enumerate(evening_items, 1):
        lines.append(f'  {i}. {item["name"]}')

    lines += [
        '',
        '⚠️ *تنبيه:* هذه معلومات تعليمية وليست بديلاً عن استشارة طبيب متخصص.',
        '━━━━━━━━━━━━━━━━━',
        '🙏 شكراً لثقتك بريمشي!'
    ]
    return '\n'.join(lines)


# ─── 14. Routine Prescription Card (printable) ───────────────────────────────

def prescription_card(request):
    cart = request.session.get('cart', {})
    currency = get_currency(request)
    cart_list = _get_cart_list(cart)
    morning = [i for i in cart_list if i.get('use_time') in ['morning', 'both']]
    evening = [i for i in cart_list if i.get('use_time') in ['evening', 'both']]
    return render(request, 'store/prescription_card.html', {
        'cart_list': cart_list,
        'morning_items': morning,
        'evening_items': evening,
        'currency': currency,
        'page_title': 'بطاقة روتيني اليومي',
    })


# ─── 15. Bundles ────────────────────────────────────────────────────────────

def bundles(request):
    currency = get_currency(request)
    bundles_qs = RoutineBundle.objects.filter(is_active=True).prefetch_related('products')
    return render(request, 'store/bundles.html', {
        'bundles': bundles_qs,
        'currency': currency,
        'page_title': 'الباقات الجاهزة',
    })


@require_POST
def add_bundle_to_cart(request, bundle_id):
    bundle = get_object_or_404(RoutineBundle, id=bundle_id, is_active=True)
    currency = get_currency(request)
    cart = request.session.get('cart', {})

    for product in bundle.products.all():
        key = str(product.id)
        discounted = product.get_discounted_price(currency)
        bundle_price = discounted * (1 - bundle.discount_percent / 100)
        ingredient_ids = list(product.active_ingredients.values_list('id', flat=True))
        if key in cart:
            cart[key]['quantity'] += 1
        else:
            cart[key] = {
                'product_id': product.id,
                'name': product.name,
                'brand': product.brand,
                'price': round(bundle_price, 2),
                'currency': currency,
                'quantity': 1,
                'image_url': product.get_image_url() or '',
                'package_color': product.package_color,
                'routine_step': product.routine_step,
                'use_time': product.use_time,
                'requires_sunscreen': product.requires_sunscreen,
                'ingredient_ids': ingredient_ids,
                'slug': product.slug,
            }

    request.session['cart'] = cart
    request.session.modified = True

    response = redirect('store:cart')
    return response
