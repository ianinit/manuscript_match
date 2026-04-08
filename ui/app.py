import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.audio_utils import check_ffmpeg, parse_manuscript
from core.transcriber import Transcriber
from core.comparer import compare

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ManuscriptApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Manuscript Match")
        self.geometry("1000x800")

        self.manuscript_path = None
        self.audio_path = None
        self.is_processing = False

        self.setup_ui()
        
        # Check ffmpeg shortly after UI starts
        self.after(500, self.check_env)

    def check_env(self):
        if not check_ffmpeg():
            messagebox.showwarning(
                "Missing FFmpeg", 
                "FFmpeg was not found in your system PATH.\nfaster-whisper requires it to process audio files."
            )

    def setup_ui(self):
        # Top Frame for File Selection
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(pady=10, padx=10, fill="x")
        
        # Manuscript Selector
        self.lbl_manuscript = ctk.CTkLabel(self.top_frame, text="No Manuscript Selected.")
        self.lbl_manuscript.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.btn_manuscript = ctk.CTkButton(self.top_frame, text="Select Manuscript (TXT/PDF)", command=self.select_manuscript)
        self.btn_manuscript.grid(row=0, column=1, padx=10, pady=10)

        # Audio Selector
        self.lbl_audio = ctk.CTkLabel(self.top_frame, text="No Audio Selected.")
        self.lbl_audio.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.btn_audio = ctk.CTkButton(self.top_frame, text="Select Audio (WAV/MP3)", command=self.select_audio)
        self.btn_audio.grid(row=1, column=1, padx=10, pady=10)

        # Process Button & Progress
        self.btn_process = ctk.CTkButton(self.top_frame, text="Start Match", command=self.start_processing, state="disabled")
        self.btn_process.grid(row=2, column=0, columnspan=2, pady=10)

        self.progress = ctk.CTkProgressBar(self.top_frame)
        self.progress.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.top_frame, text="")
        self.lbl_status.grid(row=4, column=0, columnspan=2)

        # Output Text Area
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Adding a label indicator
        self.legend_lbl = ctk.CTkLabel(self.output_frame, text="Legend: RED = Skipped word | GREEN = Added word", text_color="gray")
        self.legend_lbl.pack(pady=(5,0))

        self.textbox = ctk.CTkTextbox(self.output_frame, wrap="word", font=("Arial", 16))
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Define Tkinter text tags for colors inside CustomTkinter textbox
        self.textbox.tag_config("skipped", foreground="#ff4d4d") # Red
        self.textbox.tag_config("added", foreground="#00cc66")   # Green
        self.textbox.tag_config("match", foreground="grey")       # Neutral gray for correct matches so discrepancies stand out

    def select_manuscript(self):
        path = filedialog.askopenfilename(
            title="Select Manuscript",
            filetypes=[("Text/PDF Files", "*.txt *.pdf"), ("All Files", "*.*")]
        )
        if path:
            self.manuscript_path = path
            self.lbl_manuscript.configure(text=f"Script: {os.path.basename(path)}")
            self.check_ready()

    def select_audio(self):
        path = filedialog.askopenfilename(
            title="Select Audio Recording",
            filetypes=[("Audio Files", "*.wav *.mp3 *.m4a *.flac"), ("All Files", "*.*")]
        )
        if path:
            self.audio_path = path
            self.lbl_audio.configure(text=f"Audio: {os.path.basename(path)}")
            self.check_ready()

    def check_ready(self):
        if self.manuscript_path and self.audio_path and not self.is_processing:
            self.btn_process.configure(state="normal")
        else:
            self.btn_process.configure(state="disabled")

    def start_processing(self):
        self.is_processing = True
        self.btn_process.configure(state="disabled")
        self.progress.set(0)
        self.lbl_status.configure(text="Parsing manuscript...")
        self.textbox.delete("1.0", "end")

        # Run in thread to not freeze UI
        threading.Thread(target=self.process_task, daemon=True).start()

    def update_progress(self, val):
        self.after(0, lambda: self.progress.set(val))
        self.after(0, lambda: self.lbl_status.configure(text=f"Transcribing... {int(val*100)}%"))

    def process_task(self):
        try:
            script_text = parse_manuscript(self.manuscript_path)
            if not script_text.strip():
                self.after(0, lambda: messagebox.showerror("Error", "Could not extract text from manuscript."))
                self.finish_processing()
                return

            self.after(0, lambda: self.lbl_status.configure(text="Loading Whisper model... (This may take a moment window)"))
            transcriber = Transcriber(model_size="small")
            
            self.after(0, lambda: self.lbl_status.configure(text="Transcribing audio..."))
            transcribed_words = transcriber.transcribe(self.audio_path, progress_callback=self.update_progress)

            self.after(0, lambda: self.lbl_status.configure(text="Comparing text..."))
            results = compare(script_text, transcribed_words)

            self.after(0, lambda: self.display_results(results))

        except Exception as e:
            print(f"Error during processing: {e}")
            self.after(0, lambda e=e: messagebox.showerror("Error", f"An error occurred:\n{str(e)}"))
        finally:
            self.after(0, self.finish_processing)

    def display_results(self, results):
        self.lbl_status.configure(text="Done.")
        self.textbox.delete("1.0", "end")
        
        for item in results:
            word = item['word']
            t_type = item['type']
            start_time = item['start']
            
            if t_type == 'added':
                display_str = f" [{word}] "
                if start_time is not None:
                    # Provide a small timestamp annotation for added/spoken extra words
                    display_str = f" [{word} @ {start_time:.1f}s] "
                self.textbox.insert("end", display_str, "added")
            elif t_type == 'skipped':
                display_str = f" {{{word}}} "
                self.textbox.insert("end", display_str, "skipped")
            else:
                self.textbox.insert("end", f"{word} ", "match")

    def finish_processing(self):
        self.is_processing = False
        self.check_ready()

def run_app():
    # Make sure we run natively in High DPI awareness on Windows if applicable
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    app = ManuscriptApp()
    app.mainloop()
