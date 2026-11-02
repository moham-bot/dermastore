import os
import csv
import sys
from pathlib import Path
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from store.models import (
    SkinType, SkinConcern, ActiveIngredient, Product, RoutineBundle
)

class Command(BaseCommand):
    help = 'Seeds authentic demo dermocosmetics products using images from image/ and image_manifest.csv'

    def handle(self, *args, **options):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

        self.stdout.write(self.style.NOTICE("=" * 65))
        self.stdout.write(self.style.NOTICE("[SEED] Starting Demostore Seeding with Local Images & Cloudinary"))
        self.stdout.write(self.style.NOTICE("=" * 65))

        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        image_dir = base_dir / 'image'
        manifest_path = base_dir / 'image_manifest.csv'

        if not manifest_path.exists():
            self.stdout.write(self.style.ERROR(f"Manifest file not found at {manifest_path}"))
            return

        if not image_dir.exists():
            self.stdout.write(self.style.ERROR(f"Image directory not found at {image_dir}"))
            return

        # 1. Setup Base Taxonomy (Skin Types & Concerns)
        self.stdout.write("1. Verifying & Setting up Skin Types & Concerns...")
        skin_types = {
            'oily': SkinType.objects.get_or_create(slug='oily', defaults={'name': 'دهنية', 'icon': '✨', 'description': 'بشرة تفرز زيوتاً زائدة وتحتاج لتنظيم اللمعان وتضييق المسام.'})[0],
            'dry': SkinType.objects.get_or_create(slug='dry', defaults={'name': 'جافة', 'icon': '🏜️', 'description': 'بشرة تفتقر إلى الزيوت الطبيعية وتحتاج إلى ترميم الحاجز الدهني.'})[0],
            'sensitive': SkinType.objects.get_or_create(slug='sensitive', defaults={'name': 'حساسة', 'icon': '🌸', 'description': 'بشرة سريعة التهيج والاحمرار وتحتاج لمهدئات خالية من العطور.'})[0],
            'combination': SkinType.objects.get_or_create(slug='combination', defaults={'name': 'مختلطة', 'icon': '⚖️', 'description': 'دهنية في منطقة T-zone وجافة أو عادية في الخدين.'})[0],
            'normal': SkinType.objects.get_or_create(slug='normal', defaults={'name': 'عادية', 'icon': '💧', 'description': 'بشرة متوازنة صحياً تحتاج للحماية المستمرة والترطيب اليومي.'})[0],
        }

        skin_concerns = {
            'acne': SkinConcern.objects.get_or_create(slug='acne', defaults={'name': 'حب الشباب والمسام الواسعة', 'icon': '🔴', 'face_zone': 'cheeks', 'display_order': 1})[0],
            'dehydration': SkinConcern.objects.get_or_create(slug='dehydration', defaults={'name': 'الجفاف والخشونة', 'icon': '🏜️', 'face_zone': 'cheeks', 'display_order': 2})[0],
            'pigmentation': SkinConcern.objects.get_or_create(slug='pigmentation', defaults={'name': 'التصبغات والبقع الداكنة', 'icon': '🌑', 'face_zone': 'forehead', 'display_order': 3})[0],
            'redness': SkinConcern.objects.get_or_create(slug='redness', defaults={'name': 'الاحمرار والتهيج', 'icon': '🌡️', 'face_zone': 'nose', 'display_order': 4})[0],
            'aging': SkinConcern.objects.get_or_create(slug='aging', defaults={'name': 'التجاعيد والخطوط التعبيرية', 'icon': '⏳', 'face_zone': 'eyes', 'display_order': 5})[0],
            'dark_circles': SkinConcern.objects.get_or_create(slug='dark_circles', defaults={'name': 'الهالات السوداء وانتفاخ العين', 'icon': '👁️', 'face_zone': 'eyes', 'display_order': 6})[0],
            'stretch_marks': SkinConcern.objects.get_or_create(slug='stretch_marks', defaults={'name': 'علامات التمدد وترهل الجلد', 'icon': '〰️', 'face_zone': 'all', 'display_order': 7})[0],
            'hair_care': SkinConcern.objects.get_or_create(slug='hair_care', defaults={'name': 'صحة الشعر وفروة الرأس', 'icon': '💇', 'face_zone': 'all', 'display_order': 8})[0],
        }

        # 2. Setup Active Ingredients
        self.stdout.write("2. Verifying & Setting up Active Ingredients...")
        ingredients = {
            'retinol': ActiveIngredient.objects.get_or_create(slug='retinol', defaults={'name_ar': 'ريتينول 0.3%', 'name_en': 'Retinol', 'category': 'vitamin', 'use_time': 'evening', 'concentration': '0.3%'})[0],
            'glycolic': ActiveIngredient.objects.get_or_create(slug='glycolic-acid', defaults={'name_ar': 'حمض الجليكوليك 7%', 'name_en': 'Glycolic Acid', 'category': 'aha', 'use_time': 'evening', 'concentration': '7%'})[0],
            'hyaluronic': ActiveIngredient.objects.get_or_create(slug='hyaluronic-acid', defaults={'name_ar': 'حمض الهيالورونيك 2%', 'name_en': 'Hyaluronic Acid', 'category': 'hydrator', 'use_time': 'both', 'concentration': '2%'})[0],
            'b5': ActiveIngredient.objects.get_or_create(slug='provitamin-b5', defaults={'name_ar': 'برو فيتامين B5', 'name_en': 'Pro-Vitamin B5', 'category': 'hydrator', 'use_time': 'both', 'concentration': '1%'})[0],
            'salicylic': ActiveIngredient.objects.get_or_create(slug='salicylic-acid', defaults={'name_ar': 'حمض الساليسيليك BHA', 'name_en': 'Salicylic Acid', 'category': 'bha', 'use_time': 'evening', 'concentration': '2%'})[0],
            'zinc': ActiveIngredient.objects.get_or_create(slug='zinc-gluconate', defaults={'name_ar': 'غلوكونات الزنك', 'name_en': 'Zinc Gluconate', 'category': 'mineral', 'use_time': 'both', 'concentration': '1%'})[0],
            'centella': ActiveIngredient.objects.get_or_create(slug='centella-asiatica', defaults={'name_ar': 'سينتيلا آسياتيكا (سيكا)', 'name_en': 'Centella Asiatica', 'category': 'botanical', 'use_time': 'both', 'concentration': '5%'})[0],
            'urea': ActiveIngredient.objects.get_or_create(slug='urea-ceramide', defaults={'name_ar': 'يوريا وسيراميد', 'name_en': 'Urea & Ceramides', 'category': 'ceramide', 'use_time': 'both', 'concentration': '10%'})[0],
        }

        # 3. Setup Cloudinary
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'aeildie1')
        api_key = os.environ.get('CLOUDINARY_API_KEY', '477871866486762')
        api_secret = os.environ.get('CLOUDINARY_API_SECRET', '')
        cloudinary_enabled = bool(cloud_name and api_key and api_secret)

        if cloudinary_enabled:
            import cloudinary
            import cloudinary.uploader
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )
            self.stdout.write(self.style.SUCCESS(f"[OK] Cloudinary connected successfully (Cloud: {cloud_name})"))
        else:
            self.stdout.write(self.style.WARNING("[WARN] Cloudinary secret not available; images will be linked locally."))

        # 4. Detailed Product Metadata Dictionary mapped by SKU
        product_metadata = {
            'DEMO-NN-TRESIBA-100U': {
                'name_ar': 'قلم حقن تريسيبا فليكس تاتش 100 وحدة/مل (5 أقلام × 3 مل)',
                'brand': 'Novo Nordisk',
                'volume_ml': '5 × 3ml',
                'badge': 'featured',
                'price_yer': Decimal('48000'),
                'price_sar': Decimal('220.00'),
                'price_usd': Decimal('58.00'),
                'discount_percent': 5,
                'stock_quantity': 35,
                'routine_step': 6,
                'use_time': 'evening',
                'hydration_level': 40,
                'exfoliation_power': 0,
                'sensitivity_safety': 95,
                'absorption_speed': 90,
                'texture': 'liquid',
                'dosage': 'pump_1',
                'skin_state_before': 'dry',
                'wait_seconds': 30,
                'short_description': 'أقلام جاهزة للحقن تحت الجلد للاستخدام الفردي الموجه، محفوظة في درجة حرارة مبردة وتخزين دوائي معتمد.',
                'full_description': 'مستحضر دوائي عالي الدقة يتميز بقلم FlexTouch سهل الاستخدام. يخضع لمعايير الجودة الصيدلانية السريرية المعتمدة عالمياً.',
                'package_color': '#3b82f6',
                'safe_pregnancy': False,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'يُحفظ مبرداً بين 2-8 درجات مئوية. لا يُجمد ويُحمى من الضوء المباشر.',
                'skin_types': ['normal'],
                'concerns': ['hair_care'],
                'ingredients': [],
            },
            'DEMO-BDM-SEBIUM-GEL-500': {
                'name_ar': 'بيوديرما سيبيوم جل ميسيلار منظف رغوي منقي 500 مل',
                'brand': 'Bioderma',
                'volume_ml': '500ml',
                'badge': 'bestseller',
                'price_yer': Decimal('16500'),
                'price_sar': Decimal('75.00'),
                'price_usd': Decimal('19.90'),
                'discount_percent': 10,
                'stock_quantity': 80,
                'routine_step': 1,
                'use_time': 'both',
                'hydration_level': 70,
                'exfoliation_power': 20,
                'sensitivity_safety': 90,
                'absorption_speed': 85,
                'texture': 'gel',
                'dosage': 'pump_1',
                'skin_state_before': 'wet',
                'wait_seconds': 60,
                'short_description': 'غسول رغوي لطيف ينظف البشرة الدهنية والمختلطة بعمق دون تجفيف، يحد من الإفرازات الدهنية الزائدة ويمنع انسداد المسام.',
                'full_description': 'تركيبة صيدلانية متطورة ببراءة اختراع Fluidactiv الحصرية من بيوديرما مع غلوكونات الزنك وكبريتات النحاس لتنقية البشرة والحفاظ على توازن حاجزها الطبيعي.',
                'package_color': '#0284c7',
                'safe_pregnancy': True,
                'fragrance_free': False,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'يُشطف جيداً بالماء الفاتر ويُجفف بلطف بمنشفة قطنية نظيفة.',
                'skin_types': ['oily', 'combination'],
                'concerns': ['acne', 'redness'],
                'ingredients': ['zinc'],
            },
            'DEMO-BB-ALOE-SHAMP-330': {
                'name_ar': 'بايوبالانس شامبو خلاصة الصبار العضوي المرطب للشعر والفروة 330 مل',
                'brand': 'Bio Balance',
                'volume_ml': '330ml',
                'badge': 'new',
                'price_yer': Decimal('9500'),
                'price_sar': Decimal('42.00'),
                'price_usd': Decimal('11.50'),
                'discount_percent': 0,
                'stock_quantity': 60,
                'routine_step': 1,
                'use_time': 'both',
                'hydration_level': 85,
                'exfoliation_power': 0,
                'sensitivity_safety': 95,
                'absorption_speed': 80,
                'texture': 'foam',
                'dosage': 'coin',
                'skin_state_before': 'wet',
                'wait_seconds': 120,
                'short_description': 'شامبو عضوي ملطف معزز بعصير أوراق الصبار الطبيعية وبروفيتامين B5 لتغذية الشعر الجاف وتهدئة الفروة المتهيجة.',
                'full_description': 'تركيبة نظيفة خالية من الكبريتات والبارابين، غنية بالصبار العضوي لتنظيف الفروة بلطف واستعادة مرونة الخصلات مع حماية حاجز الترطيب الطبيعي.',
                'package_color': '#16a34a',
                'safe_pregnancy': True,
                'fragrance_free': False,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'تجنب ملامسة العينين مباشرة، واشطف بالماء فوراً في حال اللمس.',
                'skin_types': ['dry', 'sensitive', 'normal'],
                'concerns': ['hair_care', 'dehydration'],
                'ingredients': ['b5'],
            },
            'DEMO-BB-PEEL-SERUM-30': {
                'name_ar': 'بايوبالانس سوبر سيروم التقشير العميق AHA 10% + BHA 2% 30 مل',
                'brand': 'Bio Balance',
                'volume_ml': '30ml',
                'badge': 'bestseller',
                'price_yer': Decimal('14500'),
                'price_sar': Decimal('64.00'),
                'price_usd': Decimal('17.00'),
                'discount_percent': 15,
                'stock_quantity': 45,
                'routine_step': 3,
                'use_time': 'evening',
                'hydration_level': 60,
                'exfoliation_power': 90,
                'sensitivity_safety': 75,
                'absorption_speed': 90,
                'texture': 'serum',
                'dosage': 'drops_3',
                'skin_state_before': 'dry',
                'wait_seconds': 600,
                'short_description': 'محلول تقشير كيميائي مركز يجمع بين أحماض ألفا وبيتا هيدروكسي مع الطحالب الحمراء لإزالة خلايا الجلد الميتة وتوحيد لون البشرة.',
                'full_description': 'سيروم عالي الفاعلية مصمم لعلاج التصبغات وتجديد سطح البشرة. يحتوي على 10% AHA لتفتيح السطح و2% حمض الساليسيليك BHA لتنظيف عمق المسام والحد من الرؤوس السوداء.',
                'package_color': '#991b1b',
                'safe_pregnancy': False,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': True,
                'safety_warning': 'يُستخدم مساءً فقط بحد أقصى مرتين أسبوعياً. يُغسل بعد 10 دقائق ويلزم استخدام واقي شمس صباحاً.',
                'skin_types': ['oily', 'combination', 'normal'],
                'concerns': ['pigmentation', 'acne', 'aging'],
                'ingredients': ['glycolic', 'salicylic'],
            },
            'DEMO-EUC-ROUGH-LOT-500': {
                'name_ar': 'يوسيرين لوشن رافنس ريليف لتنعيم الخشونة باليوريا والسيراميد 500 مل',
                'brand': 'Eucerin',
                'volume_ml': '500ml',
                'badge': 'featured',
                'price_yer': Decimal('22000'),
                'price_sar': Decimal('98.00'),
                'price_usd': Decimal('26.00'),
                'discount_percent': 10,
                'stock_quantity': 70,
                'routine_step': 4,
                'use_time': 'both',
                'hydration_level': 95,
                'exfoliation_power': 35,
                'sensitivity_safety': 90,
                'absorption_speed': 80,
                'texture': 'lotion',
                'dosage': 'pump_2',
                'skin_state_before': 'damp',
                'wait_seconds': 60,
                'short_description': 'لوشن صيدلاني غني باليوريا وعوامل الترطيب الطبيعية والسيراميد لتقشير وترطيب البشرة شديدة الجفاف والمتقشرة والجلد الخشن.',
                'full_description': 'تركيبة مثبتة سريرياً خالية من العطور توفر ترطيباً عميقاً يدوم 48 ساعة. تقضي بفعالية على ملمس جلد الدجاجة (Keratosis Pilaris) وتستعيد نعومة ومرونة الجلد.',
                'package_color': '#b91c1c',
                'safe_pregnancy': True,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': True,
                'safety_warning': 'يحتوي على أحماض ألفا هيدروكسي التي قد تزيد حساسية البشرة للشمس. استخدم واقي شمس مناسب.',
                'skin_types': ['dry', 'sensitive', 'normal'],
                'concerns': ['dehydration', 'redness', 'stretch_marks'],
                'ingredients': ['urea'],
            },
            'DEMO-ORD-NMF-INULIN-240': {
                'name_ar': 'ذا اورديناري لوشن عوامل الترطيب الطبيعية والإنولين للجسم 240 مل',
                'brand': 'The Ordinary',
                'volume_ml': '240ml',
                'badge': 'new',
                'price_yer': Decimal('17500'),
                'price_sar': Decimal('78.00'),
                'price_usd': Decimal('21.00'),
                'discount_percent': 0,
                'stock_quantity': 55,
                'routine_step': 4,
                'use_time': 'both',
                'hydration_level': 90,
                'exfoliation_power': 0,
                'sensitivity_safety': 98,
                'absorption_speed': 90,
                'texture': 'lotion',
                'dosage': 'pump_2',
                'skin_state_before': 'damp',
                'wait_seconds': 45,
                'short_description': 'مستحلب خفيف للجسم يعزز الترطيب الفوري ويغذي الميكروبيوم بفضل البريبايوتك والإنولين والأحماض الأمينية الحيوية.',
                'full_description': 'تركيبة سطحية متطورة بدون ملمس دهني، تحاكي حاجز الترطيب الطبيعي للجلد وتمنع فقدان الماء عبر البشرة (TEWL) مع المحافظة على النعومة طوال اليوم.',
                'package_color': '#64748b',
                'safe_pregnancy': True,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'مناسب للاستخدام اليومي صباحاً ومساءً لكامل الجسم.',
                'skin_types': ['dry', 'sensitive', 'normal', 'combination'],
                'concerns': ['dehydration'],
                'ingredients': ['hyaluronic'],
            },
            'DEMO-BB-STRETCH-MARK-60': {
                'name_ar': 'بايوبالانس كريم علاج ومقاومة علامات التمدد بالسنتيلا آسياتيكا 60 مل',
                'brand': 'Bio Balance',
                'volume_ml': '60ml',
                'badge': 'featured',
                'price_yer': Decimal('13500'),
                'price_sar': Decimal('58.00'),
                'price_usd': Decimal('15.50'),
                'discount_percent': 10,
                'stock_quantity': 50,
                'routine_step': 4,
                'use_time': 'both',
                'hydration_level': 85,
                'exfoliation_power': 10,
                'sensitivity_safety': 95,
                'absorption_speed': 85,
                'texture': 'cream',
                'dosage': 'coin',
                'skin_state_before': 'damp',
                'wait_seconds': 60,
                'short_description': 'مركب متقدم غني بمستخلص نبتة السيكا وحمض الروزمارينيك لتعزيز مرونة الجلد والحد من ظهور الخطوط البيضاء والحمراء.',
                'full_description': 'كريم علاجي مخصص لمنع وتخفيف علامات التمدد أثناء الحمل أو التغير السريع في الوزن. يدعم إنتاج الكولاجين والإيلاستين في طبقات الأدمة.',
                'package_color': '#0284c7',
                'safe_pregnancy': True,
                'fragrance_free': False,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'يُدلك بحركات دائرية لمدة 2-3 دقائق حتى تمام الامتصاص مرتين يومياً.',
                'skin_types': ['dry', 'normal', 'sensitive'],
                'concerns': ['stretch_marks', 'dehydration'],
                'ingredients': ['centella'],
            },
            'DEMO-BB-DERMASEB-GEL-250': {
                'name_ar': 'بايوبالانس ديرماسيبوم جل غسول منقي للبشرة الدهنية والمعرضة للحبوب 250 مل',
                'brand': 'Bio Balance',
                'volume_ml': '250ml',
                'badge': 'bestseller',
                'price_yer': Decimal('12000'),
                'price_sar': Decimal('52.00'),
                'price_usd': Decimal('14.00'),
                'discount_percent': 10,
                'stock_quantity': 90,
                'routine_step': 1,
                'use_time': 'both',
                'hydration_level': 65,
                'exfoliation_power': 25,
                'sensitivity_safety': 92,
                'absorption_speed': 90,
                'texture': 'gel',
                'dosage': 'pump_1',
                'skin_state_before': 'wet',
                'wait_seconds': 60,
                'short_description': 'غسول علاجي خالٍ من الكبريتات والزيوت والصابون، ينظف المسام بعمق ويزيل اللمعان ويحارب تكوّن الرؤوس السوداء.',
                'full_description': 'بفضل تركيبته الغنية بمستخلصات النعناع والزنك وأحماض الفواكه الطبيعية، يعمل ديرماسيبوم على تهدئة التهابات الحبوب وتنظيم الإفرازات الدهنية دون تجفيف أو شد للبشرة.',
                'package_color': '#0284c7',
                'safe_pregnancy': True,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'يُدلك بلطف على وجه رطب ثم يُشطف جيداً.',
                'skin_types': ['oily', 'combination'],
                'concerns': ['acne', 'redness'],
                'ingredients': ['zinc', 'salicylic'],
            },
            'DEMO-BB-BRIGHT-EYE-15': {
                'name_ar': 'بايوبالانس كريم تفتيح الهالات السوداء ومحيط العين بالببتيدات وفيتامين C 15 مل',
                'brand': 'Bio Balance',
                'volume_ml': '15ml',
                'badge': 'featured',
                'price_yer': Decimal('11500'),
                'price_sar': Decimal('49.00'),
                'price_usd': Decimal('13.50'),
                'discount_percent': 0,
                'stock_quantity': 65,
                'routine_step': 3,
                'use_time': 'both',
                'hydration_level': 85,
                'exfoliation_power': 0,
                'sensitivity_safety': 96,
                'absorption_speed': 90,
                'texture': 'cream',
                'dosage': 'rice',
                'skin_state_before': 'dry',
                'wait_seconds': 45,
                'short_description': 'كريم علاجي متطور لمنطقة تحت العين مدعم بمركب الببتيدات الرباعية وفيتامين C لتفتيح الهالات وتقليل الانتفاخات.',
                'full_description': 'تركيبة صيدلانية معتمدة سريرياً تعمل على تنشيط الدورة الدموية الدقيقة حول العين وتقوية الأوعية الشعرية لمنع تراكم الصبغات الداكنة واستعادة نضارة النظرة.',
                'package_color': '#f59e0b',
                'safe_pregnancy': True,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': True,
                'safety_warning': 'يُربت برفق بأطراف الأصابع على عظمة مدار العين دون ملامسة داخل العين.',
                'skin_types': ['sensitive', 'dry', 'normal', 'combination'],
                'concerns': ['dark_circles', 'aging'],
                'ingredients': [],
            },
            'DEMO-BDM-ATODERM-500': {
                'name_ar': 'بيوديرما أتوديرم كريم ألترا فائق الترطيب والتغذية للبشرة الجافة 500 مل',
                'brand': 'Bioderma',
                'volume_ml': '500ml',
                'badge': 'bestseller',
                'price_yer': Decimal('19500'),
                'price_sar': Decimal('88.00'),
                'price_usd': Decimal('23.50'),
                'discount_percent': 10,
                'stock_quantity': 85,
                'routine_step': 4,
                'use_time': 'both',
                'hydration_level': 98,
                'exfoliation_power': 0,
                'sensitivity_safety': 99,
                'absorption_speed': 85,
                'texture': 'cream',
                'dosage': 'pump_1',
                'skin_state_before': 'damp',
                'wait_seconds': 45,
                'short_description': 'مرطب يومي فائق التغذية يعيد بناء الحاجز الجلدي ويوفر ترطيباً عميقاً يدوم 24 ساعة لجميع أفراد الأسرة.',
                'full_description': 'يحتوي على مركب Skin Protect المبتكر الذي يحفز إفراز حمض الهيالورونيك الطبيعي في الجلد ويوفر النياسيناميد والأوميغا 3 و6 لترميم الراحة الجلدية فوراً.',
                'package_color': '#0284c7',
                'safe_pregnancy': True,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'يوضع على بشرة نظيفة ورطبة قليلاً بعد الاستحمام لأقصى فاعلية.',
                'skin_types': ['dry', 'sensitive', 'normal'],
                'concerns': ['dehydration', 'redness'],
                'ingredients': ['hyaluronic'],
            },
            'DEMO-BB-POM-SHAMP-330': {
                'name_ar': 'بايوبالانس شامبو الرمان العضوي لحماية لون الشعر وفلاتر الأشعة فوق البنفسجية 330 مل',
                'brand': 'Bio Balance',
                'volume_ml': '330ml',
                'badge': 'new',
                'price_yer': Decimal('9800'),
                'price_sar': Decimal('43.00'),
                'price_usd': Decimal('11.80'),
                'discount_percent': 0,
                'stock_quantity': 50,
                'routine_step': 1,
                'use_time': 'both',
                'hydration_level': 80,
                'exfoliation_power': 0,
                'sensitivity_safety': 94,
                'absorption_speed': 85,
                'texture': 'foam',
                'dosage': 'coin',
                'skin_state_before': 'wet',
                'wait_seconds': 120,
                'short_description': 'شامبو خالٍ من الكبريتات غني بمستخلص الرمان العضوي والكيراتين النباتي لحماية الشعر المصبوغ من البهتان وأشعة الشمس.',
                'full_description': 'يوفر حماية مضادة للأكسدة تمنع تلف ألياف الشعر الناتج عن الحرارة والصبغات، مع الحفاظ على لمعان غني يدوم طويلاً وفروة رأس صحية متوازنة.',
                'package_color': '#be123c',
                'safe_pregnancy': True,
                'fragrance_free': False,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'يُشطف جيداً بالماء الفاتر.',
                'skin_types': ['normal', 'dry'],
                'concerns': ['hair_care'],
                'ingredients': [],
            },
            'DEMO-BB-RETINOL-30': {
                'name_ar': 'بايوبالانس سوبر سيروم ريتينول نقي 0.3% مع فيتامين E 2% لتجديد البشرة 30 مل',
                'brand': 'Bio Balance',
                'volume_ml': '30ml',
                'badge': 'featured',
                'price_yer': Decimal('15500'),
                'price_sar': Decimal('69.00'),
                'price_usd': Decimal('18.50'),
                'discount_percent': 10,
                'stock_quantity': 60,
                'routine_step': 3,
                'use_time': 'evening',
                'hydration_level': 70,
                'exfoliation_power': 65,
                'sensitivity_safety': 82,
                'absorption_speed': 90,
                'texture': 'serum',
                'dosage': 'drops_3',
                'skin_state_before': 'dry',
                'wait_seconds': 180,
                'short_description': 'سيروم ريتينول مركز معزز بفيتامين E لتحفيز إنتاج الكولاجين ومكافحة التجاعيد العميقة وتوحيد ملمس البشرة.',
                'full_description': 'تركيبة ليلية عالية النقاء تعمل على تجديد خلايا البشرة أثناء النوم، تخفف الخطوط التعبيرية وتشد المسام، مع فيتامين E المضاد للأكسدة لمنع التهيج.',
                'package_color': '#b45309',
                'safe_pregnancy': False,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': True,
                'safety_warning': 'يُستخدم ليلاً فقط مع التدرج أسبوعياً (ليلة واحدة أول أسبوع، ليلتان ثاني أسبوع). إلزامي استخدام واقي شمس نهاراً.',
                'skin_types': ['normal', 'combination', 'oily'],
                'concerns': ['aging', 'pigmentation'],
                'ingredients': ['retinol'],
            },
            'DEMO-OMB-HYALURONIC-60': {
                'name_ar': 'أومبريس سيروم حمض الهيالورونيك 2% مع فيتامين B5 فائق الترطيب 60 مل',
                'brand': 'Ombrace',
                'volume_ml': '60ml',
                'badge': 'bestseller',
                'price_yer': Decimal('13500'),
                'price_sar': Decimal('59.00'),
                'price_usd': Decimal('16.00'),
                'discount_percent': 0,
                'stock_quantity': 75,
                'routine_step': 3,
                'use_time': 'both',
                'hydration_level': 98,
                'exfoliation_power': 0,
                'sensitivity_safety': 99,
                'absorption_speed': 95,
                'texture': 'serum',
                'dosage': 'drops_3',
                'skin_state_before': 'damp',
                'wait_seconds': 45,
                'short_description': 'تركيبة ترطيب نباتية فائقة النقاء متعددة الأوزان الجزيئية لترطيب طبقات الجلد العميقة وملء الخطوط الدقيقة فورا.',
                'full_description': 'يجمع بين 3 أوزان جزيئية لحمض الهيالورونيك مع فيتامين B5 المرمم لخلق شبكة ترطيب ثلاثية الأبعاد على سطح البشرة وفي عمقها دون أي ملمس لزج.',
                'package_color': '#0284c7',
                'safe_pregnancy': True,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'يُطبق دائماً على بشرة رطبة خفيفة ويُتبع فوراً بكريم مرطب لحبس الرطوبة.',
                'skin_types': ['dry', 'sensitive', 'combination', 'oily', 'normal'],
                'concerns': ['dehydration', 'aging', 'redness'],
                'ingredients': ['hyaluronic', 'b5'],
            },
            'DEMO-BDM-SEB-HYDRA-40': {
                'name_ar': 'بيوديرما سيبيوم هيدرا كريم الترطيب المعوض المهدئ للبشرة المعالجة 40 مل',
                'brand': 'Bioderma',
                'volume_ml': '40ml',
                'badge': 'bestseller',
                'price_yer': Decimal('16000'),
                'price_sar': Decimal('72.00'),
                'price_usd': Decimal('19.00'),
                'discount_percent': 10,
                'stock_quantity': 65,
                'routine_step': 4,
                'use_time': 'both',
                'hydration_level': 92,
                'exfoliation_power': 0,
                'sensitivity_safety': 96,
                'absorption_speed': 85,
                'texture': 'cream',
                'dosage': 'pea',
                'skin_state_before': 'dry',
                'wait_seconds': 45,
                'short_description': 'مرطب علاجي صيدلاني مهدئ مصمم خصيصاً لتعويض الجفاف الشديد والتقشر الناتج عن علاجات حب الشباب والريتينويدات.',
                'full_description': 'يحتوي على السيراميد المجدد والإنوكسولون المهدئ مع براءة اختراع Fluidactiv لمنع تكوّن الحبوب مجدداً مع توفير راحة فورية تدوم طوال اليوم.',
                'package_color': '#16a34a',
                'safe_pregnancy': True,
                'fragrance_free': False,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'يوضع صباحاً ومساءً على بشرة نظيفة وجافة تماماً بعد السيروم العلاجي.',
                'skin_types': ['oily', 'combination', 'sensitive'],
                'concerns': ['acne', 'redness', 'dehydration'],
                'ingredients': [],
            },
            'DEMO-BB-SUN-SPF50-75': {
                'name_ar': 'بايوبالانس واقي شمس للوجه SPF 50+ حماية واسعة النطاق مقاوم للماء 75 مل',
                'brand': 'Bio Balance',
                'volume_ml': '75ml',
                'badge': 'bestseller',
                'price_yer': Decimal('14000'),
                'price_sar': Decimal('62.00'),
                'price_usd': Decimal('16.50'),
                'discount_percent': 15,
                'stock_quantity': 100,
                'routine_step': 5,
                'use_time': 'morning',
                'hydration_level': 75,
                'exfoliation_power': 0,
                'sensitivity_safety': 95,
                'absorption_speed': 90,
                'texture': 'cream',
                'dosage': 'two_fingers',
                'skin_state_before': 'dry',
                'wait_seconds': 120,
                'short_description': 'حماية قصوى واسعة النطاق من الأشعة فوق البنفسجية UVA و UVB مع فلاتر ضوئية ثابتة ومقاومة للماء والتعرق.',
                'full_description': 'واقي شمس سريري لا يترك أثراً أبيض، غني بمضادات الأكسدة لمنع التصبغات والتجاعيد الناتجة عن الشمس. مناسب كأساس مثالي تحت المكياج.',
                'package_color': '#ea580c',
                'safe_pregnancy': True,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'يُوضع بمقدار إصبعين كاملين قبل التعرض للشمس بـ 20 دقيقة، ويُجدد كل ساعتين.',
                'skin_types': ['oily', 'combination', 'dry', 'sensitive', 'normal'],
                'concerns': ['pigmentation', 'aging'],
                'ingredients': [],
            },
            'DEMO-BB-DERMASOOTHE-55': {
                'name_ar': 'بايوبالانس ديرماسوث كريم مهدئ ومرطب للبشرة الحساسة والمحمرة 55 مل',
                'brand': 'Bio Balance',
                'volume_ml': '55ml',
                'badge': 'featured',
                'price_yer': Decimal('13000'),
                'price_sar': Decimal('56.00'),
                'price_usd': Decimal('15.00'),
                'discount_percent': 5,
                'stock_quantity': 55,
                'routine_step': 4,
                'use_time': 'both',
                'hydration_level': 88,
                'exfoliation_power': 0,
                'sensitivity_safety': 99,
                'absorption_speed': 85,
                'texture': 'cream',
                'dosage': 'pea',
                'skin_state_before': 'damp',
                'wait_seconds': 45,
                'short_description': 'مرطب خفيف خالٍ من الزيوت غني بالأحماض الأمينية المهدئة ومستخلصات زهور البابونج لتخفيف الاحمرار وتهدئة حروق الشمس.',
                'full_description': 'مصمم خصيصاً للبشرة الحساسة المعرضة للوردية والاحمرار المفاجئ. يساعد في تهدئة حكة الجلد وتوحيد لون البشرة واستعادة مرونة الحاجز الواقي.',
                'package_color': '#84cc16',
                'safe_pregnancy': True,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'يُوضع بلطف دون فرك شديد صباحاً ومساءً.',
                'skin_types': ['sensitive', 'dry', 'combination'],
                'concerns': ['redness', 'dehydration'],
                'ingredients': [],
            },
            'DEMO-BDM-SEB-SENS-30': {
                'name_ar': 'بيوديرما سيبيوم سينسيتيف لعلاج الحبوب الملتهبة وتهدئة الاحمرار 30 مل',
                'brand': 'Bioderma',
                'volume_ml': '30ml',
                'badge': 'featured',
                'price_yer': Decimal('15500'),
                'price_sar': Decimal('68.00'),
                'price_usd': Decimal('18.00'),
                'discount_percent': 10,
                'stock_quantity': 60,
                'routine_step': 3,
                'use_time': 'both',
                'hydration_level': 80,
                'exfoliation_power': 15,
                'sensitivity_safety': 97,
                'absorption_speed': 90,
                'texture': 'lotion',
                'dosage': 'pea',
                'skin_state_before': 'dry',
                'wait_seconds': 45,
                'short_description': 'علاج سريري مهدئ للحبوب الملتهبة للبشرة الحساسة المعرضة للشوائب مع تقنية InflaStop الثورية.',
                'full_description': 'يهدئ الاحمرار والتهيج فوراً ويقضي على البثور دون تجفيف الجلد، بفضل الزنك والباكوتشيول المنظم للإفرازات الدهنية.',
                'package_color': '#16a34a',
                'safe_pregnancy': True,
                'fragrance_free': False,
                'non_comedogenic': True,
                'requires_sunscreen': True,
                'safety_warning': 'يُطبق على كامل الوجه بعد التنظيف بغسول سيبيوم.',
                'skin_types': ['oily', 'combination', 'sensitive'],
                'concerns': ['acne', 'redness'],
                'ingredients': ['zinc'],
            },
            'DEMO-BDM-SEB-HYDRA-BOX-40': {
                'name_ar': 'بيوديرما سيبيوم هيدرا 48 ساعة ترطيب مكثف معوض للجفاف (إصدار العبوة الخاصة) 40 مل',
                'brand': 'Bioderma',
                'volume_ml': '40ml',
                'badge': 'new',
                'price_yer': Decimal('16500'),
                'price_sar': Decimal('74.00'),
                'price_usd': Decimal('19.50'),
                'discount_percent': 0,
                'stock_quantity': 40,
                'routine_step': 4,
                'use_time': 'both',
                'hydration_level': 94,
                'exfoliation_power': 0,
                'sensitivity_safety': 97,
                'absorption_speed': 85,
                'texture': 'cream',
                'dosage': 'pea',
                'skin_state_before': 'dry',
                'wait_seconds': 45,
                'short_description': 'إصدار صيدلاني مدعم بتقنية Restores Skin Comfort لراحة تدوم 48 ساعة للبشرة المعالجة بحبوب الروكتان وعلاجات التقشير.',
                'full_description': 'يقلل من الشعور بالشد والحكة بنسبة 93% بفضل السيراميدات الحيوية والجلسرين الطبي المنقى، مما يجعله خط الدفاع الأساسي ضد الجفاف الناتج عن العلاجات القوية.',
                'package_color': '#059669',
                'safe_pregnancy': True,
                'fragrance_free': False,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'مناسب كأساس قبل تطبيق واقي الشمس أو المكياج.',
                'skin_types': ['oily', 'combination', 'sensitive'],
                'concerns': ['acne', 'redness', 'dehydration'],
                'ingredients': [],
            },
            'DEMO-BB-DERMASEB-DUO-200': {
                'name_ar': 'بايوبالانس مجموعة غسول ديرماسيبوم المنظف الثنائية للبشرة الدهنية 200 مل',
                'brand': 'Bio Balance',
                'volume_ml': '200ml',
                'badge': 'sale',
                'price_yer': Decimal('18000'),
                'price_sar': Decimal('79.00'),
                'price_usd': Decimal('21.00'),
                'discount_percent': 20,
                'stock_quantity': 30,
                'routine_step': 1,
                'use_time': 'both',
                'hydration_level': 65,
                'exfoliation_power': 20,
                'sensitivity_safety': 92,
                'absorption_speed': 90,
                'texture': 'gel',
                'dosage': 'pump_1',
                'skin_state_before': 'wet',
                'wait_seconds': 60,
                'short_description': 'عرض خاص يحتوي على عبوة ديرماسيبوم مع عبوة سفر إضافية لتنظيم الدهون ومنع انسداد المسام طوال اليوم.',
                'full_description': 'توفير استثنائي للروتين اليومي المنظم للإفرازات الدهنية، مدعم بمركب الزنك وجذور الأرقطيون المنقية.',
                'package_color': '#0284c7',
                'safe_pregnancy': True,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': False,
                'safety_warning': 'يُستخدم مرتين يومياً صباحاً ومساءً.',
                'skin_types': ['oily', 'combination'],
                'concerns': ['acne', 'redness'],
                'ingredients': ['zinc'],
            },
            'DEMO-ORD-GLYCOLIC-240': {
                'name_ar': 'ذا اورديناري تونر حمض الجليكوليك 7% لتجديد وتوحيد لون البشرة 240 مل',
                'brand': 'The Ordinary',
                'volume_ml': '240ml',
                'badge': 'bestseller',
                'price_yer': Decimal('19000'),
                'price_sar': Decimal('84.00'),
                'price_usd': Decimal('22.50'),
                'discount_percent': 10,
                'stock_quantity': 75,
                'routine_step': 2,
                'use_time': 'evening',
                'hydration_level': 70,
                'exfoliation_power': 80,
                'sensitivity_safety': 82,
                'absorption_speed': 95,
                'texture': 'mist',
                'dosage': 'drops_3',
                'skin_state_before': 'dry',
                'wait_seconds': 60,
                'short_description': 'تونر تقشير خفيف بحمض الجليكوليك AHA مع جذور الجينسنغ وصبار الألوفيرا لتفتيح البشرة وتنعيم ملمسها بفعالية ملحوظة.',
                'full_description': 'يقشر الطبقة السطحية من الجلد بلطف، مما يعزز الإشراقة ويقلل من بهتان البشرة وعدم تجانس لونها. يحتوي على فلفل تسمانيا المهدئ لتقليل التهيج المرتبط باستخدام الأحماض.',
                'package_color': '#f59e0b',
                'safe_pregnancy': True,
                'fragrance_free': True,
                'non_comedogenic': True,
                'requires_sunscreen': True,
                'safety_warning': 'يُستخدم مساءً فقط بواسطة قطعة قطن. لا يُستخدم على بشرة مقشرة أو متهيجة. إلزامي استخدام واقي شمس نهاراً.',
                'skin_types': ['combination', 'oily', 'normal'],
                'concerns': ['pigmentation', 'aging'],
                'ingredients': ['glycolic'],
            },
        }

        # 5. Process Manifest and Create Products
        self.stdout.write("3. Processing images and seeding products...")
        created_count = 0
        updated_count = 0
        failed_uploads = []

        with open(manifest_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = row['original_filename'].strip()
                sku = row['final_product_sku'].strip()
                meta = product_metadata.get(sku, {})

                img_path = image_dir / filename
                if not img_path.exists():
                    self.stdout.write(self.style.WARNING(f"⚠️ Image file not found: {filename}"))
                    continue

                # Prepare Product Data
                name = meta.get('name_ar', row['suggested_product_name'])
                brand = meta.get('brand', row['suggested_brand'])
                slug = slugify(f"{brand}-{sku}", allow_unicode=True)

                product, created = Product.objects.get_or_create(
                    sku=sku,
                    defaults={
                        'name': name,
                        'brand': brand,
                        'slug': slug,
                        'original_filename': filename,
                        'is_demo': True,
                        'volume_ml': meta.get('volume_ml', '50ml'),
                        'badge': meta.get('badge', ''),
                        'price_yer': meta.get('price_yer', Decimal('12000')),
                        'price_sar': meta.get('price_sar', Decimal('50.00')),
                        'price_usd': meta.get('price_usd', Decimal('15.00')),
                        'discount_percent': meta.get('discount_percent', 0),
                        'stock_quantity': meta.get('stock_quantity', 50),
                        'is_available': True,
                        'routine_step': meta.get('routine_step', 3),
                        'use_time': meta.get('use_time', 'both'),
                        'hydration_level': meta.get('hydration_level', 70),
                        'exfoliation_power': meta.get('exfoliation_power', 0),
                        'sensitivity_safety': meta.get('sensitivity_safety', 85),
                        'absorption_speed': meta.get('absorption_speed', 85),
                        'texture': meta.get('texture', 'cream'),
                        'dosage': meta.get('dosage', 'pea'),
                        'skin_state_before': meta.get('skin_state_before', 'damp'),
                        'wait_seconds': meta.get('wait_seconds', 60),
                        'short_description': meta.get('short_description', ''),
                        'full_description': meta.get('full_description', ''),
                        'package_color': meta.get('package_color', '#2a5741'),
                        'safe_pregnancy': meta.get('safe_pregnancy', True),
                        'fragrance_free': meta.get('fragrance_free', True),
                        'non_comedogenic': meta.get('non_comedogenic', True),
                        'requires_sunscreen': meta.get('requires_sunscreen', False),
                        'safety_warning': meta.get('safety_warning', ''),
                    }
                )

                # Cloudinary Upload
                if cloudinary_enabled and (not product.cloudinary_public_id or created):
                    try:
                        self.stdout.write(f"   [Cloudinary] Uploading {filename} (folder: medical_store/products/)...")
                        with open(img_path, 'rb') as img_fh:
                            upload_res = cloudinary.uploader.upload(
                                img_fh,
                                folder='medical_store/products',
                                resource_type='image',
                                public_id=f"prod_{sku.lower().replace('-', '_')}",
                                overwrite=True,
                                transformation=[
                                    {'quality': 'auto', 'fetch_format': 'auto'}
                                ]
                            )
                            product.cloudinary_public_id = upload_res.get('public_id', '')
                            product.cloudinary_url = upload_res.get('secure_url', '')
                            product.save(update_fields=['cloudinary_public_id', 'cloudinary_url'])
                    except Exception as e:
                        failed_uploads.append((filename, str(e)))
                        self.stdout.write(self.style.WARNING(f"   [Cloudinary Error] upload failed for {filename}: {e}"))

                # Assign Relationships
                if meta.get('skin_types'):
                    for st_key in meta['skin_types']:
                        if st_key in skin_types:
                            product.skin_types.add(skin_types[st_key])
                if meta.get('concerns'):
                    for sc_key in meta['concerns']:
                        if sc_key in skin_concerns:
                            product.skin_concerns.add(skin_concerns[sc_key])
                if meta.get('ingredients'):
                    for ing_key in meta['ingredients']:
                        if ing_key in ingredients:
                            product.active_ingredients.add(ingredients[ing_key])

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"[OK] Products Processed: {created_count} created, {updated_count} existing/updated."))

        if failed_uploads:
            self.stdout.write(self.style.WARNING("[REPORT] Failed Cloudinary Uploads Report:"))
            for fname, err in failed_uploads:
                self.stdout.write(f"   - {fname}: {err}")

        # 6. Build Curated Routine Bundles using New Authentic Products
        self.stdout.write("4. Assembling Curated Clinical Bundles...")
        bundles_data = [
            {
                'name': 'باقة علاج حب الشباب وتنقية المسام المتقدمة',
                'description': 'روتين ثلاثي صيدلاني متكامل لعلاج البشرة الدهنية المعرضة للحبوب وتخفيف الاحمرار.',
                'skus': ['DEMO-BDM-SEBIUM-GEL-500', 'DEMO-BDM-SEB-SENS-30', 'DEMO-BB-SUN-SPF50-75'],
                'discount_percent': 15,
                'concern': skin_concerns['acne']
            },
            {
                'name': 'باقة ترميم الحاجز والترطيب الفائق للبشرة الجافة والحساسة',
                'description': 'عناية سريرية مكثفة تعوض جفاف الجلد الشديد وتهدئ الاحمرار والتهيج فوراً.',
                'skus': ['DEMO-BDM-ATODERM-500', 'DEMO-OMB-HYALURONIC-60', 'DEMO-BB-DERMASOOTHE-55'],
                'discount_percent': 20,
                'concern': skin_concerns['dehydration']
            },
            {
                'name': 'باقة التجديد والتقشير الليلي لمكافحة التجاعيد والتصبغات',
                'description': 'برنامج تدوير جلدي لروتين ليلي فاعل يجمع بين الريتينول الصيدلاني وتونر الجليكوليك.',
                'skus': ['DEMO-ORD-GLYCOLIC-240', 'DEMO-BB-RETINOL-30', 'DEMO-BB-SUN-SPF50-75'],
                'discount_percent': 18,
                'concern': skin_concerns['aging']
            },
            {
                'name': 'باقة العناية الشاملة بالجسم والخطوط التعبيرية',
                'description': 'مزيج فاخر من لوشن اليوسيرين بالسيراميد وكريم علاج علامات التمدد بالسيكا.',
                'skus': ['DEMO-EUC-ROUGH-LOT-500', 'DEMO-BB-STRETCH-MARK-60', 'DEMO-ORD-NMF-INULIN-240'],
                'discount_percent': 15,
                'concern': skin_concerns['stretch_marks']
            }
        ]

        for b_data in bundles_data:
            bundle_slug = slugify(b_data['name'], allow_unicode=True)
            bundle, _ = RoutineBundle.objects.get_or_create(
                slug=bundle_slug,
                defaults={
                    'name': b_data['name'],
                    'description': b_data['description'],
                    'discount_percent': b_data['discount_percent'],
                    'skin_concern': b_data['concern'],
                    'is_active': True,
                }
            )
            bundle_prods = Product.objects.filter(sku__in=b_data['skus'])
            bundle.products.set(bundle_prods)

        # 7. Safe Demo Superuser Creation
        self.stdout.write("5. Verifying Demo Superuser...")
        User = get_user_model()
        su_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'mohammed')
        su_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '12345')

        if not User.objects.filter(username=su_username).exists():
            su = User.objects.create_superuser(
                username=su_username,
                email=f"{su_username}@remshy-dermacare.local",
                password=su_password
            )
            self.stdout.write(self.style.SUCCESS(f"[OK] Demo Superuser '{su_username}' created successfully!"))
            self.stdout.write(self.style.WARNING("[SECURITY WARNING]: Demo password '12345' is for development only. Change it immediately in production!"))
        else:
            self.stdout.write(f"[INFO] Superuser '{su_username}' already exists.")

        self.stdout.write(self.style.NOTICE("=" * 65))
        self.stdout.write(self.style.SUCCESS("[SUCCESS] DEMO STORE SEEDED SUCCESSFULLY WITH 20 AUTHENTIC PRODUCTS!"))
        self.stdout.write(self.style.NOTICE("=" * 65))
