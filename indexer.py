import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from fuzzywuzzy import fuzz
from datetime import datetime
import re
import pickle
import subprocess
import pyperclip

def save_index(filename):
    """
    Save the current index data to a file.

    Args:
        filename (str): The path to the file where the index data will be saved.
    """
    global index, index_data, timestamp
    
    index_data = {
        "index": index,
        "directory": directory,
        "search": search,
        "timestamp": timestamp  # Add the timestamp to the index_data dictionary
    }
    
    with open(filename, 'wb') as f:
        pickle.dump(index_data, f)

def load_index(filename):
    """
    Load index data from a file.

    Args:
        filename (str): The path to the file containing the index data.

    This function attempts to load the index data from the specified file.
    If the file is not found or has an unexpected format, it initializes
    empty data structures and updates the GUI accordingly.
    """
    global index, directory, search, timestamp
    global index_data
    try:
        with open(filename, 'rb') as f:
            index_data = pickle.load(f)
            index = index_data["index"]
            directory = index_data["directory"]
            search = index_data["search"]
            timestamp = index_data.get("timestamp", "N/A")
    except FileNotFoundError:
        print("No existing index found. A new index will be created when you add directories and create an index.")
        index = []
        directory = []
        search = ""
        timestamp = ""
    except (pickle.UnpicklingError, KeyError):
        tk.messagebox.showerror("Error", "The index file is corrupted or in an unexpected format. A new index will be created.")
        index = []
        directory = []
        search = ""
        timestamp = ""
    except Exception as e:
        tk.messagebox.showerror("Error", f"An unexpected error occurred while loading the index: {str(e)}")
        index = []
        directory = []
        search = ""
        timestamp = ""
    
    listbox_populate()
    directory_listbox_populate()
    update_info_bar()

def fuzzy_search(text, query, threshold=70):
    """
    Perform a fuzzy search on the given text.

    Args:
        text (str): The text to search in.
        query (str): The search query.
        threshold (int, optional): The minimum match score to consider. Defaults to 70.

    Returns:
        dict or None: A dictionary containing the match score and text if a match is found,
                      or None if no match is found.
    """
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
    """
    Handle the search action when the search button is clicked.

    This function retrieves the search query from the entry field,
    performs a fuzzy search on the index, and updates the listbox
    with the search results.
    """
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
    """
    Clear the search results and reset the listbox to show all indexed files.

    This function is called when the clear button is clicked.
    """
    listbox.delete(0, tk.END)
    for line in index:
        listbox.insert(tk.END, line)
    search_entry.delete(0, tk.END)

def update_info_bar():
    """
    Update the information bar with the current index statistics.

    This function updates the displayed information about the index date
    and the total number of files in the index.
    """
    info_bar.config(text=f"Index Date: {timestamp}  Total files: {len(index)}")

def handle_add_directory():
    """
    Handle the action of adding a new directory to the index.

    This function opens a directory selection dialog and adds the
    selected directory to the list of directories to be indexed.
    """
    new_directory = filedialog.askdirectory()
    directory_listbox.insert(tk.END, new_directory)
    global directory
    directory = directory_listbox.get(0,directory_listbox.size())

