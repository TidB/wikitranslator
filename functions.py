import re

import mwparserfromhell as mw

from helpers import clean_links, Wikilink

DISPLAYTITLE = "{{{{DISPLAYTITLE: {{{{item name|{name}}}}}}}}}\n"
METHODS = []


def create_class_list(class_links, strings):
    if "classes" in class_links[0].lower():
        return strings.SENTENCE_1_CLASSES_ALL
    else:
        classes = strings.SENTENCE_1_CLASSES_ONE.format(
            class_name=class_links[0],
            loc_class_name=strings.DICTIONARY_CLASSES[class_links[0]]
        )
        for class_ in class_links[1:-1]:
            classes = (
                classes +
                strings.SENTENCE_1_CLASSES_COMMA +
                strings.SENTENCE_1_CLASSES_ONE.format(
                    class_name=class_,
                    loc_class_name=strings.DICTIONARY_CLASSES[class_]
                )
            )

        if len(class_links) > 1:
            classes = (
                classes +
                strings.SENTENCE_1_CLASSES_AND +
                strings.SENTENCE_1_CLASSES_ONE.format(
                    class_name=class_links[-1],
                    loc_class_name=strings.DICTIONARY_CLASSES[class_links[-1]]
                )
            )

        return classes


# ==============================
# Individual translation methods
# ==============================


def add_displaytitle(wikitext):
    wikitext.wikitext.insert(0, DISPLAYTITLE.format(name=wikitext.item_name))

    return wikitext.wikitext
METHODS.append((add_displaytitle, ("extended",)))


def transform_decimal(wikitext):
    for dot in re.findall('[^"]\d+\.\d+[^"]', str(wikitext)):
        wikitext.wikitext.replace(dot, dot.replace(".", ","))

    return wikitext.wikitext
METHODS.append((transform_decimal, ()))


def transform_link(wikitext):
    for link in wikitext.wikitext.filter_wikilinks():
        if re.match(":?(category|file|image|media|w):", str(link), flags=re.I):
            continue

        wikitext.wikitext.replace(
            link,
            "{{{{item name|{0}}}}}".format(link.title)
        )

    return wikitext.wikitext
METHODS.append((transform_link, ())),


def translate_allclass_links(wikitext, strings):
    if "all" in wikitext.class_links[0].lower():
        linkiso = strings.ALLCLASSESBOX.format(wikitext.language)
        wikitext.wikitext.replace(str(wikitext.class_links[0]), linkiso)

    return wikitext.wikitext
METHODS.append((translate_allclass_links, ("strings", "extended")))


def translate_categories(wikitext):
    categories = re.findall("\[\[Category:.*?\]\]", str(wikitext.wikitext))
    for category in categories:
        category_new = category.replace("]]", "/{}]]".format(wikitext.language))
        wikitext.wikitext.replace(category, category_new)

    return wikitext.wikitext
METHODS.append((translate_categories, ()))


def translate_headlines(wikitext, strings):
    headlines = wikitext.wikitext.filter_headings()
    for heading in headlines:
        title = heading.title.strip()
        if title.lower() in strings.DICTIONARY_HEADLINES:
            trans_title = strings.DICTIONARY_HEADLINES[title.lower()]
            trans_heading = trans_title.center(len(trans_title)+2).join(
                ["="*heading.level]*2
            )
            wikitext.wikitext.replace(heading, trans_heading, recursive=False)

    return wikitext.wikitext
METHODS.append((translate_headlines, ("strings",)))


def translate_image_thumbnail(wikitext, strings):
    result = re.search(
        "\| ?(The )?(Steam )?Workshop thumbnail (image )?for.*",
        str(wikitext.wikitext)
    )
    if result:
        wikitext.wikitext.replace(result.group(), strings.SENTENCE_THUMBNAIL)

    return wikitext.wikitext
METHODS.append((translate_image_thumbnail, ("strings",)))


