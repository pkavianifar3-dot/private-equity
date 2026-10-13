"""Shared native search presentation; no publication or ranking decisions."""
from html import escape

ICON = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true" focusable="false"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/></svg>'

def search_form(*, action='/articles.html', scope='all', compact=False, home=False, results=False, brand=False):
    identity='kaavosh-rail-query' if compact else 'kaavosh-query'
    css='kaavosh-form'+(' kaavosh-form-compact' if compact else '')+(' kaavosh-form-home' if home else '')
    attributes='' if compact else f' data-kaavosh data-default-scope="{escape(scope)}"'
    if results:attributes+=' data-results="kaavosh-results" data-status="kaavosh-status" data-filters="kaavosh-filters"'
    badge='' if compact or home or not brand else f'<label class="kaavosh-brand" for="{identity}">کاوش</label>'
    label=' aria-label="جست‌وجو در اطلس و پژوهش‌ها"' if compact or home or not brand else ''
    field=f'<div class="kaavosh-field"><input type="search" name="q" id="{identity}" autocomplete="off" placeholder="مفهومی که در جست‌وجوی آن هستید…"{label}><button class="kaavosh-submit" type="submit" aria-label="جست‌وجو">{ICON}</button></div>'
    if compact or home:
        options='<input type="hidden" name="scope" value="all">'
    else:
        options='<div class="kaavosh-options"><label for="kaavosh-scope">دامنهٔ کاوش</label><select id="kaavosh-scope" name="scope" aria-label="دامنهٔ کاوش">'+''.join(f'<option value="{value}"'+(' selected' if value==scope else '')+f'>{text}</option>' for value,text in [('all','همه'),('atlas','اطلس'),('research','پژوهش‌ها')])+'</select></div>'
    return f'<form class="{css}" action="{escape(action)}" method="get" role="search"{attributes}>{badge}{field}{options}</form>'
