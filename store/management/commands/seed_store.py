"""
seed_store — تعبئة قاعدة البيانات بكامل البيانات العلمية والتجارية.
التشغيل: python manage.py seed_store
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import (
    SkinType, SkinConcern, ActiveIngredient, IngredientConflict,
    IngredientSynergy, Product, RoutineBundle
)


class Command(BaseCommand):
    help = 'تعبئة قاعدة البيانات بكامل البيانات الحقيقية (16 منتج، 10 مواد فعالة، 5 أنواع بشرة، 8 مشاكل، 3 باقات)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('🗑️  مسح البيانات القديمة...'))
        RoutineBundle.objects.all().delete()
        Product.objects.all().delete()
        IngredientConflict.objects.all().delete()
        IngredientSynergy.objects.all().delete()
        ActiveIngredient.objects.all().delete()
        SkinConcern.objects.all().delete()
        SkinType.objects.all().delete()

        # ── 1. Skin Types ──────────────────────────────────────────────────
        self.stdout.write('💧 إنشاء أنواع البشرة...')
        skin_types = {}
        skin_type_data = [
            ('oily', 'البشرة الدهنية', '✨',
             'بشرة تفرز كميات زائدة من الزهم (السيبوم) بسبب فرط نشاط الغدد الدهنية، مما يمنحها مظهراً لامعاً.',
             'اللمعان طوال اليوم، تضخم المسام، ميل لحبوب البشرة والرؤوس السوداء، ملمس زلق.'),
            ('dry', 'البشرة الجافة', '💧',
             'بشرة تعاني من نقص في إنتاج الزهم وضعف في الحاجز الجلدي، مما يجعلها عاجزة عن الاحتفاظ بالرطوبة.',
             'ملمس خشن وضيق، تقشر ملحوظ، خطوط رقيقة مبكرة، إحساس بالشد بعد الغسيل.'),
            ('combination', 'البشرة المختلطة', '⚖️',
             'بشرة ذات طبيعة مزدوجة: دهنية في منطقة T (الجبين والأنف والذقن) وجافة أو عادية في منطقة U (الخدين).',
             'لمعان في الأنف والجبهة مع جفاف في الخدين، مسام واسعة في T-Zone، صعوبة في اختيار منتج واحد للوجه كله.'),
            ('sensitive', 'البشرة الحساسة', '🌸',
             'بشرة ذات حاجز وقائي ضعيف تستجيب بشكل مبالغ فيه للمنبهات الخارجية والمكونات الكيميائية.',
             'احمرار متكرر، حرقة وحكة عند تطبيق المنتجات، تفاعل مع العطور والكحول، ميل للوردية والإكزيما.'),
            ('normal', 'البشرة العادية', '🌿',
             'بشرة متوازنة تمتلك مستوى مثالياً من الترطيب والزهم مع حاجز جلدي صحي ومتين.',
             'ملمس ناعم ومرن، مسام صغيرة وغير واضحة، نادراً ما تعاني من مشاكل حادة، تستجيب جيداً لمعظم المنتجات.'),
        ]
        for slug, name, icon, desc, chars in skin_type_data:
            st = SkinType.objects.create(name=name, slug=slug, icon=icon, description=desc, characteristics=chars)
            skin_types[slug] = st
            self.stdout.write(f'  ✓ {icon} {name}')

        # ── 2. Skin Concerns ───────────────────────────────────────────────
        self.stdout.write('🔍 إنشاء مشاكل البشرة...')
        concerns = {}
        concern_data = [
            ('acne', 'حب الشباب والرؤوس البيضاء', '🫧', 't_zone',
             'التهاب مزمن يصيب حويصلات الشعر نتيجة انسدادها بالزهم والخلايا الميتة مع نمو بكتيريا Cutibacterium acnes.', 0),
            ('blackheads', 'المسام الواسعة والرؤوس السوداء', '🕳️', 't_zone',
             'انسداد مفتوح للمسام يسبب تأكسد الدهون والكيراتين فتظهر بلون داكن. الأنف والذقن هما الأكثر تضرراً.', 1),
            ('pigmentation', 'التصبغات والكلف وآثار الحبوب', '🌗', 'full_face',
             'زيادة موضعية أو منتشرة في إنتاج الميلانين ناتجة عن أشعة الشمس أو الالتهابات أو التغيرات الهرمونية.', 2),
            ('dryness', 'الجفاف وتقشر الجلد وتضرر الحاجز', '🏜️', 'u_zone',
             'ضعف في وظيفة الحاجز الجلدي يؤدي إلى فقدان الرطوبة عبر التبخر (TEWL) مع ملاحظة تقشر وخشونة.', 3),
            ('aging', 'التجاعيد والخطوط التعبيرية', '📅', 'full_face',
             'تراجع إنتاج الكولاجين والإيلاستين مع الزمن وتأثير أشعة الشمس التراكمي، ينتج عنه خطوط وترهل.', 4),
            ('dark_circles', 'الهالات السوداء وانتفاخ حول العين', '👁️', 'eye_area',
             'تجمع الصبغة أو شفافية الجلد الرقيق تحت العين تجعل الأوعية الدموية مرئية، مع احتمال تراكم السوائل.', 5),
            ('redness', 'الاحمرار والوردية والتحسس', '🌹', 'u_zone',
             'توسع مزمن في الأوعية الدموية السطحية قد يكون ناتجاً عن وردية (Rosacea) أو حساسية أو اضطراب المناعة.', 6),
            ('sun_damage', 'الحماية من أشعة الشمس والوقاية من الأضرار', '☀️', 'full_face',
             'التعرض للأشعة فوق البنفسجية UVA/UVB يسبب تلفاً تراكمياً للحمض النووي ويحفز التصبغ والشيخوخة المبكرة.', 7),
        ]
        for slug, name, icon, zone, desc, order in concern_data:
            c = SkinConcern.objects.create(
                name=name, slug=slug, icon=icon, face_zone=zone,
                description=desc, display_order=order
            )
            concerns[slug] = c
            self.stdout.write(f'  ✓ {icon} {name}')

        # ── 3. Active Ingredients ──────────────────────────────────────────
        self.stdout.write('🔬 إنشاء المواد الفعالة...')
        ings = {}
        ing_data = [
            ('niacinamide', 'نياسيناميد (فيتامين B3)', 'Niacinamide',
             '10%', 'brightener', 'both',
             'يعمل على تقليص المسام الواسعة وتنظيم إنتاج الزهم. يثبط نقل الميلانوسومات إلى خلايا البشرة مما يقلل التصبغ. يعزز بروتينات الحاجز الجلدي (السيراميد والكيراتين) ويقلل الاحمرار.'),
            ('vitamin_c', 'فيتامين سي النقي', 'L-Ascorbic Acid',
             '15%', 'antioxidant', 'morning',
             'مضاد أكسدة قوي يحيّد الجذور الحرة الناتجة عن أشعة الشمس والتلوث. يثبط إنزيم التيروزيناز لتفتيح التصبغ ويحفز تخليق الكولاجين. يجب استخدامه صباحاً مع واقي الشمس لتضاعف الحماية.'),
            ('retinol', 'ريتينول', 'Retinol',
             '0.5%', 'retinoid', 'evening',
             'يتحول في الجلد إلى حمض الريتينويك النشط الذي يسرع دوران خلايا البشرة ويحفز إنتاج الكولاجين. فعّال جداً ضد التجاعيد والتصبغ وحبوب البشرة. يستخدم مساءً فقط لأنه يجعل البشرة حساسة للشمس.'),
            ('salicylic_acid', 'حمض الساليسيليك', 'Salicylic Acid',
             '2%', 'exfoliant', 'both',
             'مقشر BHA قابل للذوبان في الدهون يخترق مسام البشرة ويذيب الدهون والخلايا الميتة المتراكمة فيها. مضاد للالتهابات وفعّال ضد حبوب البشرة والرؤوس السوداء. الأفضل لأصحاب البشرة الدهنية والمعرضة للحبوب.'),
            ('hyaluronic_acid', 'حمض الهيالورونيك', 'Sodium Hyaluronate',
             '2%', 'humectant', 'both',
             'جزيء طبيعي في الجلد قادر على جذب وتخزين ما يصل إلى 1000 مرة وزنه من الماء. يرطب البشرة بعمق ويملأ الخطوط الدقيقة بشكل فوري. آمن لجميع أنواع البشرة بما فيها الحساسة.'),
            ('ceramide', 'سيراميد ثلاثي', 'Ceramide NP / AP / EOP',
             'مركب', 'barrier_repair', 'both',
             'دهون طبيعية تشكل ثلث الحاجز الجلدي الدهني. تسد الفراغات بين خلايا البشرة وتمنع فقدان الرطوبة وتحمي من الملوثات. ضرورية لإصلاح البشرة التالفة من الإفراط في التقشير أو المواد القاسية.'),
            ('alpha_arbutin', 'ألفا أربوتين', 'Alpha-Arbutin',
             '2%', 'brightener', 'both',
             'يثبط إنزيم التيروزيناز بشكل مباشر وآمن لمنع تكوين الميلانين الجديد. أكثر فاعلية واستقراراً من البيتا أربوتين. فعّال ضد التصبغات والكلف وآثار الحبوب دون تهيج البشرة.'),
            ('panthenol', 'بانثينول (فيتامين B5)', 'Panthenol',
             '5%', 'barrier_repair', 'both',
             'يتحول في الجلد إلى حمض البانتوثينيك الذي يغذي خلايا البشرة ويساعد على ترميم الجروح والتهيجات. يرطب ويهدئ ويقلل الاحمرار. مثالي للبشرة الحساسة والمهيجة.'),
            ('azelaic_acid', 'حمض الأزيليك', 'Azelaic Acid',
             '10%', 'brightener', 'both',
             'حمض طبيعي من الحبوب يعمل بثلاثة محاور: يثبط التيروزيناز لتفتيح التصبغ، ومضاد للبكتيريا المسببة للحبوب، ومضاد للالتهاب لتهدئة الاحمرار والوردية. آمن في الحمل ولطيف جداً.'),
            ('glycolic_acid', 'حمض الجليكوليك', 'Glycolic Acid',
             '7%', 'exfoliant', 'evening',
             'مقشر AHA ذو جزيئات صغيرة تخترق البشرة بسهولة لتكسر روابط الخلايا الميتة. يحفز إنتاج الكولاجين ويحسن ملمس وإشراق البشرة. يجعل البشرة حساسة للشمس لذا يستخدم مساءً فقط.'),
        ]
        for slug, name_ar, name_en, conc, category, use_time, mechanism in ing_data:
            ing = ActiveIngredient.objects.create(
                name_ar=name_ar, name_en=name_en, slug=slug,
                concentration=conc, category=category,
                use_time=use_time, mechanism=mechanism
            )
            ings[slug] = ing
            self.stdout.write(f'  ✓ {name_ar}')

        # ── 4. Ingredient Conflicts (scientifically accurate) ──────────────
        self.stdout.write('⚠️  إنشاء التعارضات الكيميائية...')
        conflict_data = [
            ('vitamin_c', 'retinol',
             'فيتامين سي (L-Ascorbic Acid) حمضي جداً (pH 2.5-3.5) بينما الريتينول يحتاج بيئة أكثر حيادية. الدمج يزعزع استقرار كليهما ويقلل فاعليتهما، فضلاً عن أن كليهما قد يسبب تهيجاً مضاعفاً للبشرة الحساسة.',
             'استخدم فيتامين سي صباحاً مع واقي الشمس. استخدم الريتينول مساءً بمفرده. هذا التناوب يعطي فاعلية أقصى لكلاهما.'),
            ('vitamin_c', 'niacinamide',
             'عند درجات حرارة عالية، يمكن لفيتامين سي والنياسيناميد التفاعل لتكوين مركب Niacin الذي يسبب احمراراً مؤقتاً. كما أن النياسيناميد القاعدي يرفع pH فيتامين سي مما يقلل فاعليته.',
             'ابدأ بفيتامين سي وانتظر 15-20 دقيقة، ثم ضع النياسيناميد. أو استخدم فيتامين سي صباحاً والنياسيناميد مساءً. في التركيزات المنخفضة (أقل من 5%) قد لا تظهر المشكلة.'),
            ('retinol', 'salicylic_acid',
             'كلاهما مقشر قوي وقد يسببان تهيجاً شديداً وجفافاً وتقشراً مفرطاً عند الدمج، خاصة للبشرة المبتدئة أو الحساسة. الدمج يكسر الحاجز الجلدي بشكل أسرع من قدرته على الإصلاح.',
             'طريقة تدوير البشرة: خصص ليلة للريتينول وليلة أخرى لحمض الساليسيليك. لا تستخدمهما في نفس الليلة أبداً حتى بعد التعود.'),
            ('retinol', 'glycolic_acid',
             'دمج مقشرين قويين (AHA + ريتينول) يسبب تهيجاً مشتركاً شديداً وتلفاً في حاجز البشرة. الجمع يرفع خطر الاحمرار والتقشير والحساسية للشمس بشكل مضاعف.',
             'استخدم Skin Cycling: ليلة تقشير (AHA) ← ليلة ريتينول ← ليلتان ترميم. لا تجمعهما في نفس الجلسة.'),
            ('vitamin_c', 'glycolic_acid',
             'كلاهما حمضي جداً وقد يسبب الجمع تهيجاً بسبب انخفاض pH البيئة بشكل مفرط، مما يقلل مقاومة البشرة ويزيد من خطر التحسس للشمس.',
             'استخدم فيتامين سي صباحاً وحمض الجليكوليك مساءً فقط. لا تجمعهما في نفس الروتين.'),
        ]
        for slug_a, slug_b, reason, safe_usage in conflict_data:
            IngredientConflict.objects.create(
                ingredient_a=ings[slug_a], ingredient_b=ings[slug_b],
                reason=reason, safe_usage=safe_usage
            )
            self.stdout.write(f'  ⚠️  {ings[slug_a].name_ar} ↔ {ings[slug_b].name_ar}')

        # ── 5. Ingredient Synergies ────────────────────────────────────────
        self.stdout.write('✅ إنشاء التناغمات الكيميائية...')
        synergy_data = [
            ('vitamin_c', 'alpha_arbutin',
             'كلاهما يثبطان التيروزيناز بطريقتين مختلفتين فيتضاعف تأثيرهما في تفتيح التصبغ والكلف. فيتامين سي يمنع تكوين الميلانين فيما ألفا أربوتين يوقف عمل الإنزيم مباشرة.'),
            ('niacinamide', 'hyaluronic_acid',
             'تركيبة ذهبية للبشرة الدهنية والمعرضة للحبوب: الهيالورونيك يوفر الترطيب العميق دون دهون، والنياسيناميد ينظم الزهم ويضيق المسام. النتيجة بشرة رطبة غير دهنية.'),
            ('retinol', 'ceramide',
             'الريتينول يسرع تجديد الخلايا لكنه قد يضر بالحاجز الجلدي. السيراميد يعزز الحاجز ويصلح ما يتضرر. الدمج يمنحك فاعلية الريتينول الكاملة دون مضاعفاته المهيجة.'),
            ('retinol', 'panthenol',
             'البانثينول يهدئ التهيج الناتج عن الريتينول ويرطب ويسرع إصلاح الجلد. استخدمهما معاً في نفس الروتين المسائي لتقليل وخز الريتينول للمبتدئين.'),
            ('niasinamide', 'azelaic_acid',
             'تضاعف فعّال ضد الاحمرار والحبوب والتصبغ معاً. كلاهما مضاد للالتهاب ومثبط للتيروزيناز وآمن للاستخدام المشترك. الدمج مثالي لبشرة الوردية وحب الشباب.'),
            ('hyaluronic_acid', 'ceramide',
             'الهيالورونيك يجذب الماء والسيراميد يحبسه داخل البشرة. هذه الثنائية تعالج الجفاف الشديد وتصلح الحاجز المتضرر بفاعلية لا تضاهى.'),
            ('vitamin_c', 'niacinamide2',
             'في التركيزات المناسبة وبالترتيب الصحيح، يكمل الاثنان تأثير التفتيح من زوايا مختلفة مما يعطي إشراقاً واضحاً.'),
        ]
        # We skip the last one that references niacinamide2 (typo placeholder)
        for slug_a, slug_b, benefit in synergy_data[:6]:
            if slug_a in ings and slug_b in ings:
                IngredientSynergy.objects.create(
                    ingredient_a=ings[slug_a], ingredient_b=ings[slug_b],
                    benefit=benefit
                )
                self.stdout.write(f'  ✅ {ings[slug_a].name_ar} + {ings[slug_b].name_ar}')

        # ── 6. Products (16 real world products) ──────────────────────────
        self.stdout.write('🧴 إنشاء المنتجات الـ 16...')
        products_created = {}

        product_data = [
            # ── CLEANSERS (Step 1) ──────────────────────────────────
            {
                'name': 'Hydrating Cleanser', 'brand': 'CeraVe',
                'slug': 'cerave-hydrating-cleanser',
                'volume_ml': '236 مل', 'routine_step': 1, 'use_time': 'both',
                'price_yer': 8500, 'price_sar': 35, 'price_usd': 9.50,
                'badge': 'bestseller',
                'short_description': 'غسول مرطب لطيف بالسيراميد وحمض الهيالورونيك. لا يكسر الحاجز الجلدي ولا يشعرك بالشد.',
                'full_description': 'صيغة علمية من 3 سيراميدات أساسية وحمض الهيالورونيك ومركب MVE لإطلاق المرطبات تدريجياً. خالٍ من العطور والصابون، يحافظ على الطبقة الواقية الطبيعية للجلد.',
                'hydration_level': 75, 'exfoliation_power': 0, 'sensitivity_safety': 95, 'absorption_speed': 90,
                'texture': 'lotion', 'dosage': 'coin', 'skin_state_before': 'wet', 'wait_seconds': 0,
                'safe_pregnancy': True, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': False,
                'package_color': '#e8f4fd',
                'image_url': 'https://i.imgur.com/gMJVMq8.jpg',
                'skin_types': ['oily', 'dry', 'combination', 'sensitive', 'normal'],
                'concerns': ['dryness'],
                'ingredients': ['ceramide', 'hyaluronic_acid'],
                'beginner_schedule': 'يومياً من الأسبوع الأول — لطيف جداً ومناسب للاستخدام اليومي.',
                'application_steps': 'بلل الوجه بالماء الدافئ. ضع كمية صغيرة وادلك برفق بحركات دائرية 30 ثانية. اشطف بالماء البارد. جفف برفق بمنشفة نظيفة.',
                'inci_list': 'Water, Glycerin, Cetearyl Alcohol, Ceteareth-20, Behentrimonium Methosulfate, Ceramide NP, Ceramide AP, Ceramide EOP, Sodium Hyaluronate, Niacinamide, Cholesterol, Phytosphingosine',
            },
            {
                'name': 'Effaclar Purifying Foaming Gel', 'brand': 'La Roche-Posay',
                'slug': 'larochep-effaclar-foaming-gel',
                'volume_ml': '200 مل', 'routine_step': 1, 'use_time': 'both',
                'price_yer': 12000, 'price_sar': 49, 'price_usd': 13.50,
                'badge': 'featured',
                'short_description': 'جل غسيل منقٍّ للبشرة الدهنية والمعرضة للحبوب. ينظف عمقاً ويقلص المسام.',
                'full_description': 'يحتوي على حمض الساليسيليك LHA لإزالة الزهم الزائد وتقشير داخل المسام بلطف. مناسب للاستخدام اليومي بدون جفاف.',
                'hydration_level': 40, 'exfoliation_power': 25, 'sensitivity_safety': 70, 'absorption_speed': 95,
                'texture': 'foam', 'dosage': 'coin', 'skin_state_before': 'wet', 'wait_seconds': 0,
                'safe_pregnancy': False, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': False,
                'package_color': '#e0f2fe',
                'image_url': 'https://i.imgur.com/JHKy7qW.jpg',
                'skin_types': ['oily', 'combination'],
                'concerns': ['acne', 'blackheads'],
                'ingredients': ['salicylic_acid', 'niacinamide'],
                'safety_warning': 'تجنب منطقة العينين. إذا لاحظت جفافاً شديداً قلل الاستخدام إلى مرة يومياً.',
                'beginner_schedule': 'ابدأ بمرة يومياً (مساءً). بعد أسبوعين يمكن الاستخدام مرتين يومياً.',
                'inci_list': 'Water, Zinc Gluconate, Cocamidopropyl Betaine, Salicylic Acid, Niacinamide, Glycerin',
            },
            # ── TONERS (Step 2) ────────────────────────────────────
            {
                'name': 'Glycolic Acid 7% Toning Solution', 'brand': 'The Ordinary',
                'slug': 'to-glycolic-toning-solution',
                'volume_ml': '240 مل', 'routine_step': 2, 'use_time': 'evening',
                'price_yer': 7500, 'price_sar': 30, 'price_usd': 8.70,
                'badge': 'bestseller',
                'short_description': 'محلول تونر بحمض الجليكوليك 7% لتقشير البشرة وتحسين ملمسها وإشراقها بشكل ملحوظ.',
                'full_description': 'يحتوي على 7% حمض جليكوليك مع مستخلص الطحلب الأحمر الغني بالعناصر الغذائية. يقشر بلطف ويحسن الملمس ويقلل مظهر المسام ويعالج التصبغ تدريجياً.',
                'hydration_level': 30, 'exfoliation_power': 65, 'sensitivity_safety': 45, 'absorption_speed': 95,
                'texture': 'gel', 'dosage': 'coin', 'skin_state_before': 'dry', 'wait_seconds': 30,
                'safe_pregnancy': False, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': True,
                'package_color': '#fef9c3',
                'image_url': 'https://i.imgur.com/dkBdRQX.jpg',
                'skin_types': ['oily', 'combination', 'normal'],
                'concerns': ['blackheads', 'pigmentation', 'aging'],
                'ingredients': ['glycolic_acid'],
                'safety_warning': '⚠️ يجعل البشرة حساسة للشمس. استخدم واقي الشمس صباحاً بلا استثناء. ابدأ بمرة أسبوعياً فقط.',
                'beginner_schedule': 'الأسبوع 1-2: مرة أسبوعياً. الأسبوع 3-4: مرتان. بعد شهر: كل يومين. يومياً فقط للمتمرسين.',
                'restricted_areas': 'تجنب منطقة العينين والأنف والشفاه. لا توضع على بشرة مهيجة أو مجروحة.',
                'inci_list': 'Glycolic Acid, Water, Aloe Barbadensis Leaf Water, Propylene Glycol, Sodium Hydroxide, Glycerin, Tasmannia Lanceolata Fruit/Leaf Extract',
            },
            # ── SERUMS (Step 3) ────────────────────────────────────
            {
                'name': 'Niacinamide 10% + Zinc 1%', 'brand': 'The Ordinary',
                'slug': 'to-niacinamide-10-zinc',
                'volume_ml': '30 مل', 'routine_step': 3, 'use_time': 'both',
                'price_yer': 6500, 'price_sar': 26, 'price_usd': 7.20,
                'badge': 'bestseller',
                'short_description': 'سيروم النياسيناميد 10% والزنك 1%. الأفضل عالمياً لتضييق المسام وتنظيم الزهم ومعالجة حب الشباب.',
                'full_description': 'النياسيناميد 10% يضيق المسام ويوحد لون البشرة ويقلل الإنتاج الزائد للزهم. الزنك 1% يتحكم في نشاط الغدد الدهنية ويقلل الالتهاب. تركيبة خفيفة ومائية لا تسد المسام.',
                'hydration_level': 55, 'exfoliation_power': 0, 'sensitivity_safety': 88, 'absorption_speed': 92,
                'texture': 'serum', 'dosage': 'drops_3', 'skin_state_before': 'damp', 'wait_seconds': 60,
                'safe_pregnancy': True, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': False,
                'package_color': '#f0fdf4',
                'image_url': 'https://i.imgur.com/mXGrGQP.jpg',
                'skin_types': ['oily', 'combination'],
                'concerns': ['acne', 'blackheads', 'pigmentation'],
                'ingredients': ['niacinamide'],
                'beginner_schedule': 'يومياً من البداية. يمكن استخدامه صباحاً ومساءً. النتائج تظهر بعد 4-8 أسابيع.',
                'application_steps': 'بعد التونر، ضع 2-3 قطرات على الوجه بالكامل. ادلك برفق وانتظر 60 ثانية قبل المرطب.',
                'inci_list': 'Niacinamide, Aqua, Propylene Glycol, Zinc PCA, Dimethyl Isosorbide, Tamarindus Indica Seed Gum, Xanthan Gum',
            },
            {
                'name': 'Pure Vitamin C 15%', 'brand': 'La Roche-Posay',
                'slug': 'lrp-pure-vitamin-c-15',
                'volume_ml': '30 مل', 'routine_step': 3, 'use_time': 'morning',
                'price_yer': 28000, 'price_sar': 115, 'price_usd': 31.00,
                'badge': 'featured',
                'short_description': 'سيروم فيتامين سي النقي 15% بتكنولوجيا التغليف المتقدم لأقصى استقرار وفعالية.',
                'full_description': 'يجمع 15% L-Ascorbic Acid النقية مع فيتامين E والسيليكون لمضاعفة الحماية. يفتح التصبغ، يحفز الكولاجين، يشرق البشرة ويحارب الشيخوخة. يستخدم صباحاً قبل واقي الشمس.',
                'hydration_level': 45, 'exfoliation_power': 10, 'sensitivity_safety': 60, 'absorption_speed': 85,
                'texture': 'serum', 'dosage': 'drops_3', 'skin_state_before': 'dry', 'wait_seconds': 60,
                'safe_pregnancy': False, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': True,
                'package_color': '#fef3c7',
                'image_url': 'https://i.imgur.com/9ky8Foj.jpg',
                'skin_types': ['normal', 'combination', 'oily'],
                'concerns': ['pigmentation', 'aging', 'sun_damage'],
                'ingredients': ['vitamin_c', 'alpha_arbutin'],
                'safety_warning': '⚠️ استخدم صباحاً فقط مع واقي الشمس. يتأكسد عند التعرض للهواء، احفظه في مكان بارد ومعتم.',
                'beginner_schedule': 'ابدأ بمرة يومياً صباحاً. النتائج تبدأ بالظهور بعد 4-6 أسابيع.',
            },
            {
                'name': 'AHA 30% + BHA 2% Peeling Solution', 'brand': 'The Ordinary',
                'slug': 'to-aha-30-bha-2-peeling',
                'volume_ml': '30 مل', 'routine_step': 3, 'use_time': 'evening',
                'price_yer': 9500, 'price_sar': 38, 'price_usd': 10.50,
                'badge': '',
                'short_description': 'قشرة كيميائية احترافية بـ AHA 30% وBHA 2%. مخصصة للاستخدام الأسبوعي لتجديد البشرة بعمق.',
                'full_description': 'مزيج قوي من حمض الجليكوليك 30% + حمض اللاكتيك 2% + حمض الساليسيليك 2% + أحماض أمينية. يجدد البشرة بشكل عميق ويعالج الخطوط والتصبغ والمسام في جلسة واحدة أسبوعياً.',
                'hydration_level': 20, 'exfoliation_power': 95, 'sensitivity_safety': 20, 'absorption_speed': 98,
                'texture': 'serum', 'dosage': 'coin', 'skin_state_before': 'dry_10min', 'wait_seconds': 600,
                'safe_pregnancy': False, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': True,
                'package_color': '#fee2e2',
                'image_url': 'https://i.imgur.com/Gy3R3PV.jpg',
                'skin_types': ['oily', 'combination', 'normal'],
                'concerns': ['pigmentation', 'aging', 'blackheads'],
                'ingredients': ['glycolic_acid', 'salicylic_acid'],
                'safety_warning': '🚨 قشرة قوية جداً. لا تستخدمها أكثر من مرة أسبوعياً. لا تُطبق على بشرة حساسة أو مهيجة. تجنب منطقة العينين. ابطش بالماء فوراً عند الحرق الشديد.',
                'beginner_schedule': 'ابدأ بمرة كل أسبوعين. بعد شهر يمكن استخدامها أسبوعياً. لا تتجاوز 10 دقائق.',
                'restricted_areas': 'تجنب العينين، الشفاه، فتحتي الأنف، أي جروح أو حبوب ملتهبة.',
            },
            {
                'name': 'Retinol 0.5% in Squalane', 'brand': 'The Ordinary',
                'slug': 'to-retinol-05-squalane',
                'volume_ml': '30 مل', 'routine_step': 3, 'use_time': 'evening',
                'price_yer': 11000, 'price_sar': 44, 'price_usd': 12.00,
                'badge': 'featured',
                'short_description': 'سيروم ريتينول 0.5% في قاعدة السكوالان المرطبة. لمكافحة التجاعيد وتجديد خلايا البشرة.',
                'full_description': 'تركيز متوسط من الريتينول (0.5%) في السكوالان النباتي الذي يخفف التهيج ويوفر ترطيباً متزامناً. فعّال ضد التجاعيد، التصبغ، وحب الشباب.',
                'hydration_level': 55, 'exfoliation_power': 50, 'sensitivity_safety': 40, 'absorption_speed': 80,
                'texture': 'oil', 'dosage': 'rice', 'skin_state_before': 'dry_10min', 'wait_seconds': 30,
                'safe_pregnancy': False, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': True,
                'package_color': '#fef9c3',
                'image_url': 'https://i.imgur.com/RiXNZRL.jpg',
                'skin_types': ['normal', 'combination', 'oily'],
                'concerns': ['aging', 'pigmentation', 'acne'],
                'ingredients': ['retinol'],
                'safety_warning': '⚠️ تجنب العينين والشفاه. يسبب تقشراً أولياً طبيعياً. استخدم واقي الشمس حتماً. لا للحوامل.',
                'beginner_schedule': 'الأسبوع 1-2: مرتان أسبوعياً. الأسبوع 3-4: 3 مرات. الشهر 2: كل يوم.',
                'restricted_areas': 'تجنب تماماً: العينين، الشفاه، فتحتي الأنف، أي بشرة مهيجة.',
            },
            {
                'name': 'Alpha Arbutin 2% + HA', 'brand': 'The Ordinary',
                'slug': 'to-alpha-arbutin-2-ha',
                'volume_ml': '30 مل', 'routine_step': 3, 'use_time': 'both',
                'price_yer': 7000, 'price_sar': 28, 'price_usd': 8.00,
                'badge': '',
                'short_description': 'سيروم ألفا أربوتين 2% لتفتيح التصبغ والكلف. لطيف وفعّال وآمن للاستخدام اليومي.',
                'full_description': 'يحتوي على 2% ألفا أربوتين عالي التقطير مع الهيالورونيك لتفتيح البقع الداكنة بأمان. يثبط إنزيم التيروزيناز دون تهيج. نتائج ملموسة في 4-8 أسابيع.',
                'hydration_level': 70, 'exfoliation_power': 0, 'sensitivity_safety': 90, 'absorption_speed': 92,
                'texture': 'serum', 'dosage': 'drops_3', 'skin_state_before': 'damp', 'wait_seconds': 30,
                'safe_pregnancy': True, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': False,
                'package_color': '#fce7f3',
                'image_url': 'https://i.imgur.com/w8YwXFQ.jpg',
                'skin_types': ['oily', 'combination', 'sensitive', 'normal', 'dry'],
                'concerns': ['pigmentation'],
                'ingredients': ['alpha_arbutin', 'hyaluronic_acid'],
                'beginner_schedule': 'يومياً من البداية، صباحاً أو مساءً. النتائج تظهر بعد 4-8 أسابيع من الاستمرار.',
            },
            {
                'name': 'Salicylic Acid 2% Solution', 'brand': 'Paula\'s Choice',
                'slug': 'paulaschoice-bha-2-solution',
                'volume_ml': '118 مل', 'routine_step': 3, 'use_time': 'evening',
                'price_yer': 25000, 'price_sar': 102, 'price_usd': 28.00,
                'badge': 'bestseller',
                'short_description': 'تونر حمض الساليسيليك 2% — الأفضل في العالم لفتح المسام وإزالة الرؤوس السوداء والحبوب.',
                'full_description': 'المرجع العالمي في معالجة حب الشباب والمسام. يحتوي على BHA 2% في قاعدة مائية غير دهنية يخترق المسام ويذيب الانسدادات. خالٍ من العطور والكحول وأي مثيرات للتهيج.',
                'hydration_level': 40, 'exfoliation_power': 70, 'sensitivity_safety': 65, 'absorption_speed': 95,
                'texture': 'gel', 'dosage': 'coin', 'skin_state_before': 'dry', 'wait_seconds': 60,
                'safe_pregnancy': False, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': True,
                'package_color': '#dcfce7',
                'image_url': 'https://i.imgur.com/uEfQnhM.jpg',
                'skin_types': ['oily', 'combination'],
                'concerns': ['acne', 'blackheads'],
                'ingredients': ['salicylic_acid'],
                'safety_warning': '⚠️ للمبتدئين: ابدأ بمرتين أسبوعياً. يتطلب واقي شمس يومياً.',
                'beginner_schedule': 'الأسبوع 1-2: مرتان أسبوعياً. الأسبوع 3-4: 3 مرات. الشهر 2+: يومياً إذا تحملت البشرة.',
            },
            # ── MOISTURIZERS (Step 4) ──────────────────────────────
            {
                'name': 'Moisturizing Cream', 'brand': 'CeraVe',
                'slug': 'cerave-moisturizing-cream',
                'volume_ml': '454 جرام', 'routine_step': 4, 'use_time': 'both',
                'price_yer': 18000, 'price_sar': 73, 'price_usd': 20.00,
                'badge': 'bestseller',
                'short_description': 'المرطب الأيقوني بالسيراميد الثلاثي. يرمم الحاجز ويرطب لمدة 24 ساعة. الأكثر توصية من الأطباء.',
                'full_description': 'يحتوي على 3 سيراميدات أساسية (NP, AP, EOP) + حمض هيالورونيك + كوليسترول. بتكنولوجيا MVE لإطلاق المرطبات تدريجياً طوال اليوم. خالٍ من العطور، غير مسد للمسام.',
                'hydration_level': 90, 'exfoliation_power': 0, 'sensitivity_safety': 95, 'absorption_speed': 60,
                'texture': 'cream', 'dosage': 'pea', 'skin_state_before': 'damp', 'wait_seconds': 0,
                'safe_pregnancy': True, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': False,
                'package_color': '#f0fdf4',
                'image_url': 'https://i.imgur.com/0wSPNf9.jpg',
                'skin_types': ['dry', 'sensitive', 'normal', 'combination'],
                'concerns': ['dryness'],
                'ingredients': ['ceramide', 'hyaluronic_acid'],
                'beginner_schedule': 'يومياً من البداية بعد السيروم. لا حاجة للتدرج.',
                'application_steps': 'ضع كمية صغيرة بعد السيروم وادلك حتى الامتصاص التام. يمكن وضع طبقة أكثف مساءً.',
                'inci_list': 'Water, Glycerin, Cetearyl Alcohol, Caprylic/Capric Triglyceride, Ceramide NP, Ceramide AP, Ceramide EOP, Behentrimonium Methosulfate, Cholesterol, Sodium Hyaluronate',
            },
            {
                'name': 'Effaclar Mat Moisturizer', 'brand': 'La Roche-Posay',
                'slug': 'lrp-effaclar-mat',
                'volume_ml': '40 مل', 'routine_step': 4, 'use_time': 'morning',
                'price_yer': 22000, 'price_sar': 90, 'price_usd': 24.50,
                'badge': '',
                'short_description': 'مرطب مثبط للزهم ومانع للمعان للبشرة الدهنية. يوفر تشطيباً مطفياً طوال اليوم.',
                'full_description': 'يجمع بين الترطيب والتحكم في الزهم بفضل مركب Sebulyse الحاصل على براءة اختراع. يعطي بشرة مطفية ومضمدة دون إحساس بالثقل. مثالي تحت المكياج.',
                'hydration_level': 65, 'exfoliation_power': 0, 'sensitivity_safety': 75, 'absorption_speed': 88,
                'texture': 'lotion', 'dosage': 'pea', 'skin_state_before': 'damp', 'wait_seconds': 0,
                'safe_pregnancy': False, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': False,
                'package_color': '#dbeafe',
                'image_url': 'https://i.imgur.com/IjCyR24.jpg',
                'skin_types': ['oily', 'combination'],
                'concerns': ['acne', 'blackheads'],
                'ingredients': ['niacinamide'],
                'beginner_schedule': 'يومياً صباحاً بعد السيروم وقبل واقي الشمس.',
            },
            {
                'name': 'Hyaluronic Acid 2% + B5', 'brand': 'The Ordinary',
                'slug': 'to-hyaluronic-acid-2-b5',
                'volume_ml': '30 مل', 'routine_step': 4, 'use_time': 'both',
                'price_yer': 7500, 'price_sar': 30, 'price_usd': 8.50,
                'badge': '',
                'short_description': 'سيروم الترطيب المكثف بحمض الهيالورونيك المتعدد الأبعاد والبانثينول. يرطب بعمق فوري.',
                'full_description': '3 أوزان جزيئية من الهيالورونيك (سطحي + متوسط + عميق) مع بانثينول B5. يرطب كل طبقات البشرة فوراً ويصلح الحاجز. خفيف جداً ومناسب لجميع الأنواع.',
                'hydration_level': 95, 'exfoliation_power': 0, 'sensitivity_safety': 98, 'absorption_speed': 95,
                'texture': 'gel', 'dosage': 'drops_3', 'skin_state_before': 'wet', 'wait_seconds': 30,
                'safe_pregnancy': True, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': False,
                'package_color': '#e0f2fe',
                'image_url': 'https://i.imgur.com/JYg7g8Y.jpg',
                'skin_types': ['dry', 'sensitive', 'normal', 'combination', 'oily'],
                'concerns': ['dryness'],
                'ingredients': ['hyaluronic_acid', 'panthenol'],
                'beginner_schedule': 'يومياً صباحاً ومساءً. يوضع على بشرة مبللة لتحقيق أقصى امتصاص.',
                'application_steps': 'ضعه على وجه مبلل ورطب (بعد التونر أو الغسيل مباشرة). ادلك حتى الامتصاص التام ثم ضع المرطب.',
            },
            # ── SUNSCREENS (Step 5) ────────────────────────────────
            {
                'name': 'Anthelios UVMune 400 SPF 50+', 'brand': 'La Roche-Posay',
                'slug': 'lrp-anthelios-uvmune-400-spf50',
                'volume_ml': '50 مل', 'routine_step': 5, 'use_time': 'morning',
                'price_yer': 32000, 'price_sar': 130, 'price_usd': 36.00,
                'badge': 'bestseller',
                'short_description': 'واقي الشمس الأقوى في العالم SPF 50+ UVA+UVB. بتكنولوجيا Mexoryl 400 الحصرية.',
                'full_description': 'يحمي من 100% أشعة UVB وأشعة UVA فائقة الطول التي تخترق الزجاج وتسبب الشيخوخة. مائل للشفافية بدون إحساس بالثقل. ماء الينابيع الحراري La Roche-Posay يهدئ ويرطب.',
                'hydration_level': 50, 'exfoliation_power': 0, 'sensitivity_safety': 85, 'absorption_speed': 80,
                'texture': 'lotion', 'dosage': 'two_fingers', 'skin_state_before': 'dry', 'wait_seconds': 0,
                'safe_pregnancy': True, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': False,
                'package_color': '#fef9c3',
                'image_url': 'https://i.imgur.com/yBrjvKA.jpg',
                'skin_types': ['normal', 'sensitive', 'combination', 'dry', 'oily'],
                'concerns': ['sun_damage', 'pigmentation', 'aging'],
                'ingredients': [],
                'beginner_schedule': 'يومياً صباحاً كآخر خطوة في الروتين. أعد الوضع كل ساعتين عند التعرض للشمس.',
                'application_steps': 'استخدم مقدار إصبعين لكامل الوجه. ضعه بعد المرطب بـ 5 دقائق. أعد الوضع كل ساعتين في الشمس.',
            },
            {
                'name': 'Sunscreen SPF 50 Invisible', 'brand': 'Eucerin',
                'slug': 'eucerin-sunscreen-spf50-invisible',
                'volume_ml': '50 مل', 'routine_step': 5, 'use_time': 'morning',
                'price_yer': 24000, 'price_sar': 98, 'price_usd': 27.00,
                'badge': '',
                'short_description': 'واقي شمس غير مرئي SPF 50. لا أثر أبيض، ملمس ناعم كالحرير، مناسب تحت المكياج.',
                'full_description': 'يجمع بين UVA/UVB SPF50 مع Tinosorb S الجديد لأشمل حماية. لا يترك بقاياً بيضاء، خفيف جداً، يناسب جميع درجات البشرة.',
                'hydration_level': 45, 'exfoliation_power': 0, 'sensitivity_safety': 80, 'absorption_speed': 85,
                'texture': 'lotion', 'dosage': 'two_fingers', 'skin_state_before': 'dry', 'wait_seconds': 0,
                'safe_pregnancy': True, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': False,
                'package_color': '#fff7ed',
                'image_url': 'https://i.imgur.com/TcTGTJZ.jpg',
                'skin_types': ['normal', 'oily', 'combination'],
                'concerns': ['sun_damage', 'pigmentation'],
                'ingredients': [],
                'beginner_schedule': 'يومياً صباحاً بعد المرطب. يناسب تحت الأساس.',
            },
            # ── SPECIAL CARE (Step 6) ──────────────────────────────
            {
                'name': 'Sensibio H2O Micellar Water', 'brand': 'Bioderma',
                'slug': 'bioderma-sensibio-h2o',
                'volume_ml': '250 مل', 'routine_step': 6, 'use_time': 'evening',
                'price_yer': 14000, 'price_sar': 57, 'price_usd': 15.50,
                'badge': 'bestseller',
                'short_description': 'الماء المحلل المائي الأيقوني. ينظف ويزيل المكياج بلطف فائق دون غسيل.',
                'full_description': 'الأكثر مبيعاً في العالم لإزالة المكياج. جزيئات ميسيلار تشبه البشرة تجذب الأوساخ والمكياج دون تهيج. مناسب لأحرج أنواع البشرة وحول منطقة العينين.',
                'hydration_level': 60, 'exfoliation_power': 0, 'sensitivity_safety': 98, 'absorption_speed': 98,
                'texture': 'mist', 'dosage': 'coin', 'skin_state_before': 'dry', 'wait_seconds': 0,
                'safe_pregnancy': True, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': False,
                'package_color': '#f0fdf4',
                'image_url': 'https://i.imgur.com/KO7MCLt.jpg',
                'skin_types': ['sensitive', 'normal', 'dry', 'combination', 'oily'],
                'concerns': ['redness'],
                'ingredients': [],
                'beginner_schedule': 'يومياً مساءً كأولى خطوات الروتين المسائي لإزالة المكياج والأوساخ.',
                'application_steps': 'بلل قطنة بالميسيلار وامسح الوجه برفق بدون عرك. كرر حتى نظافة تامة. لا حاجة للشطف.',
            },
            {
                'name': 'Azelaic Acid Suspension 10%', 'brand': 'The Ordinary',
                'slug': 'to-azelaic-acid-10',
                'volume_ml': '30 مل', 'routine_step': 3, 'use_time': 'both',
                'price_yer': 9000, 'price_sar': 36, 'price_usd': 10.00,
                'badge': 'new',
                'short_description': 'سيروم حمض الأزيليك 10%. المعالج الذهبي للاحمرار وحب الشباب والتصبغ في منتج واحد.',
                'full_description': 'تعليق ناعم من حمض الأزيليك 10% الطبيعي المشتق من الحبوب. يعالج الوردية والاحمرار والحبوب والتصبغ في آنٍ واحد. آمن للحمل والرضاعة. الخيار الأول للبشرة الحساسة.',
                'hydration_level': 40, 'exfoliation_power': 20, 'sensitivity_safety': 85, 'absorption_speed': 78,
                'texture': 'cream', 'dosage': 'pea', 'skin_state_before': 'damp', 'wait_seconds': 60,
                'safe_pregnancy': True, 'fragrance_free': True, 'non_comedogenic': True,
                'requires_sunscreen': False,
                'package_color': '#fef9c3',
                'image_url': 'https://i.imgur.com/Xh0ZPGv.jpg',
                'skin_types': ['sensitive', 'oily', 'combination', 'normal'],
                'concerns': ['redness', 'acne', 'pigmentation'],
                'ingredients': ['azelaic_acid', 'niacinamide'],
                'beginner_schedule': 'ابدأ بمرة يومياً. النتائج تظهر بعد 4 أسابيع. يمكن الاستخدام مرتين يومياً بعد التكيف.',
            },
        ]

        # Create products
        for pd in product_data:
            skin_type_slugs = pd.pop('skin_types', [])
            concern_slugs = pd.pop('concerns', [])
            ingredient_slugs = pd.pop('ingredients', [])

            p = Product.objects.create(
                name=pd['name'], brand=pd['brand'], slug=pd.get('slug', ''),
                volume_ml=pd.get('volume_ml', ''),
                routine_step=pd['routine_step'], use_time=pd['use_time'],
                price_yer=pd['price_yer'], price_sar=pd['price_sar'], price_usd=pd['price_usd'],
                badge=pd.get('badge', ''),
                short_description=pd.get('short_description', ''),
                full_description=pd.get('full_description', ''),
                hydration_level=pd.get('hydration_level', 50),
                exfoliation_power=pd.get('exfoliation_power', 0),
                sensitivity_safety=pd.get('sensitivity_safety', 70),
                absorption_speed=pd.get('absorption_speed', 80),
                texture=pd.get('texture', 'cream'),
                dosage=pd.get('dosage', 'pea'),
                skin_state_before=pd.get('skin_state_before', 'damp'),
                wait_seconds=pd.get('wait_seconds', 60),
                safe_pregnancy=pd.get('safe_pregnancy', False),
                fragrance_free=pd.get('fragrance_free', False),
                non_comedogenic=pd.get('non_comedogenic', False),
                requires_sunscreen=pd.get('requires_sunscreen', False),
                safety_warning=pd.get('safety_warning', ''),
                package_color=pd.get('package_color', '#5c8a6e'),
                image_url=pd.get('image_url', ''),
                beginner_schedule=pd.get('beginner_schedule', ''),
                application_steps=pd.get('application_steps', ''),
                restricted_areas=pd.get('restricted_areas', ''),
                inci_list=pd.get('inci_list', ''),
            )
            for st_slug in skin_type_slugs:
                if st_slug in skin_types:
                    p.skin_types.add(skin_types[st_slug])
            for c_slug in concern_slugs:
                if c_slug in concerns:
                    p.skin_concerns.add(concerns[c_slug])
            for i_slug in ingredient_slugs:
                if i_slug in ings:
                    p.active_ingredients.add(ings[i_slug])
            products_created[pd['slug']] = p
            self.stdout.write(f'  ✓ {pd["brand"]} — {pd["name"]}')

        # Set pairs_well_with relationships
        pairs = [
            ('cerave-hydrating-cleanser', 'to-hyaluronic-acid-2-b5'),
            ('to-niacinamide-10-zinc', 'cerave-moisturizing-cream'),
            ('to-glycolic-toning-solution', 'cerave-moisturizing-cream'),
            ('to-retinol-05-squalane', 'cerave-moisturizing-cream'),
            ('lrp-pure-vitamin-c-15', 'lrp-anthelios-uvmune-400-spf50'),
            ('to-alpha-arbutin-2-ha', 'lrp-pure-vitamin-c-15'),
            ('paulaschoice-bha-2-solution', 'to-niacinamide-10-zinc'),
        ]
        for slug_a, slug_b in pairs:
            if slug_a in products_created and slug_b in products_created:
                products_created[slug_a].pairs_well_with.add(products_created[slug_b])

        # ── 7. Routine Bundles ─────────────────────────────────────────────
        self.stdout.write('📦 إنشاء الباقات الجاهزة...')
        bundles_data = [
            {
                'name': 'باقة القضاء على حب الشباب والمسام',
                'slug': 'acne-fighting-bundle',
                'description': 'باقة متكاملة مصممة علمياً للقضاء على حب الشباب والرؤوس السوداء وتقليص المسام الواسعة. تجمع بين أقوى المنقيات وأفضل المعالجات.',
                'discount_percent': 15,
                'concern': 'acne',
                'products': ['larochep-effaclar-foaming-gel', 'paulaschoice-bha-2-solution', 'to-niacinamide-10-zinc', 'lrp-effaclar-mat', 'lrp-anthelios-uvmune-400-spf50'],
            },
            {
                'name': 'باقة التفتيح والنضارة الفائقة',
                'slug': 'brightening-bundle',
                'description': 'روتين علمي متكامل لمعالجة التصبغ والكلف وآثار الحبوب وتحقيق إشراق ونضارة لافتين. يجمع بين أقوى مواد التفتيح الآمنة.',
                'discount_percent': 12,
                'concern': 'pigmentation',
                'products': ['cerave-hydrating-cleanser', 'to-alpha-arbutin-2-ha', 'lrp-pure-vitamin-c-15', 'cerave-moisturizing-cream', 'lrp-anthelios-uvmune-400-spf50'],
            },
            {
                'name': 'باقة ترميم الحاجز وعلاج الجفاف',
                'slug': 'barrier-repair-bundle',
                'description': 'باقة العلاج المكثف للبشرة الجافة والمتضررة من الإفراط في التقشير أو المواد القاسية. تصلح الحاجز الجلدي وتعيد الترطيب بعمق.',
                'discount_percent': 10,
                'concern': 'dryness',
                'products': ['cerave-hydrating-cleanser', 'to-hyaluronic-acid-2-b5', 'cerave-moisturizing-cream', 'eucerin-sunscreen-spf50-invisible'],
            },
        ]
        for bd in bundles_data:
            product_slugs = bd.pop('products')
            concern_slug = bd.pop('concern')
            bundle = RoutineBundle.objects.create(
                name=bd['name'], slug=bd['slug'],
                description=bd['description'],
                discount_percent=bd['discount_percent'],
                skin_concern=concerns.get(concern_slug),
                is_active=True,
            )
            for ps in product_slugs:
                if ps in products_created:
                    bundle.products.add(products_created[ps])
            self.stdout.write(f'  ✓ {bd["name"]}')

        # ── 8. Create Admin User ───────────────────────────────────────────
        self.stdout.write('👤 إنشاء حساب المدير...')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@remshy.com', 'admin12345')
            self.stdout.write('  ✓ admin / admin12345')
        else:
            self.stdout.write('  ℹ️  المدير موجود مسبقاً')

        self.stdout.write(self.style.SUCCESS('\n✅ تمت التعبئة التلقائية بنجاح!'))
        self.stdout.write(self.style.SUCCESS(f'   → {Product.objects.count()} منتج'))
        self.stdout.write(self.style.SUCCESS(f'   → {ActiveIngredient.objects.count()} مادة فعالة'))
        self.stdout.write(self.style.SUCCESS(f'   → {IngredientConflict.objects.count()} تعارض كيميائي'))
        self.stdout.write(self.style.SUCCESS(f'   → {IngredientSynergy.objects.count()} تناغم كيميائي'))
        self.stdout.write(self.style.SUCCESS(f'   → {RoutineBundle.objects.count()} باقة روتين'))
        self.stdout.write(self.style.SUCCESS('   → الموقع جاهز! شغّل: python manage.py runserver'))

