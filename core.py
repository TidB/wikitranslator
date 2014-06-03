import re
from urllib.parse import quote
import urllib.request
import xml.etree.ElementTree as ET

import sDE


# ===
# ISO
# ===


def set_iso(iso):
    global S
    S = eval("s" + iso.upper())


# ===
# Run
# ===


def run_cw(wikiTextRaw):
    wikiTextType = get_wikitext_type(wikiTextRaw)
    itemName = get_itemname(wikiTextRaw)
    classLink, classLinkCounter = get_using_classes(wikiTextRaw)
    wikiTextRaw = create_sentence_1_cw(classLink,
                                       classLinkCounter,
                                       itemName,
                                       wikiTextRaw,
                                       wikiTextType)

    wikiTextRaw = create_sentence_community(itemName, wikiTextRaw)
    wikiTextRaw = create_sentence_promo(itemName, wikiTextRaw)

    wikiTextRaw = translate_headlines(wikiTextRaw)
    wikiTextRaw = translate_update_history(itemName, wikiTextRaw)
    wikiTextRaw = translate_categories(wikiTextRaw)
    wikiTextRaw = translate_classlinks(classLink, wikiTextRaw)
    wikiTextRaw = translate_levels(wikiTextRaw)
    wikiTextRaw = translate_item_flags(wikiTextRaw)

    wikiTextRaw = re.sub("\|.*?Steam Workshop.*?thumbnail.*?\.",
                         S.SENTENCE_THUMBNAIL.format(itemName),
                         wikiTextRaw)

    return wikiTextRaw


def run_st(wikiTextRaw):
    itemName = get_itemname(wikiTextRaw, wikiTextRawCopy)
    classLink, classLinkCounter = get_using_classes(wikiTextRaw)

    wikiTextRaw = add_displaytitle(itemName, wikiTextRaw)
    wikiTextRaw = create_sentence_1_set(classLink, classLinkCounter, itemName, wikiTextRaw)
    wikiTextRaw = translate_categories(wikiTextRaw)
    wikiTextRaw = translate_headlines(wikiTextRaw)

    match = re.search("(The|This) set (contains|includes) the following items:", wikiTextRaw).group()
    wikiTextRaw = re.sub(match,
                         S.SENTENCE_SET_INCLUDES,
                         wikiTextRaw)

    part = wikiTextRaw[wikiTextRaw.index(S.SENTENCE_SET_INCLUDES):]
    for link in re.finditer("\* ?\[\[.*?\]\]", part):
        link = link.group()
        wikiTextRaw = wikiTextRaw.replace(link, _lf_to_t(link))

    return wikiTextRaw


# ================
# Wikitext options
# ================


def _lf(link):
    return link.replace("[", "").replace("]", "")


def _lf_ext(link):
    return re.sub("\|.*", "", link)


def _lf_to_t(link):
    return link.replace("[[", "{{item link|").replace("]]", "}}")


def _lf_w(link):
    if "{{" in link:
        return re.sub("\|[^|]*?\}\}", "", re.sub("\{\{[Ww][\w]*?\|", "", link)).replace("}}", "")
    elif "[[" in link:
        return re.sub("\|.*?\]\]", "", re.sub("\[\[[Ww][\w]*?:", "", link)).replace("]]", "")


def _lf_t_wl(link):
    text = urllib.request.urlopen("http://wiki.teamfortress.com/w/api.php?format=xml&action=query&titles={}&prop=info&inprop=displaytitle&redirects".format(quote(link))).read()
    text = str(text, "utf-8")
    root = ET.fromstring(text)
    if root.find(".//*[@missing='']"):
        print("Invalid page name: ", link)
        return link, link, False

    pagetitle = root.find(".//*[@title]").attrib['title']
    displaytitle = root.find(".//*[@displaytitle]").attrib['displaytitle']
    
    return pagetitle, displaytitle, True


def add_displaytitle(itemName, wikiTextRaw):
    return "\n".join([S.DISPLAYTITLE.format(itemName), wikiTextRaw])


def check_quote(wikiTextRaw):
    quotes = re.findall("\{\{[Qq]uotation.*?\}\}", wikiTextRaw)
    for q in quotes:
        file = re.findall("\|sound=.*\}\}", q)
        if not file:
            print(q, "is not sound-enabled")
            continue

        file = file[0].replace("|sound=", "").replace(".wav", "").replace("}", "")
        filen = "File:{} {}.wav".format(file, S.ISO)
        if not _lf_t_wl(filen)[2]:
            print("No localized file for", filen)
            qn = "|sound={}|en-sound=yes}}}}".format(file+".wav")
        else:
            qn = "|sound={}}}}}".format(filen)

        wikiTextRaw = re.sub("\|sound.*?\}\}", qn, wikiTextRaw)

    return wikiTextRaw


