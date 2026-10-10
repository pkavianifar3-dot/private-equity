# گام ۵ — تصمیم‌های تحریریه‌ای و آماده‌سازی محلی انتشار

تاریخ بررسی: ۲۰۲۶-۱۰-۱۱. شاخه: `feat/research-content-ingestion-foundation`.
HEAD مبنا: `3bbbfb11d417e3f8f291a0842ba2c35154b0b3fc`.

**وضعیت: آماده‌سازی محلی انجام شده، انتشار نهایی باز است.**

این گزارش اجرای محلی prompt a و prompt b را ثبت می‌کند. فایل‌ها در پوشهٔ `step 5/files` یافت شدند؛ مسیر `articles/3rd` ذکرشده در پیام، محل واقعی این دو فایل نبود. هیچ commit، push، merge، deploy، تغییر تنظیمات یا بازنویسی تاریخچه انجام نشده است. فعال‌سازی `PAGES_RELEASE_ENABLED` انجام نشده؛ بررسی مجدد تنظیمات ریموت پیش از انتشار لازم است. نتیجهٔ CI قدیمی، نتیجهٔ تغییرات ثبت‌نشدهٔ حاضر نیست.

## تصمیم‌ها و دامنهٔ محتوای قابل انتشار

از ۲۷ Entity، اکنون ۱۲ مورد PUBLISHED و ۱۵ مورد REVIEW هستند. ۱۱ مورد از REVIEW به PUBLISHED منتقل شدند؛ علی سنگینیان از قبل PUBLISHED بود. عمومی‌شدن یک معرفی پایه، تأیید تمام روابط، ارقام، هویت‌های حقوقی یا سوابق مرتبط با آن نیست.