def translate_item_flags(wikitext, strings):
    infobox = wikitext.wikitext.filter_templates(matches="Item infobox")[0]
    if infobox.has("item-flags"):
        flag = infobox.get("item-flags")
        flag.value = strings.DICTIONARY_FLAGS[str(flag.value)]
    for param in infobox.params:
        if re.search("att-\d-negative", str(param.name)):
            value = str(param.value).strip()
            if value.lower() in strings.DICTIONARY_ATTS:
                param.value = str(param.value).replace(
                    value,
                    strings.DICTIONARY_ATTS[value.lower()]
                )
    return wikitext.wikitext
METHODS.append((translate_item_flags, ("strings",)))


def translate_levels(wikitext, strings):
    infobox = wikitext.wikitext.filter_templates(matches="Item infobox")[0]
    item_kind = infobox.get("item-kind")
    value = item_kind.value.strip()
    if value in strings.DICTIONARY_LEVEL_C:
        item_kind.value.replace(value, strings.DICTIONARY_LEVEL_C[value])

    return wikitext.wikitext
METHODS.append((translate_levels, ("strings",)))


def translate_set_contents(wikitext, strings):
    result = re.search(
        "(The|This)( set)?( contains| includes)?( the)?( following)? items.*?:",
        str(wikitext.wikitext)
    )
    match = result.group()
    wikitext.wikitext.replace(match, strings.SENTENCE_SET_INCLUDES, str(wikitext))

    part = str(wikitext.wikitext)[
           str(wikitext.wikitext).index(strings.SENTENCE_SET_INCLUDES):
           ]
    for link in re.finditer("\* ?\[\[.*?\]\]", part):
        link = link.group()
        wikitext.wikitext.replace(
            link,
            link.replace("[[", "{{item link|").replace("]]", "}}")
        )

    return wikitext.wikitext
METHODS.append((translate_set_contents, ("strings",)))


def translate_update_history(wikitext, strings):
    sentence = re.search(".*?[Aa]dded.*? to the game\.", str(wikitext.wikitext))
    if sentence:
        wikitext.wikitext.replace(sentence.group(), strings.ADDEDTOGAME)

    return wikitext.wikitext
METHODS.append((translate_update_history, ("strings",)))


# ==================
# Creating sentences
# ==================

def create_sentence_1_cw(wikitext, strings):
    sentence = re.findall(
        ".*?'''"+wikitext.item_name+"'''.*? for .*?\.",
        str(wikitext.wikitext)
    )[0]

    infobox = wikitext.wikitext.filter_templates(matches="Item infobox")[0]

    if wikitext.wikitext_type == "weapon":
        slot = infobox.get("slot").value.strip()
        typelink = getattr(
            strings,
            "SENTENCE_1_"+slot.upper()
        ).format(class_name=wikitext.class_links[0].title)
    else:
        typelink = getattr(
            strings,
            "SENTENCE_1_"+wikitext.wikitext_type.upper()
        )

    nounmarkerindefinite = getattr(
        strings,
        "NOUNMARKER_INDEFINITE_" + wikitext.wikitext_type.upper()
    )

    # I would rather use the "contributed-by" attribute in the item
    # infobox, but that stuff's only added after quite some time.
    if re.findall('.*?contributed.*?"*.*"*\.', wikitext.wikitext.strip_code()):
        workshop = getattr(
            strings,
            "SENTENCE_1_COMMUNITY_"+wikitext.wikitext_type.upper()
        )
    else:
        workshop = ""

    if infobox.has("promotional"):
        promotional = getattr(
            strings,
            "SENTENCE_1_PROMO_"+wikitext.wikitext_type.upper()
        )

        if wikitext.wikitext_type == "cosmetic" and wikitext.language == "de":
            typelink = ""
    else:
        promotional = ""

    class_list = create_class_list(wikitext.class_links, strings)
    sentence_trans = strings.SENTENCE_1_ALL.format(
        item_name=wikitext.item_name,
        noun_marker=nounmarkerindefinite,
        workshop_link=workshop,
        promotional=promotional,
        item_type=typelink,
        class_list=class_list
    )

    wikitext.wikitext.replace(sentence, sentence_trans + strings.ITEMLOOK)
    return wikitext.wikitext
METHODS.append((create_sentence_1_cw, ("strings", "extended")))


