import pyautogui
import sys
import tkinter as tk
from tkinter import ttk
import json
import os

class SummonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Epic 7 Reroll Helper")
        
        # Character priorities (default values)
        self.priorities = {
            'iseria': 20,
            'ravi': 19,
            'destina': 18,
            'aurius': 5,
            'magarahas': 5,
            'tagahels': 4,
            'wonderous_vial': 4,
            'crozet': 2,
            'achates': 2,
            'cidd': 1
        }
        
        # Character enabled states
        self.enabled_chars = {}
        for char in self.priorities.keys():
            self.enabled_chars[char] = tk.BooleanVar(value=True)
        
        self.load_priorities()
        self.create_widgets()
        
    def create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create Treeviews for different categories
        self.create_treeview(main_frame, "Main Characters", ['ravi', 'destina', 'iseria'], 0)
        self.create_treeview(main_frame, "Other Characters", ['crozet', 'cidd', 'achates'], 1)
        self.create_treeview(main_frame, "Artifacts", ['wonderous_vial', 'tagahels', 'magarahas', 'aurius'], 2)

        # Start button
        ttk.Button(main_frame, text="Save & Start", command=self.start_program).grid(row=3, column=0, columnspan=2, pady=10)

    def create_treeview(self, parent, title, items, row):
        # Create frame for this section
        frame = ttk.LabelFrame(parent, text=title, padding="5")
        frame.grid(row=row, column=0, columnspan=2, sticky='nsew', pady=5)
        
        # Create Treeview with Up as first column
        tree = ttk.Treeview(frame, columns=('Up', 'Name', 'Priority', 'Enabled'), height=len(items))
        tree.heading('Up', text='↑')
        tree.heading('Name', text='Name')
        tree.heading('Priority', text='Priority')
        tree.heading('Enabled', text='Enabled')
        
        # Configure column widths
        tree.column('Up', width=30, anchor='center')
        tree.column('Name', width=150)
        tree.column('Priority', width=70, anchor='center')
        tree.column('Enabled', width=70, anchor='center')
        
        # Hide the default first column
        tree['show'] = 'headings'
        
        # Sort items by priority before adding
        sorted_items = sorted(items, key=lambda x: self.priorities[x], reverse=True)
        
        # Add items
        for item in sorted_items:
            enabled_text = '✓' if self.enabled_chars[item].get() else '✗'
            tree.insert('', 'end', 
                       values=('↑', item.replace('_', ' ').capitalize(), 
                              self.priorities[item], enabled_text), 
                       iid=item)
        
        tree.grid(row=0, column=0, sticky='nsew')
        
        # Bind click events
        tree.bind('<Button-1>', lambda e: self.handle_click(e, tree, items))
        
        # Store tree reference
        setattr(self, f"{title.lower().replace(' ', '_')}_tree", tree)

    def handle_click(self, event, tree, items):
        item = tree.identify_row(event.y)
        if not item:
            return
            
        col = tree.identify_column(event.x)
        
        print(f"Clicked column: {col}, item: {item}")  # Debug print
        
        if col == '#1':  # Up arrow column
            self.move_item_up(tree, item, items)
        elif col == '#4':  # Enabled column
            self.enabled_chars[item].set(not self.enabled_chars[item].get())
            self.toggle_character(tree, item)
            enabled_text = '✓' if self.enabled_chars[item].get() else '✗'
            tree.set(item, column='Enabled', value=enabled_text)

    def move_item_up(self, tree, item, items):
        current_idx = tree.index(item)
        if current_idx > 0:
            tree.move(item, '', current_idx - 1)
            self.update_priorities(tree, items)

    def toggle_character(self, tree, item):
        enabled = self.enabled_chars[item].get()
        if not enabled:
            if not hasattr(self, '_original_priorities'):
                self._original_priorities = {}
            self._original_priorities[item] = self.priorities[item]
            self.priorities[item] = 0
        else:
            if hasattr(self, '_original_priorities') and item in self._original_priorities:
                self.priorities[item] = self._original_priorities[item]
        
        # Update the tree display
        tree.set(item, column='Priority', value=self.priorities[item])

    def update_priorities(self, tree, items):
        # Get current values before reordering
        current_values = {}
        for item in tree.get_children():
            if self.enabled_chars[item].get():  # Only include enabled characters
                current_values[item] = int(tree.set(item, 'Priority'))
        
        # Create a sorted list of values based on current order
        sorted_values = sorted(current_values.values(), reverse=True)
        
        # Update priorities based on new order while maintaining original values
        idx = 0
        for item in tree.get_children():
            if self.enabled_chars[item].get():  # Only update enabled characters
                self.priorities[item] = sorted_values[idx]
                tree.set(item, column='Priority', value=sorted_values[idx])
                idx += 1
            else:
                tree.set(item, column='Priority', value=0)

    def save_priorities(self):
        # Save both priorities and enabled states
        data = {
            'priorities': self.priorities,
            'enabled': {k: v.get() for k, v in self.enabled_chars.items()}
        }
        with open('priorities.json', 'w') as f:
            json.dump(data, f)
            
    def load_priorities(self):
        try:
            with open('priorities.json', 'r') as f:
                data = json.load(f)
                self.priorities.update(data.get('priorities', {}))
                saved_enabled = data.get('enabled', {})
                for char, enabled in saved_enabled.items():
                    if char in self.enabled_chars:
                        self.enabled_chars[char].set(enabled)
        except FileNotFoundError:
            pass
            
    def start_program(self):
        self.save_priorities()
        self.root.destroy()
        start_reroll_process(self.priorities)

