from enum import auto, Flag
from functools import wraps
import re

import mwparserfromhell as mw

from helpers import clean_links, Wikilink

DISPLAYTITLE = '{{{{DISPLAYTITLE: {{{{item name|{name}}}}}}}}}\n'
FUNCTIONS = {}


class Function(Flag):
    CACHE = auto()
    EXTENDED = auto()


def register(*flags):
    def decorator_register(func):
        FUNCTIONS[func.__name__] = (func, flags)

        @wraps(func)
        def wrapper_register(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper_register
    return decorator_register


def create_class_list(class_links, strings):
    if 'classes' in class_links[0].lower():
        return strings.SENTENCE_1_CLASSES_ALL
    else:
        classes = strings.SENTENCE_1_CLASSES_ONE.format(
            class_name=class_links[0],
            loc_class_name=strings.CLASSES[class_links[0]]
        )
        for class_ in class_links[1:-1]:
            classes = (
                classes +
                strings.SENTENCE_1_CLASSES_COMMA +
                strings.SENTENCE_1_CLASSES_ONE.format(
                    class_name=class_,
                    loc_class_name=strings.CLASSES[class_]
                )
            )

        if len(class_links) > 1:
            classes = (
                classes +
                strings.SENTENCE_1_CLASSES_AND +
                strings.SENTENCE_1_CLASSES_ONE.format(
                    class_name=class_links[-1],
                    loc_class_name=strings.CLASSES[class_links[-1]]
                )
            )

        return classes


# ==============================
# Individual translation methods
# ==============================

@register(Function.EXTENDED)
def add_displaytitle(wikitext, _):
    if wikitext.wikitext_type in ['cosmetic', 'weapon']:
        return wikitext.wikitext

    wikitext.wikitext.insert(0, DISPLAYTITLE.format(name=wikitext.item_name))

    return wikitext.wikitext


@register()
def transform_link(wikitext, _):
    for link in wikitext.wikitext.filter_wikilinks():
        if re.match(":?(category|file|image|media|w):", str(link), flags=re.I):
            continue
        if str(link) != wikitext.item_name:
            continue
        wikitext.wikitext.replace(
            link,
            "{{{{item name|{0}}}}}".format(link.title)
        )

    return wikitext.wikitext


@register(Function.EXTENDED)
def translate_allclass_links(wikitext, context):
    if "all" in wikitext.class_links[0].lower():
        linkiso = context.strings.ALLCLASSESBOX.format(wikitext.language)
        wikitext.wikitext.replace(str(wikitext.class_links[0]), linkiso)

    return wikitext.wikitext


@register()
def translate_categories(wikitext, _):
    categories = re.findall("\[\[Category:.*?\]\]", str(wikitext.wikitext))
    for category in categories:
        category_new = category.replace("]]", "/{}]]".format(wikitext.language))
        wikitext.wikitext.replace(category, category_new)

    return wikitext.wikitext


@register()
def translate_headlines(wikitext, context):
    headlines = wikitext.wikitext.filter_headings()
    for heading in headlines:
        title = heading.title.strip()
        if title.lower() in context.strings.HEADINGS:
            trans_title = context.strings.HEADINGS[title.lower()]
            trans_heading = trans_title.center(len(trans_title)+2).join(
                ["="*heading.level]*2
            )
            wikitext.wikitext.replace(heading, trans_heading, recursive=False)

    return wikitext.wikitext


@register()
def translate_image_thumbnail(wikitext, context):
    result = re.search(
        "\| ?(The )?(Steam )?Workshop thumbnail (image )?for.*",
        str(wikitext.wikitext)
    )
    if result:
        wikitext.wikitext.replace(result.group(), context.strings.SENTENCE_THUMBNAIL)

    return wikitext.wikitext


@register()
def translate_item_flags(wikitext, context):
    infobox = wikitext.wikitext.filter_templates(matches="Item infobox")
    if not infobox:
        return wikitext.wikitext

    infobox = infobox[0]
    if infobox.has("item-flags"):
        flag = infobox.get("item-flags")
        flag.value = context.strings.ITEM_FLAGS[str(flag.value)]
    for param in infobox.params:
        if re.search("att-\d-negative", str(param.name)):
            value = str(param.value).strip()
            if value.lower() in context.strings.ATTRIBUTES:
                param.value = str(param.value).replace(
                    value,
                    context.strings.ATTRIBUTES[value.lower()]
                )
    return wikitext.wikitext


@register()
def translate_levels(wikitext, context):
    infobox = wikitext.wikitext.filter_templates(matches="Item infobox")
    if not infobox:
        return wikitext.wikitext

    item_kind = infobox[0].get("item-kind")
    value = item_kind.value.strip()
    if value in context.strings.ITEM_LEVELS:
        item_kind.value.replace(value, context.strings.ITEM_LEVELS[value])

    return wikitext.wikitext


@register()
def translate_set_contents(wikitext, context):
    result = re.search(
        "(The|This)( set)? (contains|includes)?( the)?( following)? items.*?:",
        str(wikitext.wikitext)
    )
    if result is None:
        return wikitext.wikitext

    match = result.group()
    wikitext.wikitext.replace(match, context.strings.SENTENCE_SET_INCLUDES, str(wikitext))

    part = str(wikitext.wikitext)[
           str(wikitext.wikitext).index(context.strings.SENTENCE_SET_INCLUDES):
           ]
    for link in re.finditer("\* ?\[\[.*?\]\]", part):
        link = link.group()
        wikitext.wikitext.replace(
            link,
            link.replace("[[", "{{item link|").replace("]]", "}}")
        )

    return wikitext.wikitext


@register()
def translate_update_history(wikitext, context):
    sentence = re.search(".*?[Aa]dded.*? to the game\.", str(wikitext.wikitext))
    if sentence:
        wikitext.wikitext.replace(sentence.group(), context.strings.ADDEDTOGAME)

    return wikitext.wikitext


# ==================
# Creating sentences
# ==================
@register(Function.EXTENDED)
def create_sentence_1_cw(wikitext, context):
    if wikitext.wikitext_type not in ['cosmetic', 'weapon']:
        return wikitext.wikitext

    sentence = re.findall(
        ".*?'''"+wikitext.item_name+"'''.*? for .*?\.",
        str(wikitext.wikitext)
    )[0]

    infobox = wikitext.wikitext.filter_templates(matches="Item infobox")[0]

    if wikitext.wikitext_type == "weapon":
        slot = infobox.get("slot").value.strip()
        typelink = getattr(
            context.strings,
            "SENTENCE_1_"+slot.upper()
        ).format(class_name=wikitext.class_links[0].title)
    else:
        typelink = getattr(
            context.strings,
            "SENTENCE_1_"+wikitext.wikitext_type.upper()
        )

    nounmarkerindefinite = getattr(
        context.strings,
        "NOUNMARKER_INDEFINITE_" + wikitext.wikitext_type.upper()
    )

    # I would rather use the "contributed-by" attribute in the item
    # infobox, but that stuff's only added after quite some time.
    if re.findall('.*?contributed.*?"*.*"*\.', wikitext.wikitext.strip_code()):
        workshop = getattr(
            context.strings,
            "SENTENCE_1_COMMUNITY_"+wikitext.wikitext_type.upper()
        )
    else:
        workshop = ""

    if infobox.has("promotional"):
        promotional = getattr(
            context.strings,
            "SENTENCE_1_PROMO_"+wikitext.wikitext_type.upper()
        )

        if wikitext.wikitext_type == "cosmetic" and wikitext.language == "de":
            typelink = ""
    else:
        promotional = ""

    class_list = create_class_list(wikitext.class_links, context.strings)
    sentence_trans = context.strings.SENTENCE_1_ALL.format(
        item_name=wikitext.item_name,
        noun_marker=nounmarkerindefinite,
        workshop_link=workshop,
        promotional=promotional,
        item_type=typelink,
        class_list=class_list
    )

    wikitext.wikitext.replace(sentence, sentence_trans + context.strings.ITEMLOOK)
    return wikitext.wikitext


@register(Function.EXTENDED)
def create_sentence_1_set(wikitext, context):
    if wikitext.wikitext_type != 'set':
        return wikitext.wikitext

    sentence1_1 = re.findall(
        ".*?'''" + wikitext.item_name + "'''.*? for .*?\.",
        str(wikitext)
    )[0]

    class_list = create_class_list(wikitext.class_links, context.strings)
    sentence1_1trans = context.strings.SENTENCE_1_ALL.format(
        item_name=wikitext.item_name,
        noun_marker=context.strings.NOUNMARKER_INDEFINITE_SET,
        workshop_link="",
        promotional="",
        item_type=context.strings.SENTENCE_1_SET,
        class_list=class_list
    )

    sentence1_2 = re.findall("\. It was .*?\.", str(wikitext.wikitext))[0][1:]
    patch = mw.parse(sentence1_2).filter_wikilinks()[0].title
    sentence1_2trans = context.strings.SENTENCE_SET.format(update=patch)

    wikitext.wikitext.replace(sentence1_1+sentence1_2, sentence1_1trans+sentence1_2trans)
    return wikitext.wikitext


@register(Function.EXTENDED)
def create_sentence_community(wikitext, context):
    sentence_community = re.findall(".*?contributed.*?Steam Workshop.*\.", str(wikitext))
    if sentence_community:
        link = re.findall("\[http.*?contribute.*?\]", sentence_community[0])
        if link:
            link = re.sub(" contribute.*?\]", "", link[0]).replace("[", "")
            link = context.strings.SENTENCE_COMMUNITY_LINK.format(link=link)

        try:
            name = re.findall('name.*?\".*?\"', sentence_community[0])[0][6:].replace('"', '')
            name = context.strings.SENTENCE_COMMUNITY_NAME.format(name=name)
        except (TypeError, IndexError):
            name = ""

        sct = context.strings.SENTENCE_COMMUNITY.format(
            item_name=wikitext.item_name,  # Legacy
            custom_name=name,
            workshop_link=link
        )
        wikitext.wikitext.replace(sentence_community[0], sct)
    return wikitext.wikitext


@register(Function.EXTENDED)
def create_sentence_promo(wikitext, context):
    sentencepromo = re.findall(".*?Genuine.*?quality.*?\.", str(wikitext))
    if sentencepromo:
        if "[[Steam]]" in sentencepromo:
            spt_s = context.strings.SENTENCE_PROMOTIONAL_STEAM
        else:
            spt_s = ""

        try:
            date = re.findall("before .*?,.*?20\d\d", sentencepromo[0])[0]
            date = date.replace("before ", "")

            day = re.findall("\w \d[\d|,]", date)[0][2:].replace(",", "")
            month = re.findall("[A-z].*?\d", date)[0][:-2]
            year = re.findall(", \d{4}", date)[0][2:]

            datefmt = "{{{{Date fmt|{}|{}|{}}}}}".format(month, day, year)
            spt_d = context.strings.SENTENCE_PROMOTIONAL_DATE.format(date=datefmt)
        except Exception:
            spt_d = ""
        try:
            game = re.findall("\[?\[?''.*?\]?\]?''", sentencepromo[0])[0]
            game = game.replace("''", "").replace("[", "").replace("]", "")
        except IndexError:
            raise UserWarning("No game. Canceling promo sentence translation.")

        spt = context.strings.SENTENCE_PROMOTIONAL.format(
            item_name=wikitext.item_name,  # Legacy
            game_name=game,
            steam=spt_s,
            date=spt_d
        )

        wikitext.wikitext.replace(sentencepromo[0], spt)

    return wikitext.wikitext


# ====================================
# Methods operating on the Stack cache
# ====================================

@register(Function.CACHE)
def translate_quotes(wikitext, context):
    for template in wikitext.wikitext.ifilter_templates(matches="Quotation"):
        if not template.has("sound"):
            continue
        file = template.get("sound")
        for cached_file, value in context.sound_file_cache.items():
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


@register(Function.CACHE)
def translate_description(wikitext, context):
    infobox = wikitext.wikitext.filter_templates(matches="Item infobox")
    if not infobox:
        return wikitext.wikitext

    infobox = infobox[0]
    if infobox.has("item-description"):
        description = infobox.get("item-description")
        description_text = re.sub('<br/?>', '\n', str(description.value).strip())
        key_english = [
            key
            for key, value in context.localization_file_cache[wikitext.language]["lang"]["Tokens"].items()
            if value == description_text
            ][0]
        value_german = context.localization_file_cache[wikitext.language]["lang"]["Tokens"][key_english[9:]]
        description.value = value_german.replace('\n', '<br>')
    return wikitext.wikitext


@register(Function.CACHE)
def translate_main_seealso(wikitext, context):
    # Oh please, don't look at this
    for template in wikitext.wikitext.ifilter_templates(
            matches=lambda x: str(x.name).lower() in ("see also", "main")
    ):
        arg_num = 1
        for template_link in template.params:
            if template_link.showkey:
                continue
            for link, value in context.wikilink_cache.items():
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


@register(Function.CACHE)
def translate_wikilinks(wikitext, context):
    for wikilink in clean_links(wikitext.wikilinks, wikitext.language, prefixes=context.prefixes):
        if not str(wikilink) in wikitext.wikitext:
            continue
        new_wikilink = Wikilink(wikilink.title+"/"+wikitext.language)
        for link, value in context.wikilink_cache.items():
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
        if str(wikilink) in wikitext.wikitext:
            # Yes we're doing it twice because mw doesn't catch everything in
            # the first round
            wikitext.wikitext.replace(str(wikilink), str(new_wikilink))
    return wikitext.wikitext


@register(Function.CACHE)
def translate_wikipedia_links(wikitext, context):
    for wikipedia_link in wikitext.wikipedia_links:
        if not str(wikipedia_link) in wikitext.wikitext:
            continue
        new_link = Wikilink(wikipedia_link.title, interwiki=wikipedia_link.interwiki)
        for link, value in context.wikipedia_links_cache.items():
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
