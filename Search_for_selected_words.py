# Modified from https://ankiweb.net/shared/info/800190862

from aqt.webview import AnkiWebView
from aqt.qt import *
from aqt.utils import tooltip
from anki.hooks import runHook, addHook
import urllib
from collections import OrderedDict

PROVIDERS = OrderedDict([
  ('Google Images', 'https://www.google.com/search?tbm=isch&q=%s'),
  ('Jisho.org'    , 'http://jisho.org/search/%s'),
  ('Koohii', 'http://kanji.koohii.com/study/kanji/%s')
])

def selected_text_as_query(web_view):
    sel = web_view.page().selectedText()
    return " ".join(sel.split())

def on_search_for_selection(web_view, search_url):
    sel_encode = selected_text_as_query(web_view).encode('utf8', 'ignore')
    #need to do this the long way around to avoid double % encoding
    url = QUrl.fromEncoded(search_url % (urllib.quote(sel_encode)))
    #openLink(SEARCH_URL + sel_encode)
    tooltip(_("Loading..."), period=1000)
    QDesktopServices.openUrl(url)


def contextMenuEvent(self, evt):
    # lazy: only run in reviewer
    import aqt
    if aqt.mw.state != "review":
        return
    m = QMenu(self)
    a = m.addAction(_("Copy"))
    a.connect(a, SIGNAL("triggered()"),
              lambda: self.triggerPageAction(QWebPage.Copy))
    #Only change is the following statement
    runHook("AnkiWebView.contextMenuEvent",self,m)
    m.popup(QCursor.pos())

def insert_search_menu_action(anki_web_view,m,provider,search_url):
    selected = selected_text_as_query(anki_web_view)
    truncated = (selected[:40] + '..') if len(selected) > 40 else selected
    a = m.addAction('Search for "%s" on %s ' % (truncated, provider))
    a.connect(a, SIGNAL("triggered()"),
         lambda wv=anki_web_view: on_search_for_selection(wv,search_url))

def jisho(anki_web_view,m):
    for provider, url in PROVIDERS.items():
        insert_search_menu_action(anki_web_view,m,provider,url)

AnkiWebView.contextMenuEvent = contextMenuEvent
addHook("AnkiWebView.contextMenuEvent", jisho)