| Entity | قبل ← بعد | شاهد و دامنهٔ پذیرفته‌شده / اقدام باقی‌مانده |
| --- | --- | --- |
| `concept:private-capital` | REVIEW ← PUBLISHED | CFA: مالکانه و بدهی؛ Preqin: دامنهٔ وسیع‌تر. تعریف عمومی ادعای طبقه‌بندی جهانی ندارد. |
| `concept:private-equity` | REVIEW ← PUBLISHED | ECB، بخش معرفی بازارها و راهبردها؛ سرمایه‌گذاری مالکانه و راهبردهای VC، رشد و تملک. |
| `concept:private-credit` | REVIEW ← PUBLISHED | ECB: بدهی خصوصی؛ CFA: private debt. تفاوت اصطلاح و چارچوب حفظ شده است. |
| `concept:real-assets` | REVIEW ← PUBLISHED | CFA آن را جدا از private capital فهرست می‌کند؛ دامنهٔ گسترده‌تر Preqin شامل این حوزه‌هاست. رابطهٔ اطلس جمع‌بندی منتسب است. |
| `concept:venture-capital` | REVIEW ← PUBLISHED | راهبرد PE نزد ECB؛ مدخل جداگانه در فهرست Preqin. |
| `concept:growth-capital` | REVIEW ← PUBLISHED | راهبرد سرمایه مالکانه نزد ECB؛ رابطهٔ INCLUDES به معنای دامنه، نه طبقهٔ هم‌سطح مستقل. |
| `concept:private-market-access` | REVIEW ← PUBLISHED | روش‌های صندوقی، مستقیم و هم‌سرمایه‌گذاری در CFA؛ ساختار صندوق در Preqin. محدودیت دسترسی مطلق نیست. |
| `concept:private-capital-classification` | REVIEW ← PUBLISHED | مقایسهٔ تحریریه‌ای CFA/Preqin؛ تصمیم مدل‌سازی داخلی، نه مفهوم اجماعی مستقل. |
| `concept:lender` | REVIEW ← REVIEW | تعریف مستقل و شواهد مختص مدخل تکمیل نشده؛ غیرعمومی. |
| `concept:contractual-components` | REVIEW ← REVIEW | مرز و تعریف مستقل روشن نشده؛ غیرعمومی. |
| `concept:physical-assets` | REVIEW ← REVIEW | تمایز کافی از real-assets و تعریف مستقل موجود نیست؛ غیرعمومی. |
| `organization:achareh` | REVIEW ← PUBLISHED | وب‌سایت آچاره، عنوان صفحه و دسته‌های خدمات؛ صرفاً هویت عملیاتی پلتفرم. طرف حقوقی معامله کیسون احراز نشده است. |
| `organization:amin-investment-bank` | REVIEW ← PUBLISHED | وب‌سایت امین، خدمات تأمین مالی/مشاوره/دارایی/ارزش‌گذاری؛ تاریخ سمت‌ها از این معرفی نتیجه نمی‌شود. |
| `organization:kian-financial-group` | REVIEW ← PUBLISHED | وب‌سایت کیان، «خدمات گروه مالی کیان در یک قاب»؛ هویت شرکت مستقل مدیریت سهام خصوصی اثبات نمی‌شود. |
| `organization:iran-farabourse` | REVIEW ← REVIEW | مدرک مناسب برای معرفی مستقل در این بررسی به‌طور کافی احراز نشد؛ تکمیل منبع مستقیم لازم است. |
| `organization:semega` | REVIEW ← REVIEW | شواهد تاریخی شخص، جای معرفی سازمان را نمی‌گیرد؛ منبع مستقیم معرفی پایه لازم است. |
| `organization:tourism-bank` | REVIEW ← REVIEW | سابقهٔ تاریخی هیئت‌مدیره، معرفی پایه و هویت فعلی را به‌تنهایی ثابت نمی‌کند؛ منبع مستقیم لازم است. |
| `organization:kayson-group` | REVIEW ← REVIEW | ابهام هویت حقوقی/طرف معامله؛ حل ابهام پیش از انتشار. |
| `organization:kian-private-equity-management` | REVIEW ← REVIEW | نام و هویت حقوقی مستقل باید احراز شود؛ گروه مالی جایگزین این Entity نیست. |
| `organization:tehran-chamber-money-capital-commission` | REVIEW ← REVIEW | OrganizationUnit؛ عمومی‌سازی این نوع مجاز نشده و هویت/بازهٔ ساختار باید بررسی شود. |
| `project:dadman` | REVIEW ← REVIEW | Project فقط محلی؛ دامنهٔ دو رقم تأمین مالی احراز نشده است. |
| `investment:kayson-achareh` | REVIEW ← REVIEW | ۷۲۰ میلیارد ریال حفظ شده؛ برند آچاره و شرکت حقوقی اشاره‌شده در خبر یکسان فرض نشده‌اند. |
| `sector:capital-market` | REVIEW ← REVIEW | بدون مسیر عمومی طبق قرارداد تأییدشده. |
| `sector:corporate-investment` | REVIEW ← REVIEW | بدون مسیر عمومی طبق قرارداد تأییدشده. |
| `sector:investment-banking` | REVIEW ← REVIEW | بدون مسیر عمومی طبق قرارداد تأییدشده. |
| `sector:private-equity` | REVIEW ← REVIEW | بدون مسیر عمومی؛ با Concept همنام ادغام نشده است. |
| `person:ali-sanginian` | PUBLISHED ← PUBLISHED | معرفی عمومی محدود: سمت امین در مصاحبه آذر ۱۳۹۱ و گزارش ۹ تیر ۱۳۹۵. آغاز/پایان دوره، نویسندگی انحصاری قانون، تأسیس بورس کیش یا دریافت شخصی نشان، واقعیت قطعی منتشر نشده‌اند. |

## منابع، اتصال‌ها و تاریخچه