def create_class_list(classLink, classLinkCounter):
    if classLinkCounter == -1 or classLinkCounter == 9:
        classList = S.SENTENCE_1_CLASSES_ALL
    elif classLinkCounter == 1:
        classList = S.SENTENCE_1_CLASSES_ONE.format(_lf(classLink))
    elif classLinkCounter > 1:
        classList = S.SENTENCE_1_CLASSES_ONE.format(_lf(classLink[0]))
        last = classLink[-1]
        for c in classLink[1:-2]:
            classList = (classList +
                         ", " +
                         S.SENTENCE_1_CLASSES_ONE.format(_lf(c)))

        classList = (classList +
                     " und " +
                     S.SENTENCE_1_CLASSES_ONE.format(_lf(last)))

    return classList


def get_itemname(wikiTextRaw):
    itemName = re.findall("'''.*?'''.*?[is|are].*?a",
                          re.sub("{{[Qq]uotation.*?}}", "", wikiTextRaw))
    itemName = re.sub(" [is|are].*?a", "", re.sub("'''", "", itemName[0]))

    return itemName


def get_item_promo(wikiTextRaw):
    return bool(re.findall("\{\{avail.*?promo.*?\}\}",
                           wikiTextRaw))


def get_item_community(wikiTextRaw):
    return bool(re.findall('.*?contributed.*?"*.*"*\.',
                           wikiTextRaw))


def get_using_classes(wikiTextRaw):
    classLink = re.findall("used-by +=.*", wikiTextRaw)
    classLink = re.sub("used-by += +", "", classLink[0])

    if "all" in _lf(classLink).lower():
        classLinkCounter = -1
    else:
        classLinkCounter = classLink.count(",") + 1

    if classLinkCounter > 1:
        classLink = classLink.split(", ")

    return classLink, classLinkCounter


def get_weapon_slot(wikiTextRaw):
    slot = re.sub("slot.*?= ", "",
                  re.findall("slot.*?=.*", wikiTextRaw)[0])

    return slot


def get_wikitext_type(wikiTextRaw):
    if "{{item set infobox" in wikiTextRaw.lower():
        wikiTextType = "set"
    elif "{{item infobox" in wikiTextRaw.lower():
        wikiTextType = re.sub("type.*?= ", "",
                              re.findall("type.*?=.*?\n",
                                         wikiTextRaw)[0]).replace("\n", "")

        if wikiTextType.lower() == "misc" or wikiTextType.lower() == "hat":
            wikiTextType = "cosmetic"
    else:
        wikiTextType = "none"

    return wikiTextType


def transform_decimal(wikiTextRaw):
    for n in re.findall('[^"]\d+\.\d+[^"]', wikiTextRaw):
        wikiTextRaw = wikiTextRaw.replace(n, n.replace(".", ","))

    return wikiTextRaw


def translate_categories(wikiTextRaw):
    categories = re.findall("\[\[Category:.*?\]\]", wikiTextRaw)

    for c in categories:
        cn = c.replace("]]", "/{}]]".format(S.ISO))
        wikiTextRaw = wikiTextRaw.replace(c, cn)

    return wikiTextRaw


def translate_classlinks(classLink, wikiTextRaw):
    if type(classLink) is list:
        for link in classLink:
            linkIso = link.replace("]]", "/{}|{}]]".format(S.ISO, _lf_ext(_lf(link))))
            wikiTextRaw = wikiTextRaw.replace(link, linkIso)
    elif type(classLink) is str:
        if "all" in classLink.lower():
            linkIso = S.ALLCLASSESBOX.format(S.ISO)
        else:
            linkIso = classLink.replace("]]", "/{}|{}]]".format(S.ISO, _lf(classLink)))
        wikiTextRaw = wikiTextRaw.replace(classLink, linkIso)

    return wikiTextRaw


def translate_headlines(wikiTextRaw):
    headlines = re.findall("==.*?==", wikiTextRaw)
    for hl in headlines:
        hln = re.sub(" *==", "", re.sub("== *", "", hl)).strip()
        try:
            hln = S.DICTIONARY_HEADLINES[hln.lower()].join(["== ", " =="])
        except KeyError:
            print("Unknown key:", hl)
            continue
        wikiTextRaw = wikiTextRaw.replace(hl, hln)

    return wikiTextRaw


