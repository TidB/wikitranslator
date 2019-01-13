from sys import stderr
from time import sleep
from traceback import format_exc

import requests

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

            return response
        except Exception:
            print(format_exc(), file=stderr)


class API:
    def __init__(self, api_location):
        self.api_location = api_location
        self.session = requests.session()

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
