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
                      "translate_wikilinks",
                      "translate_wikipedia_links")

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
    return re.sub("\|.*[^]]", "", lf(link))


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

        self.wikitext_type = self.get_wikitext_type()
        self.item_name = self.get_itemname()
        self.class_links = self.get_using_classes()
        if None in [self.wikitext_type, self.item_name, self.class_links]:
            self.restricted = True
        else:
            self.restricted = False

    def __str__(self):
        return self.wikitext

    def add_displaytitle(self):
        self.wikitext = "\n".join([self.strings.DISPLAYTITLE.format(self.item_name), self.wikitext])

    def check_quote(self):
        quotes = re.findall("\{\{[Qq]uotation.*?\}\}", self.wikitext)
        for quote_ in quotes:
            file = re.findall("\|sound=.*\}\}", quote_)
            if not file:
                continue

            file = file[0].replace("|sound=", "").replace(".wav", "").replace("}", "")
            file_new = "File:{} {}.wav".format(file, self.language)
            if not get_wikilink(file_new, True)[2]:
                quote_new = "|sound={}|en-sound=yes}}}}".format(file+".wav")
            else:
                quote_new = "|sound={}}}}}".format(file_new)

            self.wikitext = re.sub("\|sound.*?\}\}", quote_new, self.wikitext)

    def create_class_list(self):
        if "all" in self.class_links[0].lower():
            return self.strings.SENTENCE_1_CLASSES_ALL
        else:
            for i, classLink in enumerate(self.class_links):
                if self.strings.DICTIONARY_CLASSES:
                    self.class_links[i] = self.strings.DICTIONARY_CLASSES[lf_ext(classLink)]
                else:
                    self.class_links[i] = lf_ext(classLink)

            classes = self.strings.SENTENCE_1_CLASSES_ONE.format(self.class_links[0])
            for class_ in self.class_links[1:-1]:
                classes = (classes +
                           self.strings.SENTENCE_1_CLASSES_COMMA +
                           self.strings.SENTENCE_1_CLASSES_ONE.format(class_))

            if len(self.class_links) > 1:
                classes = (classes +
                           self.strings.SENTENCE_1_CLASSES_AND +
                           self.strings.SENTENCE_1_CLASSES_ONE.format(self.class_links[-1]))

            return classes

    def get_itemname(self):
        itemname = re.search("'''.*?'''.*?(is|are).*?(a|an)",
                             re.sub("{{[Qq]uotation.*?}}", "", self.wikitext))
        if itemname:
            return re.sub(" [is|are].*?a", "", itemname.group().replace("'''", ""))
        else:
            return None

    def get_using_classes(self):
        classlink = re.findall("used-by +=.*", self.wikitext)
        try:
            classlink = re.sub("used-by += +", "", classlink[0])
        except IndexError:
            return None
        if "all" in lf(classlink).lower():
            return [classlink]
        else:
            if classlink.count(",")+1 > 1:
                return classlink.split(", ")
            else:
                return [classlink]

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
        for link in links:
            if "/{}".format(self.language) in link \
                    or "category:" in link.lower() \
                    or "image:" in link.lower() \
                    or "file:" in link.lower() \
                    or "[[w:" in link.lower():
                continue
            self.wikitext = self.wikitext.replace(link, lf_to_t(lf_ext(link)))

    def translate_categories(self):
        categories = re.findall("\[\[Category:.*?\]\]", self.wikitext)
        for category in categories:
            category_new = category.replace("]]", "/{}]]".format(self.language))
            self.wikitext = self.wikitext.replace(category, category_new)

    def translate_classlinks(self):
        if "all" in self.class_links[0].lower():
            linkiso = self.strings.ALLCLASSESBOX.format(self.language)
            self.wikitext = self.wikitext.replace(self.class_links[0], linkiso)
        elif len(self.class_links) >= 1:
            for link in self.class_links:
                linkiso = link.replace("]]", "/{}|{}]]".format(self.language, lf_ext(link)))
                self.wikitext = self.wikitext.replace(link, linkiso)

    def translate_headlines(self):
        headlines = re.findall("=+.*?=+", self.wikitext)
        for headline in headlines:
            level = int(headline.count("=") / 2)
            headline_new = headline.replace("=", "").strip()
            try:
                headline_new = self.strings.DICTIONARY_HEADLINES[headline_new.lower()].join(["="*level, "="*level])
            except KeyError:
                continue
            self.wikitext = self.wikitext.replace(headline, headline_new)

    def translate_image_thumbnail(self):
        result = re.search("\| ?(The )?(Steam )?Workshop thumbnail (image )?for.*", self.wikitext)
        if result:
            result_translated = self.strings.SENTENCE_THUMBNAIL.format(self.item_name)
            self.wikitext = self.wikitext.replace(result.group(), result_translated)

    def translate_item_flags(self):
        try:
            itemflag = re.search("\|.*?item-flags.*", self.wikitext).group()
            itemflagnew = "| item-flags   = " + self.strings.DICTIONARY_FLAGS[re.sub("\|.*?= +", "", itemflag).lower()]
            self.wikitext = self.wikitext.replace(itemflag, itemflagnew)
        except (AttributeError, KeyError):
            pass

        try:
            item_attribute = re.search("\|.*?att-\d-negative.*", self.wikitext).group()
            attribute_number = re.search("-\d-", item_attribute).group().replace("-", "")
            item_attribute_new = "| att-{}-negative   = ".format(attribute_number) + \
                                 self.strings.DICTIONARY_ATTS[re.sub("\|.*?= +", "", item_attribute).lower()]
            self.wikitext = self.wikitext.replace(item_attribute, item_attribute_new)
        except (AttributeError, KeyError):
            pass

    def translate_levels(self):
        level = re.findall("Level \d+-?\d*? [A-z ]+", self.wikitext)[0]
        level_translated = level[6:]

        level_number = re.findall("\d+-?\d*", level_translated)[0]
        level_key = re.findall("[A-z ]+", level_translated)[0]

        try:
            level_key_new = self.strings.DICTIONARY_LEVEL_C[level_key.strip()]
        except KeyError:
            level_key_new = level_key.strip()

        level_translated = self.strings.LEVEL.format(level_number, level_key_new)
        self.wikitext = self.wikitext.replace(level, level_translated)

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
                               self.strings.ADDEDTOGAME.format(self.item_name), self.wikitext)

    # ===================
    # Wikimedia API usage
    # ===================

    def translate_wikilinks(self):
        links = re.findall("\[\[.*?\]\]", re.sub("\[\[[Ww]ikipedia:", "[[w:", self.wikitext))
        for link in links:
            if "/{}".format(self.language) in link \
                    or "category:" in link.lower() \
                    or "file:" in link.lower() \
                    or "image:" in link.lower() \
                    or "[[w:" in link.lower():
                continue
            link_formatted = lf_ext(link)
            anchor = re.findall("#.*$", link_formatted)
            if anchor:
                anchor = anchor[0]
                link_formatted = link_formatted.replace(anchor, "")
            else:
                anchor = ""
            link_formatted = link_formatted.replace(" ", "_")
            link_formatted = link_formatted+"/"+self.language
            pagetitle, displaytitle, __ = get_wikilink(link_formatted)
            link_formatted = "[[{}{}|{}]]".format(pagetitle, anchor, displaytitle)
            self.wikitext = self.wikitext.replace(link, link_formatted)

    def translate_wikipedia_links(self):
        links = []
        links.extend(re.findall("\[\[[Ww][\w]*:.*?\]\]", self.wikitext))
        links.extend(re.findall("\{\{[Ww][\w]*\|.*?\}\}", self.wikitext))
        for link in links:
            link_formatted = lf_w(link)
            link_formatted = re.sub("#.*$", "", link_formatted)
            link_formatted = link_formatted.replace(" ", "_")
            root = get_wiki_root("http://en.wikipedia.org/w/api.php?format=xml&action=query&titles={}&prop=langlinks&lllimit=400&redirects".format(quote(link_formatted)))
            if root.find(".//*[@missing='']"):
                continue

            language_link = root.find(".//*[@lang='{}']".format(self.language))
            if language_link is None:
                continue

            link_translated = "[[w:{0}:{1}|{1}]]".format(self.language, language_link.text)
            self.wikitext = self.wikitext.replace(link, link_translated)

    # ==================
    # Creating sentences
    # ==================

    def create_sentence_1_cw(self):
        sentence1 = re.findall(".*?'''"+self.item_name+"'''.*? for .*?\.", self.wikitext)[0]

        if self.wikitext_type == "weapon":
            slot = re.sub("slot.*?= ", "", re.findall("slot.*?=.*", self.wikitext)[0])
            typelink = getattr(self.strings, "SENTENCE_1_"+slot.upper()).format(lf(self.class_links[0]))
        else:
            typelink = getattr(self.strings, "SENTENCE_1_"+self.wikitext_type.upper())

        nounmarkerindefinite = getattr(self.strings, "NOUNMARKER_INDEFINITE_" + self.wikitext_type.upper())

        if re.findall('.*?contributed.*?"*.*"*\.', self.wikitext):
            community = getattr(self.strings, "SENTENCE_1_COMMUNITY_"+self.wikitext_type.upper())
        else:
            community = ""
        if re.findall("\{\{avail.*?promo.*?\}\}", self.wikitext):
            promotional = getattr(self.strings, "SENTENCE_1_PROMO_"+self.wikitext_type.upper())
            if self.wikitext_type == "cosmetic" and self.language == "de":
                typelink = ""
        else:
            promotional = ""

        class_list = self.create_class_list()
        sentence1trans = self.strings.SENTENCE_1_ALL.format(self.item_name,
                                                            nounmarkerindefinite,
                                                            community,
                                                            promotional,
                                                            typelink,
                                                            class_list)

        self.wikitext = self.wikitext.replace(sentence1, (sentence1trans + self.strings.ITEMLOOK))

    def create_sentence_1_set(self):
        sentence1_1 = re.findall(".*?'''" + self.item_name + "'''.*? for .*?\.", self.wikitext)[0]
        class_list = self.create_class_list()
        sentence1_1trans = self.strings.SENTENCE_1_ALL.format(self.item_name,
                                                              self.strings.NOUNMARKER_INDEFINITE_SET,
                                                              "",
                                                              "",
                                                              self.strings.SENTENCE_1_SET,
                                                              class_list)

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

            sct = self.strings.SENTENCE_COMMUNITY.format(self.item_name, name, link)
            self.wikitext = self.wikitext.replace(sentence_community[0], sct)

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

            spt = self.strings.SENTENCE_PROMOTIONAL.format(self.item_name, game, spt_s, spt_d)

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