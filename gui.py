import pickle
import tkinter as tk
from tkinter import ttk
import webbrowser

import core

CONFIG = "config.pkl"
FILE_PATH = "autosave.txt"
URL_GITHUB = "https://github.com/TidB/WikiTranslator"
URL_WIKI = "http://wiki.teamfortress.com/wiki/User:TidB/WikiTranslator"
VERSION = "2014-06-07:1"

GUI_METHODS = ("add_displaytitle",
               "check_quote",
               "create_sentence_1_cw",
               "create_sentence_1_set",
               "create_sentence_community",
               "create_sentence_promo",
               "transform_decimal",
               "transform_link",
               "translate_categories",
               "translate_classlinks",
               "translate_headlines",
               "translate_item_flags",
               "translate_levels",
               "translate_main_seealso",
               "translate_set_contents",
               "translate_update_history",
               "translate_wikilink",
               "translate_wikipedia_link")


GUI_METHODS_NOARGS = ("check_quote",
                      "transform_decimal",
                      "transform_link",
                      "translate_categories",
                      "translate_headlines",
                      "translate_item_flags",
                      "translate_levels",
                      "translate_main_seealso",
                      "translate_set_contents",
                      "translate_wikilink",
                      "translate_wikipedia_link")

def config_exc():
    file = open(CONFIG, "wb")
    configFile = ["!", "de", []]
    pickle.dump(configFile, file)
    file.close()
    print("Recreating done")


def end():
    if textOutput.get("1.0", "end") != "":
        save_file()
    root.destroy()
    root.quit()


def help_dialog():
    fontHeadline = tk.font.Font(family='Helvetica', size=18, underline=1)
    fontLink = tk.font.Font(size=7)
    helpWindow = tk.Toplevel(root)
    helpWindow.resizable(0, 0)
    helpWindow.title("Help")
    helpFrame = ttk.Frame(helpWindow, padding="3 3 12 12")

    labelHeadline = tk.Label(helpFrame,
                          text="WikiTranslator v2",
                          font=fontHeadline)
    labelGithub = tk.Label(helpFrame, text="WikiTranslator on GitHub")
    labelGithubLink = tk.Label(helpFrame,
                            text="("+URL_GITHUB+")",
                            font=fontLink)
    labelTFWiki = tk.Label(helpFrame, text="WikiTranslator on the TF Wiki")
    labelTFWikiLink = tk.Label(helpFrame,
                            text="("+URL_WIKI+")",
                            font=fontLink)

    labelGithubLink.bind("<1>", lambda event: webbrowser.open(URL_GITHUB))
    labelTFWikiLink.bind("<1>", lambda event: webbrowser.open(URL_WIKI))

    helpFrame.grid(column=0, row=0)
    labelHeadline.grid(column=0, row=0)
    labelGithub.grid(column=0, row=1)
    labelTFWiki.grid(column=0, row=3)
    labelGithubLink.grid(column=0, row=2)
    labelTFWikiLink.grid(column=0, row=4)


def import_category(entryCategory):
    wikiTextList = core.import_category(entryCategory.get())
    for text in wikiTextList:
        textInput.insert("end", text)


def import_category_dialog():
    importWindow = tk.Toplevel(root)
    importWindow.resizable(0, 0)
    importWindow.title("Import category")
    importFrame = ttk.Frame(importWindow, padding="3 3 12 12")

    labelDesc = tk.Label(importFrame, text="Enter a existing category")
    entryCategory = tk.Entry(importFrame, exportselection=0)
    buttonSubmit = tk.Button(importFrame,
                             text="Enter",
                             command=lambda: import_category(entryCategory))
    
    importFrame.grid(column=0, row=0)
    labelDesc.grid(column=0, row=0)
    entryCategory.grid(column=0, row=1)
    buttonSubmit.grid(column=0, row=2)


def open_config(index):
        with open(CONFIG, "rb") as f:
            l = pickle.load(f)[index]
            return l

        print("Reading configFile failed. Recreating...")
        config_exc()


