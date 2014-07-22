import re


def fromstring(vdf):
    lines = re.split("(}|{)", vdf)

    vdf_dict = {}
    parents = []

    for line in iter(lines):

        line = re.sub("\[\$!?ENGLISH\]", "", line)
        line = line.strip()
        if not line.strip() or line[:1] == "//":
            continue

        if line not in ["{", "}"]:
            string_split = [re.sub("\\n|\\r*", "", part.strip()) for part in re.split('((?<!\\\\)".*?(?<!\\\\)")', line) if part.strip() != ""]
            keys, values = string_split[::2], string_split[1::2]
            if len(keys) != len(values):
                continue
            for i, keyb in enumerate(keys):
                vdf_access = "vdf_dict[" + \
                             "][".join(parents) + \
                             "][{}] = {}".format(keyb, values[i])
                exec(vdf_access)
        elif line == "{":
            parents.append(string_split[-1])
            if parents:
                vdf_access = "vdf_dict[" + \
                             "][".join(parents) + \
                             "] = {}"
                exec(vdf_access)
            else:
                raise SyntaxError("Unexpected open bracket")
        elif line == "}":
            if parents:
                parents.pop()
            else:
                raise ValueError("Unexpected close bracket")
        
    return vdf_dict