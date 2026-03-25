#!/usr/bin/env python3
"""
Simple GUI wrapper for the video transcriber.

Opens a window where the user can:
1. Browse for a video/audio file
2. Pick language and domain options
3. Click "Transcribe" and see progress
4. Get .srt and .txt files in the same folder as the video

Uses tkinter (built into Python, no extra dependencies).
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


# Redirect print() to the GUI log area
class PrintRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.after(0, self._append, text)

    def _append(self, text):
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass


class TranscriberApp:
    SUPPORTED_EXTENSIONS = (
        ("Video/Audio files", "*.mp4 *.mkv *.avi *.mov *.webm *.m4v *.flv "
         "*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus *.wma"),
        ("MP4 files", "*.mp4"),
        ("All files", "*.*"),
    )

    MODELS = ["tiny", "base", "small", "medium", "large-v3"]

    LANGUAGES = [
        ("Auto-detect", None),
        ("Cantonese / Chinese (zh)", "zh"),
        ("English (en)", "en"),
        ("Japanese (ja)", "ja"),
        ("Korean (ko)", "ko"),
        ("French (fr)", "fr"),
        ("Spanish (es)", "es"),
        ("German (de)", "de"),
    ]

    DOMAINS = [
        ("None", None),
        ("I-Ching / Metaphysics", "iching"),
        ("Philosophy", "philosophy"),
        ("I-Ching + Philosophy", "iching_philosophy"),
        ("Geopolitics", "geopolitics"),
        ("Politics", "politics"),
        ("Finance", "finance"),
        ("Crypto", "crypto"),
        ("Technology", "technology"),
        ("AI", "ai"),
    ]

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Video Transcriber")
        self.root.geometry("620x520")
        self.root.resizable(True, True)

        self.transcribing = False

        self._build_ui()

    def _build_ui(self):
        # Main frame with padding
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # --- File selection ---
        file_frame = ttk.LabelFrame(main, text="Video / Audio File", padding=8)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_var)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        browse_btn = ttk.Button(file_frame, text="Browse...", command=self._browse_file)
        browse_btn.pack(side=tk.RIGHT)

        # --- Options ---
        opts_frame = ttk.LabelFrame(main, text="Options", padding=8)
        opts_frame.pack(fill=tk.X, pady=(0, 10))

        # Row 1: Model + Language
        row1 = ttk.Frame(opts_frame)
        row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(row1, text="Model:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value="base")
        model_combo = ttk.Combobox(
            row1, textvariable=self.model_var,
            values=self.MODELS, state="readonly", width=12,
        )
        model_combo.pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(row1, text="Language:").pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value="Auto-detect")
        lang_combo = ttk.Combobox(
            row1, textvariable=self.lang_var,
            values=[l[0] for l in self.LANGUAGES], state="readonly", width=22,
        )
        lang_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Row 2: Domain + Format
        row2 = ttk.Frame(opts_frame)
        row2.pack(fill=tk.X)

        ttk.Label(row2, text="Domain:").pack(side=tk.LEFT)
        self.domain_var = tk.StringVar(value="None")
        domain_combo = ttk.Combobox(
            row2, textvariable=self.domain_var,
            values=[d[0] for d in self.DOMAINS], state="readonly", width=20,
        )
        domain_combo.pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(row2, text="Output:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="both")
        format_combo = ttk.Combobox(
            row2, textvariable=self.format_var,
            values=["both", "srt", "txt"], state="readonly", width=8,
        )
        format_combo.pack(side=tk.LEFT, padx=(5, 0))

        # --- Transcribe button ---
        self.transcribe_btn = ttk.Button(
            main, text="Transcribe", command=self._start_transcribe,
        )
        self.transcribe_btn.pack(fill=tk.X, pady=(0, 10), ipady=6)

        # --- Log output ---
        log_frame = ttk.LabelFrame(main, text="Progress", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_frame, height=12, wrap=tk.WORD,
            font=("Consolas", 9), state="disabled",
            bg="#1e1e1e", fg="#d4d4d4",
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select video or audio file",
            filetypes=self.SUPPORTED_EXTENSIONS,
        )
        if path:
            self.file_var.set(path)

    def _get_language_code(self) -> str | None:
        label = self.lang_var.get()
        for name, code in self.LANGUAGES:
            if name == label:
                return code
        return None

    def _get_domain_code(self) -> str | None:
        label = self.domain_var.get()
        for name, code in self.DOMAINS:
            if name == label:
                return code
        return None

    def _log(self, msg: str):
        self.log_text.after(0, self._append_log, msg)

    def _append_log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _start_transcribe(self):
        filepath = self.file_var.get().strip()
        if not filepath:
            messagebox.showwarning("No file selected", "Please select a video or audio file first.")
            return
        if not os.path.isfile(filepath):
            messagebox.showerror("File not found", f"File does not exist:\n{filepath}")
            return
        if self.transcribing:
            return

        self.transcribing = True
        self.transcribe_btn.configure(state="disabled", text="Transcribing...")

        # Clear log
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

        # Run transcription in a background thread so UI doesn't freeze
        thread = threading.Thread(target=self._run_transcription, daemon=True)
        thread.start()

    def _run_transcription(self):
        # Redirect stdout/stderr to the log area
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirector = PrintRedirector(self.log_text)
        sys.stdout = redirector
        sys.stderr = redirector

        try:
            filepath = self.file_var.get().strip()
            model = self.model_var.get()
            language = self._get_language_code()
            domain = self._get_domain_code()
            fmt = self.format_var.get()

            from transcription import check_ffmpeg, extract_audio_from_video, transcribe_with_timestamps
            from srt_formatter import write_srt, write_txt, generate_output_path

            if not check_ffmpeg():
                self._log("ERROR: ffmpeg not found!")
                self._log("Install it: winget install ffmpeg")
                self._finish_with_error()
                return

            # Extract audio if it's a video
            temp_audio = None
            ext = os.path.splitext(filepath)[1].lower()
            video_exts = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".flv", ".3gp"}
            audio_exts = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma"}

            if ext in video_exts:
                audio_path = extract_audio_from_video(filepath)
                temp_audio = audio_path
            elif ext in audio_exts:
                audio_path = filepath
            else:
                try:
                    audio_path = extract_audio_from_video(filepath)
                    temp_audio = audio_path
                except RuntimeError:
                    audio_path = filepath

            # Transcribe
            import time
            start_time = time.time()

            result = transcribe_with_timestamps(
                audio_path=audio_path,
                model_size=model,
                language=language,
                domain_category=domain,
            )

            elapsed = time.time() - start_time
            segments = result["segments"]

            if not segments:
                self._log("\nNo speech detected in the audio.")
                self._finish_with_error()
                return

            # Write output files
            output_dir = os.path.dirname(filepath)
            output_files = []

            if fmt in ("srt", "both"):
                srt_path = generate_output_path(filepath, output_dir, ".srt")
                write_srt(segments, srt_path)
                output_files.append(srt_path)

            if fmt in ("txt", "both"):
                txt_path = generate_output_path(filepath, output_dir, ".txt")
                write_txt(segments, txt_path)
                output_files.append(txt_path)

            # Summary
            duration = result["duration"]
            self._log("")
            self._log("=" * 50)
            self._log(f"  Done! ({elapsed:.0f}s)")
            self._log(f"  Language: {result['language']}")
            self._log(f"  Duration: {duration:.0f}s ({duration/60:.1f} min)")
            self._log(f"  Segments: {len(segments)}")
            for f in output_files:
                self._log(f"  Output: {f}")
            self._log("=" * 50)

            # Clean up temp audio
            if temp_audio and os.path.exists(temp_audio):
                os.unlink(temp_audio)

            # Show success in UI thread
            self.root.after(0, lambda: messagebox.showinfo(
                "Done",
                f"Transcription complete!\n\n" + "\n".join(output_files),
            ))

        except Exception as e:
            self._log(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.root.after(0, self._reset_button)

    def _finish_with_error(self):
        self.root.after(0, self._reset_button)

    def _reset_button(self):
        self.transcribing = False
        self.transcribe_btn.configure(state="normal", text="Transcribe")


def main():
    root = tk.Tk()

    # Set a nicer theme if available
    style = ttk.Style()
    available_themes = style.theme_names()
    for theme in ["clam", "vista", "xpnative", "winnative"]:
        if theme in available_themes:
            style.theme_use(theme)
            break

    app = TranscriberApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
