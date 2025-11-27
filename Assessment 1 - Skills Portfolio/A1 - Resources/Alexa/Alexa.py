import tkinter as tk
from tkinter import messagebox
import random
import pathlib
from PIL import Image, ImageTk 
import pygame 
from gtts import gTTS 
import pyttsx3 # Local TTS Fallback Engine
import os 
import time 
import threading # For running TTS without freezing the GUI

# --- CONFIGURATION & ASSETS ---
BASE_DIR = pathlib.Path(__file__).parent 

ASSETS = {
    # File Paths (Assumes all assets are in the same directory as this script)
    "joke_file": BASE_DIR / "randomJokes.txt",
    "laugh_sound": BASE_DIR / "laughing.mp3",
    "menu_bg": BASE_DIR / "1stpage.png",
    "qns_bg": BASE_DIR / "2nd.png", 
    "ans_bg": BASE_DIR / "2nd.png", 
    # Temporary file for TTS output
    "tts_temp_file": BASE_DIR / "temp_joke_tts.mp3"
}

# --- HELPER FUNCTIONS ---

def load_background_image(frame, image_path):
    """Loads and scales a background image for a frame."""
    try:
        img = Image.open(image_path)
        img = img.resize((700, 500), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        
        bg_label = tk.Label(frame, image=photo)
        bg_label.image = photo 
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        return photo
    except FileNotFoundError:
        messagebox.showerror("Asset Error", f"Background image not found at: {image_path}")
        frame.config(bg='#0099ff') # Fallback to blend color
        return None

def apply_hover_effects(button, default_bg, hover_bg='#ffb347'):
    """Applies hover (on enter/leave) effects to a button."""
    def on_enter(e):
        e.widget['bg'] = hover_bg
    def on_leave(e):
        e.widget['bg'] = default_bg
        
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

# --- 1. JOKE LOGIC CLASS  ---

class JokeSource:
    """Handles loading, storing, and selecting jokes from the text file."""
    def __init__(self):
        self.jokes = []
        self._load_jokes()

    def _load_jokes(self):
        """Loads all jokes from the text file into a list of tuples."""
        try:
            with open(ASSETS["joke_file"], 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line: 
                        parts = line.rsplit('?', 1) 
                        if len(parts) == 2:
                            setup = parts[0].strip() + "?" 
                            punchline = parts[1].strip()
                            self.jokes.append((setup, punchline))
                        
        except FileNotFoundError:
            messagebox.showerror("File Error", f"Joke file was not found at: {ASSETS['joke_file']}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading jokes: {e}")

    def get_random_joke(self):
        """Returns a random (setup, punchline) tuple, or None if no jokes are loaded."""
        if self.jokes:
            return random.choice(self.jokes)
        return None

# --- 2. SOUND & SPEECH MANAGER (API Integration) ---

class SpeechManager:
    """Manages playing sounds (laugh) and generating/playing TTS audio."""
    def __init__(self):
        # Initializing mixer, but ONLY for SFX and TTS now
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024) 
        self.engine = self._init_pyttsx3()
        self.tts_thread = None 

    def _init_pyttsx3(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            return engine
        except Exception as e:
            print(f"Pyttsx3 initialization failed: {e}")
            return None

    def _tts_worker(self, text, use_fallback):
        """Worker function to run synchronous TTS/gTTS commands without blocking the GUI."""
        if not use_fallback:
            try:
                tts = gTTS(text=text, lang='en')
                tts.save(ASSETS["tts_temp_file"])
                
                # --- Play MP3 via Sound object ---
                self.play_short_sfx(ASSETS["tts_temp_file"])
                return
            
            except Exception as e:
                print(f"gTTS failed ({e}). Falling back to pyttsx3...")

        # Pyttsx3 Fallback (Local, Offline)
        if self.engine:
            self.stop_tts()
            self.engine.say(text)
            self.engine.runAndWait() 
        else:
            print("Audio output is unavailable.")

    def generate_and_play_tts(self, text):
        """Starts the TTS process in a new thread."""
        self.stop_tts() # Stop any preceding TTS thread

        self.tts_thread = threading.Thread(target=self._tts_worker, args=(text, False), daemon=True)
        self.tts_thread.start()

    def play_short_sfx(self, file_path):
        """Plays short sound via a Sound object."""
        time.sleep(0.05) 
            
        try:
            sound_obj = pygame.mixer.Sound(file_path)
            channel = pygame.mixer.find_channel(True) 
            channel.play(sound_obj)
        except pygame.error as e:
            print(f"SFX Playback Error: {e}")

    def play_laugh_sfx(self):
        """Plays the separate laughter sound effect using Sound."""
        # No need to pause/unpause music
        self.play_short_sfx(ASSETS["laugh_sound"])

    def stop_tts(self):
        """Stops pyttsx3 engine and cleans up threads."""
        if self.engine and self.engine._inLoop:
            self.engine.stop()
        if self.tts_thread and self.tts_thread.is_alive():
             pass
             
    def stop_audio(self):
        """Stops all audio streams."""
        pygame.mixer.stop() # Stops SFX/TTS
        self.stop_tts()
        
    def cleanup(self):
        self.stop_audio()
        
        try:
            time.sleep(0.1) 
        except Exception:
            pass 

        if os.path.exists(ASSETS["tts_temp_file"]):
            try:
                os.remove(ASSETS["tts_temp_file"])
            except PermissionError as e:
                print(f"Warning: Could not delete temp TTS file: {e}")

# --- 3. CONTROLLER & FRAME CLASSES ---

class JokeController(tk.Tk):
    """The main application controller."""
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Alexa Tell Me A Joke")
        self.geometry("700x500")
        self.resizable(False, False)

        self.joke_source = JokeSource()
        self.speech_manager = SpeechManager()

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        
        for F in (MenuFrame, JokeFrame):
            frame_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MenuFrame") 

    def show_frame(self, frame_name):
        """Raises the selected frame to the top."""
        self.speech_manager.stop_tts() # Stop speaking if switching pages
        frame = self.frames[frame_name]
        frame.tkraise()

    def destroy(self):
        """Override destroy to cleanup audio resources."""
        self.speech_manager.cleanup()
        super().destroy()


class MenuFrame(tk.Frame):
    """The starting page with the '1stpage.png' background."""
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        load_background_image(self, ASSETS["menu_bg"])

        # Main button to start the joke
        default_bg = '#FFC107' 
        btn_play = tk.Button(self, text="PLAY", 
                             command=lambda: self.start_joke(), 
                             font=('Arial', 24, 'bold'), 
                             bg=default_bg, fg='black', 
                             width=10, height=1, bd=4, relief=tk.RAISED)
        # CHANGED: rely from 0.55 to 0.70 to move the button down
        btn_play.place(relx=0.5, rely=0.70, anchor=tk.CENTER) 
        apply_hover_effects(btn_play, default_bg)
        
    def start_joke(self):
        """Switches to the joke frame and starts the first question."""
        joke_frame = self.controller.frames["JokeFrame"]
        joke_frame.next_joke()
        self.controller.show_frame("JokeFrame")


class JokeFrame(tk.Frame):
    """Manages both the Question (Setup) and Answer (Punchline) states."""
    
    JOKE_BG_COLOR = '#0099ff' 
    
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.current_joke = None
        
        # Background
        self.bg_label = tk.Label(self)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.joke_photo = load_background_image(self.bg_label, ASSETS["qns_bg"])
        
        # Joke Text
        self.joke_text_label = tk.Label(
            self, text="", font=('Arial', 20, 'bold'),
            wraplength=550, justify=tk.CENTER,
            bg=self.JOKE_BG_COLOR, fg='white'
        )
        self.joke_text_label.place(relx=0.5, rely=0.35, anchor=tk.CENTER, width=550)

        # Show Punchline Button
        default_bg_pl = '#FFC107'
        self.punchline_button = tk.Button(
            self, text="Show Punchline", command=self.show_punchline,
            font=('Arial', 16, 'bold'), bg=default_bg_pl, fg='#333333',
            width=20, height=2, bd=4, relief=tk.RAISED
        )
        apply_hover_effects(self.punchline_button, default_bg_pl)

        # Next Joke Button
        default_bg_next = '#4CAF50'
        self.next_button = tk.Button(
            self, text="Next Joke", command=self.next_joke,
            font=('Arial', 16, 'bold'), bg=default_bg_next, fg='white',
            width=20, height=2, bd=4, relief=tk.RAISED
        )
        apply_hover_effects(self.next_button, default_bg_next)

        # Quit Button
        default_bg_quit = '#F44336'
        self.quit_button = tk.Button(
            self, text="Quit", command=self.controller.destroy,
            font=('Arial', 10), bg=default_bg_quit, fg='white',
            width=8, height=1, bd=2
        )
        apply_hover_effects(self.quit_button, default_bg_quit)
        self.quit_button.place(relx=0.5, rely=0.95, anchor=tk.S)

    def _hide_all_states(self):
        """Hide elements while switching views."""
        self.punchline_button.place_forget()
        self.next_button.place_forget()
        self.controller.speech_manager.stop_tts() # Stop TTS speaking

    def next_joke(self):
        """Show setup and speak it."""
        self._hide_all_states()
        self.current_joke = self.controller.joke_source.get_random_joke()
        # Removed: pygame.mixer.music.unpause()

        if self.current_joke is None:
            self.joke_text_label.config(
                text="No jokes loaded. Check your file.", fg='red'
            )
            return

        setup, punchline = self.current_joke

        # Display setup
        self.joke_text_label.config(text=setup, fg='white', bg=self.JOKE_BG_COLOR)

        # Speak setup
        self.controller.speech_manager.generate_and_play_tts(setup)

        # Show Punchline button
        self.punchline_button.place(relx=0.5, rely=0.60, anchor=tk.CENTER)

    def show_punchline(self):
        """Show punchline, wait for TTS to finish, then play laugh."""

        # Hide buttons
        self.punchline_button.place_forget()
        self.next_button.place_forget()

        if self.current_joke is None:
            return

        setup, punchline = self.current_joke

        # Display punchline
        self.joke_text_label.config(
            text=f"ANSWER:\n\n{punchline}",
            fg='white',
            bg=self.JOKE_BG_COLOR
        )

        # Speak punchline (starts thread)
        self.controller.speech_manager.generate_and_play_tts(punchline)

        # Wait for TTS to finish speaking in the background thread (The Pyttsx3/gTTS sync issue)
        def wait_and_laugh():
            # Wait for the TTS thread to die (i.e., finish speaking/playing)
            self.controller.speech_manager.tts_thread.join()
            
            # Once speaking is done, play the laugh SFX
            self.controller.speech_manager.play_laugh_sfx()
            
            #  delay slightly before thread finishes
            time.sleep(1.5) 


        threading.Thread(target=wait_and_laugh, daemon=True).start()

        # Show Next Button
        self.next_button.place(relx=0.5, rely=0.60, anchor=tk.CENTER)


if __name__ == '__main__':
    app = JokeController()
    app.mainloop()