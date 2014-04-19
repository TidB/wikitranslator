import re

import sDE

# ===
# Run
# ===


def run_cw(wikiTextRaw, iso):
    global S
    S = eval("s" + iso.upper())

    wikiTextRawCopy = wikiTextRaw

    wikiTextType = get_wikitext_type(wikiTextRaw)
    itemName, wikiTextRawCopy = get_itemname(wikiTextRaw, wikiTextRawCopy)
    classLink, classLinkCounter = get_using_classes(wikiTextRaw)
    print(classLink)
    classList = create_class_list(classLink, classLinkCounter)

    wikiTextRaw = create_sentence_1_cw(classLink,
                                       classList,
                                       itemName,
                                       wikiTextRaw,
                                       wikiTextRawCopy,
                                       wikiTextType,
                                       iso)

    wikiTextRaw = create_sentence_community(itemName, wikiTextRaw, wikiTextRawCopy)
    wikiTextRaw = create_sentence_promo(itemName, wikiTextRaw, wikiTextRawCopy)

    wikiTextRaw = translate_headlines(wikiTextRaw)
    wikiTextRaw = translate_update_history(itemName, wikiTextRaw)
    wikiTextRaw = translate_categories(wikiTextRaw)
    wikiTextRaw = translate_classlinks(classLink, iso, wikiTextRaw)
    wikiTextRaw = translate_levels(wikiTextRaw)

    wikiTextRaw = re.sub("\|.*?Steam Workshop.*?thumbnail.*?\.",
                         S.SENTENCE_THUMBNAIL.format(itemName),
                         wikiTextRaw)
    wikiTextRaw = re.sub("\| ?item-flags += +Not Tradable or Usable in Crafting",
                         "| item-flags   =" + S.NOT_CRAFTABLE_TRADABLE,
                         wikiTextRaw)
    wikiTextRaw = re.sub("\| ?item-flags += +Not Tradable",
                         "| item-flags   =" + S.NOT_TRADABLE,
                         wikiTextRaw)
    wikiTextRaw = re.sub("\| ?item-flags += +Not Usable in Crafting",
                         "| item-flags   =" + S.NOT_CRAFTABLE,
                         wikiTextRaw)
    wikiTextRaw = re.sub("\| ?att-1-negative += +Holiday Restriction: Halloween / Full Moon",
                         "| att-1-negative   = " + S.RESTRICTED_HALLOWEEN_FULLMOON,
                         wikiTextRaw)

    return wikiTextRaw


def run_st(wikiTextRaw, iso):
    global S
    S = eval("s" + iso.upper())

    wikiTextRawCopy = wikiTextRaw

    itemName, wikiTextRawCopy = get_itemname(wikiTextRaw, wikiTextRawCopy)
    classLink, classLinkCounter = get_using_classes(wikiTextRaw)
    classList = create_class_list(classLink, classLinkCounter)

    wikiTextRaw = add_displaytitle(itemName, wikiTextRaw)
    wikiTextRaw = create_sentence_1_set(classLink, classList, itemName, wikiTextRaw)
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


def add_displaytitle(itemName, wikiTextRaw):
    return "\n".join([S.DISPLAYTITLE.format(itemName), wikiTextRaw])


def create_class_list(classLink, classLinkCounter):
    if classLinkCounter == -1 or classLinkCounter == 9:
        classList = S.SENTENCE_1_CLASSES_ALL
    elif classLinkCounter == 1:
        classList = S.SENTENCE_1_CLASSES_ONE.format(_lf(classLink))
    elif classLinkCounter > 1:
        classList = S.SENTENCE_1_CLASSES_ONE.format(_lf(classLink[0]))
        last = classLink.pop()
        for c in classLink[1:]:
            classList = (classList +
                         ", " +
                         S.SENTENCE_1_CLASSES_ONE.format(_lf(c)))

        classList = (classList +
                     " und " +
                     S.SENTENCE_1_CLASSES_ONE.format(_lf(last)))

    return classList


def get_itemname(wikiTextRaw, wikiTextRawCopy):
    wikiTextRawCopy = re.sub("{{[Qq]uotation.*?}}", "", wikiTextRawCopy)
    itemName = re.findall("'''.*?'''.*?[is|are].*?a", wikiTextRawCopy)
    itemName = re.sub(" [is|are].*?a", "", re.sub("'''", "", itemName[0]))

    return itemName, wikiTextRawCopy


def get_item_promo(wikiTextRaw):
    return bool(re.findall("\{\{avail.*?promo.*?\}\}",
                           wikiTextRaw))


