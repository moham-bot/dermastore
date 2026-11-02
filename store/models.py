from django.db import models
from django.utils.text import slugify
import re


# ─── 1. Skin Type ────────────────────────────────────────────────────────────

class SkinType(models.Model):
    name = models.CharField(max_length=60, unique=True, verbose_name='نوع البشرة')
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    description = models.TextField(verbose_name='الوصف التشريحي')
    characteristics = models.TextField(verbose_name='أبرز العلامات')
    icon = models.CharField(max_length=10, default='🌿', verbose_name='الأيقونة')

    class Meta:
        verbose_name = 'نوع بشرة'
        verbose_name_plural = 'أنواع البشرة'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name, allow_unicode=True)
            self.slug = base or f'skin-type-{self.id or "new"}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.icon} {self.name}'


# ─── 2. Skin Concern ─────────────────────────────────────────────────────────

class SkinConcern(models.Model):
    FACE_ZONES = [
        ('t_zone', 'منطقة T (الجبين والأنف)'),
        ('u_zone', 'منطقة U (الخدين والفك)'),
        ('eye_area', 'محيط العين'),
        ('full_face', 'الوجه بالكامل'),
    ]
    name = models.CharField(max_length=100, unique=True, verbose_name='مشكلة البشرة')
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(verbose_name='الوصف')
    face_zone = models.CharField(max_length=20, choices=FACE_ZONES, default='full_face', verbose_name='منطقة الوجه')
    icon = models.CharField(max_length=10, default='🔍', verbose_name='الأيقونة')
    display_order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتيب العرض')

    class Meta:
        verbose_name = 'مشكلة بشرة'
        verbose_name_plural = 'مشاكل البشرة'
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name, allow_unicode=True)
            self.slug = base or f'concern-{self.id or "new"}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.icon} {self.name}'


# ─── 3. Active Ingredient ────────────────────────────────────────────────────

class ActiveIngredient(models.Model):
    CATEGORY_CHOICES = [
        ('antioxidant', 'مضاد أكسدة'),
        ('exfoliant', 'مقشر أحماض'),
        ('retinoid', 'مجدد خلايا / ريتينويد'),
        ('humectant', 'مرطب جاذب للماء'),
        ('barrier_repair', 'مرمم للحاجز'),
        ('brightener', 'مفتح ومبرق'),
        ('anti_inflammatory', 'مضاد للالتهاب'),
        ('sunscreen', 'واقي شمس'),
    ]
    USE_TIME_CHOICES = [
        ('morning', 'صباحاً فقط ☀️'),
        ('evening', 'مساءً فقط 🌙'),
        ('both', 'صباحاً ومساءً ☀️🌙'),
    ]

    name_ar = models.CharField(max_length=120, verbose_name='الاسم العربي')
    name_en = models.CharField(max_length=120, verbose_name='الاسم العلمي (INCI)')
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    concentration = models.CharField(max_length=30, verbose_name='التركيز الشائع', blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, verbose_name='الفئة العلمية')
    mechanism = models.TextField(verbose_name='آلية العمل (بالعربية)')
    use_time = models.CharField(max_length=10, choices=USE_TIME_CHOICES, default='both', verbose_name='وقت الاستخدام')

    class Meta:
        verbose_name = 'مادة فعالة'
        verbose_name_plural = 'المواد الفعالة'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = re.sub(r'[^\w\s-]', '', self.name_en.lower()).strip()
            self.slug = re.sub(r'[\s_-]+', '-', base) or f'ingredient-{self.id or "new"}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name_ar} ({self.name_en})'

    def get_all_conflicts(self):
        from itertools import chain
        as_a = IngredientConflict.objects.filter(ingredient_a=self).select_related('ingredient_b')
        as_b = IngredientConflict.objects.filter(ingredient_b=self).select_related('ingredient_a')
        return list(chain(as_a, as_b))

    def get_conflict_with(self, other):
        return IngredientConflict.objects.filter(
            models.Q(ingredient_a=self, ingredient_b=other) |
            models.Q(ingredient_a=other, ingredient_b=self)
        ).first()

    def get_synergy_with(self, other):
        return IngredientSynergy.objects.filter(
            models.Q(ingredient_a=self, ingredient_b=other) |
            models.Q(ingredient_a=other, ingredient_b=self)
        ).first()