تعریف‌ها در قابلیت موجود `metadata.public_profile` همراه `sourceRefs`، locator و تاریخ بررسی قرار گرفته‌اند؛ schema یا وضعیت جدیدی ایجاد نشده است. تعریف‌های تحریریه‌ای از ادعای رابطه‌ای تفکیک می‌شوند. Evidence موجود فقط Claim را هدف می‌گیرد؛ برای تعریف، predicate جدید یا Claim صوری ساخته نشده است.

| منبع بررسی‌شده | اتصال canonical | محدودیت |
| --- | --- | --- |
| `source:cfa-alternative-investment-features-2026` | تعریف‌های private-capital، private-credit، real-assets، access، classification؛ Evidence نسخه‌های جدید روابط PE/debt، real-assets، access و classification | چارچوب CFA؛ رابطهٔ real-assets از جمع‌بندی مقایسه‌ای می‌آید، نه تأیید سلسله‌مراتب اطلس توسط CFA. |
| `source:preqin-what-is-private-capital` | تعریف‌ها و Evidence روابط PE/debt، real-assets، VC، access و classification | دامنهٔ Preqin؛ با CFA یکی فرض نشده. شناسهٔ موجود دوباره ساخته نشده است. |
| `source:ecb-private-markets-public-risk` | تعریف‌های PE، credit، VC، growth؛ Evidence رابطهٔ growth و پیوند credit/PE | راهبرد با طبقهٔ دارایی یکسان فرض نشده است. |
| `source:deloitte-asian-investment` | citation نمودار/پاراگراف مقاله و فهرست منابع Research | منبع نقل‌کنندهٔ ارقام Global SWF؛ نه شاهد بازرسی مستقل دادهٔ اولیه. |
| `source:globalswf-reports` | سرنخ داخلی فهرست گزارش‌ها | مجموعهٔ اولیهٔ عددی مستقیماً احراز نشد؛ وارد بستهٔ عمومی نشده است. |
| سه `*-official-profile` آچاره/امین/کیان | `metadata.public_profile` همان سازمان، همراه محل متن معرفی و خدمات | متن صفحه بررسی شد؛ موفقیت HTTP به‌تنهایی مبنای تأیید نبوده است. |
| `source:sanginian-market-capital-interview-1391` | معرفی محدود علی سنگینیان، صفحات چاپی ۶۴ و ۶۸ | PDF مصاحبه پنج‌صفحه‌ای شماره ۳۳؛ سال پوشهٔ میزبان، تاریخ مصاحبه نیست. اظهارات شخصی دلیل تأیید مستقل همهٔ سوابق نیستند. |
| `source:tehran-chamber-independent-report` | معرفی شخص و Evidence `evidence:ali-ceo-amin-observed-1395` | مشاهدهٔ سمت در تاریخ گزارش، نه اثبات دورهٔ کامل. |

۹ Claim جانشین در `atlas/claims/stage-5-reviewed.json` و ۱۴ Evidence در فایل هم‌نام Evidence ثبت شدند. Claimهای قبلی و Evidence آن‌ها حذف یا بازنویسی نشدند. روابط جدید SUPPORTED هستند؛ روابط جمع‌بندی/مقایسه confidence=MEDIUM دارند. Claim مربوط به امین اکنون زمان observed با start/end نامعلوم دارد. REVIEW به وضعیت Claim اضافه نشده و کمبود شاهد DISPUTED نامیده نشده است.

Source بازنشر امین از معرفی نادرست به‌عنوان منبع شرکتی اصلاح شد؛ Shakhesban دادهٔ تاریخی بازار است، نه وب‌سایت بانک. تاریخ‌های احرازنشده اختراع نشده‌اند.

ارقام نمودار ۲٫۸ و ۶٫۸ تریلیون دلار در ۲۰۱۴ و ۲۰۲۳ حفظ شدند؛ caption جامعهٔ صندوق‌های ثروت ملی و بازنشستگی عمومی، بازارهای خصوصی، بازه و واحد را بیان می‌کند. انتساب «Global SWF، به نقل از Deloitte» و محدودیت بررسی دادهٔ اولیه صریح است.

