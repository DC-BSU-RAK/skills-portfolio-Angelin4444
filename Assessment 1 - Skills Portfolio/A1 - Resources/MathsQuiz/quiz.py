import tkinter as tk
from tkinter import messagebox
from tkinter import ttk # Used for modern GUI elements/scaling
import random
import time
from PIL import Image, ImageTk # For loading PNGs/JPEGs in Tkinter
import pygame # For sound and music
import pathlib 

# --- CONFIGURATION & ASSETS ---
# Dynamically get the directory where the current script (quiz.py) is located
# This ensures assets are found regardless of the working directory.
BASE_DIR = pathlib.Path(__file__).parent 

ASSETS = {
    # Update the values to be the full path using BASE_DIR
    "background_music": BASE_DIR / "background.mp3",
    "correct_sound": BASE_DIR / "correct.mp3",
    "wrong_sound": BASE_DIR / "wrong.mp3",
    "main_menu_bg": BASE_DIR / "1st page.png",
    "instructions_bg": BASE_DIR / "instruction.png",
    "level_bg": BASE_DIR / "level page.png",
    "quiz_bg_1": BASE_DIR / "quiz1.png",
    "quiz_bg_2": BASE_DIR / "quiz2.png",
}
# ... rest of your code
DIFFICULTY_SETTINGS = {
    'Beginner': (1, 9),      # Single digit
    'Intermediate': (10, 99), # Double digit
    'Advanced': (1000, 9999) # Four digit
}
QUESTION_TIME_LIMIT = 15 # Seconds per question
MAX_LIVES = 5

# --- 1. SOUND MANAGER CLASS (Library/API Integration) ---
class SoundManager:
    """Manages all sound functionality using pygame."""
    def __init__(self):
        pygame.mixer.init()
        self.music_volume = 0.5  # Default volume
        self.sfx_volume = 0.8
        self.is_muted = False
        
        # Load sound effects
        try:
            self.correct_sfx = pygame.mixer.Sound(ASSETS["correct_sound"])
            self.wrong_sfx = pygame.mixer.Sound(ASSETS["wrong_sound"])
            self.correct_sfx.set_volume(self.sfx_volume)
            self.wrong_sfx.set_volume(self.sfx_volume)
        except pygame.error as e:
            print(f"Error loading sound effects: {e}")
            self.correct_sfx = None
            self.wrong_sfx = None

    def start_music(self):
        """Starts background music looping."""
        if not self.is_muted and not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.load(ASSETS["background_music"])
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1) # -1 means loop indefinitely
            except pygame.error as e:
                print(f"Error loading or playing music: {e}")

    def stop_music(self):
        """Stops background music."""
        pygame.mixer.music.stop()

    def play_sfx(self, type):
        """Plays a sound effect."""
        if self.is_muted:
            return
            
        if type == "correct" and self.correct_sfx:
            self.correct_sfx.play()
        elif type == "wrong" and self.wrong_sfx:
            self.wrong_sfx.play()

    def set_music_volume(self, volume):
        """Sets music volume (0.0 to 1.0)."""
        self.music_volume = volume
        pygame.mixer.music.set_volume(self.music_volume)

    def toggle_mute(self):
        """Toggles mute state for all audio."""
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.stop_music()
            pygame.mixer.pause() # Pause SFX mixer
        else:
            pygame.mixer.unpause() # Unpause SFX mixer
            self.start_music() # Restart music if needed