def create_sentence_1_set(wikitext, strings):
    sentence1_1 = re.findall(
        ".*?'''" + wikitext.item_name + "'''.*? for .*?\.",
        str(wikitext)
    )[0]

    class_list = create_class_list(wikitext.class_links, strings)
    sentence1_1trans = strings.SENTENCE_1_ALL.format(
        item_name=wikitext.item_name,
        noun_marker=strings.NOUNMARKER_INDEFINITE_SET,
        workshop_link="",
        promotional="",
        item_type=strings.SENTENCE_1_SET,
        class_list=class_list
    )

    sentence1_2 = re.findall("\. It was .*?\.", str(wikitext.wikitext))[0][1:]
    patch = mw.parse(sentence1_2).filter_wikilinks()[0].title
    sentence1_2trans = strings.SENTENCE_SET.format(update=patch)

    wikitext.wikitext.replace(sentence1_1+sentence1_2, sentence1_1trans+sentence1_2trans)
    return wikitext.wikitext
METHODS.append((create_sentence_1_set, ("strings", "extended")))


def create_sentence_community(wikitext, strings):
    sentence_community = re.findall(".*?contributed.*?Steam Workshop.*\.", str(wikitext))
    if sentence_community:
        link = re.findall("\[http.*?contribute.*?\]", sentence_community[0])
        if link:
            link = re.sub(" contribute.*?\]", "", link[0]).replace("[", "")
            link = strings.SENTENCE_COMMUNITY_LINK.format(link=link)

        try:
            name = re.findall('name.*?\".*?\"', sentence_community[0])[0][6:].replace('"', '')
            name = strings.SENTENCE_COMMUNITY_NAME.format(name=name)
        except (TypeError, IndexError):
            name = ""

        sct = strings.SENTENCE_COMMUNITY.format(
            item_name=wikitext.item_name,  # Legacy
            custom_name=name,
            workshop_link=link
        )
        wikitext.wikitext.replace(sentence_community[0], sct)
        return wikitext.wikitext
METHODS.append((create_sentence_community, ("strings", "extended")))


def create_sentence_promo(wikitext, strings):
    sentencepromo = re.findall(".*?Genuine.*?quality.*?\.", str(wikitext))
    if sentencepromo:
        if "[[Steam]]" in sentencepromo:
            spt_s = strings.SENTENCE_PROMOTIONAL_STEAM
        else:
            spt_s = ""

        try:
            date = re.findall("before .*?,.*?20\d\d", sentencepromo[0])[0]
            date = date.replace("before ", "")

            day = re.findall("\w \d[\d|,]", date)[0][2:].replace(",", "")
            month = re.findall("[A-z].*?\d", date)[0][:-2]
            year = re.findall(", \d{4}", date)[0][2:]

            datefmt = "{{{{Date fmt|{}|{}|{}}}}}".format(month, day, year)
            spt_d = strings.SENTENCE_PROMOTIONAL_DATE.format(date=datefmt)
        except Exception:
            spt_d = ""
        try:
            game = re.findall("\[?\[?''.*?\]?\]?''", sentencepromo[0])[0]
            game = game.replace("''", "").replace("[", "").replace("]", "")
        except IndexError:
            raise UserWarning("No game. Canceling promo sentence translation.")

        spt = strings.SENTENCE_PROMOTIONAL.format(
            item_name=wikitext.item_name,  # Legacy
            game_name=game,
            steam=spt_s,
            date=spt_d
        )

        wikitext.wikitext.replace(sentencepromo[0], spt)

    return wikitext.wikitext
METHODS.append((create_sentence_promo, ("strings", "extended")))


# ====================================
# Methods operating on the Stack cache
# ====================================


def translate_quotes(wikitext, stack):
    for template in wikitext.wikitext.ifilter_templates(matches="Quotation"):
        if not template.has("sound"):
            continue
        file = template.get("sound")
        for cached_file, value in stack.sound_file_cache.items():
            if str(file.value) == cached_file or str(file.value) in value["aliases"]:
                if value["localized"][wikitext.language] is None:
                    new_file = str(file.value)
                    en_sound = True
                else:
                    new_file = value["localized"][wikitext.language]
                    en_sound = False
                break
        file.value = new_file
        if en_sound:
            template.add("en-sound", "yes", showkey=True)
    return wikitext.wikitext
