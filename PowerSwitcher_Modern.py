#!/usr/bin/env python3
"""
PowerSwitcher Universal - Modern Windows 11 Edition
Ultra-modern GUI with acrylic effects and native Windows theming
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
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
from PIL import Image, ImageDraw, ImageFilter
import ctypes
from ctypes import wintypes
import win32api
import win32con
import win32gui

# Set appearance mode and color theme
ctk.set_appearance_mode("system")  # Modes: system, light, dark
ctk.set_default_color_theme("blue")  # Themes: blue, dark-blue, green

class WindowsThemeManager:
    """Advanced Windows theme detection and integration"""
    
    def __init__(self):
        self.is_dark = self.detect_dark_theme()
        self.accent_color = self.get_accent_color()
        self.transparency_enabled = self.check_transparency()
        
    def detect_dark_theme(self):
        """Detect Windows dark theme"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return value == 0
        except:
            return False
    
    def get_accent_color(self):
        """Get Windows accent color"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM")
            value, _ = winreg.QueryValueEx(key, "AccentColor")
            winreg.CloseKey(key)
            # Convert DWORD to RGB
            r = (value >> 0) & 0xFF
            g = (value >> 8) & 0xFF  
            b = (value >> 16) & 0xFF
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#0078D4"
    
    def check_transparency(self):
        """Check if transparency effects are enabled"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "EnableTransparency")
            winreg.CloseKey(key)
            return value == 1
        except:
            return True

class AcrylicWindow:
    """Implements Windows 11 acrylic blur effects"""
    
    @staticmethod
    def enable_blur(hwnd):
        """Enable acrylic blur for window"""
        try:
            # Windows 11 acrylic effect
            accent_policy = ctypes.Structure._fields_ = [
                ("AccentState", ctypes.c_uint),
                ("AccentFlags", ctypes.c_uint), 
                ("GradientColor", ctypes.c_uint),
                ("AnimationId", ctypes.c_uint)
            ]
            
            class ACCENT_POLICY(ctypes.Structure):
                _fields_ = accent_policy
            
            class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
                _fields_ = [
                    ("Attribute", ctypes.c_int),
                    ("Data", ctypes.POINTER(ACCENT_POLICY)),
                    ("SizeOfData", ctypes.c_size_t)
                ]
            
            # Acrylic blur effect
            accent = ACCENT_POLICY()
            accent.AccentState = 4  # ACCENT_ENABLE_ACRYLICBLURBEHIND
            accent.AccentFlags = 2
            accent.GradientColor = 0x01000000  # Semi-transparent
            
            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = 19  # WCA_ACCENT_POLICY
            data.Data = ctypes.pointer(accent)
            data.SizeOfData = ctypes.sizeof(accent)
            
            # Apply the effect
            ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
            return True
        except:
            return False

class ModernPowerManager:
    """Enhanced power management with better detection"""
    
    def __init__(self):
        self.plans = self.get_all_power_plans()
        self.gaming_plan = self.find_gaming_plan()
        self.balanced_plan = self.find_balanced_plan()
    
    def get_all_power_plans(self):
        """Get all available power plans"""
        try:
            result = subprocess.run(['powercfg', '/list'], capture_output=True, text=True)
            plans = {}
            for line in result.stdout.split('\n'):
                if 'GUID:' in line and '(' in line:
                    guid = line.split(':')[1].split('(')[0].strip()
                    name = line.split('(')[1].split(')')[0]
                    active = '*' in line
                    plans[name] = {'guid': guid, 'active': active}
            return plans
        except:
            return {}
    
    def find_gaming_plan(self):
        """Find gaming/performance power plan"""
        gaming_keywords = ['gaming', 'performance', 'high', 'ultimate']
        for name, info in self.plans.items():
            if any(keyword in name.lower() for keyword in gaming_keywords):
                return info['guid']
        return "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"  # Default
    
    def find_balanced_plan(self):
        """Find balanced power plan"""
        balanced_keywords = ['balanced', 'casual', 'power saver', 'recommended']
        for name, info in self.plans.items():
            if any(keyword in name.lower() for keyword in balanced_keywords):
                return info['guid']
        return "381b4222-f694-41f0-9685-ff5bb260df2e"  # Default
    
    def switch_to_gaming(self):
        """Switch to gaming/performance power plan"""
        try:
            subprocess.run(['powercfg', '/setactive', self.gaming_plan], check=False)
            return True
        except Exception:
            return False
    
    def switch_to_balanced(self):
        """Switch to casual/balanced power plan"""
        try:
            subprocess.run(['powercfg', '/setactive', self.balanced_plan], check=False)
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

