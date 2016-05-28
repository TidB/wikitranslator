from collections import defaultdict, OrderedDict
import re
import sys
import traceback

import mwparserfromhell as mw

from lang import *
import vdfparser

LANGUAGES = {
    "da": "Danish",
    "de": "German",
    "fi": "Finnish",
    "fr": "French",
    "it": "Italian",
    "ko": "Korean",
    "nl": "Dutch",
    "pt-br": "Brazilian",
    "ru": "Russian",
    "tr": "Turkish",
}

DISPLAYTITLE = "{{{{DISPLAYTITLE: {{{{item name|{name}}}}}}}}}\n"

CHUNK_SIZE = 50
DELAY = 0.5

METHODS = []  # All methods. Converted to the form {"name": (function, flags)}
              # at the end of this file.


def create_class_list(class_links, strings):
    if "all" in class_links[0].lower():
        return strings.SENTENCE_1_CLASSES_ALL
    else:
        classes = strings.SENTENCE_1_CLASSES_ONE.format(
            class_name=class_links[0],
            loc_class_name=strings.DICTIONARY_CLASSES[lf_ext(class_links[0])]
        )
        for class_ in class_links[1:-1]:
            classes = (
                classes +
                strings.SENTENCE_1_CLASSES_COMMA +
                strings.SENTENCE_1_CLASSES_ONE.format(
                    class_name=class_,
                    loc_class_name=strings.DICTIONARY_CLASSES[lf_ext(class_)]
                )
            )

        if len(class_links) > 1:
            classes = (
                classes +
                strings.SENTENCE_1_CLASSES_AND +
                strings.SENTENCE_1_CLASSES_ONE.format(
                    class_name=class_links[-1],
                    loc_class_name=strings.DICTIONARY_CLASSES[lf_ext(class_links[-1])]
                )
            )

        return classes


def clean_links(wikilinks, language, prefixes):
    """Removing links that are not in the main namespace, contain the
    chars "{}[]<>", are linking to sections on the same page or are
    already localized.

    Args:
      wikilinks (iterable[Wikilink]): Iterable of the wikilinks to clean.
      language (str): ISO code of the language.
      prefixes (iterable[str]): List of prefixes to exclude.

    Returns:
      set: Cleaned wikilinks."""
    wikilinks = {
        link for link in wikilinks
        if
        not re.match(  # In main namespace
            ":?(category|file|image|media|{}):".format("|".join(prefixes)),
            link.title, flags=re.I
        ) and
        not any(x in link.title for x in "{}[]<>") and  # Special chars
        not link.title.startswith("#") and  # In-page links
        not "/{}".format(language) in link.title  # Localized links
        }

    return wikilinks


def lf(link):
    return link.replace("[", "").replace("]", "")


def lf_ext(link):
    return re.sub("\|.*[^]]", "", lf(link))


def merge_jsons(jsons):
    """Merge JSONS returned from api.API.retrieve_pages.

    Args:
      jsons (list[dict]): Having the form:
    {"query":
    {
      "normalized": [
        {
          "from": "",
          "to": "",
        },
      ],

      "redirects": [
        {
          "from": "",
          "to": "",
        }
      ],

      "pages": {
        "id": {
          ...
        },
      }
    }
    }
    Output: the same, just merged and without the "query" wrapper.

    Does not remove duplicates in "normalized" and "redirects".
    """
    end_json = {
        "normalized": [],
        "redirects": [],
        "pages": {},
    }
    for json in jsons:
        json = json["query"]
        if "normalized" in json:
            end_json["normalized"].extend(json["normalized"])
        if "redirects" in json:
            end_json["redirects"].extend(json["redirects"])
        if "pages" in json:
            end_json["pages"].update(json["pages"])

    return end_json


class Wikilink:
    """A hashable object representing a wikilink.

    Attributes:
      title (str)
      anchor (str)
      label (str)"""
    def __init__(self, title, anchor="", label="", interwiki=""):
        """Args:
          title (str)
          anchor (str): Defaults to an empty string.
          label (str): Defaults to an empty string."""
        self.title = str(title)
        self.anchor = str(anchor)
        self.label = str(label)
        self.interwiki = str(interwiki)

    def __key(self):
        return self.title, self.anchor, self.label

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def __repr__(self):
        return "<Wikilink {}>".format(str(self))

    def __str__(self):
        """Returns:
          MediaWiki representation of the wikilink as a
        string."""
        return "[[{0}{1}{2}{3}]]".format(
            self.interwiki+":" if self.interwiki else "",
            self.title,
            "#"+self.anchor if self.anchor else "",
            "|"+self.label if self.label else ""
        )


