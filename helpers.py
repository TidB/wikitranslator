import re


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


def chunker(seq, size):
    """Splits a given sequence 'seq' into chunks of size 'size'.

    Args:
      seq (list): Sequence to be split up
      size (int): Size of the chunks

    Returns:
      Generator
    """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


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


def show_progress(current_value, max_value, text, end=False):
    percentage = int((current_value/max_value)*100)
    progress = "\r[{0}{1}] {2} | {3}% | {4}{5}".format(
        "=" * (percentage//5),
        " " * (20-percentage//5),
        "{0}/{1}".format(current_value, max_value),
        percentage,
        text,
        "\n" if end else ""
    )
    print(progress, end="")
