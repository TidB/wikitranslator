from collections import OrderedDict
from sys import stderr
from time import sleep
from traceback import format_exc

import mwparserfromhell

from helpers import chunker, show_progress


def safe_request(request, api_location, **kwargs):
    """Encapsulates a request like request.post or request.get into a retry
    block. Requires the request to be a object in the JSON form. Returns
    the JSON object."""
    retry = True
    while retry:
        try:
            response = request(api_location, **kwargs).json()
            if "error" in response:
                print("Code:", response["error"]["code"], "\n",
                      "Info:", response["error"]["info"], file=stderr)
            else:
                retry = False
        except Exception:
            print(format_exc(), file=stderr)

    return response


class API:
    def __init__(self, api_location, session=None, language=None):
        self.api_location = api_location

        self.language = language

        if session is None:
            import requests
            self.session = requests.session()
        else:
            self.session = session

    def get(self, api_location, params):
        return safe_request(self.session.get, api_location, params=params)

    def post(self, api_location, data):
        return safe_request(self.session.post, api_location, data=data)

    def retrieve_pages(self, pagetitles, data, chunk_size=50, delay=0.5):
        for i, chunk in enumerate(chunker(pagetitles, chunk_size)):
            show_progress(
                i * chunk_size + len(chunk), len(pagetitles),
                "Retrieving chunk '{}'-'{}'".format(chunk[0], chunk[-1])
            )
            data["titles"] = "|".join(chunk)

            response = self.post(self.api_location, data=data)

            yield response
            sleep(delay)

        show_progress(len(pagetitles), len(pagetitles),
                      "Retrieved chunks.", True)

    @staticmethod
    def format_pages(all_pages):
        """
        Returns an OrderedDict of the form

        {
            title: {
                "title": string,
                "content": mwparserfromhell.Wikicode object,
                "categories": [string, string, ...],
                "displaytitle": string,
            },
            ...
        }
        """
        formatted_pages = OrderedDict()
        for i, page in enumerate(sorted(all_pages, key=lambda k: k["title"])):
            title = page["title"]
            show_progress(i+1, len(all_pages), "Formatting "+title)
            content = mwparserfromhell.parse(page["revisions"][0]["*"])
            categories = [category["title"] for category in page["categories"]]
            displaytitle = page["displaytitle"]
            formatted_pages[title] = {
                "title": title,
                "content": content,
                "categories": categories,
                "displaytitle": displaytitle
            }
        show_progress(len(all_pages), len(all_pages), "Formatted all.", True)

        return formatted_pages
