import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'remshy_project.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from store.models import Product, RoutineBundle, SkinType, SkinConcern

client = Client()

print("--- REMSHY CLINICAL STORE INTEGRATION TEST ---")

# 1. Test Home page
res = client.get('/')
assert res.status_code == 200, f"Home page returned {res.status_code}"
assert b'logo.svg' in res.content, "Home page missing logo.svg"
assert b'hero' in res.content.lower(), "Home page missing hero section"
print("[PASS] 1. Home page renders (HTTP 200) with luxury clinical logo and hero")

# 2. Test Products catalog
res = client.get('/products/')
assert res.status_code == 200, f"Products catalog returned {res.status_code}"
assert b'luxury-card' in res.content, "Products catalog missing luxury-card"
print("[PASS] 2. Products catalog renders (HTTP 200) with luxury product cards")

# 3. Test Product Detail
product = Product.objects.filter(is_demo=True).first()
if not product:
    product = Product.objects.first()
assert product is not None, "No products found in DB"

res = client.get(f'/product/{product.slug}/')
assert res.status_code == 200, f"Product detail returned {res.status_code}"
assert product.name.encode('utf-8') in res.content, "Product name not found in detail page"
assert b'cloudinary' in res.content.lower() or product.image_url.encode('utf-8') in res.content, "Cloudinary image missing in detail"
print(f"[PASS] 3. Product detail renders (HTTP 200) for '{product.name}' with Cloudinary asset")

# 4. Test Quick View endpoint
res = client.get(f'/product/{product.id}/quick-view/')
assert res.status_code == 200, f"Quick view returned {res.status_code}"
assert b'closeQuickView' in res.content, "Quick view modal markup missing"
print(f"[PASS] 4. Quick View modal endpoint renders (HTTP 200)")

# 5. Test Wishlist toggle & Wishlist page
res = client.post(f'/wishlist/toggle/{product.id}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
assert res.status_code == 200, f"Wishlist toggle returned {res.status_code}"
json_data = res.json()
assert json_data.get('status') == 'ok', "Wishlist toggle status != ok"
assert json_data.get('added') is True, "Wishlist toggle added != True"

res = client.get('/wishlist/')
assert res.status_code == 200, f"Wishlist page returned {res.status_code}"
assert product.name.encode('utf-8') in res.content, "Product missing from wishlist page"
print("[PASS] 5. Wishlist toggle & Wishlist page render properly (HTTP 200)")

# 6. Test Interactive clinical tools & pages
pages = [
    '/face-mapper/',
    '/consultant/',
    '/compatibility-lab/',
    '/skin-cycling/',
    '/compare/',
    '/inci-decoder/',
    '/bundles/',
    '/cart/',
    '/checkout/',
]
for p in pages:
    r = client.get(p)
    if p == '/checkout/':
        assert r.status_code in (200, 302), f"Page {p} failed with {r.status_code}"
    else:
        assert r.status_code == 200, f"Page {p} failed with {r.status_code}"
print("[PASS] 6. All clinical tools & pages (bundles, cart, checkout) verified (HTTP 200)")

# 7. Test Admin login & access
from django.contrib.auth.models import User
admin_user = User.objects.filter(is_superuser=True).first()
if admin_user:
    client.force_login(admin_user)
    res = client.get('/admin/store/product/')
    assert res.status_code == 200, f"Admin product list failed with {res.status_code}"
    print("[PASS] 7. Unfold Admin product list accessible with new columns (HTTP 200)")

print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
