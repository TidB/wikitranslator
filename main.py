import core

iso = "de"

print("WikiTranslator 1.0")
while True:
    print("Wikitext, enter 'X' to exit. End your input with '!' on its own line:")
    buffer = []
    while True:
        line = input()
        if line == "!":
            break
        buffer.append(line)
    text = "\n".join(buffer)

    if text.lower() == "lang":
        iso = input("Enter the language's ISO code: ").strip()
        continue

    elif text.lower() == "x":
        break

    if text is None:
        print("No input")
        continue

    wikiTextType = core.get_wikitext_type(text)
    if wikiTextType in ["cosmetic", "hat", "misc", "weapon"]:
        wikiTextTranslated = core.run_cw(text, iso)
    elif wikiTextType == "set":
        wikiTextTranslated = core.run_st(text, iso)
    elif wikiTextType == "none":
        print("No wikitext type detected.")
        continue

    print("##########################")
    print(wikiTextTranslated.strip())
    print("##########################")

print("Exit")