def handle_create_index():    
    """
    Handle the action of creating the index.

    This function initiates the indexing process for all added directories,
    updates the GUI with a loading popup, and refreshes the listbox and
    info bar once the indexing is complete.
    """
    global index, directory, timestamp, total_files_indexed
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")    
    directory = directory_listbox.get(0, tk.END)    
    
    # Disable the "Create Index" button
    index_button.config(state=tk.DISABLED)

    # Create a loading popup  
    loading_popup = tk.Toplevel(window)  
    loading_popup.title("Loading...")  
    loading_popup.geometry("300x200")  # Set the size of the popup
    
    # Make sure the popup has well-contrasted colors in both light and dark mode
    loading_popup.configure(background="#f0f0f0")  # Light gray background for the entire popup
    
    # Create a StringVar to hold the count of files indexed  
    count_var = tk.StringVar()  
    count_var.set("Files indexed: 0")  
    
    # Create a label to display the count with explicit foreground and background colors
    count_label = tk.Label(
        loading_popup, 
        textvariable=count_var, 
        background="#f0f0f0",  # Light gray background
        foreground="#000000",  # Black text
        font=("Arial", 12)     # Larger, more readable font
    )
    count_label.pack(pady=40)  # Add more padding for visibility
    
    # Add a progress message
    progress_label = tk.Label(
        loading_popup,
        text="Please wait while your files are being indexed...",
        background="#f0f0f0",
        foreground="#000000",
        font=("Arial", 10)
    )
    progress_label.pack(pady=10)
    
    # Clear the old index
    index = []  
    total_files_indexed = 0  

    # Start indexing each directory
    for d in directory:  
        index.extend(create_index([d], count_var, loading_popup))  
    
    # Close the loading popup  
    loading_popup.destroy()  
    listbox_populate()  
    update_info_bar() 

    # Re-enable the "Create Index" button
    index_button.config(state=tk.NORMAL)
    
def create_index(directories, count_var, loading_popup):  
    """Creates a text-based index of all files in the given directories."""  
    global total_files_indexed
    index_list = []  
    
    for directory in directories:        
        for root, dirs, files in os.walk(directory):  
            for filename in files:  
                filepath = os.path.join(root, filename).replace('/', os.sep).replace('\\', os.sep)  
                index_list.append(filepath)  
                total_files_indexed += 1  
                count_var.set(f"Files Indexed: {total_files_indexed}")        
                loading_popup.update_idletasks()  
    
    return index_list

def listbox_populate():
    listbox.delete(0, tk.END)
    for line in index:
        listbox.insert(tk.END, line)

def directory_listbox_populate():
    directory_listbox.delete(0, tk.END)
    for d in directory:
        directory_listbox.insert(tk.END, d)

def entry_populate():
    directory_listbox.delete(0, tk.END)
    search_entry.delete(0, tk.END)
    for d in directory:
        directory_listbox.insert(tk.END, d)

def handle_listbox_double_click(event):
    """Opens the selected file in its default program."""
    selected_index = listbox.curselection()
    if selected_index:
        selected_item = listbox.get(selected_index[0])
        if sys.platform == "win32":
            os.startfile(selected_item)
        elif sys.platform == "darwin":  # macOS
            subprocess.call(["open", selected_item])
        else:  # Linux
            subprocess.call(["xdg-open", selected_item])

def delete_directory():
    selected_index = directory_listbox.curselection()
    if selected_index:
        directory_listbox.delete(selected_index)

def show_directory_menu(event):
    selected_index = directory_listbox.nearest(event.y)
    directory_listbox.selection_clear(0, tk.END)
    directory_listbox.selection_set(selected_index)
    directory_listbox.activate(selected_index)
    # Use Button-2 for Mac, Button-3 for Windows/Linux
    directory_menu.post(event.x_root, event.y_root)

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

def show_listbox_menu(event):
    """Shows the right-click menu for listbox items."""
    selected_index = listbox.nearest(event.y)
    listbox.selection_clear(0, tk.END)
    listbox.selection_set(selected_index)
    listbox.activate(selected_index)
    listbox_menu.post(event.x_root, event.y_root)

def get_quicksave_path():
    # Use user's home directory instead of sys.executable
    user_home = os.path.expanduser("~")
    app_dir = os.path.join(user_home, ".fileindexer")
    os.makedirs(app_dir, exist_ok=True)  # Create dir if doesn't exist
    return os.path.join(app_dir, "quicksave.index")

def open_file():
    """Opens the selected file in its default program."""
    selected_index = listbox.curselection()
    if selected_index:
        selected_item = listbox.get(selected_index[0])
        if sys.platform == "win32":
            os.startfile(selected_item)
        elif sys.platform == "darwin":  # macOS
            subprocess.call(["open", selected_item])
        else:  # Linux
            subprocess.call(["xdg-open", selected_item])