def translate_item_flags(wikiTextRaw):
    try:
        itemFlag = re.search("\|.*?item-flags.*", wikiTextRaw).group()
        print(itemFlag)
        iF = re.sub("\|.*?= +", "", itemFlag)
        iFn = "| item-flags   = " + S.DICTIONARY_FLAGS[iF.lower()]
        wikiTextRaw = wikiTextRaw.replace(itemFlag, iFn)
    except (AttributeError, KeyError):
        pass

    try:
        itemAtt = re.search("\|.*?att-1-negative.*", wikiTextRaw).group()
        iA = re.sub("\|.*?= +", "", itemAtt)
        iAn = "| att-1-negative   = " + S.DICTIONARY_ATTS[iA.lower()]
        wikiTextRaw = wikiTextRaw.replace(itemAtt, iAn)
    except (AttributeError, KeyError):
        pass

    return wikiTextRaw


def translate_levels(wikiTextRaw):
    level = re.findall("Level \d+-?\d*? [A-z ]+", wikiTextRaw)[0]
    levelNew = level.replace("Level ", "")

    levelInt = re.findall("\d+-?\d*", levelNew)[0]
    levelKey = re.findall("[A-z ]+", levelNew)[0]

    try:
        levelKN = S.DICTIONARY_LEVEL_C[levelKey.strip()]
    except KeyError:
        print("Unknown key:", levelKey)
        levelKN = levelKey.strip()

    levelNew = S.LEVEL.format(levelKN, levelInt)

    return wikiTextRaw.replace(level, levelNew)


def translate_main_seealso(wikiTextRaw):
    temps = []
    temps.extend(re.findall("\{\{[Mm]ain.*?\}\}", wikiTextRaw))
    temps.extend(re.findall("\{\{[Ss]ee also.*?\}\}", wikiTextRaw))
    for t in temps:
        link = re.findall("\|.*?[^|]*", t)[0].replace("|", "").replace("}", "")
        pagetitle, displaytitle, _ = _lf_t_wl(link)
        if "main" in t.lower():
            tn = "{{{{Main|{}|l1={}}}}}".format(pagetitle, displaytitle)
        elif "see also" in t.lower():
            tn = "{{{{See also|{}|l1={}}}}}".format(pagetitle, displaytitle)
        wikiTextRaw = wikiTextRaw.replace(t, tn)

    return wikiTextRaw


def translate_update_history(itemName, wikiTextRaw):
    return re.sub(".*?[Aa]dded.*? to the game\.",
                  S.ADDEDTOGAME.format(itemName), wikiTextRaw)


# ===================
# Wikimedia API usage
# ===================


def translate_wikilink(wikiTextRaw):
    links = re.findall("\[\[.*?\]\]",
                       re.sub("\[\[[Ww]ikipedia:", "[[w:", wikiTextRaw))
    for l in links:
        if "/de" in l \
           or "category:" in l.lower() \
           or "file:" in l.lower() \
           or "image:" in l.lower() \
           or "[[w:" in l.lower():
            continue
        ln = _lf_ext(_lf(l))
        ln = re.sub("#.*$", "", ln)
        ln = ln.replace(" ", "_")
        ln = ln+"/"+S.ISO
        pagetitle, displaytitle, _ = _lf_t_wl(ln)
        ln = "[[{}|{}]]".format(pagetitle, displaytitle)
        wikiTextRaw = wikiTextRaw.replace(l, ln)

    return wikiTextRaw


def translate_wikipedia_link(wikiTextRaw):
    links = []
    links.extend(re.findall("\[\[[Ww][\w]*:.*?\]\]", wikiTextRaw))
    links.extend(re.findall("\{\{[Ww][\w]*\|.*?\}\}", wikiTextRaw))
    for l in links:
        ln = _lf_w(l)
        ln = re.sub("#.*$", "", ln)
        ln = ln.replace(" ", "_")
        text = urllib.request.urlopen("http://en.wikipedia.org/w/api.php?format=xml&action=query&titles={}&prop=langlinks&lllimit=400&redirects".format(quote(ln))).read()
        text = str(text, "utf-8")
        root = ET.fromstring(text)
        if root.find(".//*[@missing='']"):
            print("Invalid page name: ", l)
            continue

        t = root.find(".//*[@lang='{}']".format(S.ISO))
        if t is None:
            print("No /{} article for {} => {}".format(S.ISO, l, ln))
            continue

        tn = "[[w:{0}:{1}|{1}]]".format(S.ISO, t.text)
        wikiTextRaw = wikiTextRaw.replace(l, tn)
            
    return wikiTextRaw


