#!/usr/bin/env python3
"""
Simple GUI wrapper for the video transcriber and YouTube compressor.

Opens a window where the user can:
1. Browse for a video/audio file
2. Pick language and domain options
3. Click "Transcribe" and see progress
4. Get .srt and .txt files in the same folder as the video
5. Compress video for YouTube upload (H.264, optimized settings)

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

    COMPRESS_PRESETS = [
        ("Max compression (CRF 28)", "max_compression"),
        ("Balanced (CRF 23)", "balanced"),
        ("High quality (CRF 18)", "high_quality"),
    ]

    PRIVACY_OPTIONS = ["unlisted", "private", "public"]

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Video Transcriber")
        self.root.geometry("620x760")
        self.root.resizable(True, True)

        self.transcribing = False
        self.compressing = False
        self.uploading = False
        self.signing_in = False

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
        self.transcribe_btn.pack(fill=tk.X, pady=(0, 5), ipady=6)

        # --- YouTube compression ---
        compress_frame = ttk.Frame(main)
        compress_frame.pack(fill=tk.X, pady=(0, 10))

        self.compress_btn = ttk.Button(
            compress_frame, text="Compress for YouTube",
            command=self._start_compress,
        )
        self.compress_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))

        self.compress_var = tk.StringVar(value="Max compression (CRF 28)")
        compress_combo = ttk.Combobox(
            compress_frame, textvariable=self.compress_var,
            values=[p[0] for p in self.COMPRESS_PRESETS],
            state="readonly", width=25,
        )
        compress_combo.pack(side=tk.RIGHT)

        # --- YouTube upload ---
        upload_frame = ttk.LabelFrame(main, text="YouTube Upload", padding=8)
        upload_frame.pack(fill=tk.X, pady=(0, 10))

        # Row: Title entry
        title_row = ttk.Frame(upload_frame)
        title_row.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(title_row, text="Title:").pack(side=tk.LEFT)
        self.yt_title_var = tk.StringVar()
        title_entry = ttk.Entry(title_row, textvariable=self.yt_title_var)
        title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Row: Privacy + buttons
        upload_row = ttk.Frame(upload_frame)
        upload_row.pack(fill=tk.X)
        ttk.Label(upload_row, text="Privacy:").pack(side=tk.LEFT)
        self.yt_privacy_var = tk.StringVar(value="unlisted")
        privacy_combo = ttk.Combobox(
            upload_row, textvariable=self.yt_privacy_var,
            values=self.PRIVACY_OPTIONS, state="readonly", width=10,
        )
        privacy_combo.pack(side=tk.LEFT, padx=(5, 10))

        self.signin_btn = ttk.Button(
            upload_row, text="Sign in to YouTube",
            command=self._start_yt_signin,
        )
        self.signin_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.upload_btn = ttk.Button(
            upload_row, text="Upload to YouTube",
            command=self._start_upload,
        )
        self.upload_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Auto-fill title when file is picked
        self.file_var.trace_add("write", self._autofill_title)

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

    def _get_compress_preset(self) -> str:
        label = self.compress_var.get()
        for name, code in self.COMPRESS_PRESETS:
            if name == label:
                return code
        return "max_compression"

    def _start_compress(self):
        filepath = self.file_var.get().strip()
        if not filepath:
            messagebox.showwarning("No file selected", "Please select a video file first.")
            return
        if not os.path.isfile(filepath):
            messagebox.showerror("File not found", f"File does not exist:\n{filepath}")
            return
        if self.compressing or self.transcribing:
            return

        ext = os.path.splitext(filepath)[1].lower()
        video_exts = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".flv", ".3gp"}
        if ext not in video_exts:
            messagebox.showwarning("Not a video", "Compression is for video files only.")
            return

        self.compressing = True
        self.compress_btn.configure(state="disabled", text="Compressing...")
        self.transcribe_btn.configure(state="disabled")

        # Clear log
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

        thread = threading.Thread(target=self._run_compress, daemon=True)
        thread.start()

    def _run_compress(self):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirector = PrintRedirector(self.log_text)
        sys.stdout = redirector
        sys.stderr = redirector

        try:
            filepath = self.file_var.get().strip()
            quality = self._get_compress_preset()

            from transcription import check_ffmpeg
            from compress import compress_for_youtube

            if not check_ffmpeg():
                self._log("ERROR: ffmpeg not found!")
                self._log("Install it: winget install ffmpeg")
                self._finish_compress_error()
                return

            import time
            start_time = time.time()

            result = compress_for_youtube(filepath, quality=quality)

            elapsed = time.time() - start_time
            self._log("")
            self._log("=" * 50)
            self._log(f"  Done! ({elapsed:.0f}s)")
            self._log(f"  Compression: {result['ratio']:.1f}x smaller")
            self._log(f"  Output: {result['output_path']}")
            self._log("=" * 50)

            self.root.after(0, lambda: messagebox.showinfo(
                "Done",
                f"Compression complete!\n\n"
                f"{result['ratio']:.1f}x smaller\n"
                f"{result['output_path']}",
            ))

        except Exception as e:
            self._log(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.root.after(0, self._reset_compress_button)

    def _finish_compress_error(self):
        self.root.after(0, self._reset_compress_button)

    def _reset_compress_button(self):
        self.compressing = False
        self.compress_btn.configure(state="normal", text="Compress for YouTube")
        self.transcribe_btn.configure(state="normal")

    def _finish_with_error(self):
        self.root.after(0, self._reset_button)

    def _reset_button(self):
        self.transcribing = False
        self.transcribe_btn.configure(state="normal", text="Transcribe")

    # --- YouTube upload / auth ---

    def _autofill_title(self, *_args):
        """Populate the title field from the selected filename (without extension)."""
        path = self.file_var.get().strip()
        if not path:
            return
        base = os.path.splitext(os.path.basename(path))[0]
        # Don't overwrite a title the user has typed
        if not self.yt_title_var.get().strip():
            self.yt_title_var.set(base)

    def _busy(self) -> bool:
        return self.transcribing or self.compressing or self.uploading or self.signing_in

    def _start_yt_signin(self):
        if self._busy():
            return
        self.signing_in = True
        self.signin_btn.configure(state="disabled", text="Signing in...")
        self.upload_btn.configure(state="disabled")
        thread = threading.Thread(target=self._run_yt_signin, daemon=True)
        thread.start()

    def _run_yt_signin(self):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirector = PrintRedirector(self.log_text)
        sys.stdout = redirector
        sys.stderr = redirector
        try:
            from yt_auth import run_auth_flow
            run_auth_flow(log=self._log)
            self.root.after(0, lambda: messagebox.showinfo(
                "Signed in", "YouTube sign-in complete. You can now upload."
            ))
        except Exception as e:
            self._log(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: messagebox.showerror("Sign-in failed", str(e)))
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.root.after(0, self._reset_signin_button)

    def _reset_signin_button(self):
        self.signing_in = False
        self.signin_btn.configure(state="normal", text="Sign in to YouTube")
        self.upload_btn.configure(state="normal")

    def _start_upload(self):
        filepath = self.file_var.get().strip()
        if not filepath:
            messagebox.showwarning("No file selected", "Please select a video file first.")
            return
        if not os.path.isfile(filepath):
            messagebox.showerror("File not found", f"File does not exist:\n{filepath}")
            return
        if self._busy():
            return

        ext = os.path.splitext(filepath)[1].lower()
        video_exts = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".flv", ".3gp"}
        if ext not in video_exts:
            messagebox.showwarning("Not a video", "Upload is for video files only.")
            return

        title = self.yt_title_var.get().strip()
        if not title:
            messagebox.showwarning("No title", "Please enter a title for the video.")
            return

        self.uploading = True
        self.upload_btn.configure(state="disabled", text="Uploading...")
        self.transcribe_btn.configure(state="disabled")
        self.compress_btn.configure(state="disabled")
        self.signin_btn.configure(state="disabled")

        thread = threading.Thread(target=self._run_upload, daemon=True)
        thread.start()

    def _run_upload(self):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirector = PrintRedirector(self.log_text)
        sys.stdout = redirector
        sys.stderr = redirector
        try:
            filepath = self.file_var.get().strip()
            title = self.yt_title_var.get().strip()
            privacy = self.yt_privacy_var.get()

            from yt_upload import upload_video, format_size

            size = os.path.getsize(filepath)
            self._log(f"File:    {filepath}")
            self._log(f"Size:    {format_size(size)}")
            self._log(f"Title:   {title}")
            self._log(f"Privacy: {privacy}")
            self._log("")

            last_pct = {"value": -1}

            def on_progress(sent: int, total: int):
                pct = int(sent * 100 / total) if total else 0
                if pct != last_pct["value"]:
                    last_pct["value"] = pct
                    self._log(f"  {pct}%  ({format_size(sent)} / {format_size(total)})")

            import time
            start = time.time()
            result = upload_video(
                filepath,
                title=title,
                privacy=privacy,
                on_progress=on_progress,
                log=self._log,
            )
            elapsed = time.time() - start

            url = result.get("url") or "(no URL returned)"
            self._log("")
            self._log("=" * 50)
            self._log(f"  Done! ({elapsed:.0f}s)")
            self._log(f"  Video: {url}")
            self._log("=" * 50)

            self.root.after(0, lambda: messagebox.showinfo(
                "Upload complete",
                f"Video uploaded as {privacy}.\n\n{url}",
            ))
        except Exception as e:
            self._log(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: messagebox.showerror("Upload failed", str(e)))
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.root.after(0, self._reset_upload_button)

    def _reset_upload_button(self):
        self.uploading = False
        self.upload_btn.configure(state="normal", text="Upload to YouTube")
        self.transcribe_btn.configure(state="normal")
        self.compress_btn.configure(state="normal")
        self.signin_btn.configure(state="normal")


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