# --- 2. MATH QUIZ LOGIC CLASS (OOP Core) ---
class MathQuizLogic:
    """Handles all core game logic, including question generation, scoring, and life management."""
    def __init__(self, controller):
        self.controller = controller
        self.score = 0
        self.questions_attempted = 0
        self.current_answer = None
        self.attempts_remaining = 2
        self.lives = MAX_LIVES
        self.difficulty = None
        self.max_questions = 10
        self.start_time = None

    def set_difficulty(self, level):
        """Sets the difficulty level."""
        self.difficulty = level

    def random_int(self, min_val, max_val):
        """Determines a random value based on the difficulty range."""
        return random.randint(min_val, max_val)

    def decide_operation(self):
        """Randomly decides between addition or subtraction."""
        return random.choice(['+', '-'])

    def generate_problem(self):
        """Generates a new question and sets the correct answer."""
        min_val, max_val = DIFFICULTY_SETTINGS[self.difficulty]

        num1 = self.random_int(min_val, max_val)
        num2 = self.random_int(min_val, max_val)
        operation = self.decide_operation()
        
        # Ensure the first number is larger for subtraction (keeps results positive)
        if operation == '-' and num1 < num2:
            num1, num2 = num2, num1

        if operation == '+':
            self.current_answer = num1 + num2
        else:
            self.current_answer = num1 - num2

        self.attempts_remaining = 2
        self.start_time = time.time()
        
        return f"{num1} {operation} {num2}"

    def check_answer(self, user_input):
        """Checks the user's answer and updates score/lives/attempts."""
        
        try:
            user_answer = int(user_input)
        except ValueError:
            return "Invalid Input", False # Do not penalize life/attempt

        # Check if correct
        if user_answer == self.current_answer:
            self.controller.sound_manager.play_sfx("correct")
            points = 10 if self.attempts_remaining == 2 else 5
            self.score += points
            self.questions_attempted += 1
            return f"Correct! (+{points} points)", True
        
        # Check if incorrect
        else:
            self.controller.sound_manager.play_sfx("wrong")
            self.attempts_remaining -= 1
            
            if self.attempts_remaining == 0:
                # Two wrong attempts, lose a life and move on
                self.lives -= 1
                self.questions_attempted += 1
                feedback = f"Wrong! The answer was {self.current_answer}. You lost a life."
                
                # Check for Game Over
                if self.lives <= 0:
                    self.controller.show_results("Game Over! Out of Lives.")
                
                return feedback, True # Move to next question

            else:
                feedback = "Wrong. One more attempt remaining."
                return feedback, False # Stay on the same question

    def calculate_rank(self):
        """Returns the final rank based on the score."""
        score_percent = (self.score / (self.max_questions * 10)) * 100 if self.max_questions else 0
        
        if score_percent >= 90:
            return "A+ (Outstanding!)"
        elif score_percent >= 80:
            return "A (Excellent!)"
        elif score_percent >= 70:
            return "B (Very Good)"
        elif score_percent >= 60:
            return "C (Good)"
        else:
            return "F (Try Again)"

# --- HELPER FUNCTIONS ---

def load_background_image(frame, image_path):
    """Loads and scales a background image for a frame."""
    try:
        # Open and resize the image to fit the window size (700x500)
        img = Image.open(image_path)
        img = img.resize((700, 500), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        
        # Create a background label
        bg_label = tk.Label(frame, image=photo)
        bg_label.image = photo # Keep a reference
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except FileNotFoundError:
        print(f"Background image not found: {image_path}. Using default background.")
        frame.config(bg='#e0e0e0') # Default background color

def apply_hover_effects(button):
    """Applies hover (on enter/leave) effects to a button."""
    default_bg = button['bg']
    hover_bg = '#ffb347' # Light orange hover color
    
    def on_enter(e):
        e.widget['bg'] = hover_bg
        
    def on_leave(e):
        e.widget['bg'] = default_bg
        
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)


# --- 3. CONTROLLER & FRAME CLASSES ---

class QuizController(tk.Tk):
    """The main application window that manages frame switching and global services."""
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("CodeLab II - Advanced Maths Quiz")
        self.geometry("700x500")
        self.resizable(False, False)

        # Global Services
        self.sound_manager = SoundManager()
        self.quiz_logic = MathQuizLogic(self)

        # Container to hold all frames
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        
        # Initialize all pages (frames)
        for F in (MainMenuFrame, InstructionsFrame, SettingsFrame, LevelSelectFrame, QuizFrame):
            frame_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Start the application on the main menu
        self.show_frame("MainMenuFrame")
        self.sound_manager.start_music()

    def show_frame(self, frame_name):
        """Raises the selected frame to the top."""
        frame = self.frames[frame_name]
        frame.tkraise()
        # Optional: update frame content on switch (e.g., refresh settings display)
        if frame_name == "SettingsFrame":
            frame.update_settings_display()

    def start_game(self, level):
        """Sets difficulty, starts quiz logic, and switches to the quiz frame."""
        self.quiz_logic.set_difficulty(level)
        quiz_frame = self.frames["QuizFrame"]
        quiz_frame.initialize_quiz()
        self.show_frame("QuizFrame")

    def show_results(self, message):
        """Displays final results and returns to the menu."""
        final_rank = self.quiz_logic.calculate_rank()
        total_score = self.quiz_logic.score
        
        # Reset lives and questions attempted for the next game
        self.quiz_logic.lives = MAX_LIVES
        self.quiz_logic.questions_attempted = 0

        # Use a messagebox for the end screen
        messagebox.showinfo(
            "Quiz Complete!", 
            f"{message}\n\n"
            f"Difficulty: {self.quiz_logic.difficulty}\n"
            f"Final Score: {total_score} / 100 (Max)\n"
            f"Rank: {final_rank}"
        )
        self.show_frame("MainMenuFrame")


