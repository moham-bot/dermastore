from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db import models as db_models
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from .models import (
    SkinType, SkinConcern, ActiveIngredient, IngredientConflict,
    IngredientSynergy, Product, RoutineBundle, Order, OrderItem
)


@admin.register(SkinType)
class SkinTypeAdmin(ModelAdmin):
    list_display = ['icon', 'name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_per_page = 20


@admin.register(SkinConcern)
class SkinConcernAdmin(ModelAdmin):
    list_display = ['icon', 'name', 'face_zone', 'display_order']
    list_editable = ['display_order']
    list_filter = ['face_zone']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


class IngredientConflictInline(TabularInline):
    model = IngredientConflict
    fk_name = 'ingredient_a'
    extra = 1
    verbose_name = 'تعارض مع'
    verbose_name_plural = 'التعارضات الكيميائية'
    fields = ['ingredient_b', 'reason', 'safe_usage']


class IngredientSynergyInline(TabularInline):
    model = IngredientSynergy
    fk_name = 'ingredient_a'
    extra = 1
    verbose_name = 'تناغم مع'
    verbose_name_plural = 'التناغمات الكيميائية'
    fields = ['ingredient_b', 'benefit']


@admin.register(ActiveIngredient)
class ActiveIngredientAdmin(ModelAdmin):
    list_display = ['name_ar', 'name_en', 'category', 'use_time', 'concentration']
    list_filter = ['category', 'use_time']
    search_fields = ['name_ar', 'name_en']
    prepopulated_fields = {'slug': ('name_en',)}
    inlines = [IngredientConflictInline, IngredientSynergyInline]


from django import forms

class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'image_file': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'cloudinary-upload-input',
            })
        }


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    form = ProductAdminForm
    list_display = [
        'product_thumbnail', 'name', 'brand', 'sku', 'routine_step_display',
        'price_yer', 'discount_percent', 'stock_quantity', 'stock_qty_display',
        'badge', 'image_source_badge', 'is_available', 'view_on_site_btn'
    ]
    list_editable = ['price_yer', 'discount_percent', 'stock_quantity', 'is_available', 'badge']
    list_filter = [
        'is_demo', 'brand', 'routine_step', 'use_time', 'badge',
        'is_available', 'safe_pregnancy', 'fragrance_free', 'non_comedogenic',
        'skin_types', 'skin_concerns',
    ]
    search_fields = ['name', 'brand', 'sku', 'original_filename', 'short_description', 'inci_list', 'cloudinary_public_id']
    filter_horizontal = ['skin_types', 'skin_concerns', 'active_ingredients', 'pairs_well_with']
    readonly_fields = [
        'product_thumbnail_large', 'cloudinary_status_info',
        'cloudinary_public_id', 'cloudinary_url',
        'created_at', 'updated_at'
    ]
    list_per_page = 20

    fieldsets = [
        ('المعلومات الأساسية', {
            'fields': ['name', 'brand', 'sku', 'slug', 'volume_ml', 'badge', 'is_demo', 'short_description', 'full_description']
        }),
        ('محرك الصور السحابي (Cloudinary | رفع من الهاتف/الكمبيوتر | رابط | SVG تلقائي)', {
            'fields': [
                'product_thumbnail_large', 'cloudinary_status_info',
                'image_file', 'image_url',
                'cloudinary_public_id', 'cloudinary_url',
                'original_filename', 'package_color'
            ]
        }),
        ('التسعير والمخزون', {
            'fields': ['price_yer', 'price_sar', 'price_usd', 'discount_percent', 'stock_quantity', 'is_available']
        }),
        ('التقييمات والمراجعات', {
            'fields': ['rating', 'review_count'],
            'classes': ['collapse']
        }),
        ('بيانات الروتين', {
            'fields': ['routine_step', 'use_time']
        }),
        ('المؤشرات العلمية (0–100)', {
            'fields': ['hydration_level', 'exfoliation_power', 'sensitivity_safety', 'absorption_speed']
        }),
        ('دليل الاستخدام التفاعلي', {
            'fields': [
                'texture', 'dosage', 'skin_state_before', 'wait_seconds',
                'beginner_schedule', 'application_steps', 'restricted_areas', 'inci_list'
            ],
            'classes': ['collapse']
        }),
        ('فلاتر الأمان الطبي', {
            'fields': ['safe_pregnancy', 'fragrance_free', 'non_comedogenic', 'requires_sunscreen', 'safety_warning']
        }),
        ('العلاقات والتصنيف', {
            'fields': ['skin_types', 'skin_concerns', 'active_ingredients', 'pairs_well_with', 'cheaper_alternative']
        }),
        ('التواريخ', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    class Media:
        js = ('js/admin_image_preview.js',)

    def view_on_site_btn(self, obj):
        if obj.slug:
            return format_html(
                '<a href="/product/{}/" target="_blank" style="display:inline-flex;align-items:center;gap:4px;padding:3px 8px;background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;border-radius:6px;font-size:11px;font-weight:600;text-decoration:none;">'
                'عرض بالموقع ↗</a>',
                obj.slug
            )
        return '-'
    view_on_site_btn.short_description = 'معاينة'

    def image_source_badge(self, obj):
        if obj.cloudinary_public_id:
            return mark_safe('<span style="background:#0284c7;color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:bold;">☁️ Cloudinary</span>')
        elif obj.image_file:
            return mark_safe('<span style="background:#16a34a;color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;">📁 محلي</span>')
        elif obj.image_url:
            return mark_safe('<span style="background:#8b5cf6;color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;">🔗 رابط خارجي</span>')
        return mark_safe('<span style="background:#f59e0b;color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;">🎨 SVG تلقائي</span>')
    image_source_badge.short_description = 'مصدر الصورة'

    def product_thumbnail(self, obj):
        img_url = obj.get_image_url()
        if img_url:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:8px;border:1px solid #e5e7eb;">',
                img_url
            )
        color = obj.package_color or '#5c8a6e'
        return format_html(
            '<div style="width:48px;height:48px;border-radius:8px;background:{};display:flex;align-items:center;justify-content:center;font-size:20px;">🧴</div>',
            color
        )
    product_thumbnail.short_description = 'صورة'

    def product_thumbnail_large(self, obj):
        img_url = obj.get_image_url()
        if img_url:
            return format_html(
                '<div style="display:inline-block;padding:8px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;">'
                '<img src="{}" style="max-width:220px;max-height:220px;object-fit:contain;border-radius:10px;">'
                '</div>',
                img_url
            )
        return format_html(
            '<div style="width:200px;height:200px;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;">'
            '{}</div>',
            mark_safe(obj.get_svg_placeholder())
        )
    product_thumbnail_large.short_description = 'معاينة الصورة الحالية'

    def cloudinary_status_info(self, obj):
        if obj.cloudinary_public_id and obj.cloudinary_url:
            optimized_url = obj.get_optimized_cloudinary_url()
            return format_html(
                '<div style="padding:10px;background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;color:#0369a1;font-size:12px;">'
                '<strong>✅ متصل بـ Cloudinary بنجاح!</strong><br>'
                '<strong>Public ID:</strong> <code>{}</code><br>'
                '<strong>رابط التحسين التلقائي (f_auto, q_auto):</strong> <a href="{}" target="_blank" style="color:#0284c7;text-decoration:underline;">فتح الرابط ↗</a>'
                '</div>',
                obj.cloudinary_public_id, optimized_url
            )
        return mark_safe(
            '<div style="padding:10px;background:#fefce8;border:1px solid #fef08a;border-radius:8px;color:#854d0e;font-size:12px;">'
            'ℹ️ لم تُرفع صورة لهذا المنتج إلى Cloudinary بعد. ارفع صورة من الحقل أدناه ليتم رفعها وحفظها سحابياً تلقائياً.'
            '</div>'
        )
    cloudinary_status_info.short_description = 'حالة Cloudinary'

    def routine_step_display(self, obj):
        return obj.get_routine_step_display()
    routine_step_display.short_description = 'خطوة الروتين'

    def stock_qty_display(self, obj):
        qty = obj.stock_quantity
        if qty == 0:
            return mark_safe('<span style="color:#ef4444;font-weight:bold;">نفد المخزون</span>')
        if qty <= 5:
            return format_html('<span style="color:#f59e0b;font-weight:bold;">⚠️ بقي {} فقط</span>', qty)
        return format_html('<span style="color:#22c55e;">{}</span>', qty)
    stock_qty_display.short_description = 'المخزون'


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'unit_price', 'currency', 'subtotal_display']
    fields = ['product', 'quantity', 'unit_price', 'currency', 'subtotal_display']

    def subtotal_display(self, obj):
        return f'{obj.get_subtotal():,.0f}'
    subtotal_display.short_description = 'الإجمالي'


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = [
        'id', 'customer_name', 'whatsapp', 'city',
        'payment_method', 'currency', 'total_amount',
        'status', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    list_editable = ['status']
    search_fields = ['customer_name', 'whatsapp', 'city']
    readonly_fields = ['created_at', 'updated_at', 'total_amount']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b', 'confirmed': '#3b82f6',
            'processing': '#8b5cf6', 'shipped': '#06b6d4',
            'delivered': '#22c55e', 'cancelled': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:12px;font-size:12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'


@admin.register(RoutineBundle)
class RoutineBundleAdmin(ModelAdmin):
    list_display = ['name', 'discount_percent', 'skin_concern', 'product_count', 'is_active']
    list_editable = ['discount_percent', 'is_active']
    filter_horizontal = ['products']
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        count = obj.products.count()
        return format_html('<span style="font-weight:bold;">{} منتجات</span>', count)
    product_count.short_description = 'عدد المنتجات'
