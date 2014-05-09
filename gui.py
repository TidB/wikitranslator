import pickle
from tkinter import *
from tkinter import ttk

import core

CONFIG = "config.pkl"

def config_exc():
    file = open(CONFIG, "wb")
    configFile = ["!", "de", []]
    pickle.dump(configFile, file)
    file.close()
    print("Recreating done")


def help_dialog():
    pass


def open_config(index):
    try:
        f = open(CONFIG, "rb")
        l = pickle.load(f)[index]
        f.close()
        return l
    except:
        print("Reading configFile failed. Recreating...")
        config_exc()


def open_file():
    fileName = filedialog.askopenfilename()
    try:
        file = open(fileName, "r")
        text = file.readlines()
        file.close()
    except:
        print("Invalid input file")
        return

    if textInput.get("1.0", "end").strip() != "":
        overwrite = messagebox.askyesno(
            message="There is text left in the input box! Do you want to overwrite the text?",
            icon='warning',
            title='Overwrite?'
            )
        print(overwrite)
        if overwrite == False:
            return

    textInput.insert("1.0", text)


def save_changes():
    if textOutput.get("1.0", END) != "":
        save_file()
    root.destroy()
    root.quit()
    print("Quit")


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

    file = open(CONFIG, "wb")
    pickle.dump(configFile, file)
    file.close()
    print("Saved config")


def save_file():
    try:
        file = open("autosave.txt", "w")
    except:
        return
    file.write(textOutput.get("1.0", END))
    file.close()
    print("Autosaved")


def settings_dialog():
    separator = open_config(0)
    iso = open_config(1)
    settingWindow = Toplevel(root)
    settingWindow.resizable(FALSE, FALSE)
    settingFrame = ttk.Frame(settingWindow, padding="3 3 12 12")

    labelSeparator = Label(settingFrame, text="Standard separation character")
    entrySeparator = Entry(settingFrame, text=separator, exportselection=0)
    entrySeparator.delete(0, END)
    entrySeparator.insert(0, separator)
    buttonSeparator = Button(settingFrame, text="Save",
                             command=lambda: save_config(0, entrySeparator.get()))

    labelLanguage = Label(settingFrame, text="Language (ISO code)")
    entryLanguage = Entry(settingFrame, text=iso, exportselection=0)
    entryLanguage.delete(0, END)
    entryLanguage.insert(0, iso)
    buttonLanguage = Button(settingFrame, text="Save",
                            command=lambda: save_config(1, entryLanguage.get()))

    buttonClose = Button(settingFrame, text="Close",
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
    except:
        wikiText = textInput.get("1.0", "end").strip()
        wikiTextList = wikiText.split("\n!\n")

    #listboxMethods.curselection
    textOutput.delete("1.0", END)
    textOutput.insert("1.0", wikiText)


def update_presets(args):
    l = open_config(2)
    presetName = l[comboboxPreset.current()*2]
    try:
        i = l.index(presetName)
    except ValueError:
        print("Invalid preset name")
        return
    listboxMethods.selection_clear(0, END)
    for item in l[i+1]:
        listboxMethods.selection_set(core.GUI_METHODS.index(item))

if __name__ == "__main__":
    root = Tk()
    root.title("WikiTranslator v2")
    root.protocol('WM_DELETE_WINDOW', save_changes)

    mainframe = ttk.Frame(root, padding="3 3 12 12")

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
    comboboxPreset = ttk.Combobox(mainframe, values=presetsSaved)
    listboxMethods = Listbox(mainframe,
                             listvariable=StringVar(value=core.GUI_METHODS),
                             selectmode=MULTIPLE,
                             exportselection=0)
    progressbar = ttk.Progressbar(mainframe, orient=HORIZONTAL, length=300)
    buttonSavePreset = ttk.Button(mainframe, text="Save preset",
                                  command=lambda: save_config(2,
                                                              (comboboxPreset.get(),
                                                               [core.GUI_METHODS[i] for i in listboxMethods.curselection()])))
    buttonTranslate = ttk.Button(mainframe, text="Translate", command=translate, width=40)

    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
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

    root.bind("<Return>", update_presets)
    root.bind("<<ComboboxSelected>>", update_presets)
    root.bind("<Control-Z>", textInput.edit_undo)
    root.bind("<Control-Shift-Z>", textInput.edit_redo)

    open_config(0)
    presetsSaved = open_config(2)[::2]

    root.mainloop()