# --- Main Frames ---

class MainMenuFrame(tk.Frame):
    """The initial page with Play, Instructions, and Settings buttons."""
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        load_background_image(self, ASSETS["main_menu_bg"])

 # Title Label (Optional, to be placed over a clear area in the background image)
        tk.Label(self, text="Maths Quiz", 
                 font=('Arial', 50, 'bold'), 
                 fg='#004d40', 
                 bg="#f4ebd8",  # Changed: Use a color that matches the pale inner canvas of your image
                 relief=tk.FLAT # Changed: Remove the border/ridge effect
                ).place(relx=0.5, rely=0.15, anchor=tk.CENTER)

        button_style = {'font': ('Arial', 16, 'bold'), 'width': 15, 'bg': '#FFA500', 'fg': 'white', 'bd': 4, 'relief': tk.RAISED}
        
        # 1. Play Button
        btn_play = tk.Button(self, text="PLAY", command=lambda: controller.show_frame("LevelSelectFrame"), **button_style)
        btn_play.place(relx=0.5, rely=0.40, anchor=tk.CENTER)
        apply_hover_effects(btn_play)

        # 2. Instructions Button
        btn_instructions = tk.Button(self, text="INSTRUCTIONS", command=lambda: controller.show_frame("InstructionsFrame"), **button_style)
        btn_instructions.place(relx=0.5, rely=0.55, anchor=tk.CENTER)
        apply_hover_effects(btn_instructions)

        # 3. Settings Button
        btn_settings = tk.Button(self, text="SETTINGS", command=lambda: controller.show_frame("SettingsFrame"), **button_style)
        btn_settings.place(relx=0.5, rely=0.70, anchor=tk.CENTER)
        apply_hover_effects(btn_settings)


class InstructionsFrame(tk.Frame):
    """Displays the game instructions."""
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        load_background_image(self, ASSETS["instructions_bg"])
        
        # 1. Corrected Text (Removed Markdown symbols like ** and fixed spacing)
        instruction_text = (
            "GOAL: Answer 10 arithmetic questions to achieve the highest rank.\n\n"
            
            "LIVES: You start with 5 lives.\n"
            "TIMER: Each question has a 15-second timer. If time runs out,\n"
            "       it counts as a failed attempt.\n\n"
            
            "ATTEMPTS: You get 2 chances per question:\n"
            "   - 1st Correct: 10 points.\n"
            "   - 2nd Correct: 5 points.\n"
            "   - 2nd Wrong: You lose 1 life and move to the next question.\n\n"
            
            "RANKING: Ranks are awarded based on your final score (Max 100 points)."
        )
        
        # 2. Modified instructions_area Label properties
        instructions_area = tk.Label(
            self, 
            text=instruction_text, 
            font=('Arial', 14), # Slightly larger font for readability
            justify=tk.LEFT, 
            bg='#f7eedb', # Use a color that matches the pale inner box of your background image
            fg='#004d40', # Dark color for contrast
            pady=20, 
            padx=20, 
            relief=tk.FLAT # Removed border
        )
        
        # Position the label using a specific location in your background image
        instructions_area.place(relx=0.5, rely=0.52, anchor=tk.CENTER)
        
        btn_back = tk.Button(self, text="Back to Menu", command=lambda: controller.show_frame("MainMenuFrame"), font=('Arial', 14), bg='#8B0000', fg='white', bd=3)
        btn_back.place(relx=0.5, rely=0.85, anchor=tk.CENTER)
        apply_hover_effects(btn_back)