# ==================
# Creating sentences
# ==================


def create_sentence_1_cw(classLink, classLinkCounter,
                         itemName, wikiTextRaw,
                         wikiTextType):

    sentence1 = re.findall(".*?'''" + itemName + "'''.*? for .*?\.",
                           wikiTextRaw)[0]

    wikiTextTypeFormat = wikiTextType.upper()

    if wikiTextType == "weapon":
        slot = get_weapon_slot(wikiTextRaw)
        S.SENTENCE_1_WEAPON = eval("S.SENTENCE_1_" +
                                   slot.upper()).format(_lf(classLink).lower())

    nounMarkerIndefinite = eval("S.NOUNMARKER_INDEFINITE_" + wikiTextTypeFormat)

    if get_item_community(wikiTextRaw):
        com = eval("S.SENTENCE_1_COMMUNITY_" + wikiTextTypeFormat)
    else:
        com = ""

    typeLink = eval("S.SENTENCE_1_" + wikiTextTypeFormat)
    if get_item_promo(wikiTextRaw):
        promo = eval("S.SENTENCE_1_PROMO_" + wikiTextTypeFormat)
        if wikiTextType == "cosmetic" and S.ISO == "de":
            typeLink = ""
    else:
        promo = ""

    classList = create_class_list(classLink, classLinkCounter)

    sentence1Trans = S.SENTENCE_1_ALL.format(itemName,
                                             nounMarkerIndefinite,
                                             com,
                                             promo,
                                             typeLink,
                                             classList)

    wikiTextRaw = wikiTextRaw.replace(sentence1, (sentence1Trans + S.ITEMLOOK))

    return wikiTextRaw


def create_sentence_1_set(classLink, classLinkCounter, itemName, wikiTextRaw):
    sentence1_1 = re.findall(".*?'''" + itemName + "'''.*? for .*?\.", wikiTextRaw)[0]
    classList = create_class_list(classLink, classLinkCounter)
    sentence1_1Trans = S.SENTENCE_1_ALL.format(itemName,
                                               S.NOUNMARKER_INDEFINITE_SET,
                                               "",
                                               "",
                                               S.SENTENCE_1_SET,
                                               classList)

    sentence1_2 = re.findall(" It was .*?added to the game.*?\.", wikiTextRaw)[0]
    patch = _lf(re.findall("\[\[.*?\]\]", sentence1_2)[0])
    sentence1_2Trans = S.SENTENCE_SET.format(patch)

    return wikiTextRaw.replace(sentence1_1 + sentence1_2,
                               sentence1_1Trans + sentence1_2Trans)


def create_sentence_community(itemName, wikiTextRaw):
    sentenceCommunity = re.findall(".*?contributed.*?Steam Workshop.*?\.",
                                   wikiTextRaw)
    
    if sentenceCommunity:
        link = re.findall("\[http.*?contribute.*?\]", sentenceCommunity[0])
        if link:
            link = re.sub(" contribute.*?\]", "", link[0]).replace("[", "")
            link = S.SENTENCE_COMMUNITY_LINK.format(link)

        try:
            name = re.sub('name \"', '',
                          re.findall('name.*?\".*?\"',
                                     sentenceCommunity[0])[0]).replace('"', '')
            name = S.SENTENCE_COMMUNITY_NAME.format(name)
        except (TypeError, IndexError):
            name = ""

        sct = S.SENTENCE_COMMUNITY.format(itemName, name, link)

        return wikiTextRaw.replace(sentenceCommunity[0], sct)
    else:
        return wikiTextRaw


def create_sentence_promo(itemName, wikiTextRaw):
    sentencePromo = re.findall(".*?\[\[Genuine\]\].*?quality.*?\.",
                               wikiTextRaw)
    if sentencePromo:
        if "[[Steam]]" in sentencePromo:
            spt_s = S.SENTENCE_PROMOTIONAL_STEAM
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
            spt_d = S.SENTENCE_PROMOTIONAL_DATE.format(dateFMT)
        except:
            spt_d = ""
        try:
            game = re.findall("\[?\[?''.*?\]?\]?''", sentencePromo[0])[0]
            game = _lf(game.replace("''", ""))
        except IndexError:
            return wikiTextRaw

        spt = S.SENTENCE_PROMOTIONAL.format(itemName, game, spt_s, spt_d)

        return wikiTextRaw.replace(sentencePromo[0], spt)
    else:
        return wikiTextRaw
