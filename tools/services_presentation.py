"""A curated Services decision guide, anchored to actual public page content."""
import json
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'atlas/tools'))
from exploration import article_toc, esc
from kaavosh_markup import search_form


class DecisionTargets(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.items = []
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-service-step' not in attrs:
            return
        target, label = attrs.get('id'), attrs['data-service-step']
        if not target or not label or target in {item[0] for item in self.items}:
            raise ValueError('Services guide requires a unique target and a nonempty label')
        self.items.append((target, label))


def reading_layout(payload):
    # Headings receive stable IDs; only editorially marked sections enter the guide.
    body, _ = article_toc(payload['body'], levels=(2,), prefix='services')
    items = DecisionTargets(body).items
    if not items:
        raise ValueError('Services page has no decision-guide destinations')
    descriptions = {
        '/corporate/partners/': ('دستهٔ همکاری خود را پیدا کنید و با شرکای معرفی‌شده آشنا شوید.', 'پیشنهاد همکاری'),
        '/corporate/team/': ('با اعضای تیم آشنا شوید؛ برای بررسی امکان همکاری، گفت‌وگو را آغاز کنید.', 'گفت‌وگو دربارهٔ همکاری'),
        '/corporate/solutions/': ('از موقعیت شرکت شروع کنید و مسیر متناسب با تصمیم پیش رو را بیابید.', 'طرح مسئلهٔ شرکت من'),
        '/corporate/collaboration/': ('پیش از شروع، با مراحل، شرایط پذیرش و حدود همکاری آشنا شوید.', 'شروع گفت‌وگو'),
    }
    description, cta = descriptions.get(payload['url'], (
        'تناسب این خدمت، کارهای ما و خروجی همکاری را بررسی کنید؛ سپس مسئلهٔ شرکت را مطرح کنید.',
        'طرح مسئلهٔ شرکت من'))
    # Avoid suggesting a populated team or partner list while its source is empty.
    if payload.get('directory_empty'):
        description = ('دستهٔ همکاری خود را انتخاب کنید؛ معرفی شرکای هر دسته به‌تدریج تکمیل می‌شود.'
                       if payload['url'] == '/corporate/partners/' else
                       'معرفی اعضای تیم در حال تکمیل است؛ مسیر گفت‌وگو دربارهٔ همکاری در دسترس شماست.')
    search = '' if payload.get('has_search') else search_form(action='/corporate/solutions/', compact=True).replace(
        'مفهومی که در جست‌وجوی آن هستید…', 'جست‌وجوی راهکارها…').replace(
        'جست‌وجو در اطلس و پژوهش‌ها', 'جست‌وجو در راهکارهای خدمات شرکتی')
    links = ''.join(f'<li><a href="#{esc(target)}" data-service-guide-link>{esc(label)}</a></li>'
                    for target, label in items)
    destination = '/contact.html' if payload['url'] == '/corporate/collaboration/' else '/corporate/collaboration/'
    guide = ('<details class="svc-decision-guide" data-service-guide>'
             '<summary><span>مسیر تصمیم شما</span><span class="svc-guide-chevron" aria-hidden="true">⌄</span></summary>'
             f'<div class="svc-guide-body"><p class="svc-guide-intro">{esc(description)}</p>'
             f'<nav aria-label="مسیر تصمیم شما"><ol>{links}</ol></nav>'
             f'<a class="svc-guide-next" href="{destination}">{esc(cta)}<span aria-hidden="true">←</span></a>'
             '</div></details>')
    sidebar = ('<aside class="explore-rail svc-guide-rail" aria-label="راهنمای تصمیم در خدمات شرکتی">'
               '<div class="explore-rail-inner">' + search + guide + '</div></aside>')
    return ('<div class="container explore-reading-layout svc-reading-layout"><div class="svc-content">'
            + body + '</div>' + sidebar + '</div>')


if __name__ == '__main__':
    result = reading_layout(json.loads(sys.stdin.buffer.read().decode('utf-8')))
    sys.stdout.buffer.write(result.encode('utf-8'))