def start_reroll_process(priorities):
    highest_level_found = 0
    current_level = 0
    
    while True:
        pyautogui.PAUSE = 2

        record_button = find_image_on_screen('images/record_results.png')
        summon_again = find_image_on_screen('images/summon_again.png')
        skip = find_image_on_screen('images/skip.png')

        if record_button and summon_again:
            current_level = 0
            
            # Check for each character/artifact and add their priority value
            for name, priority in priorities.items():
                if find_image_on_screen(f'images/{name}.png'):
                    current_level += priority
                    print(f"{name.capitalize()} found")
            
            if current_level > highest_level_found:
                highest_level_found = current_level
                print(f"Found better summon results, recording summon results...")
                print(f"Highest level found: {highest_level_found}")
                record_summon()
                current_level = 0
            else:
                pyautogui.click(summon_again)
                pyautogui.PAUSE = 2
                confirm_record2 = find_image_on_screen('images/record_confirmation_2.png')
                pyautogui.PAUSE = 2
                pyautogui.click(confirm_record2)
        elif skip:
            pyautogui.click(skip)
            pyautogui.PAUSE = 2

def find_image_on_screen(image_path):
    try:
        # Search for the image on screen
        location = pyautogui.locateOnScreen(image_path, confidence=0.9)
        
        # If image is found, location will not be None
        if location is not None:
            return location
        else:
            return False
            
    except Exception as e:
        return False
    
def record_summon():
    pyautogui.PAUSE = 2
    record_summon = find_image_on_screen('images/record_results.png')
    pyautogui.click(record_summon)
    pyautogui.PAUSE = 2
    confirm_record = find_image_on_screen('images/record_confirmation.png')
    pyautogui.click(confirm_record)
    pyautogui.PAUSE = 2
    confirm_record2 = find_image_on_screen('images/record_confirmation_2.png')
    pyautogui.PAUSE = 2
    pyautogui.click(confirm_record2)
    pyautogui.PAUSE = 2
    pyautogui.click(confirm_record2)
    pyautogui.PAUSE = 2
    summon_again = find_image_on_screen('images/summon_again.png')
    pyautogui.PAUSE = 2
    pyautogui.click(summon_again)
    pyautogui.PAUSE = 2

if __name__ == "__main__":
    root = tk.Tk()
    app = SummonGUI(root)
    root.mainloop()
    