def open_file():
    if textInput.get("1.0", "end").strip() != "":
        overwrite = tk.messagebox.askyesno(
            message="There is text left in the input box! Do you want to overwrite the text?",
            icon='warning',
            title='Overwrite?'
            )
        if overwrite == False:
            return

    FILE_PATH = tk.filedialog.askopenfilename()
    try:
        file = open(FILE_PATH, "rb")
    except:
        print("Invalid input file")
        return

    text = "!"
    while text != "":
        text = file.readline().decode("utf-8")
        textInput.insert("end", text)
    file.close()


def save_config(index, item):
    print(item)
    try:
        file = open(CONFIG, "rb")
        configFile = pickle.load(file)
    except:
        print("configFile couldn't be loaded. Creating...")
        config_exc()
        return

    try:
        if index in [0,1]:
            configFile[index] = item
        elif index == 2:
            configFile[2].append(item[0])
            configFile[2].extend(item[1:])
    except IndexError:
        print("Invalid configFile. Recreating...")
        config_exc()
        return

    with open(CONFIG, "wb") as file:
        pickle.dump(configFile, file)
        print("Saved config")


def save_file(selection=False, path=FILE_PATH):
    if selection:
        path = tk.filedialog.asksaveasfilename(defaultextension=".txt",
                                               filetypes=[("text file", ".txt")])
    with open(path, "ab") as file:
        file.write(bytes(textOutput.get("1.0", "end"), "utf-8"))
        print("Autosaved")


def settings_dialog():
    separator = open_config(0)
    iso = open_config(1)
    settingWindow = tk.Toplevel(root)
    settingWindow.resizable(0, 0)
    settingWindow.title("Settings")
    settingFrame = ttk.Frame(settingWindow, padding="3 3 12 12")

    labelSeparator = tk.Label(settingFrame, text="Standard separation character")
    entrySeparator = tk.Entry(settingFrame, text=separator, exportselection=0)
    entrySeparator.delete(0, "end")
    entrySeparator.insert(0, separator)
    buttonSeparator = tk.Button(settingFrame, text="Save",
                                command=lambda: save_config(0, entrySeparator.get()))

    labelLanguage = tk.Label(settingFrame, text="Language (ISO code)")
    entryLanguage = tk.Entry(settingFrame, text=iso, exportselection=0)
    entryLanguage.delete(0, "end")
    entryLanguage.insert(0, iso)
    buttonLanguage = tk.Button(settingFrame, text="Save",
                               command=lambda: save_config(1, entryLanguage.get()))

    buttonClose = tk.Button(settingFrame, text="Close",
                            command=lambda: settingWindow.destroy())

    settingFrame.grid(column=0, row=0)
    labelSeparator.grid(column=0, row=0)
    entrySeparator.grid(column=0, row=1)
    buttonSeparator.grid(column=1, row=1)
    labelLanguage.grid(column=0, row=2)
    entryLanguage.grid(column=0, row=3)
    buttonLanguage.grid(column=1, row=3)
    buttonClose.grid(column=0, row=4, columnspan=2)


def translate():
    print("Translation started")
    if textOutput.get("1.0", "end").strip() != "":
        overwrite = messagebox.askyesno(
            message="There is text left in the output box! Do you want to overwrite the text?",
            icon='warning',
            title='Overwrite?'
            )
        if overwrite == False:
            return

    try:
        wikiText = textInput.selection_get()
        selection = True
    except:
        wikiText = textInput.get("1.0", "end").strip()
        selection = False
    finally:
        wikiTextList = wikiText.split("\n!\n")
        wikiTextListTrans = []

    for i in listboxMethods.curselection():
        print("methods[{}]: {}".format(i, GUI_METHODS[int(i)]))
    methods = [GUI_METHODS[int(i)] for i in listboxMethods.curselection()]
    iso = open_config(1)

    for wtr in wikiTextList:
        wt = core.Wikitext(wtr, iso, methods)
        wikiTextRaw = wt.translate()
        wikiTextListTrans.append(wikiTextRaw)

    wikiTextRaw = "\n!\n".join(wikiTextListTrans)

    textOutput.delete("1.0", "end")
    textOutput.insert("1.0", wikiTextRaw)


