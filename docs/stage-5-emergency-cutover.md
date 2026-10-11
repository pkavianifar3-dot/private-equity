# گام ۵ — بستهٔ اضطراری مستقل و ترتیب cutover

## انتخاب نسخهٔ بازگشت

نسخهٔ فعلی `main/root` شامل داده‌های قدیمی REVIEW است؛ حفظ عین آن، بستهٔ عمومی
مطابق سیاست انتشار نمی‌سازد. بستهٔ عمومی جدید نیز هنوز نسخه‌ای با سلامت اثبات‌شده
روی production نیست. بنابراین برای نخستین انتشار یک fallback مستقل **اضطراری**
آماده شده؛ این نسخه بازگشت کامل امکانات سایت نیست.

بستهٔ اضطراری دقیقاً چهار فایل دارد: `index.html`، `404.html`، `CNAME` و `robots.txt`.
صفحهٔ اصلی با عنوان «نسخهٔ اضطراری» وضعیت بازیابی را توضیح می‌دهد؛ صفحهٔ 404 به
خانه لینک دارد. متن راست‌به‌چپ و responsive است، سبک‌ها inline هستند و هیچ script،
font خارجی، API، Entity، Claim، canonical JSON یا دادهٔ Research مصرف نمی‌شود.
این نسخه noindex است و robots آن پیمایش را منع می‌کند؛ دامنه تغییر نمی‌کند.

### چه چیزی حفظ می‌شود؟

دسترسی به خانهٔ دامنه، هویت سایت، اطلاع‌رسانی روشن و پاسخ 404 مناسب. HTTPS و
دامنه از تنظیمات Pages موجود استفاده می‌کنند؛ bundle تنظیمات آن‌ها را تغییر نمی‌دهد.

### چه چیزی وجود ندارد؟

مقالات، اطلس، جستجو، کاوش، صفحات خدمات/تماس و دیگر امکانات عادی. URLهای آن‌ها
redirect نمی‌شوند و در وضعیت اضطراری پاسخ 404 خواهند داشت. این افت خدمت، موقت و
صریح است؛ جایگزین حفظ کامل سایت قدیمی محسوب نمی‌شود. noindex بودن نسخه نیز می‌تواند
بر ایندکس اثر بگذارد؛ بعد از رفع مشکل باید بستهٔ عمومی سالم دوباره منتشر شود.

## جداسازی و کنترل منبع

templateها در `tools/release/emergency-site/` هستند و allowlist بستهٔ عادی شامل
آن‌ها نیست. بستهٔ اضطراری به directory و artifact جدا نوشته می‌شود؛ manifest نیز
خارج از فایل‌های سایت است. artifact اضطراری نام زیر را دارد:

`emergency-recovery-<BUILD_SHA>-<RUN_ID>-<ATTEMPT>`

manifest دارای `kind=emergency` است. workflow ورودی صریح `recovery_kind` دارد؛
درخواست public برای artifact اضطراری یا برعکس رد می‌شود. کنترل‌های مشترک run،
SHA، مخزن، workflow fingerprint، branch main، digest و expiry حفظ شده‌اند. علاوه
بر هش، تمام بایت‌ها با templateهای تأییدشدهٔ SHA مبنا مقایسه و قرارداد مستقل
چهارفایلی اجرا می‌شود. canonical input یا ابزارها به خروجی تبدیل نمی‌شوند.

آرشیو اضطراری هم ۳۰ روز retention درخواست می‌کند؛ expiry واقعی و دانلود دوبارهٔ
همان artifact در CI بررسی می‌شوند. artifactهای feature/PR فقط شاهد آزمون هستند
و برای deploy یا production recovery پذیرفته نمی‌شوند. تولید و نگهداری با گیت
خاموش مجاز است؛ deploy همچنان مجوز جداگانه و Environment را لازم دارد.

## ترتیب نهایی و نقطه‌های توقف

1. CI آخرین feature SHA و PR باید موفق باشد؛ دانلود/بازیابی هر دو bundle در CI
   موفق و محتوای صفحهٔ اضطراری مورد تأیید مالک باشد.
2. مالک حفاظت `main` را تنظیم کند: PR، check دقیق **validate-atlas** از GitHub
   Actions، شاخهٔ به‌روز، رفع conversationها، منع force-push/deletion/bypass.
3. مالک Environment **github-pages** را به main بدون tag محدود کند؛ Required
   reviewer و منع admin bypass. با بازبین دوم Prevent self-review روشن؛ برای
   مالک تنها خاموش باشد و approval ناممکن برای PR الزام نشود.
4. مالک محدودیت fallback و روش آزموده‌شده را تأیید کند. ضبط SHA/deployment سالم
   فعلی و نبود اجرای قدیمیِ در جریان لازم است. گیت خاموش بماند.
