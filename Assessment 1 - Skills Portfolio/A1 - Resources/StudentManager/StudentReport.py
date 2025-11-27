import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pathlib
import os
from PIL import Image, ImageTk 

# --- CONFIGURATION ---
BASE_DIR = pathlib.Path(__file__).parent 
# Correct path for studentMarks.txt
STUDENT_FILE_PATH = BASE_DIR.parent / "StudentManager" / "studentMarks.txt"
TOTAL_MAX_MARKS = 160

# --- HELPER FUNCTIONS ---
def apply_hover_effects(button, default_bg, hover_bg='#ffb347'):
    """Applies hover (on enter/leave) effects to a button."""
    def on_enter(e):
        e.widget['bg'] = hover_bg
    def on_leave(e):
        e.widget['bg'] = default_bg
        
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

# --- 1. STUDENT CLASS (The Data Object) ---
class Student:
    """Represents a single student and calculates their results."""
    def __init__(self, code, name, c1, c2, c3, exam):
        self.code = str(code)
        self.name = name
        self.c1 = int(c1)
        self.c2 = int(c2)
        self.c3 = int(c3)
        self.exam = int(exam)
        
        self._recalculate_derived_data()

    def _recalculate_derived_data(self):
        """Recalculates total score, percentage, and grade."""
        self.coursework_total = self.c1 + self.c2 + self.c3
        self.total_score = self.coursework_total + self.exam
        self.overall_percentage = (self.total_score / TOTAL_MAX_MARKS) * 100
        self.grade = self._calculate_grade()

    def _calculate_grade(self):
        """Calculates the student grade based on overall percentage."""
        if self.overall_percentage >= 70:
            return 'A'
        elif 60 <= self.overall_percentage <= 69:
            return 'B'
        elif 50 <= self.overall_percentage <= 59:
            return 'C'
        elif 40 <= self.overall_percentage <= 49:
            return 'D'
        else:
            return 'F'

    def to_output_tuple(self):
        """Returns data formatted for display in the Treeview."""
        return (
            self.name,
            self.code,
            self.coursework_total,
            self.exam,
            f"{self.overall_percentage:.1f}%",
            self.grade
        )

    def to_file_format(self):
        """Returns data formatted for writing back to the file."""
        return (
            f"{self.code},{self.name},{self.c1},{self.c2},{self.c3},{self.exam}"
        )

# --- 2. DATA MANAGER CLASS (The Logic Core) ---
class DataManager:
    """Handles all file IO, searching, and analysis operations."""
    def __init__(self):
        self.students = []
        self.class_size = 0
        self.load_data()

    def load_data(self):
        """Loads data from the file into Student objects."""
        self.students = []
        try:
            with open(STUDENT_FILE_PATH, 'r') as f:
                lines = f.readlines()
                if not lines: return

                self.class_size = int(lines[0].strip())
                
                for line in lines[1:]:
                    parts = line.strip().split(',')
                    if len(parts) == 6:
                        self.students.append(Student(
                            code=parts[0],
                            name=parts[1],
                            c1=parts[2],
                            c2=parts[3],
                            c3=parts[4],
                            exam=parts[5]
                        ))
                
                self.class_size = len(self.students)

        except FileNotFoundError:
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Error processing student data: {e}")

    def save_data(self):
        """Writes current student list back to the file."""
        try:
            self.class_size = len(self.students)
            output_lines = [str(self.class_size) + '\n']
            
            for student in self.students:
                output_lines.append(student.to_file_format() + '\n')
            
            with open(STUDENT_FILE_PATH, 'w') as f:
                f.writelines(output_lines)
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save data to file: {e}")
            return False

    def get_summary(self):
        """Calculates and returns class summary data."""
        if not self.students:
            return 0, 0.0
            
        total_percentage = sum(s.overall_percentage for s in self.students)
        average_percentage = total_percentage / self.class_size
        return self.class_size, average_percentage

    def find_extremes(self, highest=True):
        """Finds student with highest or lowest total score."""
        if not self.students: return None

        key_func = lambda s: s.total_score
        
        if highest:
            return max(self.students, key=key_func)
        else:
            return min(self.students, key=key_func)

    def find_student(self, search_term):
        """Searches for a student by name or code (partial match for name)."""
        search_term = search_term.strip().lower()
        results = []
        for student in self.students:
            if student.code == search_term or search_term in student.name.lower():
                results.append(student)
        return results

    def sort_records(self, key_attr, ascending=True):
        """Sorts the student list based on a key attribute."""
        
        if key_attr == 'total_score':
             sort_key = lambda s: s.total_score
        elif key_attr == 'overall_percentage':
             sort_key = lambda s: s.overall_percentage
        else:
             sort_key = lambda s: getattr(s, key_attr)

        self.students.sort(key=sort_key, reverse=not ascending)

    def _format_student_output(self, student):
        """Formats the detailed output for Text widgets."""
        return (
            f"--- Student Record ---\n"
            f"Name: {student.name}\n"
            f"Code: {student.code}\n"
            f"----------------------\n"
            f"Coursework Total (out of 60): {student.coursework_total}\n"
            f"Exam Mark (out of 100): {student.exam}\n"
            f"Overall Total (out of 160): {student.total_score}\n"
            f"Overall Percentage: {student.overall_percentage:.1f}%\n"
            f"Final Grade: {student.grade}\n"
            f"----------------------\n"
        )
        
