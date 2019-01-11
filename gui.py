import json
import tkinter as tk
from tkinter import filedialog, ttk

import api
import core

CONFIG = 'config.json'
AUTOSAVE = 'autosave.txt'
URL_GITHUB = 'https://github.com/TidB/wikitranslator'
URL_WIKI = 'http://wiki.teamfortress.com/wiki/User:TidB/WikiTranslator'

TF2_WIKI_API = 'https://wiki.teamfortress.com/w/api.php'
WIKIPEDIA_API = 'https://en.wikipedia.org/w/api.php'

TEXT_MODIFIED_DELAY = 1


def open_config(key):
    try:
        file = open(CONFIG, 'r')
        file.close()
    except FileNotFoundError:
        recreate_config()
    finally:
        with open(CONFIG, 'r') as file:
            return json.load(file)[key]


def recreate_config():
    with open(CONFIG, 'w') as file:
        json.dump(core.STANDARD_CONFIG, file, indent=4)


class ControlPanel(ttk.Frame):
    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)

        language = open_config('language')

        self.label_language = ttk.Label(self, text='Language')
        self.combobox_language = ttk.Combobox(
            self,
            state='readonly',
            values=list(core.LANGUAGES.keys())
        )
        self.combobox_language.set(language)
        self.combobox_language.bind(
            '<<ComboboxSelected>>',
            lambda _: self.save_config('language', self.combobox_language.get())
        )

        self.label_language.grid(column=0, row=0, sticky='nwes')
        self.combobox_language.grid(column=0, row=1, sticky='nwes')

    def save_config(self, key, value):
        try:
            file = open(CONFIG, 'r')
            config_file = json.load(file)
        except (FileNotFoundError, TypeError):
            recreate_config()
            raise ValueError('config_file loading failed.')

        if key == 'language':
            config_file[key] = value

        with open(CONFIG, 'w') as file:
            json.dump(config_file, file, indent=4)


class GUI(tk.Tk):
    def __init__(self):
        self.context = core.Context(
            tf2_api=api.API(TF2_WIKI_API),
            wikipedia_api=api.API(WIKIPEDIA_API)
        )
        self.last_input = ''

        super().__init__()

        self.title('wikitranslator')
        self.protocol('WM_DELETE_WINDOW', self.exit)

        self.mainframe = ttk.Frame(self, padding='3 3 3 3')

        self.text_input = tk.Text(
            self.mainframe,
            width=90, height=40,
            wrap='char',
            maxundo=100,
            undo=True
        )
        self.scrollbar_input = ttk.Scrollbar(
            self.mainframe, orient='vertical', command=self.text_input.yview
        )

        self.text_output = tk.Text(
            self.mainframe,
            width=90, height=40,
            wrap='char',
            maxundo=100,
            undo=True,
            state=tk.DISABLED
        )
        self.scrollbar_output = ttk.Scrollbar(
            self.mainframe, orient='vertical', command=self.text_output.yview
        )

        self.control_panel = ControlPanel(self.mainframe, padding='6 6 6 6')

        self.mainframe.grid(column=0, row=0, sticky='nwes')

        self.text_input.grid(column=0, row=0, sticky='nwes')
        self.scrollbar_input.grid(column=1, row=0, sticky='nwes')
        self.control_panel.grid(column=2, row=0, sticky='nwes')
        self.text_output.grid(column=3, row=0, sticky='nwes')
        self.scrollbar_output.grid(column=4, row=0, sticky='nwes')

        self.text_input['yscrollcommand'] = self.scrollbar_input.set
        self.text_output['yscrollcommand'] = self.scrollbar_output.set

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1, minsize=150)
        self.mainframe.columnconfigure(0, weight=2, minsize=200)
        self.mainframe.columnconfigure(2, minsize=250)
        self.mainframe.columnconfigure(3, weight=2, minsize=130)

        self.bind('<Control-Z>', self.text_input.edit_undo)
        self.bind('<Control-Shift-Z>', self.text_input.edit_redo)

        self.after(1000, self.input_tick)

    def exit(self):
        if self.text_output.get('1.0', 'end') != '':
            self.save_file()
        self.destroy()
        self.quit()

    def input_tick(self):
        current_input = self.text_input.get('1.0', 'end').strip()
        if current_input != self.last_input:
            self.translate(current_input)
        self.after(1500, self.input_tick)

    def save_file(self, selection=False, path=None):
        if path is None:
            path = AUTOSAVE
        if selection is True:
            path = tk.filedialog.asksaveasfilename(
                defaultextension='.txt',
                filetypes=[('text file', '.txt')]
            )
            if not path:
                return
        with open(path, 'ab') as file:
            file.write(bytes(self.text_output.get('1.0', 'end'), 'utf-8'))

    def translate(self, wikitext_input):
        language = open_config('language')

        self.context.scan_all()
        self.context.retrieve_all()

        translated = self.context.translate(language, wikitext_input)

        self.text_output.configure(state=tk.NORMAL)
        self.text_output.delete('1.0', 'end')
        self.text_output.insert('1.0', translated)
        self.text_output.configure(state=tk.DISABLED)


if __name__ == '__main__':
    root = GUI()
    root.mainloop()