class IngredientConflict(models.Model):
    ingredient_a = models.ForeignKey(ActiveIngredient, on_delete=models.CASCADE, related_name='conflict_as_a')
    ingredient_b = models.ForeignKey(ActiveIngredient, on_delete=models.CASCADE, related_name='conflict_as_b')
    reason = models.TextField(verbose_name='سبب التعارض وخطورته')
    safe_usage = models.TextField(verbose_name='القاعدة الصحيحة للفصل بالتناوب')

    class Meta:
        verbose_name = 'تعارض كيميائي'
        verbose_name_plural = 'التعارضات الكيميائية'
        unique_together = [['ingredient_a', 'ingredient_b']]

    def __str__(self):
        return f'{self.ingredient_a.name_ar} ⚠️ {self.ingredient_b.name_ar}'

    def get_other(self, ingredient):
        return self.ingredient_b if self.ingredient_a == ingredient else self.ingredient_a


class IngredientSynergy(models.Model):
    ingredient_a = models.ForeignKey(ActiveIngredient, on_delete=models.CASCADE, related_name='synergy_as_a')
    ingredient_b = models.ForeignKey(ActiveIngredient, on_delete=models.CASCADE, related_name='synergy_as_b')
    benefit = models.TextField(verbose_name='فائدة الدمج وكيف يتضاعف المفعول')

    class Meta:
        verbose_name = 'تناغم كيميائي'
        verbose_name_plural = 'التناغمات الكيميائية'
        unique_together = [['ingredient_a', 'ingredient_b']]

    def __str__(self):
        return f'{self.ingredient_a.name_ar} ✅ {self.ingredient_b.name_ar}'


# ─── 4. Product ──────────────────────────────────────────────────────────────

