import pickle
import re
from _tkinter import TclError
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk
import webbrowser

import core

CONFIG = "config.pkl"
URL_GITHUB = "https://github.com/TidB/WikiTranslator"
URL_WIKI = "http://wiki.teamfortress.com/wiki/User:TidB/WikiTranslator"

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

__version__ = "2014-07-03:2"


class GUI(object):

    def __init__(self, parent):
        self.parent = parent
        self.open_config(0)
        self.filePath = "autosave.txt"
        self.presetsSaved = self.open_config(2)[::2]

        self.parent.title("WikiTranslator v2 | {}".format(__version__))
        self.parent.protocol('WM_DELETE_WINDOW', self.end)

        self.mainframe = ttk.Frame(self.parent, padding="3 3 12 12")

        self.parent.option_add('*tearOff', 0)
        menubar = tk.Menu(self.parent)
        parent['menu'] = menubar
        menu_file = tk.Menu(menubar)
        menu_options = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_file, label='File')
        menu_file.add_command(label='Open...', command=self.open_file)
        menu_file.add_command(label='Import category...', command=self.import_category_dialog)
        menu_file.add_command(label='Save...', command=lambda: self.save_file(True))
        menubar.add_cascade(menu=menu_options, label='Options')
        menu_options.add_command(label='Settings...', command=self.settings_dialog)
        menu_options.add_command(label='Help', command=self.help_dialog)

        self.textInput = tk.Text(self.mainframe, width=70, height=40, wrap="char", maxundo=100, undo=True)
        self.scrollInput = ttk.Scrollbar(self.mainframe, orient="vertical", command=self.textInput.yview)
        self.textOutput = tk.Text(self.mainframe, width=70, height=40, wrap="char", maxundo=100, undo=True)
        self.scrollOutput = ttk.Scrollbar(self.mainframe, orient="vertical", command=self.textOutput.yview)
        self.comboboxPreset = ttk.Combobox(self.mainframe, values=self.presetsSaved, exportselection=0)
        self.listboxMethods = tk.Listbox(self.mainframe,
                                         listvariable=tk.StringVar(value=GUI_METHODS),
                                         selectmode="multiple",
                                         exportselection=0)
        self.buttonSavePreset = ttk.Button(self.mainframe, text="Save preset",
                                           command=lambda: self.save_config(2,
                                                                            (self.comboboxPreset.get(),
                                                                             [GUI_METHODS[i] for i in self.listboxMethods.curselection()])))
        self.buttonClear = ttk.Button(self.mainframe, text="Clear selection",
                                      command=lambda: self.listboxMethods.selection_clear(0, "end"))
        self.buttonTranslate = ttk.Button(self.mainframe, text="Translate", command=self.translate, width=30)

        self.mainframe.grid(column=0, row=0, sticky="nwes")
        self.textInput.grid(column=0, row=1, rowspan=2, sticky="nes")
        self.scrollInput.grid(column=1, row=1, rowspan=2, sticky="nws")
        self.textOutput.grid(column=2, row=1, rowspan=2, sticky="nwes")
        self.scrollOutput.grid(column=3, row=1, rowspan=2, sticky="nws")
        self.comboboxPreset.grid(column=4, row=0, columnspan=2)
        self.listboxMethods.grid(column=4, row=1, columnspan=2, sticky="nwes")
        self.buttonSavePreset.grid(column=4, row=3)
        self.buttonClear.grid(column=5, row=3)
        self.buttonTranslate.grid(column=4, row=4, columnspan=2)

        self.textInput['yscrollcommand'] = self.scrollInput.set
        self.textOutput['yscrollcommand'] = self.scrollOutput.set

        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)
        self.mainframe.columnconfigure(0, weight=2, minsize=200)
        self.mainframe.columnconfigure(2, weight=2, minsize=200)
        self.mainframe.columnconfigure(4, weight=1, minsize=130)
        self.mainframe.columnconfigure(5, weight=1, minsize=100)
        self.mainframe.rowconfigure(1, weight=1, minsize=150)

        self.parent.bind("<<ComboboxSelected>>", self.update_presets)
        self.parent.bind("<Control-Z>", self.textInput.edit_undo)
        self.parent.bind("<Control-Shift-Z>", self.textInput.edit_redo)

    @staticmethod
    def config_exc():
        with open(CONFIG, "wb") as file:
            configfile = ["!", "de", []]
            pickle.dump(configfile, file)

    def end(self):
        if self.textOutput.get("1.0", "end") != "":
            self.save_file()
        self.parent.destroy()
        self.parent.quit()

    def help_dialog(self):
        fontheadline = tk.font.Font(family='Helvetica', size=18, underline=1)
        fontlink = tk.font.Font(size=7)
        helpwindow = tk.Toplevel(self.parent)
        helpwindow.resizable(0, 0)
        helpwindow.title("Help")
        helpframe = ttk.Frame(helpwindow, padding="3 3 12 12")

        labelheadline = tk.Label(helpframe,
                                 text="WikiTranslator v2",
                                 font=fontheadline)
        labelgithub = tk.Label(helpframe, text="WikiTranslator on GitHub")
        labelgithublink = tk.Label(helpframe,
                                   text="("+URL_GITHUB+")",
                                   font=fontlink)
        labelwiki = tk.Label(helpframe, text="WikiTranslator on the TF Wiki")
        labelwikilink = tk.Label(helpframe,
                                 text="("+URL_WIKI+")",
                                 font=fontlink)

        labelgithublink.bind("<1>", lambda event: webbrowser.open(URL_GITHUB))
        labelwikilink.bind("<1>", lambda event: webbrowser.open(URL_WIKI))

        helpframe.grid(column=0, row=0)
        labelheadline.grid(column=0, row=0)
        labelgithub.grid(column=0, row=1)
        labelwiki.grid(column=0, row=3)
        labelgithublink.grid(column=0, row=2)
        labelwikilink.grid(column=0, row=4)

    def import_category(self, category):
        category = re.sub("[Cc]ategory:", "", category)
        wikitexts = core.import_category(category)
        for text in wikitexts:
            self.textInput.insert("end", text)

    def import_category_dialog(self):
        importwindow = tk.Toplevel(self.parent)
        importwindow.resizable(0, 0)
        importwindow.title("Import category")
        importframe = ttk.Frame(importwindow, padding="3 3 12 12")

        labeldesc = tk.Label(importframe, text="Enter a existing category")
        entrycategory = tk.Entry(importframe, exportselection=0)
        buttonsubmit = tk.Button(importframe,
                                 text="Enter",
                                 command=lambda: self.import_category(entrycategory.get()))

        importframe.grid(column=0, row=0)
        labeldesc.grid(column=0, row=0)
        entrycategory.grid(column=0, row=1)
        buttonsubmit.grid(column=0, row=2)

    @staticmethod
    def open_config(index):
        with open(CONFIG, "rb") as f:
            l = pickle.load(f)[index]
            return l

        config_exc()
        raise FileNotFoundError("Reading configFile failed. Recreating...")

    def open_file(self):
        if self.textInput.get("1.0", "end").strip() != "":
            overwrite = tk.messagebox.askyesno(
                message="There is text left in the input box! Do you want to overwrite the text?",
                icon='warning',
                title='Overwrite?'
            )
            if overwrite is False:
                return

        file_path = tk.filedialog.askopenfilename()
        with open(file_path, "rb") as file:
            text = "!"
            while text != "":
                text = file.readline().decode()
                self.textInput.insert("end", text)

    def save_config(self, index, item):
        try:
            file = open(CONFIG, "rb")
            configfile = pickle.load(file)
        except (FileNotFoundError, TypeError):
            self.config_exc()
            raise ValueError("configFile couldn't be loaded. Creating...")

        try:
            if index in [0, 1]:
                configfile[index] = item
            elif index == 2:
                configfile[2].append(item[0])
                configfile[2].extend(item[1:])
        except IndexError:
            self.config_exc()
            raise IndexError("Invalid configfile. Recreating...")

        with open(CONFIG, "wb") as file:
            pickle.dump(configfile, file)
            print("Saved config")

    def save_file(self, selection=False, path=None):
        if path is None:
            path = self.filePath
        if selection is True:
            path = tk.filedialog.asksaveasfilename(defaultextension=".txt",
                                                   filetypes=[("text file", ".txt")])
        with open(path, "ab") as file:
            file.write(bytes(self.textOutput.get("1.0", "end"), "utf-8"))
            print("Autosaved")

    def settings_dialog(self):
        separator = self.open_config(0)
        iso = self.open_config(1)
        settingwindow = tk.Toplevel(self.parent)
        settingwindow.resizable(0, 0)
        settingwindow.title("Settings")
        settingframe = ttk.Frame(settingwindow, padding="3 3 12 12")

        labelseparator = tk.Label(settingframe, text="Standard separation character")
        entryseparator = tk.Entry(settingframe, text=separator, exportselection=0)
        entryseparator.delete(0, "end")
        entryseparator.insert(0, separator)
        buttonseparator = tk.Button(settingframe, text="Save",
                                    command=lambda: self.save_config(0, entryseparator.get()))

        labellanguage = tk.Label(settingframe, text="Language (ISO code)")
        entrylanguage = tk.Entry(settingframe, text=iso, exportselection=0)
        entrylanguage.delete(0, "end")
        entrylanguage.insert(0, iso)
        buttonlanguage = tk.Button(settingframe, text="Save",
                                   command=lambda: self.save_config(1, entrylanguage.get()))

        buttonclose = tk.Button(settingframe, text="Close",
                                command=lambda: settingwindow.destroy())

        settingframe.grid(column=0, row=0)
        labelseparator.grid(column=0, row=0)
        entryseparator.grid(column=0, row=1)
        buttonseparator.grid(column=1, row=1)
        labellanguage.grid(column=0, row=2)
        entrylanguage.grid(column=0, row=3)
        buttonlanguage.grid(column=1, row=3)
        buttonclose.grid(column=0, row=4, columnspan=2)

    def translate(self):
        if self.textOutput.get("1.0", "end").strip() != "":
            overwrite = tk.messagebox.askyesno(
                message="There is text left in the output box! Do you want to overwrite the text?",
                icon='warning',
                title='Overwrite?'
            )
            if overwrite is False:
                return

        try:
            wikitext = self.textInput.selection_get()
        except TclError:
            wikitext = self.textInput.get("1.0", "end").strip()
        finally:
            wikitexts = wikitext.split("\n!\n")
            wikitextstrans = []

        methods = [GUI_METHODS[int(i)] for i in self.listboxMethods.curselection()]
        iso = self.open_config(1)

        for wtr in wikitexts:
            wt = core.Wikitext(wtr, iso, methods)
            wikitextraw = wt.translate()
            wikitextstrans.append(wikitextraw)

        wikitextraw = "\n!\n".join(wikitextstrans)

        self.textOutput.delete("1.0", "end")
        self.textOutput.insert("1.0", wikitextraw)

    def update_presets(self, _):
        l = self.open_config(2)
        presetname = l[self.comboboxPreset.current()*2]
        try:
            i = l.index(presetname)
        except ValueError:
            raise ValueError("Invalid preset name")

        self.listboxMethods.selection_clear(0, "end")
        for item in l[i+1]:
            self.listboxMethods.selection_set(GUI_METHODS.index(item))


def _main():
    root = tk.Tk()
    _ = GUI(root)
    root.mainloop()

if __name__ == "__main__":
    _main()