import json
from _tkinter import TclError
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk
import webbrowser

import api
import core
from functions import METHODS

CONFIG = "config.json"
GUI_METHODS = tuple(sorted(name for name in METHODS))
AUTOSAVE = "autosave.txt"
URL_GITHUB = "https://github.com/TidB/wikitranslator"
URL_WIKI = "http://wiki.teamfortress.com/wiki/User:TidB/WikiTranslator"

TF2_WIKI_API = "https://wiki.teamfortress.com/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

STANDARD_CONFIG = {
    "separator": "!",
    "language": "de",
    "presets": {
        "Cosmetic/Weapon": [
            "translate_categories", "translate_allclass_links",
            "translate_headlines", "translate_image_thumbnail",
            "translate_item_flags", "translate_levels",
            "translate_update_history", "create_sentence_1_cw"
        ],
        "Set": [
            "add_displaytitle", "translate_categories",
            "translate_allclass_links", "translate_headlines",
            "translate_image_thumbnail", "translate_update_history",
            "create_sentence_1_set", "translate_set_contents"
        ],
    }
}


def open_config(key):
    try:
        file = open(CONFIG, "r")
        file.close()
    except FileNotFoundError:
        recreate_config()
    finally:
        with open(CONFIG, "r") as file:
            return json.load(file)[key]


def recreate_config():
    with open(CONFIG, "w") as file:
        json.dump(STANDARD_CONFIG, file, indent=4)


