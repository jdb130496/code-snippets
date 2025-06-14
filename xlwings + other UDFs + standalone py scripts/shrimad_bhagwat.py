import tkinter as tk
from tkinter import ttk
import time
import subprocess
import threading
from datetime import datetime, timedelta

class DualClockPlayer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dual Clock Player")
        self.root.geometry("600x150")
        self.root.configure(bg='black')
        
        # Variables
        self.start_time = None
        self.playback_speed = 0.65
        self.media_start_seconds = 0
        self.is_playing = False
        self.player_process = None
        self.stopped_real_time = 0  # Time where playback was stopped
        self.stopped_media_time = 0  # Media time where playback was stopped
        self.is_stopped = False  # Flag to track if we're in stopped state
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Input frame
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=10)
        
        ttk.Label(input_frame, text="Start Time (HH:MM:SS):").grid(row=0, column=0, padx=5)
        self.start_time_entry = ttk.Entry(input_frame, width=12)
        self.start_time_entry.insert(0, "01:20:17")
        self.start_time_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(input_frame, text="Speed:").grid(row=0, column=2, padx=5)
        self.speed_entry = ttk.Entry(input_frame, width=8)
        self.speed_entry.insert(0, "0.65")
        self.speed_entry.grid(row=0, column=3, padx=5)
        
        ttk.Button(input_frame, text="Play", command=self.start_playback).grid(row=0, column=4, padx=5)
        self.stop_button = ttk.Button(input_frame, text="Stop", command=self.stop_playback)
        self.stop_button.grid(row=0, column=5, padx=5)
        ttk.Button(input_frame, text="Reset", command=self.reset_playback).grid(row=0, column=6, padx=5)
        ttk.Button(input_frame, text="Exit", command=self.on_closing).grid(row=0, column=7, padx=5)
        
        # Clock display frame
        clock_frame = ttk.Frame(self.root)
        clock_frame.pack(pady=20)
        
        # Media time display
        self.media_time_label = tk.Label(clock_frame, text="Media Time: 00:00:00", 
                                       font=("Consolas", 16), fg="cyan", bg="black")
        self.media_time_label.pack()
        
        # Real-time display
        self.real_time_label = tk.Label(clock_frame, text="Real Time: 00:00:00", 
                                      font=("Consolas", 16), fg="lime", bg="black")
        self.real_time_label.pack()
        
        # Start clock update
        self.update_clocks()
        
    def time_to_seconds(self, time_str):
        """Convert HH:MM:SS to seconds"""
        try:
            h, m, s = map(int, time_str.split(':'))
            return h * 3600 + m * 60 + s
        except:
            return 0
            
    def seconds_to_time(self, seconds):
        """Convert seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
    def start_playback(self):
        if self.is_playing:
            return
            
        # Get parameters
        start_time_str = self.start_time_entry.get()
        
        # If resuming from stopped position, use stopped time
        if self.is_stopped:
            self.media_start_seconds = self.stopped_media_time
            # Calculate the position to start ffplay from
            ffplay_start_seconds = self.stopped_media_time
        else:
            self.media_start_seconds = self.time_to_seconds(start_time_str)
            ffplay_start_seconds = self.media_start_seconds
            
        self.playback_speed = float(self.speed_entry.get())
        
        # Start time tracking
        self.start_time = time.time()
        self.is_playing = True
        self.is_stopped = False
        
        # Start media player (your specific audio file)
        audio_file = r"D:\dump\Religious Books PDF And Audio\SHRIMAD BHAGWAT MAHA PURAN COMPLETE IN SANSKRIT PART 3   श्रीमद भगवत महा पुराण संस्कृत में.opus"
        
        # Convert seconds back to HH:MM:SS for ffplay
        ffplay_start_time = self.seconds_to_time(ffplay_start_seconds)
        
        # Using ffplay
        cmd = [
            "ffplay", 
            "-ss", ffplay_start_time,
            "-af", f"atempo={self.playback_speed}",
            "-nodisp",  # No video display
            "-autoexit",
            audio_file
        ]
        
        try:
            self.player_process = subprocess.Popen(cmd, 
                                                 stdout=subprocess.DEVNULL, 
                                                 stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            print("ffplay not found. Install FFmpeg or use different player.")
            self.is_playing = False
            
    def stop_playback(self):
        """Stop the media playback and preserve current position"""
        if self.is_playing and self.start_time:
            # Calculate current positions before stopping
            elapsed_real = time.time() - self.start_time
            elapsed_media = elapsed_real * self.playback_speed
            
            # Save stopped positions
            self.stopped_real_time = self.media_start_seconds + elapsed_real
            self.stopped_media_time = self.media_start_seconds + elapsed_media
            self.is_stopped = True
        
        self.is_playing = False
        if self.player_process:
            try:
                # Force terminate the process
                self.player_process.terminate()
                # Wait a bit for graceful termination
                try:
                    self.player_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    self.player_process.kill()
                    self.player_process.wait()
            except:
                pass
            finally:
                self.player_process = None
        print(f"Playback stopped at Media: {self.seconds_to_time(self.stopped_media_time)} | Real: {self.seconds_to_time(self.stopped_real_time)}")
        
    def reset_playback(self):
        """Reset to original start time"""
        self.stop_playback()
        self.is_stopped = False
        self.stopped_real_time = 0
        self.stopped_media_time = 0
        print("Reset to original start time")
        
    def on_closing(self):
        """Handle window closing - ensure audio stops"""
        print("Closing application...")
        self.stop_playback()
        self.root.quit()
        self.root.destroy()
            
    def update_clocks(self):
        if self.is_playing and self.start_time:
            # Calculate elapsed real time
            elapsed_real = time.time() - self.start_time
            
            # Calculate media time (affected by playback speed)
            elapsed_media = elapsed_real * self.playback_speed
            
            # Calculate display times
            real_time_seconds = self.media_start_seconds + elapsed_real
            media_time_seconds = self.media_start_seconds + elapsed_media
            
            # Update labels
            self.real_time_label.config(text=f"Real Time: {self.seconds_to_time(real_time_seconds)}")
            self.media_time_label.config(text=f"Media Time: {self.seconds_to_time(media_time_seconds)}")
        elif self.is_stopped:
            # Show stopped position
            self.real_time_label.config(text=f"Real Time: {self.seconds_to_time(self.stopped_real_time)} [STOPPED]")
            self.media_time_label.config(text=f"Media Time: {self.seconds_to_time(self.stopped_media_time)} [STOPPED]")
        else:
            # Show initial time when not playing and not stopped
            start_seconds = self.time_to_seconds(self.start_time_entry.get())
            time_str = self.seconds_to_time(start_seconds)
            self.real_time_label.config(text=f"Real Time: {time_str}")
            self.media_time_label.config(text=f"Media Time: {time_str}")
            
        # Schedule next update
        self.root.after(100, self.update_clocks)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = DualClockPlayer()
    app.run()
