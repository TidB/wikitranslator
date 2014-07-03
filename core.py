import re
from urllib.parse import quote
import urllib.request
import xml.etree.ElementTree as ET

import sDE
import sFI
import sKO
import sPT_BR

MAX_SIZE = 10000

GUI_METHODS_NOARGS = ("check_quote",
                      "transform_decimal",
                      "transform_link",
                      "translate_categories",
                      "translate_headlines",
                      "translate_item_flags",
                      "translate_levels",
                      "translate_main_seealso",
                      "translate_set_contents",
                      "translate_wikilink",
                      "translate_wikipedia_link")


def get_wiki_root(link):
    text = urllib.request.urlopen(link).read()
    text = text.decode("utf-8")
    return ET.fromstring(text)


def import_category(category):
    root = get_wiki_root("http://wiki.teamfortress.com/w/api.php?action=query&list=categorymembers&cmtitle=Category:{}&cmdir=asc&cmlimit=200&format=xml".format(quote(category)))
    if root.find(".//*cm") is None:
        raise ValueError("Invalid category '{}'".format(category))
    else:
        wikitexts = []
        for cmember in root.iter("cm"):
            if str(cmember.attrib['ns']) != "0":
                continue
            title = cmember.attrib['title']
            title = title.replace(" ", "_")
            root = get_wiki_root("http://wiki.teamfortress.com/w/api.php?action=query&titles={}&prop=revisions|info&rvprop=content&redirects&format=xml".format(title))
            if int(root.find(".//*page").attrib['length']) >= MAX_SIZE:
                continue
            wikitext = root.find(".//*rev").text
            wikitexts.append(wikitext)
        return wikitexts


def lf(link):
    return link.replace("[", "").replace("]", "")


def lf_ext(link):
    return re.sub("\|.*[^]]", "", link)


def lf_w(link):
    if "{{" in link:
        return re.sub("\|[^|]*?\}\}", "", re.sub("\{\{[Ww][\w]*?\|", "", link)).replace("}}", "")
    elif "[[" in link:
        return re.sub("\|.*?\]\]", "", re.sub("\[\[[Ww][\w]*?:", "", link)).replace("]]", "")


def lf_t_wl(link, sound=False):
    root = get_wiki_root("http://wiki.teamfortress.com/w/api.php?format=xml&action=query&titles={}&prop=info&inprop=displaytitle&redirects".format(quote(link)))
    if not root.find(".//*[@missing='']") is None:
        return link, link, False

    if sound:
        return link, link, True
    else:
        pagetitle = root.find(".//*[@title]").attrib['title']
        displaytitle = root.find(".//*[@displaytitle]").attrib['displaytitle']
        return pagetitle, displaytitle, True


def lf_to_t(link):
    return link.replace("[[", "{{item link|").replace("]]", "}}")


