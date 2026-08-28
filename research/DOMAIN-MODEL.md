# Research Domain Model

این سند مدل مفهومی بخش Research را تعریف می‌کند.

این مدل قبل از ایجاد `research-schema-v2` تثبیت می‌شود.

---

## 1. Research

Research یک سند پژوهشی مستقل و قابل انتشار است.

Research مالک Entityهای Atlas نیست.

Research فقط می‌تواند به Entity، Claim، Evidence و Sourceهای canonical ارجاع دهد.

```text
Research
├── metadata
├── sections
├── entityRefs
├── claimRefs
├── sourceRefs
├── relatedResearchRefs
└── mentions
```

---

## 2. Section

Section یک واحد ساختاری از متن پژوهش است.

هر Research می‌تواند چند Section داشته باشد.

Section باید بتواند در آینده شامل این اجزا باشد:

```text
Section
├── id
├── title
├── paragraphs / content
├── mentions
├── claimRefs
└── sourceRefs
```

Section نباید Entity یا Claim را کپی کند.

---

## 3. Mention

Mention یک اشاره معنایی در متن است.

Mention پاسخ این سؤال است:

> این عبارت در متن به چه موجودیت یا مفهوم شناخته‌شده‌ای اشاره می‌کند؟

نمونه:

```text
متن:
«علی سنگینیان در گروه کیان...»

Mention:
text = "علی سنگینیان"
entityRef = "person:ali-sanginian"
```

Mention با Claim متفاوت است.

```text
Mention
→ این عبارت به چه چیزی اشاره دارد؟

Claim
→ چه گزاره‌ای درباره چیزی مطرح شده است؟
```

Mention می‌تواند در ابتدا بدون Entity قطعی باشد.

```text
resolutionStatus:
UNRESOLVED
RESOLVED
REJECTED
```

این ویژگی برای پردازش‌های آینده و AI در نظر گرفته می‌شود.

---

## 4. Entity Reference

Research فقط به Entityهای canonical Atlas ارجاع می‌دهد.

نمونه:

```text
entityRef:
person:ali-sanginian
```

Research نباید مشخصات کامل Entity را دوباره ذخیره کند.

اطلاعات اصلی Entity فقط در Atlas قرار دارد.

---

## 5. Claim Reference

Research می‌تواند به Claimهای canonical Atlas اشاره کند:

```text
claimRef:
claim:...
```

Research Claim جدیدی را به‌صورت canonical تولید نمی‌کند.

گزاره‌هایی که هنوز بررسی و تأیید نشده‌اند باید در لایه Research/Review باقی بمانند تا بعداً در صورت تأیید به Atlas منتقل شوند.

---

## 6. Source Reference

Research می‌تواند به Sourceهای canonical ارجاع دهد:

```text
sourceRef:
source:...
```

اطلاعات اصلی Source فقط در لایه canonical نگهداری می‌شود.

Research نباید اطلاعات Source را به‌صورت موازی و مستقل تکرار کند.

---

## 7. Related Research

Research می‌تواند به Researchهای دیگر متصل شود:

```text
research:private-capital
        ↓
research:private-equity
```

این ارتباط باید Reference-based باشد.

---

## 8. Candidate Concepts

Candidate Conceptها بخشی از Atlas نیستند.

اگر Research مفهومی را شناسایی کند که هنوز Entity رسمی در Atlas ندارد، Research می‌تواند آن را به‌صورت موقت برای Review نگه دارد.

نمونه فعلی:

```text
سرمایه خصوصی
Private Capital
```

که هنوز Entity canonical متناظر در Atlas ندارد.

Candidate Concept نباید با Entity canonical اشتباه شود.

---

## 9. Research Workflow

مدل Research باید این مسیر را پشتیبانی کند:

```text
Raw / Human Research
        ↓
Structured Research
        ↓
Mentions
        ↓
Entity Resolution
        ↓
Candidate Claims
        ↓
Review
        ↓
Canonical Atlas
```

انتقال به Atlas فقط بعد از بررسی انجام می‌شود.

---

## 10. Architectural Boundary

مرز میان سه لایه:

```text
ATLAS
Canonical Knowledge
Entity
Claim
Evidence
Source
```

```text
RESEARCH
Narrative Knowledge
Research
Section
Mention
Reference
Candidate Claim
```

```text
WATCH
Temporal Knowledge
Event
Event Participants
Event Claims
Event Sources
```

Research نباید تبدیل به Atlas دوم شود.

Watch نیز نباید Entity Registry مستقلی ایجاد کند.

---

## 11. Core Principle

اصل اصلی معماری:

> هر داده فقط یک مالک canonical داشته باشد.

بنابراین:

```text
Entity → Atlas
Claim → Atlas
Evidence → Atlas
Source → Atlas

Research → Research
Section → Research
Mention → Research
Candidate Claim → Research/Review
```

---

## 12. Future AI Compatibility

مدل باید بدون تغییر اساسی بتواند خروجی سیستم‌های هوش مصنوعی را دریافت کند.

مثلاً:

```text
Text
 ↓
Mention Detection
 ↓
Entity Resolution
 ↓
Relation Detection
 ↓
Candidate Claim
 ↓
Human Review
 ↓
Atlas Claim
```

AI مجاز نیست مستقیماً بدون Review داده canonical Atlas را تغییر دهد.

---

## 13. Non-Goals

در این مرحله موارد زیر جزو مدل Research نیستند:

* Graph Database
* Vector Database
* LLM Pipeline
* Automatic Entity Creation
* Automatic Claim Publishing
* بازطراحی Atlas
* تغییر ظاهر مقالات