class SettingsFrame(tk.Frame):
    """Allows control of sound mute and music volume."""
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        # We will use the main menu background since it's visually appropriate
        load_background_image(self, ASSETS["main_menu_bg"]) 

        # Match the pale background area color of your image
        PALE_BG_COLOR = '#f7eedb' 

        # 1. Title Label (Match background color)
        tk.Label(self, text="Game Settings", 
                 font=('Arial', 24, 'bold'), 
                 fg='#004d40', 
                 bg=PALE_BG_COLOR, # Blended background color
                 relief=tk.FLAT # No border
                ).place(relx=0.5, rely=0.15, anchor=tk.CENTER)

        # 2. Mute Button
        self.mute_btn_text = tk.StringVar()
        self.mute_btn = tk.Button(self, textvariable=self.mute_btn_text, 
                                  command=self.toggle_mute, 
                                  font=('Arial', 16, 'bold'), 
                                  width=15, 
                                  bg='#FF4500', # Original color
                                  fg='white', 
                                  bd=4, relief=tk.RAISED)
        self.mute_btn.place(relx=0.5, rely=0.30, anchor=tk.CENTER)
        apply_hover_effects(self.mute_btn)
        
        # Music Volume Label
        tk.Label(self, text="Music Volume:", 
                 font=('Arial', 14), 
                 bg=PALE_BG_COLOR, 
                 fg='#004d40'
                ).place(relx=0.25, rely=0.50, anchor=tk.W) # rely changed from 0.45 to 0.50, relx changed from 0.30 to 0.25
        
        # Music Volume Slider
        self.music_slider = tk.Scale(self, from_=0, to=100, orient=tk.HORIZONTAL, 
                                     command=self.set_music_volume, 
                                     length=300, 
                                     bg=PALE_BG_COLOR, 
                                     troughcolor='#FFA500', 
                                     fg='#004d40', 
                                     bd=0, 
                                     highlightthickness=0)
        self.music_slider.set(self.controller.sound_manager.music_volume * 100)
        self.music_slider.place(relx=0.45, rely=0.50, anchor=tk.W) # rely changed from 0.45 to 0.50, relx changed from 0.50 to 0.45
        
        # 6. Back Button
        btn_back = tk.Button(self, text="Back to Menu", 
                             command=lambda: controller.show_frame("MainMenuFrame"), 
                             font=('Arial', 14), 
                             bg='#8B0000', 
                             fg='white', 
                             bd=3)
        btn_back.place(relx=0.5, rely=0.85, anchor=tk.CENTER)
        apply_hover_effects(btn_back)

    def update_settings_display(self):
        """Updates the mute button text based on the current state."""
        if self.controller.sound_manager.is_muted:
            self.mute_btn_text.set("Unmute Sound")
            self.mute_btn.config(bg='#4CAF50') 
        else:
            self.mute_btn_text.set("Mute Sound")
            self.mute_btn.config(bg='#FF4500') 

    def toggle_mute(self):
        self.controller.sound_manager.toggle_mute()
        self.update_settings_display()

    def set_music_volume(self, value):
        volume = int(value) / 100.0
        self.controller.sound_manager.set_music_volume(volume)

