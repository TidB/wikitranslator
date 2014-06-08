import re
from urllib.parse import quote
import urllib.request
import xml.etree.ElementTree as ET

import gui
import sDE

MAX_SIZE = 20000


def import_category(category):
    category = re.sub("[Cc]ategory:", "", category)
    text = urllib.request.urlopen("http://wiki.teamfortress.com/w/api.php?action=query&list=categorymembers&cmtitle=Category:{}&cmdir=asc&cmlimit=200&format=xml".format(quote(category))).read()
    text = str(text)
    root = ET.fromstring(text)
    if root.find(".//*cm") is None:
        print("Invalid category name:", category)
        return
    else:
        wikiTextList = []
        for i in root.iter("cm"):
            if str(i.attrib['ns']) != "0":
                continue
            title = i.attrib['title']
            title = title.replace(" ", "_")
            text = urllib.request.urlopen("http://wiki.teamfortress.com/w/api.php?action=query&titles={}&prop=revisions|info&rvprop=content&redirects&format=xml".format(title)).read()
            text = str(text)
            root = ET.fromstring(text)
            if int(root.find(".//*page").attrib['length']) >= MAX_SIZE:
                continue
            wikiText = root.find(".//*rev").text
            wikiTextList.append(wikiText)
        return wikiTextList