def open_parent_directory():
    """Opens the parent directory of the selected file."""
    selected_index = listbox.curselection()
    if selected_index:
        selected_item = listbox.get(selected_index[0])
        parent_dir = os.path.dirname(selected_item)
        if sys.platform == "win32":
            subprocess.Popen(f'explorer "{parent_dir}"')
        elif sys.platform == "darwin":  # macOS
            subprocess.call(["open", parent_dir])
        else:  # Linux
            subprocess.call(["xdg-open", parent_dir])

def copy_file_path():
    """Copies the full path of the selected file to the clipboard."""
    selected_index = listbox.curselection()
    if selected_index:
        selected_item = listbox.get(selected_index[0])
        pyperclip.copy(selected_item)

def copy_parent_directory_path():
    """Copies the path of the parent directory of the selected file to the clipboard."""
    selected_index = listbox.curselection()
    if selected_index:
        selected_item = listbox.get(selected_index[0])
        parent_dir = os.path.dirname(selected_item)
        pyperclip.copy(parent_dir)

# Create the GUI window.
window = tk.Tk()
window.title("File Indexer")
window.minsize(1200, 800)
try:
    window.iconbitmap("indexer_icon.ico")
except Exception:
    print(f'Unable to set icon')

def on_closing():
    if index:
        quicksave_path = get_quicksave_path()
        save_index(quicksave_path)
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)

# Global variables to hold the index content, last search, and path
index = []
search = ""
directory = ""
timestamp = ""
total_files_indexed = 0

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
directory_listbox = tk.Listbox(window)

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
# Create the info bar
info_bar = tk.Label(window, text="Total files: 0", anchor="e")

# Create the GUI layout.
window.grid_columnconfigure(0, weight=0)
window.grid_columnconfigure(1, weight=1)

directory_label.grid(row=0, column=0, sticky="w")
add_directory_button = tk.Button(window, text="Add Directory", command=handle_add_directory)
directory_listbox.grid(row=0, column=1, sticky="ew")
add_directory_button.grid(row=0, column=2, pady=10)
index_button.grid(row=0, column=3, pady=10)
search_label.grid(row=1, column=0, sticky="w")
search_entry.grid(row=1, column=1, sticky="ew")
search_button.grid(row=1, column=2, pady=10)
clear_button.grid(row=1, column=3, pady=10)

listbox.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)  # Fill all available space
window.grid_rowconfigure(2, weight=1)  # Allow row 2 to expand

scrollbar.grid(row=2, column=4, sticky="ns")  # Align scrollbar with listbox

# Create the right-click menu for directory_listbox
directory_menu = tk.Menu(window, tearoff=0)
directory_menu.add_command(label="Delete", command=delete_directory)

# Bind the right-click event to show the menu
if sys.platform == "darwin":  # macOS
    listbox.bind("<Button-2>", show_listbox_menu)  # Control+click or right-click on Mac
    directory_listbox.bind("<Button-2>", show_directory_menu)
else:  # Windows/Linux
    listbox.bind("<Button-3>", show_listbox_menu)
    directory_listbox.bind("<Button-3>", show_directory_menu)

# Place the info bar at the bottom of the window
info_bar.grid(row=3, column=0, columnspan=5, sticky="ew")

# Create the right-click menu for listbox
listbox_menu = tk.Menu(window, tearoff=0)
listbox_menu.add_command(label="Open File", command=open_file)
listbox_menu.add_command(label="Open Parent Directory", command=open_parent_directory)
listbox_menu.add_command(label="Copy File Path", command=copy_file_path)
listbox_menu.add_command(label="Copy Parent Directory Path", command=copy_parent_directory_path)

# Bind the right-click event to show the menu for listbox
listbox.bind("<Button-3>", show_listbox_menu)

#Loads the quicksave on start. If there is no quicksave, index will be empty. 
try:
    quicksave_path = get_quicksave_path()
    load_index(quicksave_path)
except Exception as e:
    print(f"Error loading quicksave: {e}")
    index = []

# Load the GUI
window.mainloop()