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
        self.discrepancy_tags = {}

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
        # Input Frame for Manuscript and Audio
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(pady=10, padx=10, fill="x")
        
        # Manuscript Paste / Upload Section
        self.ms_lbl = ctk.CTkLabel(self.top_frame, text="Paste Manuscript Text or Upload File:", font=("Arial", 14, "bold"))
        self.ms_lbl.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.btn_manuscript = ctk.CTkButton(self.top_frame, text="Upload File (TXT/PDF)", command=self.select_manuscript, width=150)
        self.btn_manuscript.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # We use a CTkTextbox for input
        self.ms_textbox = ctk.CTkTextbox(self.top_frame, height=120, wrap="word")
        self.ms_textbox.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.top_frame.rowconfigure(1, weight=1)
        self.top_frame.columnconfigure(0, weight=1)

        # Bind key events to check_ready so we detect typing/pasting
        self.ms_textbox.bind("<KeyRelease>", self.check_ready)

        # Audio Selector
        self.audio_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.audio_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.audio_frame.columnconfigure(0, weight=1)
        
        self.lbl_audio = ctk.CTkLabel(self.audio_frame, text="No Audio Selected.")
        self.lbl_audio.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.btn_audio = ctk.CTkButton(self.audio_frame, text="Select Audio (WAV/MP3)", command=self.select_audio, width=150)
        self.btn_audio.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        # Options Frame
        self.options_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.options_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 5))
        self.options_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self.lbl_model = ctk.CTkLabel(self.options_frame, text="Model Size:")
        self.lbl_model.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.opt_model = ctk.CTkOptionMenu(self.options_frame, values=["tiny", "base", "small", "medium"])
        self.opt_model.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.opt_model.set("base") # default to base

        self.lbl_device = ctk.CTkLabel(self.options_frame, text="Compute Device:")
        self.lbl_device.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.opt_device = ctk.CTkOptionMenu(self.options_frame, values=["auto", "cpu", "cuda"])
        self.opt_device.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.opt_device.set("auto")

        # Process Button & Progress
        self.btn_process = ctk.CTkButton(self.top_frame, text="Start Match", command=self.start_processing, state="disabled")
        self.btn_process.grid(row=4, column=0, columnspan=2, pady=10)

        self.progress = ctk.CTkProgressBar(self.top_frame)
        self.progress.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.top_frame, text="")
        self.lbl_status.grid(row=6, column=0, columnspan=2)

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
        self.textbox.tag_config("ignored", foreground="#8a8a8a", overstrike=True) # Dimmed / Strikethrough for false positives
        
        # Bindings for interactive toggling
        self.textbox.tag_bind("clickable", "<Button-1>", self.on_discrepancy_click)
        self.textbox.tag_bind("clickable", "<Enter>", lambda e: self.textbox.configure(cursor="hand2"))
        self.textbox.tag_bind("clickable", "<Leave>", lambda e: self.textbox.configure(cursor=""))

    def on_discrepancy_click(self, event):
        # Check where the user clicked
        index = self.textbox.index(f"@{event.x},{event.y}")
        tags = self.textbox.tag_names(index)
        
        chunk_tag = None
        for t in tags:
            if t.startswith("chunk_"):
                chunk_tag = t
                break
                
        if chunk_tag:
            self.textbox.configure(state="normal")
            first = f"{chunk_tag}.first"
            last = f"{chunk_tag}.last"
            
            if "ignored" in tags:
                # Revert to original
                self.textbox.tag_remove("ignored", first, last)
                orig_tag = self.discrepancy_tags.get(chunk_tag)
                if orig_tag:
                    self.textbox.tag_add(orig_tag, first, last)
            else:
                # Dim it (false positive)
                if "added" in tags:
                    self.textbox.tag_remove("added", first, last)
                if "skipped" in tags:
                    self.textbox.tag_remove("skipped", first, last)
                self.textbox.tag_add("ignored", first, last)
                
            self.textbox.configure(state="disabled")

    def select_manuscript(self):
        path = filedialog.askopenfilename(
            title="Select Manuscript",
            filetypes=[("Text/PDF Files", "*.txt *.pdf"), ("All Files", "*.*")]
        )
        if path:
            text = parse_manuscript(path)
            if not text.strip():
                messagebox.showerror("Error", f"Could not extract text from {os.path.basename(path)}")
                return
            self.ms_textbox.delete("1.0", "end")
            self.ms_textbox.insert("1.0", text)
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

    def check_ready(self, event=None):
        has_text = len(self.ms_textbox.get("1.0", "end-1c").strip()) > 0
        if has_text and self.audio_path and not self.is_processing:
            self.btn_process.configure(state="normal")
        else:
            self.btn_process.configure(state="disabled")

    def start_processing(self):
        script_text = self.ms_textbox.get("1.0", "end-1c").strip()
        if not script_text:
            return
            
        self.is_processing = True
        self.btn_process.configure(state="disabled")
        self.progress.set(0)
        self.lbl_status.configure(text="Preparing to transcribe...")
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")

        model_size = self.opt_model.get()
        device = self.opt_device.get()

        # Run in thread to not freeze UI, passing the text safely
        threading.Thread(target=self.process_task, args=(script_text, model_size, device), daemon=True).start()

    def update_progress(self, val):
        self.after(0, lambda: self.progress.set(val))
        self.after(0, lambda: self.lbl_status.configure(text=f"Transcribing... {int(val*100)}%"))

    def process_task(self, script_text, model_size, device):
        try:
            self.after(0, lambda: self.lbl_status.configure(text="Loading Whisper model... (This may take a moment window)"))
            transcriber = Transcriber(model_size=model_size, device=device)
            
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
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.discrepancy_tags.clear()
        chunk_idx = 0
        current_tag = None
        current_text = []

        def flush():
            nonlocal chunk_idx, current_tag
            if current_text:
                if current_tag in ('added', 'skipped'):
                    chunk_tag = f"chunk_{chunk_idx}"
                    self.discrepancy_tags[chunk_tag] = current_tag
                    # Apply multiple tags
                    self.textbox.insert("end", "".join(current_text), (current_tag, chunk_tag, "clickable"))
                    chunk_idx += 1
                else:
                    self.textbox.insert("end", "".join(current_text), current_tag)
                current_text.clear()

        for item in results:
            word = item['word']
            t_type = item['type']
            start_time = item['start']
            
            if t_type == 'added':
                tag = "added"
                display_str = f" [{word}] "
                if start_time is not None:
                    # Provide a small timestamp annotation for added/spoken extra words
                    hrs = int(start_time // 3600)
                    mins = int((start_time % 3600) // 60)
                    secs = int(start_time % 60)
                    ts_str = f"{hrs}:{mins:02d}:{secs:02d}"
                    display_str = f" [{word} @ {ts_str}] "
            elif t_type == 'skipped':
                tag = "skipped"
                display_str = f" {{{word}}} "
                if start_time is not None:
                    hrs = int(start_time // 3600)
                    mins = int((start_time % 3600) // 60)
                    secs = int(start_time % 60)
                    ts_str = f"{hrs}:{mins:02d}:{secs:02d}"
                    display_str = f" {{{word} @ {ts_str}}} "
            else:
                tag = "match"
                display_str = f"{word} "
                
            if tag != current_tag:
                flush()
                current_tag = tag
            
            current_text.append(display_str)
            
        flush()
        
        # Disable editing so scrolling and performance remain smooth
        self.textbox.configure(state="disabled")

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