class Wikitext:
    def __init__(self, wikiText, iso, methods):
        self.iso = iso
        self.methods = methods
        self.wikiText = wikiText
        self.strings = eval("s" + iso.upper().replace("-", "_"))
        try:
            self.get_wikitext_type()
            self.get_itemname()
            self.get_using_classes()
            self.create_class_list()
            self.restricted = False
        except:
            print("Couldn't gather all information")
            self.restricted = True

    # ================
    # Wikitext options
    # ================

    def lf(self, link):
        return link.replace("[", "").replace("]", "")

    def lf_ext(self, link):
        return re.sub("\|.*[^]]", "", link)

    def lf_to_t(self, link):
        return link.replace("[[", "{{item link|").replace("]]", "}}")

    def lf_w(self, link):
        if "{{" in link:
            return re.sub("\|[^|]*?\}\}", "", re.sub("\{\{[Ww][\w]*?\|", "", link)).replace("}}", "")
        elif "[[" in link:
            return re.sub("\|.*?\]\]", "", re.sub("\[\[[Ww][\w]*?:", "", link)).replace("]]", "")

    def lf_t_wl(self, link, sound=False):
        text = urllib.request.urlopen("http://wiki.teamfortress.com/w/api.php?format=xml&action=query&titles={}&prop=info&inprop=displaytitle&redirects".format(quote(link))).read()
        text = str(text)
        root = ET.fromstring(text)
        if not root.find(".//*[@missing='']") is None:
            print("Invalid page name:", link)
            return link, link, False

        if sound:
            return link, link, True
        else:
            pagetitle = root.find(".//*[@title]").attrib['title']
            displaytitle = root.find(".//*[@displaytitle]").attrib['displaytitle']
            return pagetitle, displaytitle, True

    def add_displaytitle(self):
        self.wikiText = "\n".join([self.strings.DISPLAYTITLE.format(self.itemName), self.wikiText])

    def check_quote(self):
        quotes = re.findall("\{\{[Qq]uotation.*?\}\}", self.wikiText)
        for q in quotes:
            file = re.findall("\|sound=.*\}\}", q)
            if not file:
                print(q, "is not sound-enabled")
                continue

            file = file[0].replace("|sound=", "").replace(".wav", "").replace("}", "")
            filen = "File:{} {}.wav".format(file, self.iso)
            if not self.lf_t_wl(filen, True)[2]:
                print("No localized file for", filen)
                qn = "|sound={}|en-sound=yes}}}}".format(file+".wav")
            else:
                qn = "|sound={}}}}}".format(filen)

            self.wikiText = re.sub("\|sound.*?\}\}", qn, self.wikiText)

    def create_class_list(self):
        if self.classLinkCounter == -1 or self.classLinkCounter == 9:
            self.classList = self.strings.SENTENCE_1_CLASSES_ALL
        elif self.classLinkCounter == 1:
            self.classList = self.strings.SENTENCE_1_CLASSES_ONE.format(self.lf(self.classLink))
        elif self.classLinkCounter > 1:
            classList = self.strings.SENTENCE_1_CLASSES_ONE.format(self.lf(self.classLink[0]))
            last = self.classLink[-1]
            for c in self.classLink[1:-2]:
                classList = (classList +
                             ", " +
                             self.strings.SENTENCE_1_CLASSES_ONE.format(self.lf(c)))

            self.classList = (classList +
                              " und " +
                              self.strings.SENTENCE_1_CLASSES_ONE.format(self.lf(last)))

    def get_itemname(self):
        itemName = re.findall("'''.*?'''.*?[is|are].*?a",
                              re.sub("{{[Qq]uotation.*?}}", "", self.wikiText))
        self.itemName = re.sub(" [is|are].*?a", "", re.sub("'''", "", itemName[0]))

    def get_item_promo(self):
        return bool(re.findall("\{\{avail.*?promo.*?\}\}",
                               self.wikiText))

    def get_item_community(self):
        return bool(re.findall('.*?contributed.*?"*.*"*\.',
                               self.wikiText))

    def get_using_classes(self):
        classLink = re.findall("used-by +=.*", self.wikiText)
        self.classLink = re.sub("used-by += +", "", classLink[0])
        if "all" in self.lf(self.classLink).lower():
            self.classLinkCounter = -1
            return
        else:
            self.classLinkCounter = self.classLink.count(",") + 1

        if self.classLinkCounter > 1:
            self.classLink = self.classLink.split(", ")

    def get_weapon_slot(self):
        self.slot = re.sub("slot.*?= ", "",
                           re.findall("slot.*?=.*", self.wikiText)[0])

    def get_wikitext_type(self):
        if "{{item set infobox" in self.wikiText.lower():
            self.wikiTextType = "set"
        elif "{{item infobox" in self.wikiText.lower():
            self.wikiTextType = re.sub("type.*?= ", "",
                                       re.findall("type.*?=.*?\n",
                                                  self.wikiText)[0]).replace("\n", "")

            if self.wikiTextType.lower() == "misc" or self.wikiTextType.lower() == "hat":
                self.wikiTextType = "cosmetic"
        else:
            self.wikiTextType = "none"

    def transform_decimal(self):
        for n in re.findall('[^"]\d+\.\d+[^"]', self.wikiText):
            self.wikiText = self.wikiText.replace(n, n.replace(".", ","))

    def transform_link(self):
        links = re.findall("\[\[.*?\]\]", self.wikiText)
        for l in links:
            if "/{}".format(self.iso) in l \
               or "category:" in l.lower() \
               or "file:" in l.lower() \
               or "image:" in l.lower() \
               or "[[w:" in l.lower():
                continue
            self.wikiText = self.wikiText.replace(l, self.lf_to_t(self.lf_ext(l)))

    def translate_categories(self):
        categories = re.findall("\[\[Category:.*?\]\]", self.wikiText)

        for c in categories:
            cn = c.replace("]]", "/{}]]".format(self.iso))
            self.wikiText = self.wikiText.replace(c, cn)

    def translate_classlinks(self):
        if type(self.classLink) is list:
            for link in self.classLink:
                linkIso = link.replace("]]", "/{}|{}]]".format(self.iso, self.lf_ext(self.lf(link))))
                self.wikiText = self.wikiText.replace(link, linkIso)
        elif type(self.classLink) is str:
            if "all" in self.classLink.lower():
                linkIso = self.strings.ALLCLASSESBOX.format(self.iso)
            else:
                linkIso = self.classLink.replace("]]", "/{}|{}]]".format(self.iso, self.lf(self.classLink)))
            self.wikiText = self.wikiText.replace(self.classLink, linkIso)

    def translate_headlines(self):
        headlines = re.findall("==.*?==", self.wikiText)
        for hl in headlines:
            hln = re.sub(" *==", "", re.sub("== *", "", hl)).strip()
            try:
                hln = self.strings.DICTIONARY_HEADLINES[hln.lower()].join(["== ", " =="])
            except KeyError:
                print("Unknown key:", hl)
                continue
            self.wikiText = self.wikiText.replace(hl, hln)

    def translate_item_flags(self):
        try:
            itemFlag = re.search("\|.*?item-flags.*", self.wikiText).group()
            iF = re.sub("\|.*?= +", "", itemFlag)
            iFn = "| item-flags   = " + self.strings.DICTIONARY_FLAGS[iF.lower()]
            self.wikiText = self.wikiText.replace(itemFlag, iFn)
        except (AttributeError, KeyError):
            pass

        try:
            itemAtt = re.search("\|.*?att-1-negative.*", self.wikiText).group()
            iA = re.sub("\|.*?= +", "", itemAtt)
            iAn = "| att-1-negative   = " + self.strings.DICTIONARY_ATTS[iA.lower()]
            self.wikiText = self.wikiText.replace(itemAtt, iAn)
        except (AttributeError, KeyError):
            pass

    def translate_levels(self):
        level = re.findall("Level \d+-?\d*? [A-z ]+", self.wikiText)[0]
        levelNew = level.replace("Level ", "")

        levelInt = re.findall("\d+-?\d*", levelNew)[0]
        levelKey = re.findall("[A-z ]+", levelNew)[0]

        try:
            levelKN = self.strings.DICTIONARY_LEVEL_C[levelKey.strip()]
        except KeyError:
            print("Unknown key:", levelKey)
            levelKN = levelKey.strip()

        levelNew = self.strings.LEVEL.format(levelKN, levelInt)
        self.wikiText = self.wikiText.replace(level, levelNew)

    def translate_main_seealso(self):
        temps = []
        temps.extend(re.findall("\{\{[Mm]ain.*?\}\}", self.wikiText))
        temps.extend(re.findall("\{\{[Ss]ee also.*?\}\}", self.wikiText))
        for t in temps:
            link = re.findall("\|.*?[^|]*", t)[0].replace("|", "").replace("}", "")
            pagetitle, displaytitle, _ = self.lf_t_wl(link)
            if "main" in t.lower():
                tn = "{{{{Main|{}|l1={}}}}}".format(pagetitle, displaytitle)
            elif "see also" in t.lower():
                tn = "{{{{See also|{}|l1={}}}}}".format(pagetitle, displaytitle)
            else:
                return
            self.wikiText = self.wikiText.replace(t, tn)

    def translate_set_contents(self):
        match = re.search("(The|This) set (contains|includes) the following items:", self.wikiText).group()
        self.wikiText = re.sub(match,
                               self.strings.SENTENCE_SET_INCLUDES,
                               self.wikiText)

        part = self.wikiText[self.wikiText.index(self.strings.SENTENCE_SET_INCLUDES):]
        for link in re.finditer("\* ?\[\[.*?\]\]", part):
            link = link.group()
            self.wikiText = self.wikiText.replace(link, self.lf_to_t(link))

    def translate_update_history(self):
        self.wikiText = re.sub(".*?[Aa]dded.*? to the game\.",
                               self.strings.ADDEDTOGAME.format(self.itemName), self.wikiText)

    # ===================
    # Wikimedia API usage
    # ===================

    def translate_wikilink(self):
        links = re.findall("\[\[.*?\]\]",
                           re.sub("\[\[[Ww]ikipedia:", "[[w:", self.wikiText))
        for l in links:
            if "/{}".format(self.iso) in l \
               or "category:" in l.lower() \
               or "file:" in l.lower() \
               or "image:" in l.lower() \
               or "[[w:" in l.lower():
                continue
            ln = self.lf_ext(self.lf(l))
            ln = re.sub("#.*$", "", ln)
            ln = ln.replace(" ", "_")
            ln = ln+"/"+self.iso
            pagetitle, displaytitle, _ = self.lf_t_wl(ln)
            ln = "[[{}|{}]]".format(pagetitle, displaytitle)
            self.wikiText = self.wikiText.replace(l, ln)

    def translate_wikipedia_link(self):
        links = []
        links.extend(re.findall("\[\[[Ww][\w]*:.*?\]\]", self.wikiText))
        links.extend(re.findall("\{\{[Ww][\w]*\|.*?\}\}", self.wikiText))
        for l in links:
            ln = self.lf_w(l)
            ln = re.sub("#.*$", "", ln)
            ln = ln.replace(" ", "_")
            text = urllib.request.urlopen("http://en.wikipedia.org/w/api.php?format=xml&action=query&titles={}&prop=langlinks&lllimit=400&redirects".format(quote(ln))).read()
            text = str(text)
            root = ET.fromstring(text)
            if root.find(".//*[@missing='']"):
                print("Invalid page name: ", l)
                continue

            t = root.find(".//*[@lang='{}']".format(self.iso))
            if t is None:
                print("No /{} article for {} => {}".format(self.iso, l, ln))
                continue

            tn = "[[w:{0}:{1}|{1}]]".format(self.iso, t.text)
            self.wikiText = self.wikiText.replace(l, tn)

    # ==================
    # Creating sentences
    # ==================

    def create_sentence_1_cw(self):
        sentence1 = re.findall(".*?'''" + self.itemName + "'''.*? for .*?\.",
                               self.wikiText)[0]

        if self.wikiTextType == "weapon":
            self.strings.SENTENCE_1_WEAPON = eval("self.strings.SENTENCE_1_" +
                                                  self.slot.upper()).format(self.lf(self.classLink).lower())

        nounMarkerIndefinite = eval("self.strings.NOUNMARKER_INDEFINITE_" + self.wikiTextType.upper())

        if self.get_item_community():
            com = eval("self.strings.SENTENCE_1_COMMUNITY_" + self.wikiTextType.upper())
        else:
            com = ""

        typeLink = eval("self.strings.SENTENCE_1_" + self.wikiTextType.upper())
        if self.get_item_promo():
            promo = eval("self.strings.SENTENCE_1_PROMO_" + self.wikiTextType.upper())
            if self.wikiTextType == "cosmetic" and self.strings == "de":
                typeLink = ""
        else:
            promo = ""

        sentence1Trans = self.strings.SENTENCE_1_ALL.format(self.itemName,
                                                            nounMarkerIndefinite,
                                                            com,
                                                            promo,
                                                            typeLink,
                                                            self.classList)

        self.wikiText = self.wikiText.replace(sentence1, (sentence1Trans + self.strings.ITEMLOOK))

    def create_sentence_1_set(self):
        sentence1_1 = re.findall(".*?'''" + self.itemName + "'''.*? for .*?\.", self.wikiText)[0]
        sentence1_1Trans = self.strings.SENTENCE_1_ALL.format(self.itemName,
                                                              self.strings.NOUNMARKER_INDEFINITE_SET,
                                                              "",
                                                              "",
                                                              self.strings.SENTENCE_1_SET,
                                                              self.classList)

        sentence1_2 = re.findall(" It was .*?added to the game.*?\.", self.wikiText)[0]
        patch = self.lf(re.findall("\[\[.*?\]\]", sentence1_2)[0])
        sentence1_2Trans = self.strings.SENTENCE_SET.format(patch)

        self.wikiText = self.wikiText.replace(sentence1_1 + sentence1_2,
                                              sentence1_1Trans + sentence1_2Trans)

    def create_sentence_community(self):
        sentenceCommunity = re.findall(".*?contributed.*?Steam Workshop.*?\.",
                                       self.wikiText)

        if sentenceCommunity:
            link = re.findall("\[http.*?contribute.*?\]", sentenceCommunity[0])
            if link:
                link = re.sub(" contribute.*?\]", "", link[0]).replace("[", "")
                link = self.strings.SENTENCE_COMMUNITY_LINK.format(link)

            try:
                name = re.sub('name \"', '',
                              re.findall('name.*?\".*?\"',
                                         sentenceCommunity[0])[0]).replace('"', '')
                name = self.strings.SENTENCE_COMMUNITY_NAME.format(name)
            except (TypeError, IndexError):
                name = ""

            sct = self.strings.SENTENCE_COMMUNITY.format(self.itemName, name, link)

            self.wikiText = self.wikiText.replace(sentenceCommunity[0], sct)
        else:
            return

    def create_sentence_promo(self):
        sentencePromo = re.findall(".*?\[\[Genuine\]\].*?quality.*?\.",
                                   self.wikiText)
        if sentencePromo:
            if "[[Steam]]" in sentencePromo:
                spt_s = self.strings.SENTENCE_PROMOTIONAL_STEAM
            else:
                spt_s = ""

            try:
                date = re.findall("before .*?,.*?20\d\d", sentencePromo[0])
                date = re.sub("before ", "", date[0])
                dateDay = re.sub("[a-z] ", "",
                                 re.findall("[a-z] \d[\d|,]",
                                            date)[0]).replace(",", "")

                dateMonth = re.sub(" \d", "",
                                   re.findall("[A-z].*?\d", date)[0])

                dateYear = re.sub(", ", "",
                                  re.findall(", \d{4}", date)[0])

                dateFMT = "{{{{Date fmt|{}|{}|{}}}}}".format(dateMonth, dateDay, dateYear)
                spt_d = self.strings.SENTENCE_PROMOTIONAL_DATE.format(dateFMT)
            except:
                spt_d = ""
            try:
                game = re.findall("\[?\[?''.*?\]?\]?''", sentencePromo[0])[0]
                game = self.lf(game.replace("''", ""))
            except IndexError:
                print("No game")
                return

            spt = self.strings.SENTENCE_PROMOTIONAL.format(self.itemName, game, spt_s, spt_d)

            self.wikiText = self.wikiText.replace(sentencePromo[0], spt)
        else:
            return

    # =========
    # Translate
    # =========

    def translate(self):
        for method in self.methods:
            print("Method: ", method)
            if self.restricted and method not in gui.GUI_METHODS_NOARGS:
                continue

            eval("self."+method+"()")

        return self.wikiText