اطلاعات ۴۴۶ میلیارد تومان مرحلهٔ نخست دادمان و ۵٫۵ همت ادغام نشده‌اند؛ ارقام ۱۰۰ مگاوات/۵۰ میلیون دلار و ۲۰۰ مگاوات/۹۰ میلیون دلار نیز جدا و غیرعمومی مانده‌اند. معرفی پایه کیان، شاهد انتشار این ارقام نشده است. هیچ Entity جدید ساخته نشده است.

## مرز عمومی و URL

`tools/public_projection.py` فقط هنگام بسته‌بندی release، نمای مشتق‌شدهٔ عمومی را می‌سازد؛ دادهٔ canonical و indexهای داخلی کامل می‌مانند. خروجی قابل ویرایش به منبع حقیقت دوم تبدیل نشده است. چهار نوع مسیر عمومی قبلی و IDها حفظ شده‌اند.

عمومی‌شدن صفحهٔ پایه به‌تنهایی Claimهای آن را منتشر نمی‌کند: فقط نسخهٔ جاری، با دو سر عمومی، وضعیت مجاز، Evidence قابل‌حل، locator و Source دارای URL وارد نمای عمومی می‌شود. REPORTED انتساب لازم دارد. هیچ edge به Entity پنهان، domain پنهان یا روایت قدیمی تأییدنشدهٔ شخص در بسته نیست.

JSON عمومی، نمای جاری برای runtime است و دفتر canonical تاریخچه نیست. `revision` نسخهٔ اصلی باقی می‌ماند، اما `supersedes` به نسخهٔ تاریخی غیرمنتشرشده از این نمای مشتق حذف می‌شود. قواعد کامل زنجیرهٔ تاریخچه بر canonical، پیش از build، اجرا می‌شوند؛ JSON خروجی جایگزین canonical یا ورودی validator تاریخچه نیست. نسخهٔ پیشین در مخزن باقی است. این تفاوت قرارداد export باید در مصرف‌کننده‌های آینده حفظ شود.

مسیرهای ۱۲ Entity عمومی با نام قبلی حفظ می‌شوند. ۹ صفحهٔ static قدیمیِ REVIEW و aliasهای `index.html` آن‌ها در artifact نیستند و 404 واقعی می‌دهند. ۶ Entity بدون مسیر عمومی همچنان بدون مسیر هستند. هیچ redirect غیرمعادل یا مسیر جدیدی ایجاد نشده است. queryهای Entity عمومی محتوای همان صفحهٔ بررسی‌شده را reuse می‌کنند؛ queryهای پنهان/ناموجود، پیام عمومی یافت‌نشدن و noindex بدون fetch جزئیات دارند. HTTP200 پوستهٔ مشترک در میزبانی استاتیک همچنان محدودیت واقعی است.

Research مستقل PUBLISHED می‌ماند. Resolver همهٔ مقاله‌ها فقط Entity عمومی را لینک می‌کند؛ استثنای قدیمی مقالهٔ راهنمای سرمایه خصوصی برداشته شده است. لینک‌های معتبر قبلی حفظ و اتصال معکوس منتشرشده بازسازی شد. جدول دقیق مسیرها در `stage-5-url-disposition.md` است.

## انتقال فایل‌های تحریریه‌ای

چهار فایل پیش از حذف از نسخهٔ جاری، با تطبیق SHA-256 به مسیر زیر کپی شدند:

