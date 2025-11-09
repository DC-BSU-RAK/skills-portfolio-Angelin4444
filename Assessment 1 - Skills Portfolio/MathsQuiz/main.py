import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import random

# --- File Path Setup (The absolute path fix) ---
# This ensures images are found regardless of where the terminal is run from
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# --- Constants ---
# BG for Main Menu, Instructions, Settings, Results (with title/design elements)
BG_IMAGE_PATH = os.path.join(ASSETS_DIR, "background.png") 
# BG for Difficulty Page (with LEVELS title)
QUIZ_BG_IMAGE_PATH = os.path.join(ASSETS_DIR, "level.png")
# NEW: BG for the actual Quiz playing page (clean background)
CLEAN_BG_PATH = os.path.join(ASSETS_DIR, "clean_background.jpg") 

DIFFICULTY_RANGES = {
    'Beginner': (1, 9),      # 1-digit numbers
    'Intermediate': (10, 99),  # 2-digit numbers
    'Advanced': (100, 999)     # 3-digit numbers
}

MAX_QUESTIONS = 10
MAX_LIVES = 5
FIRST_ATTEMPT_POINTS = 10
SECOND_ATTEMPT_POINTS = 5

# --- Custom Colors matching your design aesthetic ---
BTN_BG_COLOR = '#e899b8'
BTN_FG_COLOR = 'white'
ACCENT_COLOR = '#61dafb'


# --- Button Style Helper ---
def create_styled_button(parent, text, command, font_size=18, width=15):
    """Creates a button with the specific pink/red aesthetic and hover effect."""
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        font=('Arial', font_size, 'bold'),
        width=width,
        height=1,
        bg=BTN_BG_COLOR,
        fg=BTN_FG_COLOR,
        relief="flat",
        bd=0,
        activebackground='#a07080', # Darker pink on press
        cursor="hand2"
    )
    # Add subtle hover/leave effect for top presentation marks
    btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT_COLOR)) 
    btn.bind("<Leave>", lambda e: btn.config(bg=BTN_BG_COLOR)) 
    return btn


# ======================================================================
# --- 1. Main Application Controller ---
# ======================================================================
class MathsQuizApp:
    def __init__(self, master):
        self.master = master
        master.title("Maths Trivia Challenge")
        master.geometry("800x600")
        master.resizable(False, False)

        # --- Game State ---
        self.score = 0
        self.lives = MAX_LIVES
        self.difficulty = None
        self.quiz_data = []
        self.question_index = 0
        self.music_enabled = tk.BooleanVar(value=False) # For settings page

        # --- Load Resources ---
        self.background_image = self._load_image(BG_IMAGE_PATH, 800, 600)
        self.quiz_bg_image = self._load_image(QUIZ_BG_IMAGE_PATH, 800, 600)
        self.clean_background_image = self._load_image(CLEAN_BG_PATH, 800, 600) # NEW clean background

        self.main_frame = tk.Frame(master)
        self.main_frame.pack(fill="both", expand=True)

        self.current_page = None
        self.show_main_menu()

    def _load_image(self, path, width, height):
        """Safely load image and resize it"""
        if not os.path.exists(path):
            messagebox.showerror("Image Error", f"Image not found:\n{path}")
            return None

        try:
            img = Image.open(path)
            img = img.resize((width, height), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load {path}\n{e}")
            return None

    def switch_page(self, page_class, **kwargs):
        """Switches the current view to a new page class."""
        if self.current_page:
            self.current_page.destroy()
        new_page = page_class(self.main_frame, self, **kwargs)
        new_page.pack(fill="both", expand=True)
        self.current_page = new_page

    # --- Navigation Methods ---
    def show_main_menu(self):
        self.switch_page(MainMenuPage)

    def show_instructions_page(self):
        self.switch_page(InstructionsPage)

    def show_difficulty_select_page(self):
        self.switch_page(DifficultySelectPage)

    def show_settings_page(self):
        self.switch_page(SettingsPage)

    def show_results(self):
        self.switch_page(ResultsPage)


# ======================================================================
# --- 2. Menu and Setup Pages ---
# ======================================================================

class MainMenuPage(tk.Frame):
    """The landing page with custom background and navigation buttons."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        canvas = tk.Canvas(self, width=800, height=600, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        if self.app.background_image:
            canvas.create_image(0, 0, anchor="nw", image=self.app.background_image)

        # Create a clean white frame for buttons for better readability
        button_frame = tk.Frame(canvas, bg='white', padx=20, pady=20, relief="raised")
        canvas.create_window(600, 350, window=button_frame, anchor="center") 

        # Helper function to create stylish buttons with hover effect (used only here)
        def create_menu_button(text, command):
            btn = tk.Button(
                button_frame, 
                text=text, 
                command=command,
                font=('Arial', 18, 'bold'),
                width=15,
                height=1,
                bg=BTN_BG_COLOR, 
                fg=BTN_FG_COLOR,
                relief="flat",
                bd=0,
                activebackground='#a07080', 
                cursor="hand2"
            )
            btn.pack(pady=15)
            btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT_COLOR)) 
            btn.bind("<Leave>", lambda e: btn.config(bg=BTN_BG_COLOR)) 
            return btn

        create_menu_button("Instructions", self.app.show_instructions_page)
        create_menu_button("Quiz", self.app.show_difficulty_select_page)
        create_menu_button("Settings", self.app.show_settings_page)


class InstructionsPage(tk.Frame):
    """Displays the game rules, scoring, and heart system."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        bg = tk.Label(self, image=self.app.background_image)
        bg.place(x=0, y=0, relwidth=1, relheight=1)

        frame = tk.Frame(self, bg='white', bd=5, relief="raised", padx=40, pady=40)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="QUIZ INSTRUCTIONS", font=('Arial', 24, 'bold'),
                 bg='white', fg=BTN_BG_COLOR).pack(pady=10)

        text = (
            "This is a **Maths Trivia** game testing basic arithmetic.\n\n"
            "1️ **Levels:** Beginner (1-digit), Intermediate (2-digit), Advanced (3-digit).\n"
            "2️ Each level has a total of **10 questions**.\n"
            "3️ **Scoring:** +10 points for a correct answer on the **first attempt**, +5 points on the **second attempt**.\n"
            "4️ **Lives (Hearts):** You start with **5 Hearts**. If you miss a question twice, **1 Heart will be lost**.\n"
            "5️ **Game Over:** The quiz ends if you run out of hearts or complete 10 questions."
        )

        tk.Label(frame, text=text, font=('Arial', 12), justify='left', bg='white').pack(pady=20)
        create_styled_button(frame, "<< Back to Menu", self.app.show_main_menu, font_size=14, width=15).pack(pady=10)