class ModernGameDetector:
    """Enhanced game detection with launcher support"""
    
    def __init__(self):
        self.game_list_path = Path("C:/PowerSwitcher/GameList.txt")
        self.games = []
        self.launchers = ['steam.exe', 'EpicGamesLauncher.exe', 'Battle.net.exe', 'Origin.exe', 'upc.exe']
        self.load_games()
    
    def load_games(self):
        """Load comprehensive game list"""
        default_games = [
            # Popular Games
            "Blur.exe", "WRCG.exe", "ForzaHorizon4.exe", "ForzaHorizon5.exe",
            "eFootball.exe", "bf4.exe", "bf1.exe", "bfv.exe", "bf2042.exe",
            "Client-Win64-Shipping.exe", "SparkingZERO.exe", "TslGame.exe",
            "DetroitBecomeHuman.exe", "osu!.exe", "RidersRepublic_BE.exe",
            # AAA Games
            "GTA5.exe", "RDR2.exe", "Cyberpunk2077.exe", "witcher3.exe",
            "valorant.exe", "CSGO.exe", "cs2.exe", "overwatch.exe",
            "ApexLegends.exe", "destiny2.exe", "warframe.exe",
            # Launchers
            "steam.exe", "EpicGamesLauncher.exe", "Battle.net.exe"
        ]
        
        try:
            if self.game_list_path.exists():
                with open(self.game_list_path, 'r', encoding='utf-8') as f:
                    loaded_games = [line.strip() for line in f if line.strip()]
                self.games = loaded_games if loaded_games else default_games
            else:
                self.games = default_games
                self.save_games()
        except:
            self.games = default_games
    
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