class Product(models.Model):
    BADGE_CHOICES = [
        ('bestseller', '🔥 الأكثر مبيعاً'),
        ('featured', '⭐ منتج مميز'),
        ('new', '✨ وصل حديثاً'),
        ('sale', '🏷️ عرض خاص'),
        ('', 'بدون شارة'),
    ]
    ROUTINE_STEP_CHOICES = [
        (1, '1 — غسول منظف 🧴'),
        (2, '2 — تونر وموازنة 💦'),
        (3, '3 — سيروم وعلاج مركز 💊'),
        (4, '4 — مرطب ومجدد للحاجز 🥛'),
        (5, '5 — واقي شمس ☀️'),
        (6, '6 — عناية خاصة / ماسك 🎭'),
    ]
    USE_TIME_CHOICES = [
        ('morning', 'صباحي فقط ☀️'),
        ('evening', 'مسائي فقط 🌙'),
        ('both', 'صباحي ومسائي ☀️🌙'),
    ]
    TEXTURE_CHOICES = [
        ('gel', 'جل مائي'),
        ('serum', 'سيروم خفيف'),
        ('lotion', 'لوشن حليبي'),
        ('cream', 'كريم غني'),
        ('balm', 'بلسم ثقيل'),
        ('foam', 'رغوة'),
        ('oil', 'زيت'),
        ('mist', 'مستحضر رذاذ'),
        ('stick', 'ستيك / قلم'),
        ('powder', 'بودرة'),
    ]
    DOSAGE_CHOICES = [
        ('pea', 'مقدار حبة بازلاء 🫛'),
        ('drops_3', '3 قطرات بالقطارة 💧'),
        ('two_fingers', 'مقدار إصبعين كاملين ✌️'),
        ('coin', 'مقدار عملة معدنية 🪙'),
        ('pump_1', 'ضغطة واحدة'),
        ('pump_2', 'ضغطتان'),
        ('rice', 'مقدار حبة أرز'),
    ]
    SKIN_STATE_CHOICES = [
        ('wet', 'على بشرة مبللة'),
        ('damp', 'على بشرة رطبة قليلاً بعد التجفيف الخفيف'),
        ('dry', 'على بشرة جافة تماماً'),
        ('dry_10min', 'على بشرة جافة تماماً لمدة 10 دقائق'),
    ]

    # Basic Info
    name = models.CharField(max_length=200, verbose_name='اسم المنتج')
    brand = models.CharField(max_length=100, verbose_name='الماركة')
    sku = models.CharField(max_length=80, blank=True, null=True, unique=True, verbose_name='رمز SKU')
    original_filename = models.CharField(max_length=255, blank=True, verbose_name='اسم ملف الصورة الأصلي')
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    volume_ml = models.CharField(max_length=30, blank=True, verbose_name='الحجم')
    short_description = models.TextField(verbose_name='وصف مختصر', blank=True)
    full_description = models.TextField(verbose_name='وصف كامل', blank=True)
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, blank=True, default='', verbose_name='الشارة')
    is_demo = models.BooleanField(default=False, verbose_name='منتج تجريبي للعرض Demo')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8, verbose_name='التقييم')
    review_count = models.PositiveIntegerField(default=32, verbose_name='عدد التقييمات')

    # Pricing (multi-currency)
    price_yer = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='السعر (ر.ي)', default=0)
    price_sar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='السعر (ر.س)', default=0)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='السعر ($)', default=0)
    discount_percent = models.PositiveSmallIntegerField(default=0, verbose_name='نسبة الخصم %')
    stock_quantity = models.PositiveIntegerField(default=100, verbose_name='الكمية في المخزون')
    is_available = models.BooleanField(default=True, verbose_name='متاح للبيع')

    # Images — Triple Fallback Engine
    image_file = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='صورة مرفوعة (كاميرا/معرض)')
    image_url = models.URLField(max_length=500, blank=True, verbose_name='رابط صورة خارجي مباشر')
    cloudinary_public_id = models.CharField(max_length=255, blank=True, verbose_name='معرف صورة Cloudinary (Public ID)')
    cloudinary_url = models.URLField(max_length=500, blank=True, verbose_name='رابط صورة Cloudinary الآمن')
    package_color = models.CharField(max_length=7, default='#5c8a6e', verbose_name='لون العبوة (HEX)')

    # Routine
    routine_step = models.PositiveSmallIntegerField(choices=ROUTINE_STEP_CHOICES, default=3, verbose_name='خطوة الروتين')
    use_time = models.CharField(max_length=10, choices=USE_TIME_CHOICES, default='both', verbose_name='وقت الاستخدام')

    # Scientific Indicators (0–100)
    hydration_level = models.PositiveSmallIntegerField(default=50, verbose_name='مستوى الترطيب %')
    exfoliation_power = models.PositiveSmallIntegerField(default=0, verbose_name='قوة التقشير %')
    sensitivity_safety = models.PositiveSmallIntegerField(default=70, verbose_name='درجة الأمان للبشرة الحساسة %')
    absorption_speed = models.PositiveSmallIntegerField(default=70, verbose_name='سرعة الامتصاص %')

    # Application Guide
    texture = models.CharField(max_length=20, choices=TEXTURE_CHOICES, default='cream', verbose_name='قوام المنتج')
    dosage = models.CharField(max_length=20, choices=DOSAGE_CHOICES, default='pea', verbose_name='الكمية القياسية')
    skin_state_before = models.CharField(max_length=20, choices=SKIN_STATE_CHOICES, default='damp', verbose_name='حالة الجلد قبل التطبيق')
    wait_seconds = models.PositiveSmallIntegerField(default=60, verbose_name='ثواني الانتظار')
    beginner_schedule = models.TextField(blank=True, verbose_name='جدول التدرج للمبتدئين')
    application_steps = models.TextField(blank=True, verbose_name='خطوات التطبيق الصحيحة')
    restricted_areas = models.TextField(blank=True, verbose_name='المناطق المحظورة')
    inci_list = models.TextField(blank=True, verbose_name='قائمة المكونات INCI الكاملة')

    # Safety Filters
    safe_pregnancy = models.BooleanField(default=False, verbose_name='آمن للحمل والرضاعة')
    fragrance_free = models.BooleanField(default=False, verbose_name='خالٍ من العطور')
    non_comedogenic = models.BooleanField(default=False, verbose_name='لا يسد المسام')
    requires_sunscreen = models.BooleanField(default=False, verbose_name='يتطلب واقي شمس صباحاً')
    safety_warning = models.TextField(blank=True, verbose_name='تحذير صيدلاني')

    # Relations
    skin_types = models.ManyToManyField(SkinType, blank=True, verbose_name='أنواع البشرة المناسبة')
    skin_concerns = models.ManyToManyField(SkinConcern, blank=True, verbose_name='المشاكل التي يعالجها')
    active_ingredients = models.ManyToManyField(ActiveIngredient, blank=True, verbose_name='المواد الفعالة')
    pairs_well_with = models.ManyToManyField('self', blank=True, symmetrical=True, verbose_name='يكمله في الروتين')
    cheaper_alternative = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='premium_version', verbose_name='البديل الأوفر'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'
        ordering = ['routine_step', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f'{self.brand}-{self.name}'
            slug = slugify(base, allow_unicode=True)
            if not slug:
                slug = re.sub(r'[^\w-]', '-', base.lower())
            self.slug = slug or f'product-{self.id or "new"}'

        # Cloudinary Auto-Upload Engine on new or changed image
        has_new_image = False
        old_public_id = None
        if self.pk:
            old_inst = Product.objects.filter(pk=self.pk).first()
            if old_inst:
                old_public_id = old_inst.cloudinary_public_id
                if self.image_file and old_inst.image_file != self.image_file:
                    has_new_image = True
        elif self.image_file:
            has_new_image = True

        import os
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'aeildie1')
        api_key = os.environ.get('CLOUDINARY_API_KEY', '477871866486762')
        api_secret = os.environ.get('CLOUDINARY_API_SECRET', '')

        if has_new_image and cloud_name and api_key and api_secret:
            try:
                import cloudinary
                import cloudinary.uploader
                cloudinary.config(
                    cloud_name=cloud_name,
                    api_key=api_key,
                    api_secret=api_secret,
                    secure=True
                )
                # Delete replaced previous image from Cloudinary
                if old_public_id:
                    try:
                        cloudinary.uploader.destroy(old_public_id)
                    except Exception:
                        pass

                # Upload to Cloudinary with automatic optimization (f_auto, q_auto)
                upload_res = cloudinary.uploader.upload(
                    self.image_file,
                    folder='remshy_products',
                    resource_type='image',
                    transformation=[
                        {'quality': 'auto', 'fetch_format': 'auto'}
                    ]
                )
                self.cloudinary_public_id = upload_res.get('public_id', '')
                self.cloudinary_url = upload_res.get('secure_url', '')
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Cloudinary upload skipped or failed: {e}")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.cloudinary_public_id:
            import os
            cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'aeildie1')
            api_key = os.environ.get('CLOUDINARY_API_KEY', '477871866486762')
            api_secret = os.environ.get('CLOUDINARY_API_SECRET', '')
            if cloud_name and api_key and api_secret:
                try:
                    import cloudinary
                    import cloudinary.uploader
                    cloudinary.config(
                        cloud_name=cloud_name,
                        api_key=api_key,
                        api_secret=api_secret,
                        secure=True
                    )
                    cloudinary.uploader.destroy(self.cloudinary_public_id)
                except Exception:
                    pass
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.brand} — {self.name}'

    def get_optimized_cloudinary_url(self, width=None, height=None, crop='fill'):
        """Generate Cloudinary URL optimized with f_auto and q_auto."""
        if self.cloudinary_public_id:
            try:
                import cloudinary.utils
                options = {
                    'secure': True,
                    'fetch_format': 'auto',
                    'quality': 'auto',
                }
                if width:
                    options['width'] = width
                if height:
                    options['height'] = height
                    options['crop'] = crop
                url, _ = cloudinary.utils.cloudinary_url(self.cloudinary_public_id, **options)
                return url
            except Exception:
                pass
        if self.cloudinary_url:
            if '/upload/' in self.cloudinary_url and '/f_auto,q_auto/' not in self.cloudinary_url:
                return self.cloudinary_url.replace('/upload/', '/upload/f_auto,q_auto/')
            return self.cloudinary_url
        return None

    def get_image_url(self):
        """
        Triple fallback image engine:
        Level 1: Cloudinary optimized URL (f_auto, q_auto)
        Level 2: Uploaded file or external image URL
        Level 3: Dynamic Clinical SVG Placeholder
        """
        cloud_url = self.get_optimized_cloudinary_url()
        if cloud_url:
            return cloud_url
        if self.image_file:
            try:
                return self.image_file.url
            except Exception:
                pass
        if self.image_url:
            return self.image_url
        return None

    def get_svg_placeholder(self):
        """Dynamic Clinical SVG Placeholder with package color & typography."""
        brand = self.brand or 'REMSHY CLINICAL'
        name = (self.name or 'منتج علاجي')[:22]
        color = self.package_color or '#5c8a6e'
        volume = self.volume_ml or 'Dermocosmetics'
        pid = self.id or 'new'
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%" style="background: radial-gradient(circle at 50% 30%, {color}25 0%, #0f172a 100%); font-family: 'Cairo', 'Readex Pro', sans-serif;">
          <defs>
            <linearGradient id="grad_{pid}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="{color}" stop-opacity="0.95"/>
              <stop offset="100%" stop-color="{color}" stop-opacity="0.6"/>
            </linearGradient>
            <filter id="shadow_{pid}" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#000000" flood-opacity="0.5"/>
            </filter>
          </defs>
          <circle cx="200" cy="180" r="130" fill="none" stroke="{color}" stroke-opacity="0.18" stroke-width="1.5" stroke-dasharray="4 6"/>
          <circle cx="200" cy="180" r="85" fill="none" stroke="{color}" stroke-opacity="0.25" stroke-width="1"/>
          <g filter="url(#shadow_{pid})">
            <rect x="155" y="125" width="90" height="150" rx="18" fill="url(#grad_{pid})"/>
            <rect x="175" y="90" width="50" height="35" rx="6" fill="#f8fafc" opacity="0.95"/>
            <rect x="185" y="70" width="30" height="20" rx="3" fill="#cbd5e1"/>
            <rect x="165" y="65" width="45" height="10" rx="4" fill="#94a3b8"/>
            <rect x="165" y="150" width="70" height="95" rx="8" fill="#ffffff" opacity="0.94"/>
            <line x1="175" y1="170" x2="225" y2="170" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>
            <line x1="180" y1="185" x2="220" y2="185" stroke="#64748b" stroke-width="1.5" stroke-linecap="round"/>
            <line x1="185" y1="195" x2="215" y2="195" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="200" cy="220" r="7" fill="{color}" opacity="0.8"/>
          </g>
          <text x="200" y="320" text-anchor="middle" fill="#f8fafc" font-size="15" font-weight="bold" letter-spacing="1">{brand}</text>
          <text x="200" y="345" text-anchor="middle" fill="#cbd5e1" font-size="13">{name}</text>
          <text x="200" y="370" text-anchor="middle" fill="{color}" font-size="11" font-weight="600">{volume} • CLINICAL PHARMACY</text>
        </svg>'''

    def get_price(self, currency='yer'):
        return {'yer': self.price_yer, 'sar': self.price_sar, 'usd': self.price_usd}.get(currency, self.price_yer)

    def get_discounted_price(self, currency='yer'):
        price = float(self.get_price(currency))
        if self.discount_percent > 0:
            return round(price * (1 - self.discount_percent / 100), 2)
        return price

    @property
    def discounted_price_yer(self):
        return self.get_discounted_price('yer')

    @property
    def discounted_price_sar(self):
        return self.get_discounted_price('sar')

    @property
    def discounted_price_usd(self):
        return self.get_discounted_price('usd')

    def is_low_stock(self):
        return 0 < self.stock_quantity <= 5

    def has_sunscreen_warning(self):
        return self.requires_sunscreen or self.exfoliation_power > 30


# ─── 5. Routine Bundle ───────────────────────────────────────────────────────

class RoutineBundle(models.Model):
    name = models.CharField(max_length=200, verbose_name='اسم الباقة')
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(verbose_name='وصف الباقة')
    products = models.ManyToManyField(Product, verbose_name='المنتجات')
    discount_percent = models.PositiveSmallIntegerField(default=10, verbose_name='نسبة خصم الباقة %')
    skin_concern = models.ForeignKey(SkinConcern, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='المشكلة المستهدفة')
    is_active = models.BooleanField(default=True, verbose_name='نشطة')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'باقة روتين'
        verbose_name_plural = 'باقات الروتين'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True) or f'bundle-{self.id or "new"}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_total_price(self, currency='yer'):
        total = sum(float(p.get_price(currency)) for p in self.products.all())
        return round(total * (1 - self.discount_percent / 100), 2)


# ─── 6. Order & OrderItem ────────────────────────────────────────────────────

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار ⏳'),
        ('confirmed', 'تم التأكيد ✅'),
        ('processing', 'جاري التجهيز 📦'),
        ('shipped', 'تم الشحن 🚚'),
        ('delivered', 'تم التسليم 🎉'),
        ('cancelled', 'ملغي ❌'),
    ]
    PAYMENT_CHOICES = [
        ('cod', 'الدفع عند الاستلام 💵'),
        ('kreemi', 'الكريمي 💳'),
        ('jawali', 'محفظة جوالي 📱'),
        ('jaib', 'محفظة جيب 👜'),
        ('onecash', 'ون كاش 💚'),
        ('flooss', 'فلوسك 🏦'),
        ('mobile_money', 'موبايل موني 📲'),
    ]
    CURRENCY_CHOICES = [
        ('yer', 'ريال يمني (ر.ي)'),
        ('sar', 'ريال سعودي (ر.س)'),
        ('usd', 'دولار أمريكي ($)'),
    ]

    customer_name = models.CharField(max_length=120, verbose_name='اسم العميل')
    whatsapp = models.CharField(max_length=20, verbose_name='رقم الواتساب')
    city = models.CharField(max_length=80, verbose_name='المدينة')
    address = models.TextField(verbose_name='العنوان التفصيلي')
    skin_notes = models.TextField(blank=True, verbose_name='ملاحظات البشرة')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod', verbose_name='طريقة الدفع')
    currency = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default='yer', verbose_name='العملة')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المبلغ الإجمالي')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='حالة الطلب')
    notes = models.TextField(blank=True, verbose_name='ملاحظات إضافية')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الطلب')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'طلب'
        verbose_name_plural = 'الطلبات'
        ordering = ['-created_at']

    def __str__(self):
        return f'طلب #{self.pk} — {self.customer_name}'

    def get_morning_products(self):
        return self.items.filter(product__use_time__in=['morning', 'both']).order_by('product__routine_step')

    def get_evening_products(self):
        return self.items.filter(product__use_time__in=['evening', 'both']).order_by('product__routine_step')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name='الطلب')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='المنتج')
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name='الكمية')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='سعر الوحدة')
    currency = models.CharField(max_length=5, default='yer', verbose_name='العملة')

    class Meta:
        verbose_name = 'صنف الطلب'
        verbose_name_plural = 'أصناف الطلب'

    def __str__(self):
        return f'{self.product.name} × {self.quantity}'

    def get_subtotal(self):
        return float(self.unit_price) * self.quantity
