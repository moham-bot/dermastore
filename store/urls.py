from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('bundles/', views.bundles, name='bundles'),
    path('bundles/<int:bundle_id>/add/', views.add_bundle_to_cart, name='add_bundle_to_cart'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),

    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('prescription-card/', views.prescription_card, name='prescription_card'),

    # Interactive Tools
    path('face-mapper/', views.face_mapper, name='face_mapper'),
    path('consultant/', views.skin_consultant, name='skin_consultant'),
    path('consultant/result/', views.consultant_result, name='consultant_result'),
    path('skin-cycling/', views.skin_cycling, name='skin_cycling'),
    path('compatibility-lab/', views.compatibility_lab, name='compatibility_lab'),
    path('compatibility-lab/check/', views.check_compatibility, name='check_compatibility'),
    path('inci-decoder/', views.inci_decoder, name='inci_decoder'),
    path('compare/', views.compare, name='compare'),

    # Settings
    path('set-currency/', views.set_currency, name='set_currency'),
    path('set-theme/', views.set_theme, name='set_theme'),
]

