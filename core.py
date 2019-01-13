from collections import defaultdict
import itertools
import sys
import traceback

from functions import *
from helpers import clean_links, Wikilink
from lang import *
import vdfparser


CHUNK_SIZE = 50
DELAY = 0.5


LANGUAGES = {
    'da': 'Danish',
    'de': 'German',
    'fi': 'Finnish',
    'fr': 'French',
    'it': 'Italian',
    'ko': 'Korean',
    'nl': 'Dutch',
    'pt-br': 'Brazilian',
    'ru': 'Russian',
    'tr': 'Turkish',
}

STANDARD_CONFIG = {
    'language': 'de',
    'api_access': True,
}


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


class Context:
    """An object for caching purposes.

    Atrributes:
        tf2_api (api.API or None): Used for API calls at the TF2 Wiki. Defaults
            to 'None'.
        wikipedia_api (api.API or None): Used for API calls of Wikipedia.
            Defaults to 'None'.
        wikilinks (dict[set]): Stores all wikilinks sorted by language.
    """
    def __init__(self, tf2_api=None, wikipedia_api=None):
        """Input:
          List of dictionaries of the form:
            key: wikitext (Wikitext)
            value: methods (list of functions)

          Creates collections.OrderedDict with:
            key: wikitext (Wikitext)
            value: methods (list of str)"""

        self.tf2_api = tf2_api
        self.wikipedia_api = wikipedia_api

        self.strings = None

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

        self.cache_methods = set()  # Methods in the texts requiring the cache
        self.file_languages = set()  # Languages needed for localization files

    def translate(self, language, api_access, *texts):
        if api_access and (self.tf2_api is None or self.wikipedia_api is None):
            raise ValueError('API access invalid without API locations')

        self.strings = globals()[language.lower()]

        wikitexts = []
        for text in texts:
            wikitext = Wikitext(text, language)
            if api_access:
                if wikitext.uses_description():
                    self.file_languages.add(language)

                self.wikilinks[language] |= wikitext.wikilinks
                self.wikipedia_links[language] |= wikitext.wikipedia_links
                self.sound_files[language] |= wikitext.sound_files
            wikitexts.append(wikitext)

        self.scan_all()
        self.retrieve_all()

        return [str(wikitext.translate(self, api_access)) for wikitext in wikitexts]

    def scan_all(self):
        if self.wikilinks:
            self.prefixes = self.get_prefixes()
            for language, wikilinks in self.wikilinks.items():
                self.wikilinks[language] = clean_links(wikilinks, language, prefixes=self.prefixes)

    def retrieve_all(self):
        self.update_english_sound_file_cache()
        self.update_localized_sound_file_cache()
        self.update_localization_file_cache()
        self.update_english_wikilink_cache()
        self.update_localized_wikilink_cache()
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
                translated to.
        """
        if language.lower() not in LANGUAGES:
            print("Language '{}' not supported.".format(language), file=sys.stderr)

        self.language = language
        self.wikitext = mw.parse(wikitext)

        self.wikitext_type = self.get_wikitext_type()
        self.item_name = self.get_item_name()
        if None in [self.wikitext_type, self.item_name]:
            self.restricted = True
            self.class_links = None
        else:
            self.restricted = False
            self.class_links = self.get_using_classes()

        self.wikilinks = self.get_wikilinks() | self.get_template_links()
        self.wikipedia_links = self.get_wikipedia_links()
        self.sound_files = self.get_sound_files()

    def __str__(self):
        """Returns:
             String representation of the stored wikitext."""
        return str(self.wikitext)

    def translate(self, context, api_access):
        for function, flags in FUNCTIONS.values():
            if self.restricted and Function.EXTENDED in flags:
                continue
            elif not api_access and Function.CACHE in flags:
                continue
            try:
                self.wikitext = function(self, context)
            except Exception:
                print(traceback.format_exc(), file=sys.stderr)

        return self.wikitext

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
            wikitext_type = infobox[0].get("type").value.strip().lower()
            if wikitext_type in ["misc", "hat"]:  # Old cosmetics system
                wikitext_type = "cosmetic"
        elif self.wikitext.filter_templates(matches="item set infobox"):
            wikitext_type = "set"
        else:
            wikitext_type = None

        return wikitext_type

    def get_sound_files(self):
        """Get the files mentioned in the "sound" parameter of Quotation
        templates."""
        sound_files = set()
        for template in self.wikitext.ifilter_templates(matches="Quotation"):
            if template.has("sound"):
                sound_files.add(str(template.get("sound").value))
        return sound_files

    def get_template_links(self):
        template_links = set()
        for template in self.wikitext.ifilter_templates(
            matches=lambda x: str(x.name).lower() in ("see also", "main")
        ):
            for link in template.params:
                if not link.showkey:
                    template_links.add(Wikilink(link))
        return template_links

    def get_wikilinks(self):
        wikilinks = set()

        # mwparserfromhell doesn't parse inside tags so we do that manually
        tag_wikilinks = [
            wikilink
            for tag in self.wikitext.ifilter_tags()
            if tag.contents is not None
            for wikilink in mw.parse(str(tag.contents)).ifilter_wikilinks()
        ]

        for wikilink in itertools.chain(self.wikitext.ifilter_wikilinks(), tag_wikilinks):
            title = str(wikilink.title)
            label = wikilink.text if wikilink.text else ""
            # We don't need to check the links, clean_links() does that
            link, anchor = title.rsplit("#", maxsplit=1) if "#" in title else (title, "")
            wikilinks.add(Wikilink(
                link,
                anchor=anchor,
                label=label,
            ))
        return wikilinks

    def get_wikipedia_links(self):
        wikipedia_links = set()
        for wikipedia_link in self.wikitext.filter_wikilinks():
            title = str(wikipedia_link.title)
            if not re.match("^(w|wikipedia):", title, flags=re.I):
                continue
            label = wikipedia_link.text if wikipedia_link.text else ""
            link, anchor = title.rsplit("#", maxsplit=1) if "#" in title else (title, "")
            interwiki, link = link.split(":", maxsplit=1)
            wikipedia_links.add(Wikilink(
                link,
                anchor=anchor,
                label=label,
                interwiki=interwiki
            ))
        return wikipedia_links

    def uses_description(self):
        infobox = self.wikitext.filter_templates(matches="Item infobox")
        if not infobox:
            return False

        return infobox[0].has("item-description")
