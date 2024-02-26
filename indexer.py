import os
import tkinter as tk
from tkinter import filedialog
from fuzzywuzzy import fuzz
import re


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
    index = create_index(directory_entry.get())
    listbox.delete(0, tk.END)
    for line in index:
        listbox.insert(tk.END ,line)

def handle_listbox_double_click(event):
    """Copies the selected item in the listbox to the clipboard."""
    selected_index = listbox.curselection()[0]  # Get the index of the selected item
    selected_item = listbox.get(selected_index)  # Get the text of the selected item
    # pyperclip.copy(selected_item)  # Copy the item to the clipboard
    os.startfile(selected_item)

# Create the GUI window.
window = tk.Tk()
window.title("File Indexer")

# Variable to hold the index content
index = []

# Create the GUI widgets.
directory_label = tk.Label(window, text="Directory:")
directory_var = tk.StringVar()
directory_entry = tk.Entry(window, width=50, text=directory_var)

browse_button = tk.Button(window, text="Browse...", command=lambda: directory_var.set(filedialog.askdirectory()))
index_button = tk.Button(window, text="Create Index", command=handle_create_index)
search_label = tk.Label(window, text="Search:")
search_entry = tk.Entry(window, width=50)
clear_button = tk.Button(window, text="Clear Search", command= handle_clear)
scrollbar = tk.Scrollbar(window)
listbox = tk.Listbox(window, width=100, yscrollcommand=scrollbar.set)
search_button = tk.Button(window, text="Search", command=handle_search)
scrollbar.config(command=listbox.yview)
# Add a binding for clicking on listbox items
listbox.bind('<Double-Button-1>', handle_listbox_double_click)
search_entry.bind('<Return>', handle_search_return)

# Create the GUI layout.
directory_label.grid(row=0, column=0)
directory_entry.grid(row=0, column=1)
browse_button.grid(row=0, column=2, pady=10)
index_button.grid(row=0, column=3, pady=10)
search_label.grid(row=1, column=0)
search_entry.grid(row=1, column=1)
search_button.grid(row=1, column=2, pady=10)
clear_button.grid(row=1, column=3, pady=10)

# **Key changes for resizing the listbox:**
listbox.grid(row=2, column=0, columnspan=4, sticky="nsew")  # Fill all available space
window.grid_rowconfigure(2, weight=1)  # Allow row 2 to expand
window.grid_columnconfigure(0, weight=1)  # Allow column 0 to expand

scrollbar.grid(row=2, column=4, sticky="ns")  # Align scrollbar with listbox

# Load the GUI
window.mainloop()