# --- 3. STUDENT APP GUI (Tkinter Interface) ---
class StudentApp(tk.Tk):
    NAVY_BLUE = '#000080'
    GOLD_YELLOW = '#FFC107'
    ACADEMIC_GRAY = '#F0F0F0'
    
    def __init__(self):
        super().__init__()
        self.title("Bath Spa University Student Manager")
        # Increase size for more professional appearance
        self.geometry("1100x750") 
        self.data_manager = DataManager()
        
        # --- Load and Display Logo ---
        try:
            # Assumes unilogo.ico is in the same folder as the script
            logo_path = BASE_DIR / "unilogo.png"
            self.logo_img = Image.open(logo_path)
            # Make logo bigger
            self.logo_img = self.logo_img.resize((50, 50), Image.LANCZOS) 
            self.logo_photo = ImageTk.PhotoImage(self.logo_img)
        except Exception as e:
            self.logo_photo = None
        
        self._create_layout()
        
    def _create_layout(self):
        """Sets up the main structure: Header, Sidebar, and Content area."""
        
        # 1. Header Frame (Top Banner)
        header_frame = tk.Frame(self, bg=self.NAVY_BLUE, height=70) # Increased height
        header_frame.pack(side="top", fill="x")
        
        # Header Label (Branding)
        ttk.Label(header_frame, text="BATH SPA UNIVERSITY STUDENT MANAGER", 
                  font=('Arial', 24, 'bold'), # Increased font size
                  foreground='white', 
                  background=self.NAVY_BLUE,
                  image=self.logo_photo, 
                  compound=tk.LEFT, 
                  padding=(15, 10)
                 ).pack(side="left", padx=10, pady=5)
        
        # 2. Main Content Area (Sidebar + Dynamic View)
        main_area = tk.Frame(self, bg=self.ACADEMIC_GRAY)
        main_area.pack(side="top", expand=True, fill="both")
        
        # 3. Sidebar Frame (Vertical Menu)
        sidebar_frame = tk.Frame(main_area, bg=self.NAVY_BLUE, width=220, relief=tk.RAISED) 
        sidebar_frame.pack(side="left", fill="y")
        
        # 4. Content Frame (Dynamic Area for views)
        self.content_container = ttk.Frame(main_area, padding=(10, 10, 10, 10))
        self.content_container.pack(side="right", expand=True, fill="both")
        self.content_container.grid_rowconfigure(0, weight=1) # Make content fill height
        self.content_container.grid_columnconfigure(0, weight=1) # Make content fill width

        # --- Initialize Views (Content Frames) ---
        self.views = {}
        for F in (ViewAllFrame, SearchFrame, ExtremesFrame, ManageFrame):
            frame_name = F.__name__
            frame = F(self.content_container, self)
            self.views[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self._create_sidebar_buttons(sidebar_frame)
        self.show_view("ViewAllFrame") 

    def _create_sidebar_buttons(self, parent_frame):
        """Creates all 9 buttons for the sidebar menu."""
        
        menu_items = [
            ("1. View All Records", lambda: self.show_view("ViewAllFrame")),
            ("2. View Individual", lambda: self.show_view("SearchFrame")),
            ("3. Highest Score", lambda: self._handle_extremes_sidebar(True)),
            ("4. Lowest Score", lambda: self._handle_extremes_sidebar(False)),
            ("5. Sort Records", lambda: self.show_view("ViewAllFrame", sort_mode=True)),
            ("6. Add Student", lambda: self.show_view("ManageFrame", action="add")),
            ("7. Delete Student", lambda: self.show_view("ManageFrame", action="delete")),
            ("8. Update Student", lambda: self.show_view("ManageFrame", action="update")),
        ]

        for text, command in menu_items:
            btn = tk.Button(parent_frame, text=text, command=command,
                            font=('Arial', 14), fg='white', bg=self.NAVY_BLUE, 
                            relief=tk.FLAT, activebackground=self.GOLD_YELLOW, activeforeground=self.NAVY_BLUE, 
                            anchor='w', width=20, padx=10, pady=10) 
            btn.pack(fill='x', pady=(5, 0), padx=5)
            apply_hover_effects(btn, self.NAVY_BLUE, self.GOLD_YELLOW)
        
        # Quit Button 
        quit_btn = tk.Button(parent_frame, text="Quit Application", command=self.destroy,
                             font=('Arial', 14, 'bold'), fg='white', bg=self.GOLD_YELLOW,
                             relief=tk.RAISED, activebackground='#FF8C00', activeforeground='white', 
                             width=20, pady=10) 
        quit_btn.pack(fill='x', pady=(30, 10), padx=5)
        apply_hover_effects(quit_btn, self.GOLD_YELLOW, '#FF8C00')


    def show_view(self, frame_name, **kwargs):
        """Raises the selected view frame and passes optional arguments."""
        view = self.views[frame_name]
        view.tkraise()
        
        if hasattr(view, 'refresh_data'):
            view.refresh_data(self.data_manager.students, **kwargs)

    def _handle_extremes_sidebar(self, highest):
        self.show_view("ExtremesFrame", highest=highest)

    def refresh_treeview(self, student_list):
        if "ViewAllFrame" in self.views:
            self.views["ViewAllFrame"]._populate_treeview(student_list)


    # --- HANDLERS FOR EXTENSION PROBLEMS (6, 7, 8) ---
    
    def _handle_submission(self, code, name, c1, c2, c3, exam):
        """Centralized handler for adding a student."""
        new_student = Student(code, name, c1, c2, c3, exam)
        self.data_manager.students.append(new_student)
        
        if self.data_manager.save_data():
            messagebox.showinfo("Success", f"Student {name} added and saved.")
            self.refresh_treeview(self.data_manager.students)
        else:
            self.data_manager.students.pop() 

    # All management actions now redirect to ManageFrame to handle the view
    def _handle_add_student(self):
        self.show_view("ManageFrame", action="add")

    def _handle_delete_student(self):
        self.show_view("ManageFrame", action="delete")

    def _handle_update_student(self):
        self.show_view("ManageFrame", action="update")


# --- VIEW FRAMES ---

class ViewAllFrame(ttk.Frame):
    """Handles 1. View All and 5. Sort Records."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack_propagate(False) # Allows the frame to expand properly

        # Summary Panel
        self.summary_frame = tk.Frame(self, bg=controller.ACADEMIC_GRAY, bd=1, relief=tk.RIDGE, padx=10, pady=10)
        self.summary_frame.pack(fill='x', pady=5)
        self.summary_label = ttk.Label(self.summary_frame, text="Class Summary: ", font=('Arial', 14, 'bold')) # Larger font
        self.summary_label.pack(side=tk.LEFT)

        # Sorting Controls (Visible when sorting is required)
        self.sort_controls = ttk.LabelFrame(self, text="5. Sort Options", padding="10")
        self.sort_key = tk.StringVar(value='name')
        self.sort_order = tk.BooleanVar(value=True) 
        
        ttk.Label(self.sort_controls, text="Sort By:").pack(side=tk.LEFT, padx=5)
        ttk.OptionMenu(self.sort_controls, self.sort_key, 'name', 'name', 'total_score', 'overall_percentage').pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(self.sort_controls, text="Ascending", variable=self.sort_order, value=True).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.sort_controls, text="Descending", variable=self.sort_order, value=False).pack(side=tk.LEFT, padx=10)
        ttk.Button(self.sort_controls, text="Apply Sort", command=self._handle_sort_view).pack(side=tk.LEFT, padx=20)
        
        # Treeview (Table) setup
        columns = ('Name', 'Code', 'CW Total (60)', 'Exam (100)', 'Percentage', 'Grade')
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        self.tree.pack(expand=True, fill='both') # Treeview now EXPANDS to fill empty space

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor=tk.CENTER)
            
        # Tagging for Grade Color-Coding
        self.tree.tag_configure('A_grade', background='#D4EDDA', foreground='#155724', font=('Arial', 11, 'bold')) # Font size increased
        self.tree.tag_configure('B_grade', background='#CCE5FF', foreground='#004085', font=('Arial', 11))
        self.tree.tag_configure('C_grade', background='#FFF3CD', foreground='#856404', font=('Arial', 11))
        self.tree.tag_configure('D_grade', background='#FFE0B2', foreground='#B35900', font=('Arial', 11))
        self.tree.tag_configure('F_grade', background='#F8D7DA', foreground='#721C24', font=('Arial', 11, 'bold')) 

    def _populate_treeview(self, student_list):
        """Clears and loads the Treeview with student data, applying color tags."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for student in student_list:
            tags = (f"{student.grade}_grade",) 
            self.tree.insert('', tk.END, values=student.to_output_tuple(), tags=tags)
            
    def refresh_data(self, student_list, sort_mode=False, **kwargs):
        """Called by controller to switch to this view."""
        self._update_summary()
        self._populate_treeview(student_list)
        
        if sort_mode:
            self.sort_controls.pack(fill='x', pady=5)
        else:
            self.sort_controls.pack_forget()


    def _update_summary(self):
        """Updates the summary label."""
        size, avg_perc = self.controller.data_manager.get_summary()
        summary_text = (
            f"Class Summary: Total Students: {size}. Average Percentage: {avg_perc:.1f}%"
        )
        self.summary_label.config(text=summary_text)

    def _handle_sort_view(self):
        """Handler for Menu Item 5 (Sort)."""
        key = self.sort_key.get()
        ascending = self.sort_order.get()
        
        self.controller.data_manager.sort_records(key, ascending)
        self._populate_treeview(self.controller.data_manager.students)
        messagebox.showinfo("Sort Complete", f"Records sorted by {key} ({'Ascending' if ascending else 'Descending'}).")


class SearchFrame(ttk.Frame):
    """Handles 2. View Individual Record."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Search Controls
        search_frame = ttk.Frame(self, padding="10")
        search_frame.pack(fill='x', pady=10)
        
        ttk.Label(search_frame, text="2. View Individual Record\n\nEnter Student Name or Code:").pack(side=tk.LEFT, padx=5, anchor=tk.N)
        self.search_entry = ttk.Entry(search_frame, width=25, font=('Arial', 12))
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=10, fill='y')
        
        ttk.Button(search_frame, text="Search", command=self._handle_search).pack(side=tk.LEFT, padx=10, pady=10)
        
        # Output Area
        self.individual_output_area = tk.Text(self, height=18, width=70, font=('Courier', 11))
        self.individual_output_area.pack(pady=10, padx=10, expand=True, fill='both')

    def refresh_data(self, student_list, **kwargs):
        """Clears output area when view is raised."""
        self.individual_output_area.delete(1.0, tk.END)
        self.search_entry.delete(0, tk.END)

    def _handle_search(self):
        """Handles searching and displaying an individual student record."""
        search_term = self.search_entry.get()
        results = self.controller.data_manager.find_student(search_term)
        
        self.individual_output_area.delete(1.0, tk.END)
        
        if not results:
            self.individual_output_area.insert(tk.END, "No student found matching the search term.")
        else:
            output = "\n".join(self.controller.data_manager._format_student_output(s) for s in results)
            self.individual_output_area.insert(tk.END, output)


class ExtremesFrame(ttk.Frame):
    """Handles 3. Highest and 4. Lowest Score (using a dashboard card)."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.result_frame = ttk.LabelFrame(self, text="Extreme Score Results", padding="20")
        self.result_frame.pack(pady=20, padx=20, expand=True, fill='both')

        self.title_label = ttk.Label(self.result_frame, text="Select an option from the sidebar...", font=('Arial', 16, 'bold'))
        self.title_label.pack(pady=10)
        
        self.extreme_student_output = tk.Text(self.result_frame, height=15, width=70, font=('Courier', 11))
        self.extreme_student_output.pack(pady=10, expand=True, fill='both')

    def refresh_data(self, student_list, highest=True, **kwargs):
        """Handles showing the highest or lowest scoring student."""
        extreme_student = self.controller.data_manager.find_extremes(highest)
        
        self.extreme_student_output.delete(1.0, tk.END)
        
        title = "3. HIGHEST OVERALL SCORE" if highest else "4. LOWEST OVERALL SCORE"
        self.title_label.config(text=title, foreground=self.controller.NAVY_BLUE if highest else self.controller.GOLD_YELLOW)
        
        if extreme_student:
            output = self.controller.data_manager._format_student_output(extreme_student)
            self.extreme_student_output.insert(tk.END, output)
        else:
            self.extreme_student_output.insert(tk.END, "No student data available.")


class ManageFrame(ttk.Frame):
    """Handles 6. Add, 7. Delete, and 8. Update Records (Inline Form for all)."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.action_title = ttk.Label(self, text="Student Management", font=('Arial', 16, 'bold'))
        self.action_title.pack(pady=10)
        
        self.status_label = ttk.Label(self, text="Select a function from the sidebar (Add/Delete/Update).", foreground='blue')
        self.status_label.pack(pady=10)

        # --- Form Container (Persistent) ---
        self.form_container = ttk.LabelFrame(self, text="Management Form", padding=20)
        self.form_container.pack(fill='x', expand=False, pady=10) 
        
        # --- Persistent Widgets Dictionaries ---
        self.inputs = {}     # Stores tk.StringVar
        self.widgets = {}    # Stores ttk.Label and ttk.Entry widgets (CRITICAL for stable visibility control)
        self._setup_add_inline_form_widgets()
        
        # --- Action Buttons ---
        self.submit_button = ttk.Button(self.form_container, text="Execute Action", command=self._execute_action)
        self.submit_button.grid(row=8, column=0, columnspan=2, pady=20)
        
        self.current_action = None 
        
        # Clear/Hide form content initially
        self._set_form_visibility(False)

    def _setup_add_inline_form_widgets(self):
        """Creates all 6 input fields permanently in the grid, storing widgets directly."""
        fields = [
            ("Student Code (4 digits):", 'code'),
            ("Student Name:", 'name'),
            ("Coursework 1 (Max 20):", 'c1'),
            ("Coursework 2 (Max 20):", 'c2'),
            ("Coursework 3 (Max 20):", 'c3'),
            ("Exam Mark (Max 100):", 'exam'),
        ]
        
        for i, (text, key) in enumerate(fields):
            # 1. Create and store Label widget
            label = ttk.Label(self.form_container, text=text, font=('Arial', 11))
            label.grid(row=i, column=0, sticky='w', pady=5, padx=10)
            self.widgets[f'label_{key}'] = label
            
            # 2. Create and store StringVar
            var = tk.StringVar()
            self.inputs[key] = var
            
            # 3. Create and store Entry widget
            entry = ttk.Entry(self.form_container, textvariable=var, width=25, font=('Arial', 11))
            entry.grid(row=i, column=1, sticky='ew', pady=5, padx=10)
            self.widgets[f'entry_{key}'] = entry
            
            # Numeric validation
            if key in ['c1', 'c2', 'c3', 'exam']:
                vcmd = self.register(self._validate_numeric_input)
                entry.config(validate='key', validatecommand=(vcmd, '%P', key))

    def _set_form_visibility(self, visible, fields_to_show=None):
        """Shows/Hides form widgets using direct dictionary access."""
        
        # Determine which fields need to be visible
        if fields_to_show is None and visible:
            fields_to_show = self.inputs.keys()
        
        for key in self.inputs.keys():
            label_widget = self.widgets[f'label_{key}']
            entry_widget = self.widgets[f'entry_{key}']
            
            # Show/Hide the label and entry widget
            if visible and key in fields_to_show:
                label_widget.grid()
                entry_widget.grid()
            else:
                label_widget.grid_remove()
                entry_widget.grid_remove()
                self.inputs[key].set("") # Clear fields when hiding
                
        # Handle submit button text
        self.submit_button.config(text=f"Execute {self.current_action.capitalize()}" if self.current_action else "Execute Action")
        
    def _validate_numeric_input(self, P, key):
        """Validates if input is numeric and within range."""
        if P.isdigit() or P == "":
            if P == "": return True
            
            val = int(P)
            if key == 'exam' and val > 100: return False
            if key in ['c1', 'c2', 'c3'] and val > 20: return False
            return True
        return False
        
    def _execute_action(self):
        """Determines which action handler to call based on current_action."""
        if self.current_action == 'add':
            self._submit_inline_add()
        elif self.current_action == 'delete':
            self._submit_inline_delete()
        elif self.current_action == 'update':
            self._submit_inline_update()

    def _submit_inline_add(self):
        """Handles the final submission for adding a student."""
        code, name = self.inputs['code'].get(), self.inputs['name'].get()
        try:
            c1, c2, c3 = int(self.inputs['c1'].get()), int(self.inputs['c2'].get()), int(self.inputs['c3'].get())
            exam = int(self.inputs['exam'].get())
            
            if len(code) != 4 or not code.isdigit() or not name:
                messagebox.showwarning("Validation Error", "Code must be 4 digits and Name must be filled.")
                return
            
            self.controller._handle_submission(code, name, c1, c2, c3, exam)
            self._set_form_visibility(False) # Hide form after success
            self.status_label.config(text=f"Student {name} added. View All Records to confirm.", foreground='darkgreen')
            
        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all mark fields are complete numbers.")

    # --- INLINE DELETE/UPDATE HANDLERS ---
    
    def _submit_inline_delete(self):
        """Handles deleting the student whose code/name is in the 'code' field."""
        search_term = self.inputs['code'].get()
        
        if not search_term:
            messagebox.showwarning("Search Required", "Please enter a Student Code or Name to identify the record.")
            return

        results = self.controller.data_manager.find_student(search_term)
        
        if not results:
            messagebox.showwarning("Not Found", "No student found matching that code/name.")
            return

        student_to_delete = results[0]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {student_to_delete.name} ({student_to_delete.code})?"):
            self.controller.data_manager.students.remove(student_to_delete)
            if self.controller.data_manager.save_data():
                messagebox.showinfo("Success", f"Record for {student_to_delete.name} deleted and file saved.")
                self.controller.refresh_treeview(self.controller.data_manager.students)
                self._set_form_visibility(False)
                self.status_label.config(text=f"Record deleted for {student_to_delete.name}.", foreground='red')
    
    def _submit_inline_update(self):
        """Handles updating the student whose code/name is in the 'code' field."""
        search_term = self.inputs['code'].get()
        
        if not search_term:
            messagebox.showwarning("Search Required", "Please enter the Student Code or Name to identify the record.")
            return
            
        results = self.controller.data_manager.find_student(search_term)
        if not results:
            messagebox.showwarning("Not Found", "Student not found.")
            return
            
        student = results[0]
        
        try:
            # Update only the fields that are NOT empty
            new_name = self.inputs['name'].get()
            
            if new_name: student.name = new_name
            if self.inputs['c1'].get(): student.c1 = int(self.inputs['c1'].get())
            if self.inputs['c2'].get(): student.c2 = int(self.inputs['c2'].get())
            if self.inputs['c3'].get(): student.c3 = int(self.inputs['c3'].get())
            if self.inputs['exam'].get(): student.exam = int(self.inputs['exam'].get())
            
            student._recalculate_derived_data()
            
            if self.controller.data_manager.save_data():
                messagebox.showinfo("Success", f"Record for {student.name} updated and file saved.")
                self.controller.refresh_treeview(self.controller.data_manager.students)
                self._set_form_visibility(False)
                self.status_label.config(text=f"Record updated for {student.name}.", foreground='blue')
                
        except ValueError:
            messagebox.showerror("Input Error", "Please ensure mark fields contain valid numbers.")

    def refresh_data(self, student_list, action=None, **kwargs):
        """Manages which fields and buttons are visible based on the sidebar action."""
        
        # 1. Reset and hide everything
        self.current_action = action
        self._set_form_visibility(False)
        
        # 2. Update title and visibility based on action
        if action == "add":
            self.action_title.config(text="6. Add New Student")
            self.status_label.config(text="Enter all details to submit a new student.", foreground='darkgreen')
            self.form_container.config(text="6. Add New Student Record")
            self._set_form_visibility(True)
            
        elif action == "delete":
            self.action_title.config(text="7. Delete Student Record")
            self.status_label.config(text="Enter Student Code or Name below, then press Execute.", foreground='red')
            self.form_container.config(text="7. Delete Student Search")
            self._set_form_visibility(True, fields_to_show=['code', 'name']) # Only show search fields
            
        elif action == "update":
            self.action_title.config(text="8. Update Student Record")
            self.status_label.config(text="Enter Name/Code to find student, then enter new marks/name below.", foreground='blue')
            self.form_container.config(text="8. Update Student Fields")
            self._set_form_visibility(True, fields_to_show=['code', 'name', 'c1', 'c2', 'c3', 'exam']) # Show all fields
            
        else:
            self.action_title.config(text="Student Management")
            self.status_label.config(text="Select a function from the sidebar.", foreground='blue')


if __name__ == '__main__':
    app = StudentApp()
    app.mainloop()