def get_item_community(wikiTextRawCopy):
    return bool(re.findall('.*?contributed.*?"*.*"*\.',
                           wikiTextRawCopy))


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
        cn = c.replace("]]", "/de]]")
        wikiTextRaw = wikiTextRaw.replace(c, cn)

    return wikiTextRaw


def translate_classlinks(classLink, iso, wikiTextRaw):
    if type(classLink) is list:
        for link in classLink:
            linkIso = link.replace("]]", "/{}|{}]]".format(iso, _lf_ext(_lf(link))))
            wikiTextRaw = wikiTextRaw.replace(link, linkIso)
    elif type(classLink) is str:
        if "all" in classLink.lower():
            linkIso = S.ALLCLASSESBOX.format(iso)
        else:
            linkIso = classLink.replace("]]", "/{}|{}]]".format(iso, _lf(classLink)))
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


def translate_update_history(itemName, wikiTextRaw):
    return re.sub(r".*?[Aa]dded.*? to the game.",
                  S.ADDEDTOGAME.format(itemName), wikiTextRaw)


# ==================
# Creating sentences
# ==================


def create_sentence_1_cw(classLink, classList,
                         itemName, wikiTextRaw,
                         wikiTextRawCopy, wikiTextType,
                         iso):

    wikiTextTypeFormat = wikiTextType.upper()
    
    if wikiTextType == "weapon":
        slot = get_weapon_slot(wikiTextRaw)
        S.SENTENCE_1_WEAPON = eval("S.SENTENCE_1_" +
                                   slot.upper()).format(_lf(classLink).lower())
        
    typeLink = eval("S.SENTENCE_1_" + wikiTextTypeFormat)
    if get_item_community(wikiTextRawCopy):
        com = eval("S.SENTENCE_1_COMMUNITY_" + wikiTextTypeFormat)
    else:
        com = ""
        
    if get_item_promo(wikiTextRawCopy):
        promo = eval("S.SENTENCE_1_PROMO_" + wikiTextTypeFormat)
        if wikiTextType == "cosmetic" and iso.lower() == "de":
            typeLink = ""
    else:
        promo = ""

    nounMarkerIndefinite = eval("S.NOUNMARKER_INDEFINITE_" + wikiTextTypeFormat)

    sentence1 = re.findall(".*?'''" + itemName + "'''.*? for .*?\.",
                           wikiTextRawCopy)[0]

    sentence1Trans = S.SENTENCE_1_ALL.format(itemName,
                                             nounMarkerIndefinite,
                                             com,
                                             promo,
                                             typeLink,
                                             classList)

    wikiTextRawCopy = wikiTextRawCopy.replace(sentence1, "")
    wikiTextRaw = wikiTextRaw.replace(sentence1, (sentence1Trans + S.ITEMLOOK))

    return wikiTextRaw


def create_sentence_1_set(classLink, classList, itemName, wikiTextRaw):
    sentence1_1 = re.findall(".*?'''" + itemName + "'''.*? for .*?\.", wikiTextRaw)[0]
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


def create_sentence_community(itemName, wikiTextRaw, wikiTextRawCopy):
    sentenceCommunity = re.findall(".*?contributed.*?\[\[Steam Workshop\]\].*?\.",
                                   wikiTextRawCopy)

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


def create_sentence_promo(itemName, wikiTextRaw, wikiTextRawCopy):
    sentencePromo = re.findall(".*?\[\[Genuine\]\].*?quality.*?\.",
                               wikiTextRawCopy)

    if sentencePromo:
        game = re.findall("''\[\[.*?\]\]''", sentencePromo[0])[0]
        game = _lf(game.replace("''", ""))

        date = re.findall("before .*?,.*?\d{4}", sentencePromo[0])
        date = re.sub("before ", "", date[0])

        dateDay = re.sub("[a-z] ", "",
                         re.findall("[a-z] \d[\d|,]",
                                    date)[0]).replace(",", "")

        dateMonth = re.sub(" \d", "",
                               re.findall("[A-z].*?\d", date)[0])

        dateMonth = S.DICTIONARY_MONTHS[dateMonth]

        dateYear = re.sub(", ", "",
                              re.findall(", \d{4}", date)[0])
        date = S.DATE.format(dateDay, dateMonth, dateYear)

        spt = S.SENTENCE_PROMOTIONAL.format(itemName, game, date)

        return wikiTextRaw.replace(sentencePromo[0], spt)
    else:
        return wikiTextRaw