class LevelSelectFrame(tk.Frame):
    """Presents the difficulty selection buttons."""
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        load_background_image(self, ASSETS["level_bg"])
        
        # Define the blending color for the central graphic
        PALE_BG_COLOR = '#f7eedb' 

        # 1. FIX: Title Label - Remove white background and border
        tk.Label(self, text="Select Difficulty", 
                 font=('Arial', 24, 'bold'), 
                 fg='#8B0000', 
                 bg=PALE_BG_COLOR, # Blended background color
                 relief=tk.FLAT # Removed border
                ).place(relx=0.5, rely=0.15, anchor=tk.CENTER)

        # 2. FIX: Button Style - Increase width to prevent text cutoff
        button_style = {'font': ('Arial', 18, 'bold'), 
                        'width': 22, # Increased width from 18 to 22
                        'fg': 'white', 
                        'bd': 5, 
                        'relief': tk.RAISED}
        
        levels = list(DIFFICULTY_SETTINGS.keys())
        
        # Beginner Button
        btn_beginner = tk.Button(self, text="Beginner (Single Digit)", command=lambda: controller.start_game(levels[0]), bg='#4CAF50', **button_style)
        btn_beginner.place(relx=0.5, rely=0.40, anchor=tk.CENTER)
        apply_hover_effects(btn_beginner)

        # Intermediate Button (Will now display full text)
        btn_intermediate = tk.Button(self, text="Intermediate (Double Digit)", command=lambda: controller.start_game(levels[1]), bg='#FFC300', **button_style)
        btn_intermediate.place(relx=0.5, rely=0.55, anchor=tk.CENTER)
        apply_hover_effects(btn_intermediate)

        # Advanced Button
        btn_advanced = tk.Button(self, text="Advanced (Four Digit)", command=lambda: controller.start_game(levels[2]), bg='#D90000', **button_style)
        btn_advanced.place(relx=0.5, rely=0.70, anchor=tk.CENTER)
        apply_hover_effects(btn_advanced)
        
        # Back Button
        btn_back = tk.Button(self, text="Back to Menu", command=lambda: controller.show_frame("MainMenuFrame"), font=('Arial', 14), bg='#8B0000', fg='white', bd=3)
        btn_back.place(relx=0.5, rely=0.85, anchor=tk.CENTER)
        apply_hover_effects(btn_back)

