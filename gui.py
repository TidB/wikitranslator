from tkinter import *
from tkinter import ttk

import core

def translate():
    if textOutput.get("1.0", "end").strip() != "":
        overwrite = messagebox.askyesnocancel(
            message="There is text left in the output box! Do you want to overwrite the text?",
            icon='warning',
            title='Overwrite?'
            )
        if overwrite == "cancel":
            return

    try:
        wikiText = textInput.selection_get()
    except:
        wikiText = textInput.get("1.0", "end").strip()
        wikiTextList = wikiText.split("\n!\n")

    #listboxMethods.curselection
        
    textOutput.insert("1.0", wikiText)
    

def open_file():
    file = filedialog.askopenfilename()
    return file

def save_file():
    file = filedialog.asksaveasfilename()
    return file

def settings_dialog():
    separator = "!" # Pseudo
    iso = "de" # Pseudo
    settingWindow = Toplevel(root)
    settingWindow.resizable(FALSE, FALSE)
    settingFrame = ttk.Frame(settingWindow, padding="3 3 12 12")
    
    labelSeparator = Label(settingFrame, text="Standard separation character")
    entrySeparator = Entry(settingFrame, text=separator, exportselection=0)
    entrySeparator.insert(0, separator)
    buttonSeparator = Button(settingFrame, text="Save")

    labelLanguage = Label(settingFrame, text="Language (ISO code)")
    entryLanguage = Entry(settingFrame, text=iso, exportselection=0)
    entryLanguage.insert(0, iso)
    buttonLanguage = Button(settingFrame, text="Save")

    buttonClose = Button(settingFrame, text="Close", command=lambda: settingWindow.destroy())

    settingFrame.grid(column=0, row=0)
    labelSeparator.grid(column=0, row=0)
    entrySeparator.grid(column=0, row=1)
    buttonSeparator.grid(column=1, row=1)
    labelLanguage.grid(column=0, row=2)
    entryLanguage.grid(column=0, row=3)
    buttonLanguage.grid(column=1, row=3)
    buttonClose.grid(column=0, row=4, columnspan=2)

def help_dialog():
    pass

def save_preset():
    pass

root = Tk()
root.title("WikiTranslator v2")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

root.option_add('*tearOff', FALSE)
menubar = Menu(root)
root['menu'] = menubar
menu_file = Menu(menubar)
menu_options = Menu(menubar)
menubar.add_cascade(menu=menu_file, label='File')
menu_file.add_command(label='Open...', command=open_file)
menu_file.add_command(label='Save...', command=save_file)
menubar.add_cascade(menu=menu_options, label='Options')
menu_options.add_command(label='Settings...', command=settings_dialog)
menu_options.add_command(label='Help', command=help_dialog)

textInput = Text(mainframe, width=70, height=40, wrap="char", maxundo=100)
textOutput = Text(mainframe, width=70, height=40, wrap="char", maxundo=100)
presetsSaved = ("Preset cw", "Preset st", "Preset 1", "Preset 2", "Preset 3") # Pseudo
comboboxPreset = ttk.Combobox(mainframe, values=presetsSaved)
listboxMethods = Listbox(mainframe,
                         listvariable=StringVar(value=core.GUI_METHODS),
                         selectmode=MULTIPLE,
                         exportselection=0)
progressbar = ttk.Progressbar(mainframe, orient=HORIZONTAL, length=140)
buttonSavePreset = ttk.Button(mainframe, text="Save preset", command=save_preset)
buttonTranslate = ttk.Button(mainframe, text="Translate", command=translate, width=40)

textInput.grid(column=0, row=1, rowspan=2, sticky=(N,S,E,W))
textOutput.grid(column=1, row=1, rowspan=2, sticky=(N,S,E,W))
comboboxPreset.grid(column=2, row=0)
listboxMethods.grid(column=2, row=1, rowspan=5, sticky=(N,S,E,W))
progressbar.grid(column=0, row=3)
buttonSavePreset.grid(column=2, row=2)
buttonTranslate.grid(column=2, row=3)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
mainframe.columnconfigure(0, weight=2, minsize=200)
mainframe.columnconfigure(1, weight=2, minsize=200)
mainframe.columnconfigure(2, weight=1, minsize=130)
mainframe.rowconfigure(1, weight=1, minsize=150)

root.mainloop()