`C:\Users\No1\architecture-v3-private\editorial\private-capital-research\`

| فایل | SHA-256 |
| --- | --- |
| `editorial-review.json` | `044be854a8aebd9a010a5b5f9f3a33144e14d23f9552b09c2174ceef033911ab` |
| `private-capital-claims-v1.json` | `2e1196b3659d89fcdc86598d2ee2f05463016507643dbe2bc3c39391cf72afaa` |
| `private-capital-mapping-v1.json` | `de40c9f2e0c4d98c6bc853b44197ceb1823442d4657ff0e816f0ed75a5cc8327` |
| `private-capital-sources-v1.json` | `50b1892f8959257b13fee57e9dd3258eb0cae065040b92158cf62d18e90e2d6c` |

مسیر نسبی کامل فایل‌ها در `copy-manifest.json` مقصد ثبت است. فایل‌ها وابستگی لازم build/validator نیستند؛ اسکریپت مهاجرت اختیاری اکنون `--mappings-dir` برای آرشیو خارجی می‌گیرد. آرشیو نسخهٔ canonical نیست. تاریخچه و نسخه‌های فعلی ریموت همچنان این اطلاعات را دارند؛ این انتقال پاک‌سازی تاریخچه یا تضمین محرمانگی نیست.

## Verification و انتشار واقعی

اجرای کامل `tools/release.py verify` موفق: validator، ۱۸۳ تست Python، ۲۱ فایل آزمون JavaScript، syntax check تمام JS مرورگر، پنج builder، sitemap، drift، ۸۱۰ بررسی لینک/runtime و ۱۳۵ بررسی HTTP. ۹ آزمون جدید Python بستهٔ عمومی و آزمون JS رد query غیرمجاز/سازگاری query مجاز اضافه شدند. آزمون‌های شمارش ثابت قدیمی با کنترل index و محدودکردن شمارش لینک به متن مقاله اصلاح شدند؛ کنترل منفی REVIEW حفظ شده است.

بستهٔ نهایی بررسی‌شده: ۹۱ فایل، ۳۱ صفحهٔ HTML، ۲۵ URL sitemap، صفر publication blocker و صفر transport retry در smoke نهایی. چند آزمون HTTP با fixture عمداً retry/خطای انتقال را پوشش می‌دهند؛ نتیجهٔ آن‌ها با retry بستهٔ نهایی اشتباه نشود. هش بسته:

`18bb57bb9ed7ba957f69056ab0f08a4335e0ad871bb342cbdc16817bef214696`

مسیر محلی artifact: `%TEMP%\privatecapital-stage5-20261011-public-final3`؛ manifest هم‌نام در کنار آن است. manifest commit مبنا و dirty working tree را ثبت می‌کند؛ این خروجی در commit فعلی ثبت نشده و CI ریموت تغییرات حاضر اجرا نشده است. آماده‌بودن artifact، وضعیت production را تغییر نمی‌دهد.

برای انتشار واقعی هنوز لازم است:

1. بازبینی و مجوز جداگانهٔ commit/push، سپس نتیجهٔ CI همان commit.
2. پیش از ادغام main، تغییر تأییدشدهٔ Pages از main/root به GitHub Actions؛ publisher شاخه‌ای، دروازه‌های جدید را دور می‌زند.
3. بررسی دستی حفاظت محیط github-pages و مجوز انتشار از main؛ فعال‌سازی جداگانهٔ متغیر فقط پس از تأیید انتشار.
4. بررسی DNS دامنه، وضعیت گواهی GitHub و Enforce HTTPS؛ موفقیت HTTPS از Cloudflare اثبات سلامت TLS مبدأ نیست. این نوبت وضعیت ریموت دوباره بازرسی نشده است.
5. تصمیم مالک دربارهٔ محرمانگی داده‌های باقی‌مانده در تاریخچهٔ عمومی و نگهداری امن آرشیو خصوصی؛ visibility/history دست‌کاری نشده است.

موانع تکمیل Entityهای غیرعمومی، مانع انتشار بستهٔ پاک نیستند؛ شواهد و معرفی آن‌ها می‌توانند بعداً تکمیل شوند. گام ۶ آغاز نشده است.

پیشنهاد commit: `feat(release): prepare evidence-backed public projection and safe URL cutover`