class QuizFrame(tk.Frame):
    """The main quiz playing area with question, entry, timer, score, and lives."""
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.after_id = None # To store the timer ID
        self.setup_ui() # This now correctly calls the method defined below

    def setup_ui(self):
        """Sets up the static widgets on the quiz frame."""
        # Define the blending color for the central graphic (used in all frames)
        PALE_BG_COLOR = '#f7eedb' 
        # Define the contrasting color (used for question text and calculator details)
        CONTRAST_COLOR = '#004d40' 
        
        # Load a random background for the quiz frame
        bg_asset = random.choice([ASSETS["quiz_bg_1"], ASSETS["quiz_bg_2"]])
        load_background_image(self, bg_asset)
        
        # 1. FIX: Top Info Bar - Set background to blend color, remove border/relief
        self.info_frame = tk.Frame(self, bg=PALE_BG_COLOR, bd=0, relief=tk.FLAT)
        self.info_frame.place(relx=0.5, rely=0.10, anchor=tk.CENTER, width=650, height=50)

        # 2. FIX: Score, Question Count, Lives, and Timer Labels - Match Frame BG and use contrast FG
        self.score_label = tk.Label(self.info_frame, text="Score: 0", font=('Arial', 14, 'bold'), 
                                     bg=PALE_BG_COLOR, fg=CONTRAST_COLOR)
        self.score_label.pack(side=tk.LEFT, padx=10)
        
        self.question_count_label = tk.Label(self.info_frame, text="Q: 1/10", font=('Arial', 14, 'bold'), 
                                              bg=PALE_BG_COLOR, fg=CONTRAST_COLOR)
        self.question_count_label.pack(side=tk.LEFT, padx=10)
        
        self.lives_label = tk.Label(self.info_frame, text=f"❤️ Lives: {MAX_LIVES}", font=('Arial', 14, 'bold'), 
                                    bg=PALE_BG_COLOR, fg='red') 
        self.lives_label.pack(side=tk.RIGHT, padx=10)
        
        # Timer Label (Right side)
        self.timer_label = tk.Label(self.info_frame, text="⏱ 15s", font=('Arial', 14, 'bold'), 
                                    bg=PALE_BG_COLOR, fg='#FFA500') 
        self.timer_label.pack(side=tk.RIGHT, padx=10)

        # Question and Answer Area (Centered)
        
        # FIX: Question Label Background
        self.question_label = tk.Label(self, text="Ready?", font=('Arial', 36, 'bold'), 
                                       bg=PALE_BG_COLOR, fg=CONTRAST_COLOR, pady=10, padx=20)
        self.question_label.place(relx=0.5, rely=0.40, anchor=tk.CENTER)

        # FIX: Answer Label Background
        tk.Label(self, text="Answer:", font=('Arial', 16), bg=PALE_BG_COLOR).place(relx=0.35, rely=0.60, anchor=tk.CENTER)
        
        self.answer_entry = tk.Entry(self, font=('Arial', 18), width=10, justify=tk.CENTER)
        self.answer_entry.place(relx=0.5, rely=0.60, anchor=tk.CENTER)
        self.answer_entry.bind('<Return>', lambda event=None: self.submit_answer())

        self.submit_button = tk.Button(self, text="Submit", command=self.submit_answer, font=('Arial', 16, 'bold'), bg='#4CAF50', fg='white')
        self.submit_button.place(relx=0.68, rely=0.60, anchor=tk.CENTER)
        apply_hover_effects(self.submit_button)
        
        # FIX: Feedback Label Background
        self.feedback_label = tk.Label(self, text="Select a level to begin!", font=('Arial', 12), fg='blue', bg=PALE_BG_COLOR)
        self.feedback_label.place(relx=0.5, rely=0.75, anchor=tk.CENTER)
        
    def initialize_quiz(self):
        """Resets state and starts the first question."""
        self.time_left = QUESTION_TIME_LIMIT
        self.controller.quiz_logic.score = 0
        self.controller.quiz_logic.questions_attempted = 0
        self.controller.quiz_logic.lives = MAX_LIVES
        self.next_question()

    def start_timer(self):
        """Starts the 15-second countdown."""
        if self.after_id:
            self.after_cancel(self.after_id)
            
        self.time_left = QUESTION_TIME_LIMIT
        self.update_timer_display()

    def update_timer_display(self):
        """Updates timer label and handles timeout."""
        if self.time_left >= 0:
            self.timer_label.config(text=f"⏱ {self.time_left}s")
            self.time_left -= 1
            # Schedule next update
            self.after_id = self.after(1000, self.update_timer_display)
        else:
            # Time's up! Force a wrong answer/life penalty
            self.submit_button.config(state=tk.DISABLED) # Disable button instantly
            self.answer_entry.config(state=tk.DISABLED)
            self.feedback_label.config(text="TIME'S UP! (Two attempts failed)", fg='red')
            
            # This triggers the life penalty logic:
            self.controller.quiz_logic.attempts_remaining = 1 # Force it to be the last attempt
            self.controller.quiz_logic.check_answer("Timeout") # Pass non-int to trigger loss of life
            
            self.after(1500, self.next_question)

    def next_question(self):
        """Moves to the next question or ends the quiz."""
        logic = self.controller.quiz_logic
        
        if logic.questions_attempted >= logic.max_questions:
            self.controller.show_results("Quiz Completed Successfully!")
            return

        # Enable controls
        self.submit_button.config(state=tk.NORMAL)
        self.answer_entry.config(state=tk.NORMAL)
        self.answer_entry.focus() # Auto-focus the entry box

        # Update UI info
        self.score_label.config(text=f"Score: {logic.score}")
        self.question_count_label.config(text=f"Q: {logic.questions_attempted + 1}/{logic.max_questions}")
        self.lives_label.config(text=f"❤️ Lives: {logic.lives}")

        # Generate and display new question
        question_text = logic.generate_problem()
        self.question_label.config(text=question_text + " = ")
        self.feedback_label.config(text="Time to solve!", fg='blue')
        self.answer_entry.delete(0, tk.END)

        self.start_timer() # Start or restart the timer

    def submit_answer(self):
        """Handles the submission of the user's answer."""
        user_input = self.answer_entry.get().strip()
        logic = self.controller.quiz_logic
        
        if not user_input:
            self.feedback_label.config(text="Please enter an answer!", fg='orange')
            return

        # Stop timer momentarily to check answer
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
            
        feedback, solved = logic.check_answer(user_input)
        
        # Update feedback label
        if "Correct" in feedback or "Wrong!" in feedback:
            color = 'green' if solved and "Correct" in feedback else 'red'
            self.feedback_label.config(text=feedback, fg=color)
        elif "Invalid Input" in feedback:
            self.feedback_label.config(text=feedback, fg='orange')
            self.start_timer() # Restart timer for this question
            return

        # If solved (correct or 2 failed attempts), move to the next question
        if solved:
            self.after(1500, self.next_question)
        else:
            # Still on the same question, update UI and restart timer
            self.answer_entry.delete(0, tk.END)
            self.start_timer()


if __name__ == '__main__':
    app = QuizController()
    app.mainloop()