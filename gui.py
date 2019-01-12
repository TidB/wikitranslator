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


def save_config(key, value):
    try:
        with open(CONFIG, 'r') as file:
            config_file = json.load(file)
    except (FileNotFoundError, TypeError):
        recreate_config()
        raise ValueError('config_file loading failed.')

    config_file[key] = value

    with open(CONFIG, 'w') as file:
        json.dump(config_file, file, indent=4)


class ControlPanel(ttk.Frame):
    def __init__(self, parent, translate_callback, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)

        self.translate_callback = translate_callback
        language = open_config('language')
        api_access = open_config('api_access')

        self.language_label = ttk.Label(self, text='Language: ')
        self.language = ttk.Combobox(
            self,
            width=7,
            state='readonly',
            values=list(core.LANGUAGES.keys())
        )
        self.language.set(language)
        self.language.bind(
            '<<ComboboxSelected>>', self.combobox_updated
        )

        self.var_api_access = tk.IntVar()
        self.checkbutton_api_access = ttk.Checkbutton(
            self, text='Use TF Wiki connection to improve translations',
            variable=self.var_api_access,
            command=lambda: save_config('api_access', self.var_api_access.get())
        )
        self.var_api_access.set(api_access)

        self.language_label.grid(column=0, row=0, sticky='nwes')
        self.language.grid(column=1, row=0, sticky='nwes', padx=(0, 15))
        self.checkbutton_api_access.grid(column=2, row=0, sticky='nwes')

    def combobox_updated(self, _):
        save_config('language', self.language.get())
        self.translate_callback()


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

        self.frame = ttk.Frame(self, padding='3 3 3 3', style='Wat.TFrame')

        self.text_input = tk.Text(
            self.frame,
            width=90, height=40,
            wrap='char',
            undo=True, maxundo=100
        )
        self.scrollbar_input = ttk.Scrollbar(
            self.frame, orient='vertical', command=self.text_input.yview
        )

        self.text_output = tk.Text(
            self.frame,
            width=90, height=40,
            wrap='char',
            state=tk.DISABLED
        )
        self.scrollbar_output = ttk.Scrollbar(
            self.frame, orient='vertical', command=self.text_output.yview
        )

        self.control_panel = ControlPanel(
            self.frame, self.translate, padding='3 3 3 3'
        )

        self.frame.grid(column=0, row=0, sticky='nwes')

        self.control_panel.grid(column=0, row=0, sticky='nwes')
        self.text_input.grid(column=0, row=1, sticky='nwes')
        self.scrollbar_input.grid(column=1, row=1, sticky='nwes')
        self.text_output.grid(column=2, row=1, sticky='nwes')
        self.scrollbar_output.grid(column=3, row=1, sticky='nwes')

        self.text_input['yscrollcommand'] = self.scrollbar_input.set
        self.text_output['yscrollcommand'] = self.scrollbar_output.set

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1, minsize=150)
        self.frame.columnconfigure(0, weight=2, minsize=400)
        self.frame.columnconfigure(2, weight=2, minsize=400)

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
            self.last_input = current_input
            self.translate()
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

    def translate(self):
        language = open_config('language')

        self.context.scan_all()
        self.context.retrieve_all()

        translated = self.context.translate(
            language, self.control_panel.var_api_access.get(), self.last_input
        )

        self.text_output.configure(state=tk.NORMAL)
        self.text_output.delete('1.0', 'end')
        self.text_output.insert('1.0', translated)
        self.text_output.configure(state=tk.DISABLED)


if __name__ == '__main__':
    root = GUI()
    root.mainloop()