class Stack(OrderedDict):
    """An collections.OrderedDict with additional attributes, used for storing
    multiple wikitexts.

    Atrributes:
        tf2_api (api.API or None): Used for API calls at the TF2 Wiki. Defaults
            to 'None'.
        wikipedia_api (api.API or None): Used for API calls of Wikipedia.
            Defaults to 'None'.
        wikilinks (dict[set]): Stores all wikilinks sorted by language.
    """
    def __init__(self, args, tf2_api=None, wikipedia_api=None):
        """Input:
          List of dictionaries of the form:
            key: wikitext (Wikitext)
            value: methods (list of functions)

          Creates collections.OrderedDict with:
            key: wikitext (Wikitext)
            value: methods (list of str)"""

        if args:
            self.update(args)
            self.update_methods()

        self.tf2_api = tf2_api
        self.wikipedia_api = wikipedia_api

        self.wikilinks = defaultdict(set)  # Format: {language: {link,},}
        self.wikipedia_links = defaultdict(set)  # Format: {language: {link,},}
        self.sound_files = defaultdict(set)  # Format: {language: {file,},}

        """localization_file_cache format:
        {
          "language": dict returned by vdfparser.fromstring,
        }"""
        self.localization_file_cache = dict()

        """wikilink_cache format:
        {
          "root title": {
            "anchors": {"anchor",},
            "displaytitle": {
              "language": "displayed title",
            },
            "aliases": {
              "title": "anchor if redirect 'tofragment' present",
            }
          }
        }"""
        self.wikilink_cache = dict()

        """wikipedia_links_cache format:
        {
          "root title": {
            "anchors": {"anchor",},
            "localized": {
              "language": "title" if existing else None,
            },
            "aliases": {
              "title": "anchor if redirect 'tofragment' present",
            }
          }
        }"""
        self.wikipedia_links_cache = dict()

        """
        sound_file_cache format:
        {
          "root file": {
            "localized": {
              "language": "file name" if existing else None,
            },
            "aliases": {"file name",}
          }
        }
        """
        self.sound_file_cache = dict()

        self.prefixes = []

        super().__init__()

        self.cache_methods = set()  # Methods in the texts requiring the cache
        self.file_languages = set()  # Languages needed for localization files

    def update_methods(self):
        for wikitext, methods in self.items():
            for method, flags in methods:
                if "cache" in flags:
                    self.cache_methods.add(method)
                if method == translate_description:
                    self.file_languages.add(wikitext.language)

    def translate(self):
        for wikitext, methods in self.items():
            wikitext.translate(methods, self)

    def scan_all(self):
        if translate_main_seealso in self.cache_methods or \
                        translate_wikilinks in self.cache_methods:
            self.wikilinks = defaultdict(set)
        if translate_quotes in self.cache_methods:
            self.get_used_sound_files()
        if translate_main_seealso in self.cache_methods:
            self.get_template_links()
        if translate_wikilinks in self.cache_methods:
            self.get_wikilinks()
        if translate_wikipedia_links in self.cache_methods:
            self.get_wikipedia_links()

        if translate_main_seealso in self.cache_methods or \
                translate_wikilinks in self.cache_methods:
            self.prefixes = self.get_prefixes()
            for language, wikilinks in self.wikilinks.items():
                self.wikilinks[language] = clean_links(wikilinks, language, prefixes=self.prefixes)

    def retrieve_all(self):
        if translate_quotes in self.cache_methods:
            self.update_english_sound_file_cache()
            self.update_localized_sound_file_cache()
        if translate_description in self.cache_methods:
            self.update_localization_file_cache()
        if translate_main_seealso in self.cache_methods or \
                translate_wikilinks in self.cache_methods:
            self.update_english_wikilink_cache()
            self.update_localized_wikilink_cache()
        if translate_wikipedia_links in self.cache_methods:
            self.update_wikipedia_links_cache()

    def get_prefixes(self):
        """Get the used prefixes for interwiki links which have to be ignored.
        Returns:
             list[str], each item being a prefix."""
        response = self.tf2_api.get(
            self.tf2_api.api_location,
            params={
                "action": "query",
                "meta": "siteinfo",
                "siprop": "interwikimap",
                "format": "json",
            }
        )

        prefixes = [i["prefix"] for i in response["query"]["interwikimap"]]
        return prefixes

    # --------
    # Scanning
    # --------

    def get_used_sound_files(self):
        self.sound_files = defaultdict(set)
        for text in self:
            text.get_used_sound_files()
            self.sound_files[text.language] |= text.sound_files

    def get_template_links(self):
        for text in self:
            text.get_template_links()
            self.wikilinks[text.language] |= text.template_links

    def get_wikilinks(self):
        for text in self:
            text.get_wikilinks()
            self.wikilinks[text.language] |= text.wikilinks

    def get_wikipedia_links(self):
        self.wikipedia_links = defaultdict(set)
        for text in self:
            text.get_wikipedia_links()
            self.wikipedia_links[text.language] |= text.wikipedia_links

    # ----------
    # Retrieving
    # ----------

    def update_english_wikilink_cache(self):
        """Retrieves all links from self.wikilinks.

        Links already cached are ignored."""
        all_wikilinks = {
            link.title for links in self.wikilinks.values() for link in links
        }

        cached_wikilinks = set()
        for link, value in self.wikilink_cache.items():
            cached_wikilinks.add(link)
            cached_wikilinks |= set(value["aliases"].keys())

        new_wikilinks = all_wikilinks - cached_wikilinks
        if not new_wikilinks:
            return

        items = merge_jsons(self.tf2_api.retrieve_pages(
            list(new_wikilinks),
            data={
                "action": "query",
                "format": "json",
                "redirects": "",
                "prop": "info",
                "inprop": "displaytitle",
            },
            chunk_size=CHUNK_SIZE,
            delay=DELAY,
        ))

        # Create entries for each page we're *actually* linking to (after
        # normalizing links and resolving redirects)
        for value in items["pages"].values():
            if value["title"] not in self.wikilink_cache and "missing" not in value:
                self.wikilink_cache[value["title"]] = {
                    "anchors": set(),
                    "aliases": {},
                    "displaytitle": {}
                }

        # Add resolved redirects to a page's aliases
        if "redirects" in items:
            for redirect in items["redirects"]:
                for page in self.wikilink_cache:
                    if redirect["to"] == page:
                        anchor = redirect["tofragment"] if "tofragment" in redirect else ""
                        self.wikilink_cache[page]["aliases"][redirect["from"]] = anchor
                        if anchor:
                            self.wikilink_cache[page]["anchors"].add(anchor)

        # Add normalized forms of the link or its aliases
        if "normalized" in items:
            for normal in items["normalized"]:
                for page, value in self.wikilink_cache.items():
                    if normal["to"] == page or normal["to"] in value["aliases"]:
                        self.wikilink_cache[page]["aliases"][normal["from"]] = ""

        # Add additional anchors
        for links in self.wikilinks.values():
            for link in links:
                if not link.anchor:
                    continue

                for existing_link, value in self.wikilink_cache.items():
                    if link.title == existing_link or link.title in value["aliases"]:
                        self.wikilink_cache[existing_link]["anchors"].add(link.anchor)

    def update_localized_wikilink_cache(self):
        """Retrieves the localized versions of links in self.wikilinks.

        Links already cached are ignored."""
        new_wikilinks = set()
        for language, links in self.wikilinks.items():
            for link in links:
                for existing_link, value in self.wikilink_cache.items():
                    if link.title == existing_link or link.title in value["aliases"]:
                        if language not in value["displaytitle"]:
                            new_wikilinks.add(existing_link+"/"+language)

        if not new_wikilinks:
            return

        items = merge_jsons(self.tf2_api.retrieve_pages(
            list(new_wikilinks),
            data={
                "action": "query",
                "format": "json",
                "redirects": "",
                "prop": "info",
                "inprop": "displaytitle",
            },
            chunk_size=CHUNK_SIZE,
            delay=DELAY,
        ))

        for value in items["pages"].values():
            english_title, language = value["title"].rsplit("/", maxsplit=1)
            if english_title not in self.wikilink_cache:  # Edge cases
                continue
            if "missing" in value:
                displaytitle = None  # Page doesn't exist
            else:
                displaytitle = value["displaytitle"]

            self.wikilink_cache[english_title]["displaytitle"][language] = displaytitle

    def update_english_sound_file_cache(self):
        all_files = {
            file
            for language, files in self.sound_files.items()
            for file in files
        }

        cached_files = set()
        for link, value in self.sound_file_cache.items():
            cached_files.add(link)
            cached_files |= value["aliases"]

        new_files = all_files - cached_files
        if not new_files:
            return

        new_files = {
            "File:{}.wav".format(re.sub("\.wav$", "", file))
            for file in new_files
        }

        items = merge_jsons(self.tf2_api.retrieve_pages(
            list(new_files),
            data={
                "action": "query",
                "format": "json",
                "redirects": "",
            },
            chunk_size=CHUNK_SIZE,
            delay=DELAY,
        ))

        # Create entries for each page we're *actually* linking to (after
        # normalizing links and resolving redirects)
        for value in items["pages"].values():
            file_name = value["title"][5:]  # Skip "File:"
            if file_name not in self.sound_file_cache and "missing" not in value:
                self.sound_file_cache[file_name] = {
                    "aliases": set(),
                    "localized": {}
                }

        # Add resolved redirects to a page's aliases
        if "redirects" in items:
            for redirect in items["redirects"]:
                for page in self.sound_file_cache:
                    if redirect["to"][5:] == page:
                        self.sound_file_cache[page]["aliases"].add(redirect["from"][5:])

        # Add normalized forms of the link or its aliases
        if "normalized" in items:
            for normal in items["normalized"]:
                for page, value in self.sound_file_cache.items():
                    if normal["to"][5:] == page or normal["to"][5:] in value["aliases"]:
                        self.sound_file_cache[page]["aliases"].add(normal["from"][5:])

    def update_localized_sound_file_cache(self):
        new_files = set()
        for language, files in self.sound_files.items():
            for file in files:
                for existing_file, value in self.sound_file_cache.items():
                    if file == existing_file or file in value["aliases"]:
                        if language not in value["localized"]:
                            file_name, extension = file.rsplit(".", maxsplit=1)
                            new_files.add("File:"+file_name+" "+language+"."+extension)

        if not new_files:
            return

        items = merge_jsons(self.tf2_api.retrieve_pages(
            list(new_files),
            data={
                "action": "query",
                "format": "json",
                "redirects": "",
            },
            chunk_size=CHUNK_SIZE,
            delay=DELAY,
        ))

        for value in items["pages"].values():
            raw_file_name, extension = value["title"][5:].rsplit(".", maxsplit=1)
            file_name, language = raw_file_name.rsplit(" ", maxsplit=1)
            english_file_name = file_name+"."+extension
            existing = None if "missing" in value else file_name+" "+language+"."+extension

            self.sound_file_cache[english_file_name]["localized"][language] = existing

    def update_localization_file_cache(self):
        cached_languages = set(self.localization_file_cache.keys())
        new_languages = self.file_languages - cached_languages

        if not new_languages:
            return

        pagetitles = [
            "File:Tf {}.txt".format(LANGUAGES[language].lower())
            for language in new_languages
        ]

        response = list(self.tf2_api.retrieve_pages(
                pagetitles,
                data={
                    "action": "query",
                    "format": "json",
                    "prop": "imageinfo",
                    "iiprop": "url",
                    "continue": ""
                },
                delay=0
        ))[0]

        for page, language in zip(
                response["query"]["pages"].values(),
                sorted(new_languages, key=lambda k: LANGUAGES[k])
        ):
            url = page["imageinfo"][0]["url"]
            response = self.tf2_api.session.get(url)
            response.encoding = "utf-8-sig"  # Fuck the BOM
            self.localization_file_cache[language] = vdfparser.fromstring(response.text)

    def update_wikipedia_links_cache(self):
        # Since the 'lllang' parameter of the MW API doesn't accept multiple
        # languages, it's just faster to divide the requests by language.
        for language, all_links in self.wikipedia_links.items():
            cached_links = set()
            for link, value in self.wikipedia_links_cache.items():
                if language in value["localized"] and value["localized"][language] is not None:
                    cached_links.add(link)
                    cached_links |= set(value["aliases"].keys())

            all_links = {
                link.title
                for links in self.wikipedia_links.values() for link in links
                }

            new_links = all_links - cached_links
            if not new_links:
                continue

            items = merge_jsons(self.wikipedia_api.retrieve_pages(
                list(new_links),
                data={
                    "action": "query",
                    "format": "json",
                    "redirects": "",
                    "prop": "langlinks",
                    "lllimit": "max",
                    "lllang": language,
                },
                chunk_size=CHUNK_SIZE,
                delay=DELAY,
            ))

            for value in items["pages"].values():
                if value["title"] not in self.wikipedia_links_cache and "missing" not in value:
                    self.wikipedia_links_cache[value["title"]] = {
                        "anchors": set(),
                        "aliases": {},
                        "localized": {}
                    }

                    if "langlinks" in value:
                        localized_title = value["langlinks"][0]["*"]
                    else:
                        localized_title = None
                    self.wikipedia_links_cache[value["title"]]["localized"][language] = localized_title

                    # Add resolved redirects to a page's aliases
                    if "redirects" in items:
                        for redirect in items["redirects"]:
                            for page in self.wikipedia_links_cache:
                                if redirect["to"] == page:
                                    anchor = redirect["tofragment"] if "tofragment" in redirect else ""
                                    self.wikipedia_links_cache[page]["aliases"][redirect["from"]] = anchor
                                    if anchor:
                                        self.wikipedia_links_cache[page]["anchors"].add(anchor)

                    # Add normalized forms of the link or its aliases
                    if "normalized" in items:
                        for normal in items["normalized"]:
                            for page, value in self.wikipedia_links_cache.items():
                                if normal["to"] == page or normal["to"] in value["aliases"]:
                                    self.wikipedia_links_cache[page]["aliases"][normal["from"]] = ""

                    # Add additional anchors
                    for links in self.wikipedia_links.values():
                        for link in links:
                            if not link.anchor:
                                continue

                            for existing_link, value in self.wikipedia_links_cache.items():
                                if link.title == existing_link or link.title in value["aliases"]:
                                    self.wikipedia_links_cache[existing_link]["anchors"].add(link.anchor)

    # --------------
    # Clearing cache
    # --------------

    def clear_all(self):
        self.clear_wikilink_cache()
        self.clear_localization_file_cache()
        self.clear_sound_file_cache()

    def clear_wikilink_cache(self):
        self.wikilink_cache = dict()

    def clear_localization_file_cache(self):
        self.localization_file_cache = dict()

    def clear_sound_file_cache(self):
        self.sound_file_cache = dict()


