# Research — Current Architecture Baseline

این پوشه زیرساخت فعلی بخش Research سایت Private Capital را نگهداری می‌کند.

این فایل وضعیت پایه معماری Research را ثبت می‌کند تا تغییرات بعدی مرحله‌به‌مرحله و قابل بازگشت انجام شوند.

## Current Structure

```text
research/
├── index.json
├── schemas/
│   └── research-schema-v1.json
├── content/
│   └── private-capital.json
└── mappings/
    ├── private-capital-claims-v1.json
    ├── private-capital-mapping-v1.json
    └── private-capital-sources-v1.json
```

## Current Responsibilities

### index.json

Registry فعلی Research Documents را نگهداری می‌کند.

در حال حاضر دو Research منتشرشده ثبت شده‌اند:

* `research:private-capital`
* `research:private-equity`

### schemas/research-schema-v1.json

قرارداد فعلی ساختار Research Document است.

### content/

منبع داده Research Documents فعلی است.

در حال حاضر:

```text
content/private-capital.json
```

مدل ساختاریافته مقاله «سرمایه خصوصی» را نگهداری می‌کند.

### mappings/

این پوشه اطلاعات تحلیلی و موقت مربوط به Mapping پژوهش را نگهداری می‌کند:

* Candidate Concepts / Entity Mapping
* Research Claims
* Candidate Sources

این داده‌ها در وضعیت فعلی هنوز بخشی از Canonical Atlas نیستند.

## Architectural Boundary

در معماری فعلی، Atlas و Research دو لایه متفاوت هستند.

Atlas باید مرجع canonical برای Entity، Claim، Evidence و Source باشد.

Research نباید Entity یا Claim canonical را دوباره تعریف کند.

Research باید بتواند به داده‌های canonical Atlas با Reference متصل شود.

## Current Research Document

`research:private-capital` در حال حاضر شامل این بخش‌های اصلی است:

```text
Identity
Title
Summary
Publication
Entity References
Claim References
Evidence References
Source References
Related Research References
Sections
```

## Current State

وضعیت فعلی Research هنوز مدل نهایی سیستم دانش نیست.

به‌خصوص:

* Candidate Concepts هنوز با Entityهای canonical یکسان نیستند.
* Research Claims فعلی هنوز Claimهای canonical Atlas نیستند.
* Candidate Sources هنوز الزاماً Sourceهای canonical Atlas نیستند.
* ساختار Section هنوز حداقلی است.
* ارتباط معنایی متن با Entityها هنوز به‌صورت مستقل مدل نشده است.

این موارد عمداً در این مرحله تغییر داده نمی‌شوند.

## Freeze Rules

تا پایان طراحی Research v2:

1. فایل‌های HTML مقالات فعلی نباید صرفاً برای تغییر معماری داده اصلاح شوند.
2. CSS و ظاهر مقالات نباید تغییر کند.
3. Atlas نباید بازطراحی شود.
4. Candidate Entityها نباید مستقیماً به Canonical Atlas تبدیل شوند.
5. Mappingهای فعلی نباید بدون طراحی مدل جدید حذف شوند.
6. هر تغییر معماری در Commit مستقل انجام شود.
7. تغییرات هر مرحله باید بعد از تست قابل rollback باشند.

## Next Phase

مرحله بعد:

**Define the Research Domain Model**

در آن مرحله مدل مفهومی Research، Section، Mention، Reference و ارتباط آنها با Atlas قبل از ایجاد `research-schema-v2` تعریف خواهد شد.
