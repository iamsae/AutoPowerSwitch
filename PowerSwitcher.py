#!/usr/bin/env python3
"""
PowerSwitcher Universal - Python Edition
Intelligent Windows Power Management with Modern GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import time
import os
import sys
import json
import winreg
from pathlib import Path
import psutil
import pystray
from PIL import Image, ImageDraw
import ctypes
from ctypes import wintypes

class PowerManager:
    """Handles Windows power plan management"""
    
    def __init__(self):
        self.gaming_plan = None
        self.casual_plan = None
        self.detect_power_plans()
    
    def detect_power_plans(self):
        """Detect available power plans"""
        try:
            result = subprocess.run(['powercfg', '/list'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if 'GUID:' in line:
                    if any(keyword in line.lower() for keyword in ['gaming', 'performance', 'high']):
                        self.gaming_plan = line.split(':')[1].split('(')[0].strip()
                    elif any(keyword in line.lower() for keyword in ['casual', 'balanced', 'power saver']):
                        self.casual_plan = line.split(':')[1].split('(')[0].strip()
            
            # Fallback GUIDs if detection fails
            if not self.gaming_plan:
                self.gaming_plan = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
            if not self.casual_plan:
                self.casual_plan = "381b4222-f694-41f0-9685-ff5bb260df2e"
                
        except Exception:
            # Use default GUIDs
            self.gaming_plan = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
            self.casual_plan = "381b4222-f694-41f0-9685-ff5bb260df2e"
    
    def switch_to_gaming(self):
        """Switch to gaming/performance power plan"""
        try:
            subprocess.run(['powercfg', '/setactive', self.gaming_plan], check=False)
            return True
        except Exception:
            return False
    
    def switch_to_casual(self):
        """Switch to casual/balanced power plan"""
        try:
            subprocess.run(['powercfg', '/setactive', self.casual_plan], check=False)
            return True
        except Exception:
            return False
    
    def get_current_plan(self):
        """Get current active power plan name"""
        try:
            result = subprocess.run(['powercfg', '/getactivescheme'], capture_output=True, text=True)
            if 'gaming' in result.stdout.lower() or 'performance' in result.stdout.lower():
                return "Gaming Mode"
            elif 'balanced' in result.stdout.lower() or 'casual' in result.stdout.lower():
                return "Balanced Mode"
            else:
                return "Unknown Mode"
        except Exception:
            return "Unknown Mode"

class GameDetector:
    """Handles game process detection"""
    
    def __init__(self):
        self.game_list_path = Path("C:/PowerSwitcher/GameList.txt")
        self.games = []
        self.load_games()
    
    def load_games(self):
        """Load game list from file"""
        try:
            if self.game_list_path.exists():
                with open(self.game_list_path, 'r', encoding='utf-8') as f:
                    self.games = [line.strip() for line in f if line.strip()]
            else:
                # Create default game list
                default_games = [
                    "Blur.exe", "WRCG.exe", "ForzaHorizon4.exe", "eFootball.exe",
                    "bf4.exe", "Client-Win64-Shipping.exe", "SparkingZERO.exe",
                    "TslGame.exe", "DetroitBecomeHuman.exe", "bf1.exe", "osu!.exe",
                    "RidersRepublic_BE.exe", "steam.exe", "EpicGamesLauncher.exe"
                ]
                self.games = default_games
                self.save_games()
        except Exception:
            self.games = ["steam.exe", "EpicGamesLauncher.exe"]
    
    def save_games(self):
        """Save game list to file"""
        try:
            self.game_list_path.parent.mkdir(exist_ok=True)
            with open(self.game_list_path, 'w', encoding='utf-8') as f:
                for game in self.games:
                    f.write(f"{game}\n")
        except Exception:
            pass
    
    def is_game_running(self):
        """Check if any game is currently running"""
        try:
            running_processes = [p.name() for p in psutil.process_iter(['name'])]
            for game in self.games:
                if game.lower() in [p.lower() for p in running_processes]:
                    return True, game
            return False, None
        except Exception:
            return False, None

class ThemeManager:
    """Handles Windows theme detection"""
    
    def __init__(self):
        self.is_dark_theme = self.detect_dark_theme()
        self.accent_color = self.get_accent_color()
    
    def detect_dark_theme(self):
        """Detect if Windows is using dark theme"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return value == 0
        except Exception:
            return False
    
    def get_accent_color(self):
        """Get Windows accent color"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM")
            value, _ = winreg.QueryValueEx(key, "AccentColor")
            winreg.CloseKey(key)
            # Convert DWORD to hex color
            color = f"#{value:06x}"[-6:]
            return f"#{color[4:6]}{color[2:4]}{color[0:2]}"
        except Exception:
            return "#0078D7"
    
    def get_colors(self):
        """Get theme-appropriate colors"""
        if self.is_dark_theme:
            return {
                'bg': '#2D2D30',
                'fg': '#FFFFFF',
                'card_bg': '#3E3E42',
                'secondary': '#CCCCCC',
                'accent': self.accent_color,
                'border': '#555555'
            }
        else:
            return {
                'bg': '#FFFFFF',
                'fg': '#000000',
                'card_bg': '#F0F0F0',
                'secondary': '#666666',
                'accent': self.accent_color,
                'border': '#E1E1E1'
            }

class PowerSwitcherGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.power_manager = PowerManager()
        self.game_detector = GameDetector()
        self.theme_manager = ThemeManager()
        
        self.monitoring = True
        self.monitor_thread = None
        self.tray_icon = None
        
        self.setup_window()
        self.create_widgets()
        self.start_monitoring()
        self.create_tray_icon()
    
    def setup_window(self):
        """Configure main window"""
        self.root.title("PowerSwitcher Universal")
        self.root.geometry("340x260")
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (340 // 2)
        y = (self.root.winfo_screenheight() // 2) - (260 // 2)
        self.root.geometry(f"340x260+{x}+{y}")
        
        # Apply theme colors
        colors = self.theme_manager.get_colors()
        self.root.configure(bg=colors['bg'])
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
    
    def create_widgets(self):
        """Create and layout GUI widgets"""
        colors = self.theme_manager.get_colors()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=16, pady=16)
        
        # Status card
        status_frame = tk.Frame(main_frame, bg=colors['card_bg'], relief='solid', bd=1)
        status_frame.pack(fill='x', pady=(0, 8))
        
        status_inner = tk.Frame(status_frame, bg=colors['card_bg'])
        status_inner.pack(fill='x', padx=12, pady=12)
        
        # Status text (left side)
        status_text_frame = tk.Frame(status_inner, bg=colors['card_bg'])
        status_text_frame.pack(side='left', fill='x', expand=True)
        
        self.status_label = tk.Label(status_text_frame, text="Monitoring Active", 
                                   font=('Segoe UI', 11, 'bold'), 
                                   bg=colors['card_bg'], fg=colors['fg'])
        self.status_label.pack(anchor='w')
        
        self.detail_label = tk.Label(status_text_frame, text="Intelligent power switching", 
                                   font=('Segoe UI', 8), 
                                   bg=colors['card_bg'], fg=colors['secondary'])
        self.detail_label.pack(anchor='w')
        
        # Toggle switch (right side)
        toggle_frame = tk.Frame(status_inner, bg=colors['card_bg'])
        toggle_frame.pack(side='right')
        
        self.toggle_button = tk.Button(toggle_frame, text="ON", width=6, height=1,
                                     font=('Segoe UI', 8, 'bold'),
                                     bg=colors['accent'], fg='white',
                                     relief='flat', cursor='hand2',
                                     command=self.toggle_monitoring)
        self.toggle_button.pack()
        
        # Game detection card
        game_frame = tk.Frame(main_frame, bg=colors['card_bg'], relief='solid', bd=1)
        game_frame.pack(fill='x', pady=(0, 12))
        
        game_inner = tk.Frame(game_frame, bg=colors['card_bg'])
        game_inner.pack(fill='x', padx=12, pady=12)
        
        game_title = tk.Label(game_inner, text="Game Detection", 
                            font=('Segoe UI', 11, 'bold'), 
                            bg=colors['card_bg'], fg=colors['fg'])
        game_title.pack(anchor='w', pady=(0, 6))
        
        self.game_label = tk.Label(game_inner, text="No games detected", 
                                 font=('Segoe UI', 9), 
                                 bg=colors['card_bg'], fg=colors['secondary'])
        self.game_label.pack(anchor='w', pady=(0, 3))
        
        self.power_label = tk.Label(game_inner, text="Current: Balanced mode", 
                                  font=('Segoe UI', 8), 
                                  bg=colors['card_bg'], fg=colors['secondary'])
        self.power_label.pack(anchor='w')
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=colors['bg'])
        button_frame.pack(fill='x')
        
        self.edit_button = tk.Button(button_frame, text="Edit Games", 
                                   font=('Segoe UI', 9),
                                   bg=colors['card_bg'], fg=colors['fg'],
                                   relief='solid', bd=1, cursor='hand2',
                                   command=self.edit_games)
        self.edit_button.pack(side='left', fill='x', expand=True, padx=(0, 3))
        
        self.exit_button = tk.Button(button_frame, text="Exit", 
                                   font=('Segoe UI', 9),
                                   bg=colors['card_bg'], fg=colors['fg'],
                                   relief='solid', bd=1, cursor='hand2',
                                   command=self.exit_app)
        self.exit_button.pack(side='right', fill='x', expand=True, padx=(3, 0))
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        self.monitoring = not self.monitoring
        colors = self.theme_manager.get_colors()
        
        if self.monitoring:
            self.toggle_button.configure(text="ON", bg=colors['accent'])
            self.status_label.configure(text="Monitoring Active")
            self.detail_label.configure(text="Intelligent power switching")
        else:
            self.toggle_button.configure(text="OFF", bg='#CCCCCC')
            self.status_label.configure(text="Monitoring Paused")
            self.detail_label.configure(text="Click to resume")
    
    def edit_games(self):
        """Open game list for editing"""
        try:
            os.startfile(str(self.game_detector.game_list_path))
        except Exception:
            messagebox.showerror("Error", "Could not open game list file")
    
    def exit_app(self):
        """Exit application"""
        if messagebox.askyesno("Exit", "Exit PowerSwitcher?"):
            self.monitoring = False
            if self.tray_icon:
                self.tray_icon.stop()
            self.root.quit()
    
    def hide_window(self):
        """Hide window to system tray"""
        self.root.withdraw()
        self.show_notification("PowerSwitcher", "Minimized to system tray")
    
    def show_window(self):
        """Show window from system tray"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def monitor_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                if self.monitoring:
                    self.update_status()
                time.sleep(5)  # Check every 5 seconds
            except Exception:
                break
    
    def update_status(self):
        """Update status information"""
        try:
            # Check for running games
            game_running, game_name = self.game_detector.is_game_running()
            current_plan = self.power_manager.get_current_plan()
            
            # Update power plan based on game status
            if game_running:
                if "balanced" in current_plan.lower():
                    self.power_manager.switch_to_gaming()
                    self.show_notification("PowerSwitcher", f"Switched to Gaming Mode for {game_name}")
                
                self.root.after(0, lambda: self.game_label.configure(text=f"Game detected: {game_name}"))
            else:
                if "gaming" in current_plan.lower():
                    self.power_manager.switch_to_casual()
                    self.show_notification("PowerSwitcher", "Switched to Balanced Mode")
                
                self.root.after(0, lambda: self.game_label.configure(text="No games detected"))
            
            # Update current plan display
            updated_plan = self.power_manager.get_current_plan()
            self.root.after(0, lambda: self.power_label.configure(text=f"Current: {updated_plan}"))
            
        except Exception:
            pass
    
    def create_tray_icon(self):
        """Create system tray icon"""
        try:
            # Create a simple icon
            image = Image.new('RGB', (64, 64), color='#0078D7')
            draw = ImageDraw.Draw(image)
            draw.text((20, 20), "⚡", fill='white', font_size=24)
            
            menu = pystray.Menu(
                pystray.MenuItem("Show PowerSwitcher", self.show_window),
                pystray.MenuItem("Exit", self.exit_app)
            )
            
            self.tray_icon = pystray.Icon("PowerSwitcher", image, "PowerSwitcher Universal", menu)
            
            # Start tray icon in separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
        except Exception:
            pass  # Tray icon is optional
    
    def show_notification(self, title, message):
        """Show Windows notification"""
        try:
            if self.tray_icon:
                self.tray_icon.notify(message, title)
        except Exception:
            pass
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        # Ensure we're running as administrator
        if not ctypes.windll.shell32.IsUserAnAdmin():
            messagebox.showerror("Administrator Required", 
                               "PowerSwitcher requires administrator privileges to manage power plans.\n"
                               "Please run as administrator.")
            return
        
        # Create PowerSwitcher directory
        Path("C:/PowerSwitcher").mkdir(exist_ok=True)
        
        # Start GUI
        app = PowerSwitcherGUI()
        app.run()
        
    except Exception as e:
        messagebox.showerror("PowerSwitcher Error", f"Failed to start PowerSwitcher:\n{str(e)}")

if __name__ == "__main__":
    main()