def update_presets(args):
    l = open_config(2)
    presetName = l[comboboxPreset.current()*2]
    try:
        i = l.index(presetName)
    except ValueError:
        print("Invalid preset name")
        return
    listboxMethods.selection_clear(0, "end")
    for item in l[i+1]:
        listboxMethods.selection_set(GUI_METHODS.index(item))

if __name__ == "__main__":
    print("Running")
    open_config(0)
    presetsSaved = open_config(2)[::2]
    print("presetsSaved: ", presetsSaved)

    root = tk.Tk()
    root.title("WikiTranslator v2 | {}".format(VERSION))
    root.protocol('WM_DELETE_WINDOW', end)

    mainframe = ttk.Frame(root, padding="3 3 12 12")

    root.option_add('*tearOff', 0)
    menubar = tk.Menu(root)
    root['menu'] = menubar
    menu_file = tk.Menu(menubar)
    menu_options = tk.Menu(menubar)
    menubar.add_cascade(menu=menu_file, label='File')
    menu_file.add_command(label='Open...', command=open_file)
    menu_file.add_command(label='Import category...', command=import_category_dialog)
    menu_file.add_command(label='Save...', command=lambda: save_file(True))
    menubar.add_cascade(menu=menu_options, label='Options')
    menu_options.add_command(label='Settings...', command=settings_dialog)
    menu_options.add_command(label='Help', command=help_dialog)

    textInput = tk.Text(mainframe, width=70, height=40, wrap="char", maxundo=100, undo=True)
    scrollInput = ttk.Scrollbar(mainframe, orient="vertical", command=textInput.yview)
    textOutput = tk.Text(mainframe, width=70, height=40, wrap="char", maxundo=100, undo=True)
    scrollOutput = ttk.Scrollbar(mainframe, orient="vertical", command=textOutput.yview)
    comboboxPreset = ttk.Combobox(mainframe, values=presetsSaved, exportselection=0)
    listboxMethods = tk.Listbox(mainframe,
                             listvariable=tk.StringVar(value=GUI_METHODS),
                             selectmode="multiple",
                             exportselection=0)
    buttonSavePreset = ttk.Button(mainframe, text="Save preset",
                                  command=lambda: save_config(2,
                                                              (comboboxPreset.get(),
                                                               [GUI_METHODS[i] for i in listboxMethods.curselection()])))
    buttonClear = ttk.Button(mainframe, text="Clear selection",
                             command=lambda: listboxMethods.selection_clear(0, "end"))
    buttonTranslate = ttk.Button(mainframe, text="Translate", command=translate, width=30)

    mainframe.grid(column=0, row=0, sticky=("n","w","e","s"))
    textInput.grid(column=0, row=1, rowspan=2, sticky=("n","e","s"))
    scrollInput.grid(column=1, row=1, rowspan=2, sticky=("n","w","s"))
    textOutput.grid(column=2, row=1, rowspan=2, sticky=("n","w","e","s"))
    scrollOutput.grid(column=3, row=1, rowspan=2, sticky=("n","w","s"))
    comboboxPreset.grid(column=4, row=0, columnspan=2)
    listboxMethods.grid(column=4, row=1, columnspan=2, rowspan=5, sticky=("n","w","e","s"))
    buttonSavePreset.grid(column=4, row=2)
    buttonClear.grid(column=5, row=2)
    buttonTranslate.grid(column=3, row=3, columnspan=2)

    textInput['yscrollcommand'] = scrollInput.set
    textOutput['yscrollcommand'] = scrollOutput.set

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    mainframe.columnconfigure(0, weight=2, minsize=200)
    mainframe.columnconfigure(2, weight=2, minsize=200)
    mainframe.columnconfigure(4, weight=1, minsize=130)
    mainframe.columnconfigure(5, weight=1, minsize=100)
    mainframe.rowconfigure(1, weight=1, minsize=150)

    root.bind("<<ComboboxSelected>>", update_presets)
    root.bind("<Control-Z>", textInput.edit_undo)
    root.bind("<Control-Shift-Z>", textInput.edit_redo)

    root.mainloop()