5. فقط با تأیید این پیش‌شرط‌ها، مالک Source را **پیش از merge** به Actions تغییر
   دهد؛ دامنه، DNS و HTTPS دست‌نخورده بمانند. بازشدن سایت فعلی دوباره بررسی شود؛
   در صورت اختلال، merge متوقف و وضعیت Pages بررسی شود. صفر downtime تضمین نشده.
6. با مجوز جداگانه PR ادغام شود. اجرای push روی **SHA جدید main**، با گیت خاموش،
   هم بستهٔ عمومی و هم اضطراری را می‌سازد، archive/download/rehearse می‌کند و
   deploy نمی‌کند. run باید completed/success باشد. شناسهٔ دقیق artifact اضطراری،
   Run ID، SHA، attempt، manifest و expiry آن ثبت شود. پیش از نخستین deploy هیچ
   bundle منقضی یا متعلق به feature را جایگزین این baseline نکنید.
7. **dry-run معتبر main** اجرا شود: در `Validate Atlas / Run workflow` شاخه main
   و ورودی‌های جدول زیر انتخاب شوند. اجرای recover-prepare باید موفق باشد؛
   pages upload و deploy باید skipped بمانند. همین آزمون برای بستهٔ public هم
   پیشنهاد می‌شود. شکست این مرحله، مانع نخستین deploy است.
8. فقط پس از موفقیت مرحلهٔ ۷، مجوز جداگانهٔ مالک برای نخستین deploy عادی لازم
   است: run دستی جدید روی main، recovery_run_id خالی، release_authorized=true
   و گیت موقتاً روشن؛ تأیید Environment پس از بررسی SHA/artifact.
9. خانه، Research، Atlas، assets، canonical، sitemap، 404 و HTTPS روی سایت واقعی
   بررسی شوند. اگر سالم است گیت خاموش و runهای اضافه لغو شوند؛ شناسهٔ این نسخه
   به‌عنوان baseline کامل و سالم ثبت شود.

### ورودی‌های dry-run اضطراری

| ورودی | مقدار |
| --- | --- |
| Branch | `main` |
| `recovery_run_id` | Run ID موفق main از مرحلهٔ ۶ |
| `recovery_artifact_id` | شناسهٔ artifact با پیشوند `emergency-recovery-` همان run |
| `recovery_sha` | SHA کامل مبنای همان bundle |
| `recovery_kind` | `emergency` |
| `recovery_dry_run` | `true` |
| `release_authorized` | `false` |
| `PAGES_RELEASE_ENABLED` | خاموش |

## فعال‌کردن اضطراری پس از خرابی

با مجوز جداگانه، ورودی‌های شناسهٔ همان bundle حفظ می‌شوند؛ اجرا از main فعلی،
`recovery_kind=emergency`، `recovery_dry_run=false`، `release_authorized=true` و
گیت موقتاً روشن. Environment باید deployment را تأیید کند. قبل از deploy، Source
Actions، main HEAD و حفاظت‌ها دوباره بررسی می‌شوند. تنها directory چهارفایلی به
قالب رسمی Pages تبدیل می‌شود؛ Source هرگز به main/root برگردانده نمی‌شود.

پس از فعال‌شدن اضطراری، رفع مشکل با PR و CI انجام می‌شود و بستهٔ عمومی سالم از
همین مسیر دستی منتشر می‌شود. خاموش‌کردن متغیر جای لغو runهای معلق را نمی‌گیرد.
اگر workflow عوض شده و fingerprint bundle قبلی دیگر معتبر نیست، توقف و بازبینی
سازگاری لازم است؛ کنترل اعتماد برای سبزشدن CI دور زده نمی‌شود.

## مرز شواهد

آزمون محلی و CI feature می‌توانند استقلال محتوا، HTTP خانه/404، hashing، manifest،
archive/download/restore و tar را اثبات کنند. تا ادغام، اجرای main تولیدکنندهٔ
این بسته وجود ندارد. پذیرش منبع main در recovery، checkout تاریخی، تأیید
Environment و رفتار واقعی Pages پس از deploy باید در مراحل مجاز بعدی بررسی شوند.
هیچ موفقیت feature معادل بازیابی production اعلام نمی‌شود.

## ?????? ????? ???? ??? ?????

validator? ???? ??? ????? Python (?? ???? recovery ?????/???????)? ???? ?? ????
????? JavaScript? syntax? ??? builder? sitemap ? drift ???? ????. ????? ?????
?????? ?? ???? ? ???? ?? ???? ?? ????? ??? ????? ????/runtime ? ??? ????? HTTP
???? retry ? publication blocker ???? ???. actionlint ? diff check ??? ????????.
?????? CI ?????? commit ?????? ??????? ????? ??????? ??? ???? ????? deploy ??
??????? production ????.
