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
               "translate_image_thumbnail",
               "translate_item_flags",
               "translate_levels",
               "translate_main_seealso",
               "translate_set_contents",
               "translate_update_history",
               "translate_wikilinks",
               "translate_wikipedia_links")

__version__ = "2014-07-12:1"


def open_config(index):
    try:
        file = open(CONFIG, "rb")
        file.close()
    except FileNotFoundError:
        recreate_config()
    finally:
        with open(CONFIG, "rb") as file:
            return pickle.load(file)[index]


def recreate_config():
    with open(CONFIG, "wb") as file:
        configfile = ["!", "de", {}]
        pickle.dump(configfile, file)


class GUI(object):
    def __init__(self, parent):
        self.parent = parent
        open_config(0)
        self.path = "autosave.txt"
        self.presets = list(open_config(2).keys())

        self.parent.title("WikiTranslator v2 | {}".format(__version__))
        self.parent.protocol('WM_DELETE_WINDOW', self.quit)

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

        self.text_input = tk.Text(self.mainframe, width=70, height=40, wrap="char", maxundo=100, undo=True)
        self.scrollbar_input = ttk.Scrollbar(self.mainframe, orient="vertical", command=self.text_input.yview)
        self.text_output = tk.Text(self.mainframe, width=70, height=40, wrap="char", maxundo=100, undo=True)
        self.scrollbar_output = ttk.Scrollbar(self.mainframe, orient="vertical", command=self.text_output.yview)
        self.combobox_presets = ttk.Combobox(self.mainframe, values=self.presets, exportselection=0)
        self.methods = tk.Listbox(self.mainframe,
                                  listvariable=tk.StringVar(value=GUI_METHODS),
                                  selectmode="multiple",
                                  exportselection=0)
        self.save_preset = ttk.Button(self.mainframe, text="Save preset",
                                      command=lambda: self.save_config(2, None))
        self.clear = ttk.Button(self.mainframe, text="Clear selection",
                                command=lambda: self.methods.selection_clear(0, "end"))
        self.translate = ttk.Button(self.mainframe, text="Translate", command=self.translate, width=30)

        self.mainframe.grid(column=0, row=0, sticky="nwes")
        self.text_input.grid(column=0, row=1, rowspan=2, sticky="nes")
        self.scrollbar_input.grid(column=1, row=1, rowspan=2, sticky="nws")
        self.text_output.grid(column=2, row=1, rowspan=2, sticky="nwes")
        self.scrollbar_output.grid(column=3, row=1, rowspan=2, sticky="nws")
        self.combobox_presets.grid(column=4, row=0, columnspan=2)
        self.methods.grid(column=4, row=1, columnspan=2, sticky="nwes")
        self.save_preset.grid(column=4, row=3)
        self.clear.grid(column=5, row=3)
        self.translate.grid(column=4, row=4, columnspan=2)

        self.text_input['yscrollcommand'] = self.scrollbar_input.set
        self.text_output['yscrollcommand'] = self.scrollbar_output.set

        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)
        self.mainframe.columnconfigure(0, weight=2, minsize=200)
        self.mainframe.columnconfigure(2, weight=2, minsize=200)
        self.mainframe.columnconfigure(4, weight=1, minsize=130)
        self.mainframe.columnconfigure(5, weight=1, minsize=100)
        self.mainframe.rowconfigure(1, weight=1, minsize=150)

        self.parent.bind("<<ComboboxSelected>>", self.update_methods)
        self.parent.bind("<Return>", self.update_methods)
        self.parent.bind("<Control-Z>", self.text_input.edit_undo)
        self.parent.bind("<Control-Shift-Z>", self.text_input.edit_redo)

    def quit(self):
        if self.text_output.get("1.0", "end") != "":
            self.save_file()
        self.parent.destroy()
        self.parent.quit()

    def help_dialog(self):
        headline_font = tk.font.Font(family='Helvetica', size=18, underline=1)
        link_font = tk.font.Font(size=7)
        window = tk.Toplevel(self.parent)
        window.resizable(0, 0)
        window.title("Help")
        frame = ttk.Frame(window, padding="3 3 12 12")

        headline = tk.Label(frame,
                            text="WikiTranslator v2",
                            font=headline_font)
        github = tk.Label(frame, text="WikiTranslator on GitHub")
        github_link = tk.Label(frame,
                               text="("+URL_GITHUB+")",
                               font=link_font)
        wiki_page = tk.Label(frame, text="WikiTranslator on the TF Wiki")
        wiki_page_link = tk.Label(frame,
                                  text="("+URL_WIKI+")",
                                  font=link_font)

        github_link.bind("<1>", lambda event: webbrowser.open(URL_GITHUB))
        wiki_page_link.bind("<1>", lambda event: webbrowser.open(URL_WIKI))

        frame.grid(column=0, row=0)
        headline.grid(column=0, row=0)
        github.grid(column=0, row=1)
        wiki_page.grid(column=0, row=3)
        github_link.grid(column=0, row=2)
        wiki_page_link.grid(column=0, row=4)

    def import_category(self, category):
        category = re.sub("[Cc]ategory:", "", category)
        wikitexts = core.import_category(category)
        for text in wikitexts:
            self.text_input.insert("end", text)

    def import_category_dialog(self):
        window = tk.Toplevel(self.parent)
        window.resizable(0, 0)
        window.title("Import category")
        frame = ttk.Frame(window, padding="3 3 12 12")

        instruction = tk.Label(frame, text="Enter a existing category")
        category = tk.Entry(frame, exportselection=0)
        submit = tk.Button(frame, text="Enter", command=lambda: self.import_category(category.get()))

        frame.grid(column=0, row=0)
        instruction.grid(column=0, row=0)
        category.grid(column=0, row=1)
        submit.grid(column=0, row=2)

    def open_file(self):
        if self.text_input.get("1.0", "end").strip() != "":
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
                self.text_input.insert("end", text)

    def save_config(self, index, item):
        try:
            file = open(CONFIG, "rb")
            config_file = pickle.load(file)
        except (FileNotFoundError, TypeError):
            recreate_config()
            raise ValueError("config_file loading failed.")

        try:
            if index in [0, 1]:
                config_file[index] = item
            elif index == 2:
                config_file[2][self.combobox_presets.get()] = [GUI_METHODS[i] for i in self.methods.curselection()]
        except IndexError:
            recreate_config()
            raise IndexError("Invalid config_file.")

        with open(CONFIG, "wb") as file:
            pickle.dump(config_file, file)

    def save_file(self, selection=False, path=None):
        if path is None:
            path = self.path
        if selection is True:
            path = tk.filedialog.asksaveasfilename(defaultextension=".txt",
                                                   filetypes=[("text file", ".txt")])
        with open(path, "ab") as file:
            file.write(bytes(self.text_output.get("1.0", "end"), "utf-8"))

    def settings_dialog(self):
        separator = open_config(0)
        iso = open_config(1)
        setting_window = tk.Toplevel(self.parent)
        setting_window.resizable(0, 0)
        setting_window.title("Settings")
        setting_frame = ttk.Frame(setting_window, padding="3 3 12 12")

        label_separator = tk.Label(setting_frame, text="Standard separation character")
        entry_separator = tk.Entry(setting_frame, text=separator, exportselection=0)
        entry_separator.delete(0, "end")
        entry_separator.insert(0, separator)
        button_separator = tk.Button(setting_frame, text="Save",
                                     command=lambda: self.save_config(0, entry_separator.get()))

        label_language = tk.Label(setting_frame, text="Language (ISO code)")
        entry_language = tk.Entry(setting_frame, text=iso, exportselection=0)
        entry_language.delete(0, "end")
        entry_language.insert(0, iso)
        button_language = tk.Button(setting_frame, text="Save",
                                    command=lambda: self.save_config(1, entry_language.get()))

        button_close = tk.Button(setting_frame, text="Close",
                                 command=lambda: setting_window.destroy())

        setting_frame.grid(column=0, row=0)
        label_separator.grid(column=0, row=0)
        entry_separator.grid(column=0, row=1)
        button_separator.grid(column=1, row=1)
        label_language.grid(column=0, row=2)
        entry_language.grid(column=0, row=3)
        button_language.grid(column=1, row=3)
        button_close.grid(column=0, row=4, columnspan=2)

    def translate(self):
        if self.text_output.get("1.0", "end").strip() != "":
            overwrite = tk.messagebox.askyesno(
                message="There is text left in the output box! Do you want to overwrite the text?",
                icon='warning',
                title='Overwrite?'
            )
            if overwrite is False:
                return

        wikitext_input = ""
        try:
            wikitext_input = self.text_input.selection_get()
        except TclError:
            wikitext_input = self.text_input.get("1.0", "end").strip()
        finally:
            wikitexts = wikitext_input.split("\n!\n")
            wikitexts_trans = []

        separation = open_config(0)
        iso = open_config(1)
        methods = [GUI_METHODS[int(i)] for i in self.methods.curselection()]

        for wikitext in wikitexts:
            wikitext = core.Wikitext(wikitext, iso, methods)
            wikitext_translated = wikitext.translate()
            wikitexts_trans.append(wikitext_translated)

        wikitext_translated = "\n{}\n".format(separation).join(wikitexts_trans)

        self.text_output.delete("1.0", "end")
        self.text_output.insert("1.0", wikitext_translated)

    def update_methods(self, _):
        presets = open_config(2)
        methods = presets[self.combobox_presets.get()]
        self.methods.selection_clear(0, "end")
        for method in methods:
            self.methods.selection_set(GUI_METHODS.index(method))


def _main():
    root = tk.Tk()
    _ = GUI(root)
    root.mainloop()

if __name__ == "__main__":
    _main()