METHODS.append((translate_quotes, ("cache",)))


def translate_description(wikitext, stack):
    infobox = wikitext.wikitext.filter_templates(matches="Item infobox")[0]
    if infobox.has("item-description"):
        description = infobox.get("item-description")
        description_text = str(description.value).strip()
        key_english = [
            key
            for key, value in stack.localization_file_cache[wikitext.language]["lang"]["Tokens"].items()
            if value == description_text
            ][0]
        value_german = stack.localization_file_cache[wikitext.language]["lang"]["Tokens"][key_english[9:]]
        description.value = str(description.value).replace(description_text, value_german)
    return wikitext.wikitext
METHODS.append((translate_description, ("cache",)))


def translate_main_seealso(wikitext, stack):
    # Oh please, don't look at this
    for template in wikitext.wikitext.ifilter_templates(
            matches=lambda x: str(x.name).lower() in ("see also", "main")
    ):
        arg_num = 1
        for template_link in template.params:
            if not template_link.showkey:
                for link, value in stack.wikilink_cache.items():
                    if template_link == link:  # Kill me
                        title, anchor = str(template_link).rsplit("#", maxsplit=1) if "#" in template_link else (str(template_link), "")
                        title += "/" + wikitext.language
                        template_link.value = title+"#"+anchor if anchor else title
                    elif str(template_link) in value["aliases"]:
                        title = str(template_link)+"/"+wikitext.language
                        template_link.value = title+("#"+value["aliases"][str(template_link)] if value["aliases"][str(template_link)] else "")
                    else:
                        continue

                    if value["displaytitle"][wikitext.language] is None:
                        label = template_link
                    else:
                        label = value["displaytitle"][wikitext.language]
                    template.add("l"+str(arg_num), label, showkey=True)
                    arg_num += 1
    return wikitext.wikitext
METHODS.append((translate_main_seealso, ("cache",)))


def translate_wikilinks(wikitext, stack):
    for wikilink in clean_links(wikitext.wikilinks, wikitext.language, prefixes=stack.prefixes):
        if not str(wikilink) in wikitext.wikitext:
            continue
        new_wikilink = Wikilink(wikilink.title+"/"+wikitext.language)
        for link, value in stack.wikilink_cache.items():
            if wikilink.title == link:
                new_wikilink.anchor = wikilink.anchor
            elif wikilink.title in value["aliases"]:
                new_wikilink.anchor = value["aliases"][wikilink.title]
            else:
                continue

            if wikilink.label:
                new_wikilink.label = wikilink.label
            else:
                if value["displaytitle"][wikitext.language] is None:
                    new_wikilink.label = wikilink.title
                else:
                    new_wikilink.label = value["displaytitle"][wikitext.language]
            break
        wikitext.wikitext.replace(str(wikilink), str(new_wikilink))
    return wikitext.wikitext
METHODS.append((translate_wikilinks, ("cache",)))


def translate_wikipedia_links(wikitext, stack):
    for wikipedia_link in wikitext.wikipedia_links:
        if not str(wikipedia_link) in wikitext.wikitext:
            continue
        new_link = Wikilink(wikipedia_link.title, interwiki=wikipedia_link.interwiki)
        for link, value in stack.wikipedia_links_cache.items():
            if wikipedia_link.title == link:
                new_link.anchor = wikipedia_link.anchor
            elif wikipedia_link.title in value["aliases"]:
                new_link.anchor = value["aliases"][wikipedia_link.title]
            else:
                continue

            if value["localized"][wikitext.language] is None:
                new_link.label = wikipedia_link.label
            else:
                new_link.label = value["localized"][wikitext.language]
                new_link.interwiki += ":"+wikitext.language
            break
        wikitext.wikitext.replace(str(wikipedia_link), str(new_link))
    return wikitext.wikitext
METHODS.append((translate_wikipedia_links, ("cache",)))

__all__ = [method.__name__ for method, _ in METHODS]
METHODS = {method.__name__: (method, flags) for method, flags in METHODS}
