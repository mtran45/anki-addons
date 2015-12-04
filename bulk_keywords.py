# -*- coding: utf-8 -*-
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
# Bulk update of keywords for kanji characters.
#
# ------------------------------------------------------------------------
# Based on the bulkreading.py of the Japanese Support plugin by Damien Elmes:
#   https://ankiweb.net/shared/info/3918629684
#
# Uses KanjiDic2 and some code adapted from JGlossator by cb4960:
#   http://jglossator.sourceforge.net
#

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from aqt import mw
from aqt.utils import showInfo
import re

srcFields = ['vocab-furigana']
dstFields = ['vocab-rtk']
separator = " "

KANJI_DIC_FILE = '../../addons/kanji.dat'
_kanji_dic = []

class KanjiInfo:
    """Container of various properties for a kanji character"""

    def __init__(self):
        self.kanji = None
        # self.radicals = None
        self.meanings = None
        self.rtk = None  # RTK index

    def keyword(self):
        """Returns the first meaning"""
        if len(self.meanings) >= 1:
            return self.meanings[0]

def create_kanji_dic():
    if len(_kanji_dic) > 0:
        return

    file = open(KANJI_DIC_FILE, 'r')
    for line in file:
        ki = KanjiInfo()
        fields = line.split('|')

        ki.kanji = fields[0].strip()
        code_fields = fields[1].strip().split(' ')
        ki.meanings = fields[5].strip().split(', ')

        for code in code_fields:
            if code[0] == 'L':
                ki.rtk = code[1:]

        _kanji_dic.append(ki)

def get_keyword(kanji):
    ki = [ki for ki in _kanji_dic if ki.kanji.decode('utf-8') == kanji]
    return ki[0].keyword() if ki else None

def get_keywords(kanjis):
    """Returns an array of keywords for a given array of kanji"""
    keywords = [get_keyword(k) for k in kanjis if get_keyword(k)]
    return keywords

def contains_kanji(char):
    pattern = re.compile(u"[\u4E00-\u9FFF]")
    return pattern.match(char)

def get_kanji(text):
    """Returns an array of kanji"""
    return [c for c in text
            if contains_kanji(c)]

def get_keywords_from_string(text):
    """Returns a string of keywords"""
    create_kanji_dic()
    kanjis = get_kanji(text)
    keywords = get_keywords(kanjis)
    return separator.join(keywords)


# Bulk updates
##########################################################################

def regenerateKeywords(nids):
    mw.checkpoint("Bulk-add Keywords")
    mw.progress.start()
    for nid in nids:
        note = mw.col.getNote(nid)
        # if "japanese" not in note.model()['name'].lower():
        #     continue
        src = None
        for fld in srcFields:
            if fld in note:
                src = fld
                break
        if not src:
            # no src field
            showInfo("no src")
            continue
        dst = None
        for fld in dstFields:
            if fld in note:
                dst = fld
                break
        if not dst:
            # no dst field
            showInfo("no dst")
            continue
        if note[dst]:
            # already contains data, skip
            continue
        srcTxt = mw.col.media.strip(note[src])
        if not srcTxt.strip():
            continue
        keywords = get_keywords_from_string(srcTxt)
        try:
            note[dst] = keywords
        except Exception, e:
            raise
        note.flush()
    mw.progress.finish()
    mw.reset()

def setupMenu(browser):
    a = QAction("Bulk-add Keywords", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: onRegenerate(e))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)

def onRegenerate(browser):
    regenerateKeywords(browser.selectedNotes())

addHook("browser.setupMenus", setupMenu)