class PowerSwitcherModern:
    """Ultra-modern PowerSwitcher with Windows 11 styling"""
    
    def __init__(self):
        # Initialize managers
        self.theme_manager = WindowsThemeManager()
        self.power_manager = ModernPowerManager()
        self.game_detector = ModernGameDetector()
        
        # App state
        self.monitoring = True
        self.current_game = None
        
        # Create main window
        self.setup_window()
        self.create_modern_ui()
        self.apply_theme()
        self.start_services()
    
    def setup_window(self):
        """Setup ultra-modern window with acrylic effects"""
        self.root = ctk.CTk()
        self.root.title("PowerSwitcher Universal")
        self.root.geometry("360x280")
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (360 // 2)
        y = (self.root.winfo_screenheight() // 2) - (280 // 2)
        self.root.geometry(f"360x280+{x}+{y}")
        
        # Apply acrylic blur after window is created
        self.root.after(100, self.apply_acrylic_effect)
        
        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
    
    def apply_acrylic_effect(self):
        """Apply Windows 11 acrylic blur effect"""
        try:
            hwnd = self.root.winfo_id()
            AcrylicWindow.enable_blur(hwnd)
        except:
            pass  # Fallback gracefully if acrylic fails
    
    def create_modern_ui(self):
        """Create ultra-modern UI with Windows 11 design"""
        # Main container with modern spacing
        main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header with modern typography
        header_frame = ctk.CTkFrame(main_frame, corner_radius=12, height=60)
        header_frame.pack(fill="x", pady=(0, 16))
        header_frame.pack_propagate(False)
        
        # Logo and title with modern styling
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(expand=True, fill="both", padx=16, pady=12)
        
        # Modern logo
        self.logo_label = ctk.CTkLabel(title_frame, text="⚡", font=ctk.CTkFont(size=24))
        self.logo_label.pack(side="left", padx=(0, 12))
        
        # Title and subtitle
        text_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)
        
        self.title_label = ctk.CTkLabel(text_frame, text="PowerSwitcher", 
                                       font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.pack(anchor="w")
        
        self.subtitle_label = ctk.CTkLabel(text_frame, text="Intelligent Power Management",
                                         font=ctk.CTkFont(size=11))
        self.subtitle_label.pack(anchor="w")
        
        # Status card with modern design
        self.status_card = ctk.CTkFrame(main_frame, corner_radius=12, height=80)
        self.status_card.pack(fill="x", pady=(0, 12))
        self.status_card.pack_propagate(False)
        
        status_inner = ctk.CTkFrame(self.status_card, fg_color="transparent")
        status_inner.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Status text (left)
        status_text_frame = ctk.CTkFrame(status_inner, fg_color="transparent")
        status_text_frame.pack(side="left", fill="both", expand=True)
        
        self.status_label = ctk.CTkLabel(status_text_frame, text="Monitoring Active",
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(anchor="w")
        
        self.detail_label = ctk.CTkLabel(status_text_frame, text="Intelligent power switching",
                                        font=ctk.CTkFont(size=11))
        self.detail_label.pack(anchor="w")
        
        # Modern toggle switch (right)
        self.toggle_switch = ctk.CTkSwitch(status_inner, text="", width=50, height=24,
                                          command=self.toggle_monitoring)
        self.toggle_switch.pack(side="right", padx=(12, 0))
        self.toggle_switch.select()  # Start enabled
        
        # Game detection card
        self.game_card = ctk.CTkFrame(main_frame, corner_radius=12, height=80)
        self.game_card.pack(fill="x", pady=(0, 16))
        self.game_card.pack_propagate(False)
        
        game_inner = ctk.CTkFrame(self.game_card, fg_color="transparent")
        game_inner.pack(fill="both", expand=True, padx=16, pady=16)
        
        self.game_title = ctk.CTkLabel(game_inner, text="Game Detection",
                                      font=ctk.CTkFont(size=14, weight="bold"))
        self.game_title.pack(anchor="w")
        
        self.game_status = ctk.CTkLabel(game_inner, text="No games detected",
                                       font=ctk.CTkFont(size=11))
        self.game_status.pack(anchor="w", pady=(4, 0))
        
        self.power_status = ctk.CTkLabel(game_inner, text="Current: Balanced Mode",
                                        font=ctk.CTkFont(size=10))
        self.power_status.pack(anchor="w")
        
        # Modern button row
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        self.edit_button = ctk.CTkButton(button_frame, text="Edit Games", height=36,
                                        corner_radius=8, command=self.edit_games)
        self.edit_button.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        self.exit_button = ctk.CTkButton(button_frame, text="Exit", height=36,
                                        corner_radius=8, command=self.exit_app,
                                        fg_color="transparent", border_width=1)
        self.exit_button.pack(side="right", fill="x", expand=True, padx=(8, 0))
    
    def apply_theme(self):
        """Apply Windows theme colors and styling"""
        if self.theme_manager.is_dark:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
        
        # Update accent colors
        accent = self.theme_manager.accent_color
        self.logo_label.configure(text_color=accent)
        self.toggle_switch.configure(progress_color=accent)
        self.edit_button.configure(fg_color=accent)
    
    def toggle_monitoring(self):
        """Toggle monitoring with modern feedback"""
        self.monitoring = self.toggle_switch.get()
        
        if self.monitoring:
            self.status_label.configure(text="Monitoring Active")
            self.detail_label.configure(text="Intelligent power switching")
        else:
            self.status_label.configure(text="Monitoring Paused") 
            self.detail_label.configure(text="Click switch to resume")
    
    def edit_games(self):
        """Open game list for editing"""
        try:
            os.startfile(str(self.game_detector.game_list_path))
        except:
            messagebox.showerror("Error", "Could not open game list")
    
    def exit_app(self):
        """Exit with confirmation"""
        if messagebox.askyesno("Exit PowerSwitcher", "Are you sure you want to exit?"):
            self.monitoring = False
            self.root.quit()
    
    def hide_to_tray(self):
        """Hide to system tray with modern notification"""
        self.root.withdraw()
        # Show modern Windows notification
        self.show_notification("PowerSwitcher", "Minimized to system tray")
    
    def show_notification(self, title, message):
        """Show Windows 10/11 style notification"""
        try:
            import plyer
            plyer.notification.notify(
                title=title,
                message=message,
                app_name="PowerSwitcher Universal",
                timeout=3
            )
        except:
            pass  # Fallback silently
    
    def start_services(self):
        """Start background monitoring services"""
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start theme monitoring
        self.theme_thread = threading.Thread(target=self.theme_monitor_loop, daemon=True)
        self.theme_thread.start()
    
    def monitor_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                if self.monitoring:
                    self.update_status()
                time.sleep(3)  # Check every 3 seconds
            except:
                break
    
    def theme_monitor_loop(self):
        """Monitor Windows theme changes"""
        last_theme = self.theme_manager.is_dark
        while True:
            try:
                current_theme = self.theme_manager.detect_dark_theme()
                if current_theme != last_theme:
                    self.theme_manager.is_dark = current_theme
                    self.root.after(0, self.apply_theme)
                    last_theme = current_theme
                time.sleep(2)  # Check theme every 2 seconds
            except:
                break
    
    def update_status(self):
        """Update game detection and power status"""
        try:
            game_running, game_name = self.game_detector.is_game_running()
            
            if game_running and game_name != self.current_game:
                # Switch to gaming mode
                self.power_manager.switch_to_gaming()
                self.current_game = game_name
                self.root.after(0, lambda: self.game_status.configure(text=f"Game: {game_name}"))
                self.root.after(0, lambda: self.power_status.configure(text="Current: Gaming Mode"))
                self.show_notification("PowerSwitcher", f"Gaming mode activated for {game_name}")
                
            elif not game_running and self.current_game:
                # Switch to balanced mode
                self.power_manager.switch_to_balanced()
                self.current_game = None
                self.root.after(0, lambda: self.game_status.configure(text="No games detected"))
                self.root.after(0, lambda: self.power_status.configure(text="Current: Balanced Mode"))
                self.show_notification("PowerSwitcher", "Balanced mode restored")
                
        except:
            pass
    
    def run(self):
        """Start the modern application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        # Check admin privileges
        if not ctypes.windll.shell32.IsUserAnAdmin():
            messagebox.showerror("Administrator Required", 
                               "PowerSwitcher requires administrator privileges.\n"
                               "Please run as administrator.")
            return
        
        # Create directory
        Path("C:/PowerSwitcher").mkdir(exist_ok=True)
        
        # Launch modern app
        app = PowerSwitcherModern()
        app.run()
        
    except Exception as e:
        messagebox.showerror("PowerSwitcher Error", f"Failed to start:\n{str(e)}")

if __name__ == "__main__":
    main()
