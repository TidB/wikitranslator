import re
from urllib.parse import quote
import urllib.request
import xml.etree.ElementTree as ET

import sDE
import sFI
import sKO
import sPT_BR

API_LOCATION = "http://wiki.teamfortress.com/w/api.php?action=query&format=xml"

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

MAX_PAGE_SIZE = 10000


def get_wiki_root(link):
    text = urllib.request.urlopen(link).read()
    text = text.decode("utf-8")
    return ET.fromstring(text)


def import_category(category):
    root = get_wiki_root(API_LOCATION+"&list=categorymembers&cmtitle=Category:{}&cmdir=asc&cmlimit=200".format(quote(category)))
    if root.find(".//*cm") is None:
        raise ValueError("Invalid category '{}'".format(category))
    else:
        wikitexts = []
        for cmember in root.iter("cm"):
            if str(cmember.attrib['ns']) != "0":
                continue
            title = cmember.attrib['title']
            title = title.replace(" ", "_")
            root = get_wiki_root(API_LOCATION+"&titles={}&prop=revisions|info&rvprop=content&redirects".format(title))
            if int(root.find(".//*page").attrib['length']) >= MAX_PAGE_SIZE:
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


def get_wikilink(link, sound=False):
    root = get_wiki_root(API_LOCATION+"&titles={}&prop=info&inprop=displaytitle&redirects".format(quote(link)))
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
        self.wikitext = wikitext
        try:
            self.strings = eval("s" + language.upper().replace("-", "_"))
        except ImportError:
            raise
        try:
            self.wikiTextType = self.get_wikitext_type()
            self.itemName = self.get_itemname()
            self.classLinks = self.get_using_classes()
            self.classList = self.create_class_list()
            self.restricted = False
        except Exception:
            self.restricted = True

    def __str__(self):
        return self.wikitext

    def add_displaytitle(self):
        self.wikitext = "\n".join([self.strings.DISPLAYTITLE.format(self.itemName), self.wikitext])

    def check_quote(self):
        quotes = re.findall("\{\{[Qq]uotation.*?\}\}", self.wikitext)
        for q in quotes:
            file = re.findall("\|sound=.*\}\}", q)
            if not file:
                continue

            file = file[0].replace("|sound=", "").replace(".wav", "").replace("}", "")
            filen = "File:{} {}.wav".format(file, self.language)
            if not get_wikilink(filen, True)[2]:
                qn = "|sound={}|en-sound=yes}}}}".format(file+".wav")
            else:
                qn = "|sound={}}}}}".format(filen)

            self.wikitext = re.sub("\|sound.*?\}\}", qn, self.wikitext)

    def create_class_list(self):
        if "all" in self.classLinks[0].lower():
            return self.strings.SENTENCE_1_CLASSES_ALL
        else:
            for i, classLink in enumerate(self.classLinks):
                if self.strings.DICTIONARY_CLASSES:
                    self.classLinks[i] = self.strings.DICTIONARY_CLASSES[lf_ext(lf(classLink))]
                else:
                    self.classLinks[i] = lf_ext(lf(classLink))

            if len(self.classLinks) == 1:
                return self.strings.SENTENCE_1_CLASSES_ONE.format(self.classLinks[0])
            elif len(self.classLinks) > 1:
                classes = self.strings.SENTENCE_1_CLASSES_ONE.format(self.classLinks[0])
                for c in self.classLinks[1:-1]:
                    classes = (classes +
                               self.strings.SENTENCE_1_CLASSES_COMMA +
                               self.strings.SENTENCE_1_CLASSES_ONE.format(c))

                classes = (classes +
                           self.strings.SENTENCE_1_CLASSES_AND +
                           self.strings.SENTENCE_1_CLASSES_ONE.format(self.classLinks[-1]))

                return classes

    def get_itemname(self):
        itemname = re.search("'''.*?'''.*?(is|are).*?(a|an)",
                             re.sub("{{[Qq]uotation.*?}}", "", self.wikitext)).group()
        itemname = re.sub(" [is|are].*?a", "", itemname.replace("'''", ""))

        return itemname

    def get_using_classes(self):
        classlink = re.findall("used-by +=.*", self.wikitext)
        classlink = re.sub("used-by += +", "", classlink[0])
        if "all" in lf(classlink).lower():
            return [classlink]
        else:
            if classlink.count(",")+1 > 1:
                return classlink.split(", ")
            else:
                return [classlink]

    def get_weapon_slot(self):
        return re.sub("slot.*?= ", "", re.findall("slot.*?=.*", self.wikitext)[0])

    def get_wikitext_type(self):
        if "{{item set infobox" in self.wikitext.lower():
            wikitext_type = "set"
        elif "{{item infobox" in self.wikitext.lower():
            wikitext_type = re.sub("type.*?= ", "",
                                   re.findall("type.*?=.*?\n",
                                              self.wikitext)[0]).replace("\n", "")

            if wikitext_type.lower() == "misc" or wikitext_type.lower() == "hat":
                wikitext_type = "cosmetic"
        else:
            wikitext_type = "none"

        return wikitext_type

    def transform_decimal(self):
        for dot in re.findall('[^"]\d+\.\d+[^"]', self.wikitext):
            self.wikitext = self.wikitext.replace(dot, dot.replace(".", ","))

    def transform_link(self):
        links = re.findall("\[\[.*?\]\]", self.wikitext)
        for l in links:
            if "/{}".format(self.language) in l \
                    or "category:" in l.lower() \
                    or "image:" in l.lower() \
                    or "file:" in l.lower() \
                    or "[[w:" in l.lower():
                continue
            self.wikitext = self.wikitext.replace(l, lf_to_t(lf_ext(l)))

    def translate_categories(self):
        categories = re.findall("\[\[Category:.*?\]\]", self.wikitext)

        for c in categories:
            cn = c.replace("]]", "/{}]]".format(self.language))
            self.wikitext = self.wikitext.replace(c, cn)

    def translate_classlinks(self):
        if "all" in self.classLinks[0].lower():
            linkiso = self.strings.ALLCLASSESBOX.format(self.language)
            self.wikitext = self.wikitext.replace(self.classLinks[0], linkiso)
        elif len(self.classLinks) >= 1:
            for link in self.classLinks:
                linkiso = link.replace("]]", "/{}|{}]]".format(self.language, lf_ext(lf(link))))
                self.wikitext = self.wikitext.replace(link, linkiso)

    def translate_headlines(self):
        headlines = re.findall("=+.*?=+", self.wikitext)
        for hl in headlines:
            level = int(hl.count("=") / 2)
            hln = hl.replace("=", "").strip()
            try:
                hln = self.strings.DICTIONARY_HEADLINES[hln.lower()].join(["="*level, "="*level])
            except KeyError:
                continue
            self.wikitext = self.wikitext.replace(hl, hln)

    def translate_image_thumbnail(self):
        result = re.search("\| ?(The )?(Steam )?Workshop thumbnail (image )?for.*", self.wikitext)
        if result:
            result_translated = self.strings.SENTENCE_THUMBNAIL.format(self.itemName)
            self.wikitext = self.wikitext.replace(result.group(), result_translated)

    def translate_item_flags(self):
        try:
            itemflag = re.search("\|.*?item-flags.*", self.wikitext).group()
            itemflagnew = "| item-flags   = " + self.strings.DICTIONARY_FLAGS[re.sub("\|.*?= +", "", itemflag).lower()]
            self.wikitext = self.wikitext.replace(itemflag, itemflagnew)
        except (AttributeError, KeyError):
            pass

        try:
            itematt = re.search("\|.*?att-1-negative.*", self.wikitext).group()
            itemattn = "| att-1-negative   = " + self.strings.DICTIONARY_ATTS[re.sub("\|.*?= +", "", itematt).lower()]
            self.wikitext = self.wikitext.replace(itematt, itemattn)
        except (AttributeError, KeyError):
            pass

    def translate_levels(self):
        level = re.findall("Level \d+-?\d*? [A-z ]+", self.wikitext)[0]
        levelnew = level[6:]

        levelint = re.findall("\d+-?\d*", levelnew)[0]
        levelkey = re.findall("[A-z ]+", levelnew)[0]

        try:
            levelkeyn = self.strings.DICTIONARY_LEVEL_C[levelkey.strip()]
        except KeyError:
            levelkeyn = levelkey.strip()

        levelnew = self.strings.LEVEL.format(levelint, levelkeyn)
        self.wikitext = self.wikitext.replace(level, levelnew)

    def translate_main_seealso(self):
        templates = []
        templates.extend(re.findall("\{\{[Mm]ain.*?\}\}", self.wikitext))
        templates.extend(re.findall("\{\{[Ss]ee also.*?\}\}", self.wikitext))
        for template in templates:
            link = re.findall("\|.*?[^|]*", template)[0].replace("|", "").replace("}", "")
            pagetitle, displaytitle, __ = get_wikilink(link)
            if "main" in template.lower():
                tn = "{{{{Main|{}|l1={}}}}}".format(pagetitle, displaytitle)
            elif "see also" in template.lower():
                tn = "{{{{See also|{}|l1={}}}}}".format(pagetitle, displaytitle)
            else:
                return
            self.wikitext = self.wikitext.replace(template, tn)

    def translate_set_contents(self):
        result = re.search("(The|This)( set)?( contains| includes)?( the)?( following)? items.*?:", self.wikitext)
        match = result.group()
        self.wikitext = re.sub(match, self.strings.SENTENCE_SET_INCLUDES, self.wikitext)

        part = self.wikitext[self.wikitext.index(self.strings.SENTENCE_SET_INCLUDES):]
        for link in re.finditer("\* ?\[\[.*?\]\]", part):
            link = link.group()
            self.wikitext = self.wikitext.replace(link, lf_to_t(link))

    def translate_update_history(self):
        self.wikitext = re.sub(".*?[Aa]dded.*? to the game\.",
                               self.strings.ADDEDTOGAME.format(self.itemName), self.wikitext)

    # ===================
    # Wikimedia API usage
    # ===================

    def translate_wikilink(self):
        links = re.findall("\[\[.*?\]\]", re.sub("\[\[[Ww]ikipedia:", "[[w:", self.wikitext))
        for l in links:
            if "/{}".format(self.language) in l \
                    or "category:" in l.lower() \
                    or "file:" in l.lower() \
                    or "image:" in l.lower() \
                    or "[[w:" in l.lower():
                continue
            ln = lf_ext(lf(l))
            anchor = re.findall("#.*$", ln)
            if anchor:
                anchor = anchor[0]
                ln = ln.replace(anchor, "")
            else:
                anchor = ""
            ln = ln.replace(" ", "_")
            ln = ln+"/"+self.language
            pagetitle, displaytitle, __ = get_wikilink(ln)
            ln = "[[{}{}|{}]]".format(pagetitle, anchor, displaytitle)
            self.wikitext = self.wikitext.replace(l, ln)

    def translate_wikipedia_link(self):
        links = []
        links.extend(re.findall("\[\[[Ww][\w]*:.*?\]\]", self.wikitext))
        links.extend(re.findall("\{\{[Ww][\w]*\|.*?\}\}", self.wikitext))
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
            self.wikitext = self.wikitext.replace(l, tn)

    # ==================
    # Creating sentences
    # ==================

    def create_sentence_1_cw(self):
        sentence1 = re.findall(".*?'''"+self.itemName+"'''.*? for .*?\.", self.wikitext)[0]

        if self.wikiTextType == "weapon":
            slot = self.get_weapon_slot()
            typelink = getattr(self.strings, "SENTENCE_1_"+slot.upper()).format(lf(self.classLinks[0]))
        else:
            typelink = getattr(self.strings, "SENTENCE_1_"+self.wikiTextType.upper())

        nounmarkerindefinite = getattr(self.strings, "NOUNMARKER_INDEFINITE_" + self.wikiTextType.upper())

        if re.findall('.*?contributed.*?"*.*"*\.', self.wikitext):
            com = getattr(self.strings, "SENTENCE_1_COMMUNITY_"+self.wikiTextType.upper())
        else:
            com = ""
        if re.findall("\{\{avail.*?promo.*?\}\}", self.wikitext):
            promo = getattr(self.strings, "SENTENCE_1_PROMO_"+self.wikiTextType.upper())
            if self.wikiTextType == "cosmetic" and self.language == "de":
                typelink = ""
        else:
            promo = ""

        sentence1trans = self.strings.SENTENCE_1_ALL.format(self.itemName,
                                                            nounmarkerindefinite,
                                                            com,
                                                            promo,
                                                            typelink,
                                                            self.classList)

        self.wikitext = self.wikitext.replace(sentence1, (sentence1trans + self.strings.ITEMLOOK))

    def create_sentence_1_set(self):
        sentence1_1 = re.findall(".*?'''" + self.itemName + "'''.*? for .*?\.", self.wikitext)[0]
        sentence1_1trans = self.strings.SENTENCE_1_ALL.format(self.itemName,
                                                              self.strings.NOUNMARKER_INDEFINITE_SET,
                                                              "",
                                                              "",
                                                              self.strings.SENTENCE_1_SET,
                                                              self.classList)

        sentence1_2 = re.findall("\. It was .*?\.", self.wikitext)[0][1:]
        patch = lf(re.findall("\[\[.*?\]\]", sentence1_2)[0])
        sentence1_2trans = self.strings.SENTENCE_SET.format(patch)
        self.wikitext = self.wikitext.replace(sentence1_1+sentence1_2, sentence1_1trans+sentence1_2trans)

    def create_sentence_community(self):
        sentence_community = re.findall(".*?contributed.*?Steam Workshop.*\.", self.wikitext)
        if sentence_community:
            link = re.findall("\[http.*?contribute.*?\]", sentence_community[0])
            if link:
                link = re.sub(" contribute.*?\]", "", link[0]).replace("[", "")
                link = self.strings.SENTENCE_COMMUNITY_LINK.format(link)

            try:
                name = re.findall('name.*?\".*?\"', sentence_community[0])[0][6:].replace('"', '')
                name = self.strings.SENTENCE_COMMUNITY_NAME.format(name)
            except (TypeError, IndexError):
                name = ""

            sct = self.strings.SENTENCE_COMMUNITY.format(self.itemName, name, link)
            self.wikitext = self.wikitext.replace(sentence_community[0], sct)
        else:
            return

    def create_sentence_promo(self):
        sentencepromo = re.findall(".*?\[\[Genuine\]\].*?quality.*?\.", self.wikitext)
        if sentencepromo:
            if "[[Steam]]" in sentencepromo:
                spt_s = self.strings.SENTENCE_PROMOTIONAL_STEAM
            else:
                spt_s = ""

            try:
                date = re.findall("before .*?,.*?20\d\d", sentencepromo[0])[0]
                date = date.replace("before ", "")

                day = re.findall("\w \d[\d|,]", date)[0][2:].replace(",", "")
                month = re.findall("[A-z].*?\d", date)[0][:-2]
                year = re.findall(", \d{4}", date)[0][2:]

                datefmt = "{{{{Date fmt|{}|{}|{}}}}}".format(month, day, year)
                spt_d = self.strings.SENTENCE_PROMOTIONAL_DATE.format(datefmt)
            except Exception:
                spt_d = ""
            try:
                game = re.findall("\[?\[?''.*?\]?\]?''", sentencepromo[0])[0]
                game = lf(game.replace("''", ""))
            except IndexError:
                raise UserWarning("No game. Canceling promo sentence translation.")

            spt = self.strings.SENTENCE_PROMOTIONAL.format(self.itemName, game, spt_s, spt_d)

            self.wikitext = self.wikitext.replace(sentencepromo[0], spt)
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

        return self.wikitext