class Wikitext:
    """
    Attributes:

        language (str): ISO code of the language the wikitext should be trans-
            lated to.
        wikitext (mwparserfromhell.Wikicode): The actual wikitext.
        wikitext_type (str): Type of the item determined by the item infobox (if
            existing).
            Determined by method 'get_wikitext_type'.
        item_name (str): Name of the item in the wikitext (if existing).
            Determined by method 'get_item_name'.
        restricted (bool): Set to 'True' if the wikitext is restricted, meaning
            its type or the item name couldn't be determined, li-
            miting the available translation methods. If set to
            'False', no limitations apply. Information about
            whether a method can operate on restricted wikitexts
            or not can be found on the individual method docs.
        class_links: Set to 'None' if the wikitext is restricted.
            Set to "all" (str) if the item can be used by all classes.
            Set to list of 'mwparserfromhell.nodes.wikilink.Wikilink'
            if one or more classes can use the item.
            Determined by method 'get_using_classes'
        wikilinks (set[Wikilink]): List of all wikilinks in the wikitext.
            Defaults to an empty set.
            Determined by method 'get_wikilinks'.
        template_links (set[Wikilink]): List of all links found in {{Main}} and
            {{See also}} templates in the wikitext.
            Defaults to an empty set.
            Determined by method 'get_template_links'.
        wikipedia_links (set[Wikilink]): List of all Wikipedia links found in
            the wikitext. Defaults to an empty set.
            Determined by method 'get_wikipedia_links'.
        sound_files (set[str]): List of all sound files found in the wikitext.
            Defaults to an empty set.
            Determined by method 'get_used_sound_files'.
    """

    def __init__(self, wikitext, language):
        """Creates a Wikitext object.

        Args:
            wikitext: The wikitext. Type can be anything that can be parsed by
                'mwparserfromhell.utils.parse_anything'.
            language (str): ISO code of the language the wikitext should be
                translate to.
        """
        self.language = language
        self.wikitext = mw.parse(wikitext)

        if language.lower() not in LANGUAGES:
            print("Language '{}' not supported.".format(language), file=sys.stderr)

        self.wikitext_type = self.get_wikitext_type()
        self.item_name = self.get_item_name()
        if None in [self.wikitext_type, self.item_name]:
            self.restricted = True
            self.class_links = None
        else:
            self.restricted = False
            self.class_links = self.get_using_classes()

        self.wikilinks = set()
        self.template_links = set()
        self.wikipedia_links = set()
        self.sound_files = set()

    def __str__(self):
        """Returns:
             String representation of the stored wikitext."""
        return str(self.wikitext)

    # =========
    # Translate
    # =========

    def translate(self, methods, stack):
        for method, flags in methods:
            if self.restricted and "extended" in flags:
                continue
            print("trying method:", method.__name__)
            try:
                if "strings" in flags:
                    self.wikitext = method(self, globals()[self.language.lower()])
                elif "cache" in flags:
                    self.wikitext = method(self, stack)
                else:
                    self.wikitext = method(self)
            except Exception:
                print(traceback.format_exc(), file=sys.stderr)

        return self.wikitext

    # =======
    # Analyze
    # =======

    def get_item_name(self):
        itemname = self.wikitext.filter_tags(
            recursive=False,
            matches=re.compile("^'''.*?'''$"),
            flags=0
        )

        return str(itemname[0].contents) if itemname else None

    def get_using_classes(self):
        if self.wikitext_type in ("cosmetic", "weapon"):
            infobox = self.wikitext.filter_templates(matches="item infobox")[0]
            return [
                str(link.title)
                for link in infobox.get("used-by").value.filter_wikilinks()
                    ]
        elif self.wikitext_type == "set":
            infobox = self.wikitext.filter_templates(matches="item set infobox")[0]
            return [str(infobox.get("used-by").value).strip()]

    def get_wikitext_type(self):
        infobox = self.wikitext.filter_templates(matches="item infobox")
        if infobox:
            wikitext_type = infobox[0].get("type").value.strip()
            if wikitext_type.lower() in ["misc", "hat"]:
                wikitext_type = "cosmetic"
        elif self.wikitext.filter_templates(matches="item set infobox"):
            wikitext_type = "set"
        else:
            wikitext_type = None

        return wikitext_type

    # -------------
    # Used by Stack
    # -------------

    def get_used_sound_files(self):
        """Get the files mentioned in the "sound" parameter of Quotation
        templates."""
        self.sound_files = set()
        for template in self.wikitext.ifilter_templates(matches="Quotation"):
            if template.has("sound"):
                self.sound_files.add(str(template.get("sound").value))

    def get_template_links(self):
        self.template_links = set()
        for template in self.wikitext.ifilter_templates(
            matches=lambda x: str(x.name).lower() in ("see also", "main")
        ):
            for link in template.params:
                if not link.showkey:
                    self.template_links.add(Wikilink(link))

    def get_wikilinks(self):
        self.wikilinks = set()
        for wikilink in self.wikitext.ifilter_wikilinks():
            title = str(wikilink.title)
            label = wikilink.text if wikilink.text else ""
            # We don't need to check the links, clean_links() does that
            link, anchor = title.rsplit("#", maxsplit=1) if "#" in title else (title, "")
            self.wikilinks.add(Wikilink(
                link,
                anchor=anchor,
                label=label,
            ))

    def get_wikipedia_links(self):
        self.wikipedia_links = set()
        for wikipedia_link in self.wikitext.filter_wikilinks():
            title = str(wikipedia_link.title)
            if not re.match("^(w|wikipedia):", title, flags=re.I):
                continue
            label = wikipedia_link.text if wikipedia_link.text else ""
            link, anchor = title.rsplit("#", maxsplit=1) if "#" in title else (title, "")
            interwiki, link = link.split(":", maxsplit=1)
            self.wikipedia_links.add(Wikilink(
                link,
                anchor=anchor,
                label=label,
                interwiki=interwiki
            ))


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
            game = lf(game.replace("''", ""))
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


METHODS = {method.__name__: (method, flags) for method, flags in METHODS}