class SettingsPage(tk.Frame):
    """Simple settings page with music placeholder."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        bg = tk.Label(self, image=self.app.background_image)
        bg.place(x=0, y=0, relwidth=1, relheight=1)

        frame = tk.Frame(self, bg='white', bd=5, relief="raised", padx=40, pady=40)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="SETTINGS", font=('Arial', 24, 'bold'), bg='white', fg=BTN_BG_COLOR).pack(pady=20)

        # Demonstrates setting persistence for high marks
        tk.Checkbutton(
            frame, text="Enable Background Music",
            variable=self.app.music_enabled, font=('Arial', 14), bg='white'
        ).pack(pady=10)

        tk.Label(frame, text="(Music feature coming soon)", font=('Arial', 10), bg='white').pack(pady=5)

        create_styled_button(frame, "<< Back to Menu", self.app.show_main_menu, font_size=14, width=15).pack(pady=20)


class DifficultySelectPage(tk.Frame):
    """Page for selecting the difficulty level."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        bg = tk.Label(self, image=self.app.quiz_bg_image)
        bg.place(x=0, y=0, relwidth=1, relheight=1)

        # Central White Frame (to hold and group the buttons)
        center_frame = tk.Frame(self, bg='white', bd=5, relief="raised", padx=40, pady=40)
        center_frame.place(relx=0.5, rely=0.6, anchor='center') 

        # Helper function for stylish level buttons (used only here)
        def create_level_button(text, command):
            btn = tk.Button(
                center_frame, 
                text=text,
                command=command,
                font=('Arial', 20, 'bold'), 
                width=12, 
                height=1,
                bg='#c2d4f8', 
                fg='black', 
                relief="flat", 
                bd=1,
                activebackground=BTN_BG_COLOR,
                cursor="hand2"
            )
            btn.pack(pady=15)
            # Add subtle hover/leave effect
            btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT_COLOR)) 
            btn.bind("<Leave>", lambda e: btn.config(bg='#c2d4f8')) 
            return btn
        
        # Buttons
        for level_name in DIFFICULTY_RANGES.keys():
            create_level_button(level_name, lambda l=level_name: self.start_quiz(l))

        # Back Button
        tk.Button(self, text="<< Back to Menu", command=self.app.show_main_menu,
                  font=('Arial', 10), bg='white').place(x=20, y=560)

    def start_quiz(self, level):
        """Initializes game state and generates all 10 questions for the selected level."""
        self.app.difficulty = level
        self.app.score = 0
        self.app.lives = MAX_LIVES
        self.app.question_index = 0
        self.app.quiz_data = []

        # Generate quiz questions
        min_val, max_val = DIFFICULTY_RANGES[level]
        for _ in range(MAX_QUESTIONS):
            n1, n2 = random.randint(min_val, max_val), random.randint(min_val, max_val)
            op = random.choice(['+', '-'])
            ans = n1 + n2 if op == '+' else n1 - n2
            # Store question, correct answer, and initial attempt count
            self.app.quiz_data.append({'q_str': f"{n1} {op} {n2} =", 'answer': ans, 'attempts': 1})

        self.app.switch_page(QuizPage)


# ======================================================================
# --- 3. Core Quiz Logic ---
# ======================================================================