class GUI(tk.Tk):
    def __init__(self):
        self.stack = core.Stack(
            (),
            tf2_api=api.API(TF2_WIKI_API),
            wikipedia_api=api.API(WIKIPEDIA_API)
        )

        super().__init__()
        self.state("zoomed")

        self.presets = list(open_config("presets").keys())

        self.title("WikiTranslator v3")
        self.protocol('WM_DELETE_WINDOW', self.exit)

        self.mainframe = ttk.Frame(self, padding="3 3 3 3")

        self.option_add('*tearOff', 0)
        menubar = tk.Menu(self)
        self['menu'] = menubar
        menu_file = tk.Menu(menubar)
        menu_options = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_file, label='File')
        menu_file.add_command(label='Open…', command=self.open_file)
        menu_file.add_command(label='Save…', command=lambda: self.save_file(True))
        menubar.add_cascade(menu=menu_options, label='Options')
        menu_options.add_command(label='Settings…', command=self.settings_dialog)
        menu_options.add_command(label='Help', command=self.help_dialog)

        self.text_input = tk.Text(
                self.mainframe,
                width=90, height=40,
                wrap="char",
                maxundo=100,
                undo=True
        )
        self.scrollbar_input = ttk.Scrollbar(
            self.mainframe, orient="vertical", command=self.text_input.yview
        )

        self.text_output = tk.Text(
                self.mainframe,
                width=90, height=40,
                wrap="char",
                maxundo=100,
                undo=True
        )
        self.scrollbar_output = ttk.Scrollbar(
            self.mainframe, orient="vertical", command=self.text_output.yview
        )

        self.combobox_presets = ttk.Combobox(
            self.mainframe, values=self.presets, exportselection=0
        )

        self.methods = tk.Listbox(
                self.mainframe,
                listvariable=tk.StringVar(value=GUI_METHODS),
                selectmode="multiple",
                exportselection=0
        )

        self.save_preset = ttk.Button(
            self.mainframe, text="Save preset",
            command=lambda: self.save_config("presets", None)
        )
        self.clear = ttk.Button(
            self.mainframe, text="Clear selection",
            command=lambda: self.methods.selection_clear(0, "end")
        )
        self.translate = ttk.Button(
            self.mainframe, text="Translate", command=self.translate, width=30
        )

        self.mainframe.grid(column=0, row=0, sticky="nwes")
        self.text_input.grid(column=0, row=0, rowspan=5, sticky="nwes")
        self.scrollbar_input.grid(column=1, row=0, rowspan=5, sticky="nwes")
        self.text_output.grid(column=2, row=0, rowspan=5, sticky="nwes")
        self.scrollbar_output.grid(column=3, row=0, rowspan=5, sticky="nwes")
        self.combobox_presets.grid(column=4, row=0, columnspan=2, sticky="nwes")
        self.methods.grid(column=4, row=1, columnspan=2, sticky="nwes")
        self.save_preset.grid(column=4, row=3, sticky="nwes")
        self.clear.grid(column=5, row=3, sticky="nwes")
        self.translate.grid(column=4, row=4, columnspan=2, sticky="nwes")

        self.text_input['yscrollcommand'] = self.scrollbar_input.set
        self.text_output['yscrollcommand'] = self.scrollbar_output.set

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.mainframe.rowconfigure(1, weight=1, minsize=150)
        self.mainframe.columnconfigure(0, weight=2, minsize=200)
        self.mainframe.columnconfigure(2, weight=2, minsize=200)
        self.mainframe.columnconfigure(4, weight=1, minsize=130)
        self.mainframe.columnconfigure(5, weight=1, minsize=100)

        self.bind("<<ComboboxSelected>>", self.update_methods)
        self.bind("<Control-Z>", self.text_input.edit_undo)
        self.bind("<Control-Shift-Z>", self.text_input.edit_redo)

    def exit(self):
        if self.text_output.get("1.0", "end") != "":
            self.save_file()
        self.destroy()
        self.quit()

    def help_dialog(self):
        headline_font = tk.font.Font(family='Helvetica', size=18, underline=1)
        link_font = tk.font.Font(size=7)
        window = tk.Toplevel(self)
        window.resizable(0, 0)
        window.title("Help")
        frame = ttk.Frame(window, padding="3 3 3 3")

        headline = tk.Label(frame,
                            text="WikiTranslator v3",
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

    def open_file(self):
        if self.text_input.get("1.0", "end").strip() != "":
            overwrite = tk.messagebox.askyesno(
                message="Do you want to overwrite the text in the infobox?",
                icon='warning',
                title='Overwrite?'
            )
            if overwrite is False:
                return

        file_path = tk.filedialog.askopenfilename()
        if not file_path:
            return

        with open(file_path, "rb") as file:
            text = "!"
            while text != "":
                text = file.readline().decode()
                self.text_input.insert("end", text)

    def save_config(self, key, item):
        try:
            file = open(CONFIG, "r")
            config_file = json.load(file)
        except (FileNotFoundError, TypeError):
            recreate_config()
            raise ValueError("config_file loading failed.")

        if key in ["separator", "language"]:
            config_file[key] = item
        elif key == "presets":
            config_file["presets"][self.combobox_presets.get()] = [
                GUI_METHODS[i] for i in self.methods.curselection()
                ]

        with open(CONFIG, "w") as file:
            json.dump(config_file, file, indent=4)

    def save_file(self, selection=False, path=None):
        if path is None:
            path = AUTOSAVE
        if selection is True:
            path = tk.filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("text file", ".txt")]
            )
            if not path:
                return
        with open(path, "ab") as file:
            file.write(bytes(self.text_output.get("1.0", "end"), "utf-8"))

    def settings_dialog(self):
        separator = open_config("separator")
        language = open_config("language")
        setting_window = tk.Toplevel(self)
        setting_window.resizable(0, 0)
        setting_window.title("Settings")
        setting_frame = ttk.Frame(setting_window, padding="3 3 3 3")

        label_separator = tk.Label(setting_frame, text="Separation character")
        entry_separator = tk.Entry(setting_frame, text=separator, exportselection=0)
        entry_separator.delete(0, "end")
        entry_separator.insert(0, separator)
        button_separator = ttk.Button(
            setting_frame, text="Save",
            command=lambda: self.save_config("separator", entry_separator.get())
        )

        label_language = tk.Label(setting_frame, text="Language (ISO code)")
        entry_language = tk.Entry(setting_frame, text=language, exportselection=0)
        entry_language.delete(0, "end")
        entry_language.insert(0, language)
        button_language = ttk.Button(
            setting_frame, text="Save",
            command=lambda: self.save_config("language", entry_language.get())
        )

        button_clear_every_cache = ttk.Button(
            setting_frame, text="Clear all caches",
            command=self.stack.clear_all
        )
        button_clear_wikilink_cache = ttk.Button(
            setting_frame, text="Clear wikilink cache",
            command=self.stack.clear_wikilink_cache
        )
        button_clear_sound_file_cache = ttk.Button(
            setting_frame, text="Clear sound file cache",
            command=self.stack.clear_sound_file_cache
        )
        button_clear_localization_file_cache = ttk.Button(
            setting_frame, text="Clear localization file cache",
            command=self.stack.clear_localization_file_cache
        )

        button_close = ttk.Button(
            setting_frame, text="Close",
            command=lambda: setting_window.destroy()
        )

        setting_frame.grid(column=0, row=0, sticky="nwes")
        label_separator.grid(column=0, row=0, sticky="nwes")
        entry_separator.grid(column=0, row=1, sticky="nwes")
        button_separator.grid(column=1, row=1, sticky="nwes")
        label_language.grid(column=0, row=2, sticky="nwes")
        entry_language.grid(column=0, row=3, sticky="nwes")
        button_language.grid(column=1, row=3, sticky="nwes")

        button_clear_every_cache.grid(column=0, row=5, columnspan=2, sticky="nwes")
        button_clear_wikilink_cache.grid(column=0, row=6, columnspan=2, sticky="nwes")
        button_clear_sound_file_cache.grid(column=0, row=7, columnspan=2, sticky="nwes")
        button_clear_localization_file_cache.grid(column=0, row=8, columnspan=2, sticky="nwes")

        button_close.grid(column=0, row=9, columnspan=2)

    def translate(self):
        if self.text_output.get("1.0", "end").strip() != "":
            overwrite = tk.messagebox.askyesno(
                message="Do you want to overwrite the text in the output box?",
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

        separation = open_config("separator")
        language = open_config("language")
        methods = [
            METHODS[GUI_METHODS[int(i)]] for i in self.methods.curselection()
            ]

        self.stack.clear()
        self.stack.update({
            core.Wikitext(wikitext, language): methods
            for wikitext in wikitexts
        })
        self.stack.update_methods()

        self.stack.scan_all()
        self.stack.retrieve_all()
        self.stack.translate()

        wikitext_translated = "\n{}\n".format(separation).join(
                str(wikitext.wikitext) for wikitext in self.stack.keys()
        )

        self.text_output.delete("1.0", "end")
        self.text_output.insert("1.0", wikitext_translated)

    def update_methods(self, _):
        presets = open_config("presets")
        methods = presets[self.combobox_presets.get()]
        self.methods.selection_clear(0, "end")
        for method in methods:
            self.methods.selection_set(GUI_METHODS.index(method))


if __name__ == "__main__":
    root = GUI()
    root.mainloop()
