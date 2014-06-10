import pickle
from _tkinter import TclError
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk
import webbrowser

import core

CONFIG = "config.pkl"
URL_GITHUB = "https://github.com/TidB/WikiTranslator"
URL_WIKI = "http://wiki.teamfortress.com/wiki/User:TidB/WikiTranslator"

__version__ = "2014-06-07:1"


class GUI(object):

    def __init__(self, parent):
        print("Running")
        self.parent = parent
        self.open_config(0)
        self.filePath = "autosave.txt"
        self.presetsSaved = self.open_config(2)[::2]
        print("presetsSaved: ", self.presetsSaved)

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
                                         listvariable=tk.StringVar(value=core.GUI_METHODS),
                                         selectmode="multiple",
                                         exportselection=0)
        self.buttonSavePreset = ttk.Button(self.mainframe, text="Save preset",
                                           command=lambda: self.save_config(2,
                                                                            (self.comboboxPreset.get(),
                                                                             [core.GUI_METHODS[i] for i in self.listboxMethods.curselection()])))
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
        file = open(CONFIG, "wb")
        configFile = ["!", "de", []]
        pickle.dump(configFile, file)
        file.close()
        print("Recreating done")

    def end(self):
        if self.textOutput.get("1.0", "end") != "":
            self.save_file()
        self.parent.destroy()
        self.parent.quit()

    def help_dialog(self):
        fontHeadline = tk.font.Font(family='Helvetica', size=18, underline=1)
        fontLink = tk.font.Font(size=7)
        helpWindow = tk.Toplevel(self.parent)
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

    def import_category(self, category):
        wikiTextList = core.import_category(category)
        for text in wikiTextList:
            self.textInput.insert("end", text)

    def import_category_dialog(self):
        importWindow = tk.Toplevel(self.parent)
        importWindow.resizable(0, 0)
        importWindow.title("Import category")
        importFrame = ttk.Frame(importWindow, padding="3 3 12 12")

        labelDesc = tk.Label(importFrame, text="Enter a existing category")
        entryCategory = tk.Entry(importFrame, exportselection=0)
        buttonSubmit = tk.Button(importFrame,
                                 text="Enter",
                                 command=lambda: self.import_category(entryCategory.get()))

        importFrame.grid(column=0, row=0)
        labelDesc.grid(column=0, row=0)
        entryCategory.grid(column=0, row=1)
        buttonSubmit.grid(column=0, row=2)

    @staticmethod
    def open_config(index):
        with open(CONFIG, "rb") as f:
            l = pickle.load(f)[index]
            return l

        print("Reading configFile failed. Recreating...")
        config_exc()

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
        try:
            file = open(file_path, "rb")
        except:
            print("Invalid input file")
            return

        text = "!"
        while text != "":
            text = file.readline().decode()
            self.textInput.insert("end", text)
        file.close()

    def save_config(self, index, item):
        try:
            file = open(CONFIG, "rb")
            configFile = pickle.load(file)
        except:
            print("configFile couldn't be loaded. Creating...")
            self.config_exc()
            return

        try:
            if index in [0, 1]:
                configFile[index] = item
            elif index == 2:
                configFile[2].append(item[0])
                configFile[2].extend(item[1:])
        except IndexError:
            print("Invalid configFile. Recreating...")
            self.config_exc()
            return

        with open(CONFIG, "wb") as file:
            pickle.dump(configFile, file)
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
        settingWindow = tk.Toplevel(self.parent)
        settingWindow.resizable(0, 0)
        settingWindow.title("Settings")
        settingFrame = ttk.Frame(settingWindow, padding="3 3 12 12")

        labelSeparator = tk.Label(settingFrame, text="Standard separation character")
        entrySeparator = tk.Entry(settingFrame, text=separator, exportselection=0)
        entrySeparator.delete(0, "end")
        entrySeparator.insert(0, separator)
        buttonSeparator = tk.Button(settingFrame, text="Save",
                                    command=lambda: self.save_config(0, entrySeparator.get()))

        labelLanguage = tk.Label(settingFrame, text="Language (ISO code)")
        entryLanguage = tk.Entry(settingFrame, text=iso, exportselection=0)
        entryLanguage.delete(0, "end")
        entryLanguage.insert(0, iso)
        buttonLanguage = tk.Button(settingFrame, text="Save",
                                   command=lambda: self.save_config(1, entryLanguage.get()))

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

    def translate(self):
        print("Translation started")
        if self.textOutput.get("1.0", "end").strip() != "":
            overwrite = tk.messagebox.askyesno(
                message="There is text left in the output box! Do you want to overwrite the text?",
                icon='warning',
                title='Overwrite?'
            )
            if overwrite is False:
                return

        try:
            wikiText = self.textInput.selection_get()
        except TclError:
            wikiText = self.textInput.get("1.0", "end").strip()
        finally:
            wikiTextList = wikiText.split("\n!\n")
            wikiTextListTrans = []

        methods = [core.GUI_METHODS[int(i)] for i in self.listboxMethods.curselection()]
        iso = self.open_config(1)

        for wtr in wikiTextList:
            wt = core.Wikitext(wtr, iso, methods)
            wikiTextRaw = wt.translate()
            wikiTextListTrans.append(wikiTextRaw)

        wikiTextRaw = "\n!\n".join(wikiTextListTrans)

        self.textOutput.delete("1.0", "end")
        self.textOutput.insert("1.0", wikiTextRaw)

    def update_presets(self, _):
        l = self.open_config(2)
        presetName = l[self.comboboxPreset.current()*2]
        try:
            i = l.index(presetName)
        except ValueError:
            print("Invalid preset name")
            return
        self.listboxMethods.selection_clear(0, "end")
        for item in l[i+1]:
            self.listboxMethods.selection_set(core.GUI_METHODS.index(item))


def _main():
    root = tk.Tk()
    _gui = GUI(root)
    root.mainloop()

if __name__ == "__main__":
    _main()