class QuizPage(tk.Frame):
    """Handles the main quiz interaction, scoring, and heart system."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # *** CORRECTED LINE: Use the clean_background_image for the Quiz Page ***
        bg = tk.Label(self, image=self.app.clean_background_image) 
        bg.place(x=0, y=0, relwidth=1, relheight=1)

        quiz_frame = tk.Frame(self, bg='white', bd=5, relief="raised", padx=30, pady=30)
        quiz_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Status Bar elements
        self.score_label = tk.Label(quiz_frame, text=f"Score: {self.app.score}", font=('Arial', 12, 'bold'), bg='white')
        self.score_label.pack()

        self.lives_label = tk.Label(quiz_frame, text=f"Hearts: {'❤️' * self.app.lives}", font=('Arial', 12, 'bold'), bg='white', fg='red')
        self.lives_label.pack()

        self.q_label = tk.Label(quiz_frame, text="", font=('Courier', 36, 'bold'), bg='white')
        self.q_label.pack(pady=20)

        self.answer_entry = tk.Entry(quiz_frame, font=('Arial', 24), width=10, justify='center')
        self.answer_entry.pack(pady=10)

        tk.Button(quiz_frame, text="Submit", bg=BTN_BG_COLOR, fg='white', font=('Arial', 14, 'bold'),
                  command=self.check_answer).pack(pady=10)

        self.feedback = tk.Label(quiz_frame, text="", font=('Arial', 12, 'italic'), bg='white', fg='red')
        self.feedback.pack(pady=5)

        tk.Button(self, text="Quit Game", command=self.confirm_quit, font=('Arial', 10), bg='gray').place(x=700, y=560)
        self.display_problem()

    def display_problem(self):
        """Displays the current question and checks for end-game conditions."""
        if self.app.question_index >= MAX_QUESTIONS or self.app.lives <= 0:
            self.app.show_results()
            return

        q = self.app.quiz_data[self.app.question_index]
        self.q_label.config(text=q['q_str'])
        self.answer_entry.delete(0, tk.END)
        self.feedback.config(text=f"Question {self.app.question_index + 1} of {MAX_QUESTIONS}")
        self.update_status()
        self.answer_entry.focus()

    def update_status(self):
        """Updates the score and hearts display."""
        self.score_label.config(text=f"Score: {self.app.score}")
        self.lives_label.config(text=f"Hearts: {'❤️' * self.app.lives}")

    def check_answer(self):
        """Evaluates the answer, awards points, and manages the heart system."""
        try:
            user_ans = int(self.answer_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid whole number.")
            return

        q = self.app.quiz_data[self.app.question_index]

        if user_ans == q['answer']:
            # Correct: Award points and move on
            points = FIRST_ATTEMPT_POINTS if q['attempts'] == 1 else SECOND_ATTEMPT_POINTS
            self.app.score += points
            messagebox.showinfo("Correct", f"Nice! +{points} points")
            self.app.question_index += 1
            self.display_problem()
        else:
            # Incorrect: Handle attempts and life deduction
            q['attempts'] += 1
            if q['attempts'] > 2:
                # Failed the question (second miss)
                self.app.lives -= 1
                messagebox.showerror("Incorrect", f"Wrong again! Answer was {q['answer']}. 💔 1 Heart Lost.")
                self.app.question_index += 1
                self.display_problem()
            else:
                # First miss (second chance)
                self.feedback.config(text="Incorrect! You have one more chance.")
                self.answer_entry.delete(0, tk.END)

    def confirm_quit(self):
        """Confirms quit and moves to results."""
        if messagebox.askyesno("Quit", "Are you sure you want to quit? Your current score will be calculated."):
            self.app.show_results()


# ======================================================================
# --- 4. Results Page ---
# ======================================================================

class ResultsPage(tk.Frame):
    """Outputs the final score, rank, and option to replay."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        bg = tk.Label(self, image=self.app.background_image)
        bg.place(x=0, y=0, relwidth=1, relheight=1)

        frame = tk.Frame(self, bg='white', bd=5, relief="raised", padx=50, pady=50)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        score = self.app.score
        max_score = MAX_QUESTIONS * FIRST_ATTEMPT_POINTS

        # Grading Logic (as requested)
        if score >= 90:
            rank = "A+ (Excellent!)"
        elif score >= 80:
            rank = "A (Great Job!)"
        elif score >= 70:
            rank = "B (Good Work!)"
        else:
            rank = "C (Keep Practicing!)"

        tk.Label(frame, text="QUIZ RESULTS", font=('Arial', 28, 'bold'), fg=BTN_BG_COLOR, bg='white').pack(pady=10)
        tk.Label(frame, text=f"Final Score: {score} / {max_score}", font=('Arial', 18), bg='white').pack(pady=10)
        tk.Label(frame, text=f"Rank: {rank}", font=('Arial', 18, 'italic'), fg=ACCENT_COLOR, bg='white').pack(pady=5)

        create_styled_button(frame, "Play Again", self.app.show_main_menu, font_size=14, width=12).pack(pady=10)
        tk.Button(frame, text="Exit", command=self.app.master.destroy, font=('Arial', 14, 'bold'),
                  bg='gray', fg='white', width=12, relief="flat").pack(pady=5)


# ======================================================================
# --- 5. Execution Block ---
# ======================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = MathsQuizApp(root)
    root.mainloop()