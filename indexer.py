import os
import tkinter as tk
from tkinter import filedialog
from fuzzywuzzy import fuzz
import re
import pickle


def create_index(directory):
    """Creates a text-based index of all files in the given directory."""

    i = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            filepath = filepath.replace('/', os.sep)
            filepath = filepath.replace('\\', os.sep)
            i.append(filepath)
    global index
    index = i
    return i

def save_index(filename):
    global index
    global index_data
    index_data = {
        "index": index,
        "directory": directory,
        "search": search
    }
    with open(filename, 'wb') as f:
        pickle.dump(index_data, f)

def load_index(filename):
    global index, directory, search
    global index_data
    with open(filename, 'rb') as f:
        index_data = pickle.load(f)
        index = index_data["index"]
        directory = index_data["directory"]
        search = index_data["search"]
    listbox_populate()
    entry_populate()

def fuzzy_search(text, query, threshold=70):
    result = {}
    # Fuzzy search logic  
    match_score = max(
        fuzz.token_set_ratio(text, query),
        fuzz.ratio(text, query),
        fuzz.partial_ratio(text, query)
    )
    
    # Boost score if exact substring match
    if query in text: 
        match_score += 30
        
    if match_score >= threshold:
        result["match_score"] = match_score
        result["text"] = text
        return result
    else:
        return None

def preprocess_filepath(filepath):
    """Preprocesses a filepath for fuzzy matching."""

    # Case-insensitive
    filepath = filepath.lower()  
    # Normalize path separators
    filepath = filepath.replace(os.path.sep, "/")  
    # Remove punctuation and special characters except slashes
    filepath = re.sub(r"[^\w/]", "", filepath)  
    return filepath

# Functions to handle button clicks. 
def handle_search():
    results = []
    global search
    search = search_entry.get()

    for line in index:
        result = fuzzy_search(line, search_entry.get())
        if result:
            results.append(result)
            
    # Sort results by match score in descending order 
    results.sort(key=lambda x: x["match_score"], reverse=True) 

    listbox.delete(0, tk.END)
    for result in results:
        listbox.insert(tk.END, result["text"])

def handle_search_return(event):
    handle_search()

def handle_clear():
    listbox.delete(0, tk.END)
    for line in index:
        listbox.insert(tk.END, line)
    search_entry.delete(0, tk.END)

def handle_create_index():
    global index
    global directory
    directory = directory_entry.get()
    index = create_index(directory_entry.get())
    listbox_populate()
    entry_populate()

def listbox_populate():
    listbox.delete(0, tk.END)
    for line in index:
        listbox.insert(tk.END ,line)

def entry_populate():
    directory_entry.delete(0, tk.END)
    search_entry.delete(0, tk.END)
    directory_entry.insert(0, directory)

def handle_listbox_double_click(event):
    """Copies the selected item in the listbox to the clipboard."""
    selected_index = listbox.curselection()[0]  # Get the index of the selected item
    selected_item = listbox.get(selected_index)  # Get the text of the selected item
    # pyperclip.copy(selected_item)  # Copy the item to the clipboard
    os.startfile(selected_item)

def save_as():
    filename = filedialog.asksaveasfilename(defaultextension=".index",
                                              filetypes=[("Index Files", "*.index")])
    if filename:
        save_index(filename)

def load():
    filename = filedialog.askopenfilename(defaultextension=".index",
                                            filetypes=[("Index Files", "*.index")])
    if filename:
        load_index(filename)

# Create the GUI window.
window = tk.Tk()
window.title("File Indexer")
window.minsize(1600, 1000)
window.iconbitmap("indexer_icon.ico")

def on_closing():
    if index:
        save_index("quicksave.index")
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)

# Variables to hold the index content, last search, and path
index = []
search = ""
directory = ""

# Create the menu
menubar = tk.Menu(window)
window.config(menu=menubar)
file_menu = tk.Menu(menubar, tearoff=False)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Save As...", command=save_as)
file_menu.add_command(label="Load...", command=load)
file_menu.add_command(label="Quit", command=on_closing)


# Create the GUI widgets.
directory_label = tk.Label(window, text="Directory:")
directory_var = tk.StringVar()
directory_entry = tk.Entry(window, text=directory_var)

browse_button = tk.Button(window, text="Browse...", command=lambda: directory_var.set(filedialog.askdirectory()))
index_button = tk.Button(window, text="Create Index", command=handle_create_index)
search_label = tk.Label(window, text="Search:")
search_entry = tk.Entry(window)
clear_button = tk.Button(window, text="Clear Search", command= handle_clear)
scrollbar = tk.Scrollbar(window)
listbox = tk.Listbox(window, yscrollcommand=scrollbar.set)
search_button = tk.Button(window, text="Search", command=handle_search)
scrollbar.config(command=listbox.yview)
# Add a binding for clicking on listbox items
listbox.bind('<Double-Button-1>', handle_listbox_double_click)
search_entry.bind('<Return>', handle_search_return)

# Create the GUI layout.
window.grid_columnconfigure(0, weight=0)
window.grid_columnconfigure(1, weight=1)

directory_label.grid(row=0, column=0, sticky="w")
directory_entry.grid(row=0, column=1, sticky="ew")
browse_button.grid(row=0, column=2, pady=10)
index_button.grid(row=0, column=3, pady=10)
search_label.grid(row=1, column=0, sticky="w")
search_entry.grid(row=1, column=1, sticky="ew")
search_button.grid(row=1, column=2, pady=10)
clear_button.grid(row=1, column=3, pady=10)

# **Key changes for resizing the listbox:**
listbox.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)  # Fill all available space
window.grid_rowconfigure(2, weight=1)  # Allow row 2 to expand

scrollbar.grid(row=2, column=4, sticky="ns")  # Align scrollbar with listbox


#Loads the quicksave on start. If there is no quicksave, index will be empty. 
try:
    load_index("quicksave.index")
except(Exception):
    index = []

# Load the GUI
window.mainloop()

