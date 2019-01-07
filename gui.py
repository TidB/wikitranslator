import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import time

import api
import core
from functions import FUNCTIONS

CONFIG = 'config.json'
METHOD_NAMES = {
    'Add DISPLAYTITLE': 'add_displaytitle',
    '\'All classes\' links': 'translate_allclass_links',
    'Categories': 'translate_categories',
    'Headings': 'translate_headlines',
    'Workshop thumbnails descriptions': 'translate_image_thumbnail',
    'Item flags': 'translate_item_flags',
    'Levels': 'translate_levels',
    'Set contents': 'translate_set_contents',
    'Update history': 'translate_update_history',
    'First item sentence': 'create_sentence_1_cw',
    'First item set sentence': 'create_sentence_1_set',
    'Community-created sentence': 'create_sentence_community',
    'Promotional sentence': 'create_sentence_promo',
    'Quotes': 'translate_quotes',
    'Item description': 'translate_description',
    'Main/See also templates': 'translate_main_seealso',
    'Wikilinks': 'translate_wikilinks',
    'Wikipedia links': 'translate_wikipedia_links'
}
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


class CheckbuttonState(tk.IntVar):
    def __init__(self, method_name):
        super().__init__()
        self.method_name = method_name


class ControlPanel(ttk.Frame):
    def __init__(self, parent, translate_callback, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)

        language = open_config('language')
        self.presets = open_config('presets')
        method_count = len(METHOD_NAMES)

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

        self.separator = ttk.Separator(self, orient=tk.HORIZONTAL)

        self.label_presets = ttk.Label(self, text='Preset')
        self.combobox_presets = ttk.Combobox(
            self, values=list(self.presets.keys()),
            exportselection=0, state='readonly'
        )
        self.combobox_presets.current(0)

        self.button_add_preset = ttk.Button(self, text='New')

        self.method_selection = {}
        for i, (display_name, method_name) in enumerate(METHOD_NAMES.items()):
            checkbutton_var = CheckbuttonState(method_name)
            checkbutton = ttk.Checkbutton(
                self,
                text=display_name,
                variable=checkbutton_var,
                command=self.save_current_preset
            )
            checkbutton.grid(column=0, row=5+i, sticky='nwes')
            self.method_selection[method_name] = checkbutton_var

        self.translate = ttk.Button(
            self, text='Translate', command=translate_callback, width=30
        )

        self.label_language.grid(column=0, row=0, sticky='nwes')
        self.combobox_language.grid(column=0, row=1, sticky='nwes')
        self.separator.grid(column=0, row=2, columnspan=2, stick='nwes', pady=(10, 3))
        self.label_presets.grid(column=0, row=3, sticky='nwes')
        self.combobox_presets.grid(column=0, row=4, sticky='nwes')
        self.button_add_preset.grid(column=1, row=4, sticky='nwes')

        self.translate.grid(column=0, row=5+method_count, columnspan=2, sticky='nwes')

        self.combobox_presets.bind('<<ComboboxSelected>>', self.update_checkbuttons)
        self.update_checkbuttons()

    def update_checkbuttons(self, *_):
        current_preset = self.combobox_presets.get()
        for method_name, checkbutton in self.method_selection.items():
            if method_name in self.presets[current_preset]:
                checkbutton.set(1)
            else:
                checkbutton.set(0)

    def save_current_preset(self):
        self.save_config(
            'presets',
            [method_name
             for method_name, selected in self.method_selection.items()
             if selected.get()]
        )

    def save_config(self, key, value):
        try:
            file = open(CONFIG, 'r')
            config_file = json.load(file)
        except (FileNotFoundError, TypeError):
            recreate_config()
            raise ValueError('config_file loading failed.')

        if key == 'language':
            config_file[key] = value
        elif key == 'presets':
            config_file['presets'][self.combobox_presets.get()] = value

        with open(CONFIG, 'w') as file:
            json.dump(config_file, file, indent=4)


class GUI(tk.Tk):
    def __init__(self):
        self.context = core.Context(
            tf2_api=api.API(TF2_WIKI_API),
            wikipedia_api=api.API(WIKIPEDIA_API)
        )
        self.last_change = TEXT_MODIFIED_DELAY

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
            undo=True
        )
        self.scrollbar_output = ttk.Scrollbar(
            self.mainframe, orient='vertical', command=self.text_output.yview
        )

        self.control_panel = ControlPanel(self.mainframe, self.translate, padding='6 6 6 6')

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

        self.text_input.bind('<<Modified>>', self.input_changed)
        self.bind('<Control-Z>', self.text_input.edit_undo)
        self.bind('<Control-Shift-Z>', self.text_input.edit_redo)

    def exit(self):
        if self.text_output.get('1.0', 'end') != '':
            self.save_file()
        self.destroy()
        self.quit()

    def input_changed(self, *_):
        if self.text_input.edit_modified() and \
                (time.time() - self.last_change) > TEXT_MODIFIED_DELAY:
            self.last_change = time.time()
        self.text_input.edit_modified(False)

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
        if self.text_output.get('1.0', 'end').strip() != '':
            if tk.messagebox.askyesno(
                message='Do you want to overwrite the text in the output box?',
                icon='warning',
                title='Overwrite?'
            ) is False:
                return

        wikitext_input = self.text_input.get('1.0', 'end').strip()

        language = open_config('language')
        methods = [
            FUNCTIONS[method_name]
            for method_name, selected in self.control_panel.method_selection.items()
            if selected.get()
        ]

        self.context.scan_all()
        self.context.retrieve_all()

        translated = self.context.translate(wikitext_input, language, methods)

        self.text_output.delete('1.0', 'end')
        self.text_output.insert('1.0', translated)


if __name__ == '__main__':
    root = GUI()
    root.mainloop()