class Wikitext:
    def __init__(self, wikitext, language, methods):
        self.language = language
        self.methods = methods
        self.wikiText = wikitext
        self.strings = eval("s" + language.upper().replace("-", "_"))
        try:
            self.wikiTextType = self.get_wikitext_type()
            self.itemName = self.get_itemname()
            self.classLink = self.get_using_classes()
            self.classList = self.create_class_list()
            self.restricted = False
        except Exception:
            self.restricted = True

    def __str__(self):
        return self.wikiText

    def add_displaytitle(self):
        self.wikiText = "\n".join([self.strings.DISPLAYTITLE.format(self.itemName), self.wikiText])

    def check_quote(self):
        quotes = re.findall("\{\{[Qq]uotation.*?\}\}", self.wikiText)
        for q in quotes:
            file = re.findall("\|sound=.*\}\}", q)
            if not file:
                continue

            file = file[0].replace("|sound=", "").replace(".wav", "").replace("}", "")
            filen = "File:{} {}.wav".format(file, self.language)
            if not lf_t_wl(filen, True)[2]:
                qn = "|sound={}|en-sound=yes}}}}".format(file+".wav")
            else:
                qn = "|sound={}}}}}".format(filen)

            self.wikiText = re.sub("\|sound.*?\}\}", qn, self.wikiText)

    def create_class_list(self):
        if "all" in self.classLink[0].lower():
            return self.strings.SENTENCE_1_CLASSES_ALL
        else:
            if self.strings.DICTIONARY_CLASSES:
                linktranslated = self.strings.DICTIONARY_CLASSES[lf_ext(lf(self.classLink[0]))]
            else:
                linktranslated = lf_ext(lf(self.classLink[0]))
            if len(self.classLink) == 1:
                return self.strings.SENTENCE_1_CLASSES_ONE.format(linktranslated)
            elif len(self.classLink) > 1:
                classes = self.strings.SENTENCE_1_CLASSES_ONE.format(linktranslated)
                for c in self.classLink[1:-1]:
                    if self.strings.DICTIONARY_CLASSES:
                        linktranslated = self.strings.DICTIONARY_CLASSES[lf_ext(lf(c))]
                    else:
                        linktranslated = lf_ext(lf(c))
                    classes = (classes +
                               self.strings.SENTENCE_1_CLASSES_COMMA +
                               self.strings.SENTENCE_1_CLASSES_ONE.format(linktranslated))

                classes = (classes +
                           self.strings.SENTENCE_1_CLASSES_AND +
                           self.strings.SENTENCE_1_CLASSES_ONE.format(linktranslated))

                return classes

    def get_itemname(self):
        itemname = re.search("'''.*?'''.*?(is|are).*?(a|an)",
                             re.sub("{{[Qq]uotation.*?}}", "", self.wikiText)).group()
        itemname = re.sub(" [is|are].*?a", "", itemname.replace("'''", ""))

        return itemname

    def get_item_promo(self):
        return bool(re.findall("\{\{avail.*?promo.*?\}\}", self.wikiText))

    def get_item_community(self):
        return bool(re.findall('.*?contributed.*?"*.*"*\.', self.wikiText))

    def get_using_classes(self):
        classlink = re.findall("used-by +=.*", self.wikiText)
        classlink = re.sub("used-by += +", "", classlink[0])
        if "all" in lf(classlink).lower():
            return [classlink]
        else:
            if classlink.count(",")+1 > 1:
                return classlink.split(", ")
            else:
                return [classlink]

    def get_weapon_slot(self):
        return re.sub("slot.*?= ", "", re.findall("slot.*?=.*", self.wikiText)[0])

    def get_wikitext_type(self):
        if "{{item set infobox" in self.wikiText.lower():
            wikitexttype = "set"
        elif "{{item infobox" in self.wikiText.lower():
            wikitexttype = re.sub("type.*?= ", "",
                                  re.findall("type.*?=.*?\n",
                                             self.wikiText)[0]).replace("\n", "")

            if wikitexttype.lower() == "misc" or wikitexttype.lower() == "hat":
                wikitexttype = "cosmetic"
        else:
            wikitexttype = "none"

        return wikitexttype

    def transform_decimal(self):
        for dot in re.findall('[^"]\d+\.\d+[^"]', self.wikiText):
            self.wikiText = self.wikiText.replace(dot, dot.replace(".", ","))

    def transform_link(self):
        links = re.findall("\[\[.*?\]\]", self.wikiText)
        for l in links:
            if "/{}".format(self.language) in l \
                    or "category:" in l.lower() \
                    or "image:" in l.lower() \
                    or "file:" in l.lower() \
                    or "[[w:" in l.lower():
                continue
            self.wikiText = self.wikiText.replace(l, lf_to_t(lf_ext(l)))

    def translate_categories(self):
        categories = re.findall("\[\[Category:.*?\]\]", self.wikiText)

        for c in categories:
            cn = c.replace("]]", "/{}]]".format(self.language))
            self.wikiText = self.wikiText.replace(c, cn)

    def translate_classlinks(self):
        if "all" in self.classLink[0].lower():
            linkiso = self.strings.ALLCLASSESBOX.format(self.language)
            self.wikiText = self.wikiText.replace(self.classLink[0], linkiso)
        elif len(self.classLink) >= 1:
            for link in self.classLink:
                linkiso = link.replace("]]", "/{}|{}]]".format(self.language, lf_ext(lf(link))))
                self.wikiText = self.wikiText.replace(link, linkiso)

    def translate_headlines(self):
        headlines = re.findall("=+.*?=+", self.wikiText)
        for hl in headlines:
            level = int(hl.count("=") / 2)
            hln = hl.replace("=", "").strip()
            try:
                hln = self.strings.DICTIONARY_HEADLINES[hln.lower()].join(["="*level, "="*level])
            except KeyError:
                continue
            self.wikiText = self.wikiText.replace(hl, hln)

    def translate_item_flags(self):
        try:
            itemflag = re.search("\|.*?item-flags.*", self.wikiText).group()
            itemflagnew = "| item-flags   = " + self.strings.DICTIONARY_FLAGS[re.sub("\|.*?= +", "", itemflag).lower()]
            self.wikiText = self.wikiText.replace(itemflag, itemflagnew)
        except (AttributeError, KeyError):
            pass

        try:
            itematt = re.search("\|.*?att-1-negative.*", self.wikiText).group()
            itemattn = "| att-1-negative   = " + self.strings.DICTIONARY_ATTS[re.sub("\|.*?= +", "", itematt).lower()]
            self.wikiText = self.wikiText.replace(itematt, itemattn)
        except (AttributeError, KeyError):
            pass

    def translate_levels(self):
        level = re.findall("Level \d+-?\d*? [A-z ]+", self.wikiText)[0]
        levelnew = level[6:]

        levelint = re.findall("\d+-?\d*", levelnew)[0]
        levelkey = re.findall("[A-z ]+", levelnew)[0]

        try:
            levelkeyn = self.strings.DICTIONARY_LEVEL_C[levelkey.strip()]
        except KeyError:
            levelkeyn = levelkey.strip()

        levelnew = self.strings.LEVEL.format(levelint, levelkeyn)
        self.wikiText = self.wikiText.replace(level, levelnew)

    def translate_main_seealso(self):
        temps = []
        temps.extend(re.findall("\{\{[Mm]ain.*?\}\}", self.wikiText))
        temps.extend(re.findall("\{\{[Ss]ee also.*?\}\}", self.wikiText))
        for t in temps:
            link = re.findall("\|.*?[^|]*", t)[0].replace("|", "").replace("}", "")
            pagetitle, displaytitle, __ = lf_t_wl(link)
            if "main" in t.lower():
                tn = "{{{{Main|{}|l1={}}}}}".format(pagetitle, displaytitle)
            elif "see also" in t.lower():
                tn = "{{{{See also|{}|l1={}}}}}".format(pagetitle, displaytitle)
            else:
                return
            self.wikiText = self.wikiText.replace(t, tn)

    def translate_set_contents(self):
        match = re.search("(The|This)( set)?( contains| includes)?( the)?( following)? items.*?:", self.wikiText).group()
        self.wikiText = re.sub(match,
                               self.strings.SENTENCE_SET_INCLUDES,
                               self.wikiText)

        part = self.wikiText[self.wikiText.index(self.strings.SENTENCE_SET_INCLUDES):]
        for link in re.finditer("\* ?\[\[.*?\]\]", part):
            link = link.group()
            self.wikiText = self.wikiText.replace(link, lf_to_t(link))

    def translate_update_history(self):
        self.wikiText = re.sub(".*?[Aa]dded.*? to the game\.",
                               self.strings.ADDEDTOGAME.format(self.itemName), self.wikiText)

    # ===================
    # Wikimedia API usage
    # ===================

    def translate_wikilink(self):
        links = re.findall("\[\[.*?\]\]", re.sub("\[\[[Ww]ikipedia:", "[[w:", self.wikiText))
        for l in links:
            if "/{}".format(self.language) in l \
                    or "category:" in l.lower() \
                    or "file:" in l.lower() \
                    or "image:" in l.lower() \
                    or "[[w:" in l.lower():
                continue
            ln = lf_ext(lf(l))
            ln = re.sub("#.*$", "", ln)
            ln = ln.replace(" ", "_")
            ln = ln+"/"+self.language
            pagetitle, displaytitle, __ = lf_t_wl(ln)
            ln = "[[{}|{}]]".format(pagetitle, displaytitle)
            self.wikiText = self.wikiText.replace(l, ln)

    def translate_wikipedia_link(self):
        links = []
        links.extend(re.findall("\[\[[Ww][\w]*:.*?\]\]", self.wikiText))
        links.extend(re.findall("\{\{[Ww][\w]*\|.*?\}\}", self.wikiText))
        for l in links:
            ln = lf_w(l)
            ln = re.sub("#.*$", "", ln)
            ln = ln.replace(" ", "_")
            root = get_wiki_root("http://en.wikipedia.org/w/api.php?format=xml&action=query&titles={}&prop=langlinks&lllimit=400&redirects".format(quote(ln)))
            if root.find(".//*[@missing='']"):
                continue

            t = root.find(".//*[@lang='{}']".format(self.language))
            if t is None:
                continue

            tn = "[[w:{0}:{1}|{1}]]".format(self.language, t.text)
            self.wikiText = self.wikiText.replace(l, tn)

    # ==================
    # Creating sentences
    # ==================

    def create_sentence_1_cw(self):
        sentence1 = re.findall(".*?'''" + self.itemName + "'''.*? for .*?\.", self.wikiText)[0]

        if self.wikiTextType == "weapon":
            slot = self.get_weapon_slot()
            self.strings.SENTENCE_1_WEAPON = eval("self.strings.SENTENCE_1_" +
                                                  slot.upper()).format(lf(self.classLink[0]).lower())

        nounmarkerindefinite = eval("self.strings.NOUNMARKER_INDEFINITE_" + self.wikiTextType.upper())

        if self.get_item_community():
            com = eval("self.strings.SENTENCE_1_COMMUNITY_" + self.wikiTextType.upper())
        else:
            com = ""
        typelink = eval("self.strings.SENTENCE_1_" + self.wikiTextType.upper())
        if self.get_item_promo():
            promo = eval("self.strings.SENTENCE_1_PROMO_" + self.wikiTextType.upper())
            if self.wikiTextType == "cosmetic" and self.strings == "de":
                #Special case for German
                typelink = ""
        else:
            promo = ""

        sentence1trans = self.strings.SENTENCE_1_ALL.format(self.itemName,
                                                            nounmarkerindefinite,
                                                            com,
                                                            promo,
                                                            typelink,
                                                            self.classList)

        self.wikiText = self.wikiText.replace(sentence1, (sentence1trans + self.strings.ITEMLOOK))

    def create_sentence_1_set(self):
        sentence1_1 = re.findall(".*?'''" + self.itemName + "'''.*? for .*?\.", self.wikiText)[0]
        sentence1_1trans = self.strings.SENTENCE_1_ALL.format(self.itemName,
                                                              self.strings.NOUNMARKER_INDEFINITE_SET,
                                                              "",
                                                              "",
                                                              self.strings.SENTENCE_1_SET,
                                                              self.classList)

        sentence1_2 = re.findall("\. It was .*?\.", self.wikiText)[0][1:]
        patch = lf(re.findall("\[\[.*?\]\]", sentence1_2)[0])
        sentence1_2trans = self.strings.SENTENCE_SET.format(patch)
        self.wikiText = self.wikiText.replace(sentence1_1 + sentence1_2,
                                              sentence1_1trans + sentence1_2trans)

    def create_sentence_community(self):
        sentencecommunity = re.findall(".*?contributed.*?Steam Workshop.*?\.",
                                       self.wikiText)

        if sentencecommunity:
            link = re.findall("\[http.*?contribute.*?\]", sentencecommunity[0])
            if link:
                link = re.sub(" contribute.*?\]", "", link[0]).replace("[", "")
                link = self.strings.SENTENCE_COMMUNITY_LINK.format(link)

            try:
                name = re.findall('name.*?\".*?\"', sentencecommunity[0])[0][6:].replace('"', '')
                name = self.strings.SENTENCE_COMMUNITY_NAME.format(name)
            except (TypeError, IndexError):
                name = ""

            sct = self.strings.SENTENCE_COMMUNITY.format(self.itemName, name, link)
            self.wikiText = self.wikiText.replace(sentencecommunity[0], sct)
        else:
            return

    def create_sentence_promo(self):
        sentencepromo = re.findall(".*?\[\[Genuine\]\].*?quality.*?\.", self.wikiText)
        if sentencepromo:
            if "[[Steam]]" in sentencepromo:
                spt_s = self.strings.SENTENCE_PROMOTIONAL_STEAM
            else:
                spt_s = ""

            try:
                date = re.findall("before .*?,.*?20\d\d", sentencepromo[0])[0]
                date = date.replace("before ", "")

                dateday = re.findall("\w \d[\d|,]", date)[0][2:].replace(",", "")
                datemonth = re.findall("[A-z].*?\d", date)[0][:-2]
                dateyear = re.findall(", \d{4}", date)[0][2:]

                datefmt = "{{{{Date fmt|{}|{}|{}}}}}".format(datemonth, dateday, dateyear)
                spt_d = self.strings.SENTENCE_PROMOTIONAL_DATE.format(datefmt)
            except Exception:
                spt_d = ""
            try:
                game = re.findall("\[?\[?''.*?\]?\]?''", sentencepromo[0])[0]
                game = lf(game.replace("''", ""))
            except IndexError:
                raise UserWarning("No game. Canceling promo sentence translation.")

            spt = self.strings.SENTENCE_PROMOTIONAL.format(self.itemName, game, spt_s, spt_d)

            self.wikiText = self.wikiText.replace(sentencepromo[0], spt)
        else:
            return

    # =========
    # Translate
    # =========

    def translate(self):
        for method in self.methods:
            if self.restricted and method not in GUI_METHODS_NOARGS:
                continue

            getattr(self, method)()

        return self.wikiText