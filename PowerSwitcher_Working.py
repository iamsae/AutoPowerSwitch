import customtkinter as ctk
from tkinter import messagebox
import subprocess
import threading
import time
import os
import winreg
from pathlib import Path
import psutil
import ctypes
import pystray
from PIL import Image, ImageDraw

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

class PowerManager:
    def __init__(self):
        self.gaming_plan = None
        self.casual_plan = None
        self.detect_power_plans()
    
    def detect_power_plans(self):
        try:
            result = subprocess.run(['powercfg', '/list'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if 'GUID:' in line:
                    if any(keyword in line.lower() for keyword in ['gaming', 'performance', 'high']):
                        self.gaming_plan = line.split(':')[1].split('(')[0].strip()
                    elif any(keyword in line.lower() for keyword in ['casual', 'balanced', 'power saver']):
                        self.casual_plan = line.split(':')[1].split('(')[0].strip()
            if not self.gaming_plan:
                self.gaming_plan = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
            if not self.casual_plan:
                self.casual_plan = "381b4222-f694-41f0-9685-ff5bb260df2e"
        except Exception:
            self.gaming_plan = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
            self.casual_plan = "381b4222-f694-41f0-9685-ff5bb260df2e"
    
    def switch_to_gaming(self):
        try:
            subprocess.run(['powercfg', '/setactive', self.gaming_plan], check=False)
            return True
        except Exception:
            return False
    
    def switch_to_casual(self):
        try:
            subprocess.run(['powercfg', '/setactive', self.casual_plan], check=False)
            return True
        except Exception:
            return False

class GameDetector:
    def __init__(self):
        self.game_list_path = Path("C:/PowerSwitcher/GameList.txt")
        self.games = []
        self.load_games()

    def load_games(self):
        try:
            if self.game_list_path.exists():
                with open(self.game_list_path, 'r', encoding='utf-8') as f:
                    self.games = [line.strip() for line in f if line.strip()]
            else:
                self.games = ["osu!.exe", "steam.exe", "EpicGamesLauncher.exe"]
                self.save_games()
        except Exception:
            self.games = ["osu!.exe", "steam.exe", "EpicGamesLauncher.exe"]

    def save_games(self):
        try:
            self.game_list_path.parent.mkdir(exist_ok=True)
            with open(self.game_list_path, 'w', encoding='utf-8') as f:
                for game in self.games:
                    f.write(f"{game}\n")
        except Exception:
            pass

    def is_game_running(self):
        try:
            running_processes = [p.name() for p in psutil.process_iter(['name'])]
            for game in self.games:
                if game.lower() in [p.lower() for p in running_processes]:
                    return True, game
            return False, None
        except Exception:
            return False, None
            return False, None

class ThemeManager:
    def __init__(self):
        self.refresh_theme()
    
    def refresh_theme(self):
        self.is_dark = self.detect_dark_theme()
        self.accent_color = self.get_accent_color()
    
    def detect_dark_theme(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return value == 0
        except:
            return False
    
    def get_accent_color(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM")
            value, _ = winreg.QueryValueEx(key, "AccentColor")
            winreg.CloseKey(key)
            r = (value >> 0) & 0xFF
            g = (value >> 8) & 0xFF  
            b = (value >> 16) & 0xFF
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#0078D4"

class PowerSwitcherWorking:
    def __init__(self):
        self.power_manager = PowerManager()
        self.game_detector = GameDetector()
        self.theme_manager = ThemeManager()
        self.monitoring = True
        self.current_game = None
        self.scan_animation_state = 0
        self.tray_icon = None
        self.theme_check_counter = 0
        self.settings_window = None
        self.setup_window()
        self.create_ui()
        self.apply_theme()
        self.setup_tray_icon()
        self.start_monitoring()
    
    def setup_window(self):
        self.root = ctk.CTk()
        self.root.title("PowerSwitcher Universal")
        self.root.geometry("360x420")
        self.root.resizable(False, False)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (360 // 2)
        y = (self.root.winfo_screenheight() // 2) - (420 // 2)
        self.root.geometry(f"360x420+{x}+{y}")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
    
    def create_ui(self):
        main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        header = ctk.CTkFrame(main_frame, corner_radius=12, height=60)
        header.pack(fill="x", pady=(0, 16))
        header.pack_propagate(False)
        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(expand=True, fill="both", padx=16, pady=12)
        logo = ctk.CTkLabel(header_inner, text="⚡", font=ctk.CTkFont(size=24))
        logo.pack(side="left", padx=(0, 12))
        title_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        title_frame.pack(side="left", fill="both", expand=True)
        title = ctk.CTkLabel(title_frame, text="PowerSwitcher", 
                           font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(anchor="w")
        subtitle = ctk.CTkLabel(title_frame, text="Intelligent Power Management",
                              font=ctk.CTkFont(size=11))
        subtitle.pack(anchor="w")
        status_card = ctk.CTkFrame(main_frame, corner_radius=12, height=80)
        status_card.pack(fill="x", pady=(0, 12))
        status_card.pack_propagate(False)
        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.pack(fill="both", expand=True, padx=16, pady=16)
        status_text_frame = ctk.CTkFrame(status_inner, fg_color="transparent")
        status_text_frame.pack(side="left", fill="both", expand=True)
        self.status_label = ctk.CTkLabel(status_text_frame, text="Monitoring Active",
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(anchor="w")
        self.detail_label = ctk.CTkLabel(status_text_frame, text="Intelligent power switching",
                                        font=ctk.CTkFont(size=11))
        self.detail_label.pack(anchor="w")
        self.toggle_switch = ctk.CTkSwitch(status_inner, text="", width=50, height=24,
                                          command=self.toggle_monitoring)
        self.toggle_switch.pack(side="right", padx=(12, 0))
        self.toggle_switch.select()
        game_card = ctk.CTkFrame(main_frame, corner_radius=12, height=80)
        game_card.pack(fill="x", pady=(0, 16))
        game_card.pack_propagate(False)
        game_inner = ctk.CTkFrame(game_card, fg_color="transparent")
        game_inner.pack(fill="both", expand=True, padx=16, pady=16)
        game_title = ctk.CTkLabel(game_inner, text="Game Detection",
                                 font=ctk.CTkFont(size=14, weight="bold"))
        game_title.pack(anchor="w")
        self.game_status = ctk.CTkLabel(game_inner, text="🔍 Scanning for games...",
                                       font=ctk.CTkFont(size=11))
        self.game_status.pack(anchor="w", pady=(4, 0))
        self.power_status = ctk.CTkLabel(game_inner, text="Current: Balanced Mode",
                                        font=ctk.CTkFont(size=10))
        self.power_status.pack(anchor="w")
        button_area = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_area.pack(fill="x", pady=(16, 0))
        edit_btn = ctk.CTkButton(button_area, text="📝 Edit Games", height=40, width=320,
                               corner_radius=8, command=self.edit_games)
        edit_btn.pack(pady=(0, 8), padx=20)
        settings_btn = ctk.CTkButton(button_area, text="⚙️ Settings", height=40, width=320,
                                   corner_radius=8, command=self.open_settings)
        settings_btn.pack(pady=(0, 8), padx=20)
        minimize_btn = ctk.CTkButton(button_area, text="📋 Minimize to Tray", height=40, width=320,
                                   corner_radius=8, command=self.hide_window,
                                   fg_color="transparent", border_width=1)
        minimize_btn.pack(pady=(0, 8), padx=20)
        exit_btn = ctk.CTkButton(button_area, text="❌ Exit", height=40, width=320,
                               corner_radius=8, command=self.exit_app,
                               fg_color="transparent", border_width=1)
        exit_btn.pack(padx=20)
    
    def apply_theme(self):
        if self.theme_manager.is_dark:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
    
    def create_tray_icon_image(self):
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        points = [(32, 8), (20, 28), (28, 28), (24, 48), (36, 28), (28, 28), (32, 8)]
        draw.polygon(points, fill=(255, 193, 7, 255), outline=(255, 152, 0, 255))
        return image
    
    def setup_tray_icon(self):
        try:
            icon_image = self.create_tray_icon_image()
            menu = pystray.Menu(
                pystray.MenuItem("PowerSwitcher Universal", self.show_window, default=True),
                pystray.MenuItem("Show Window", self.show_window),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Gaming Mode", self.force_gaming_mode),
                pystray.MenuItem("Balanced Mode", self.force_balanced_mode),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Settings", self.open_settings),
                pystray.MenuItem("Edit Games", self.edit_games),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self.exit_app)
            )
            self.tray_icon = pystray.Icon("PowerSwitcher", icon_image,
                                        "PowerSwitcher Universal - Intelligent Power Management",
                                        menu)
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
        except Exception:
            self.tray_icon = None
    
    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def update_tray_tooltip(self, status):
        try:
            if self.tray_icon:
                self.tray_icon.title = f"PowerSwitcher Universal - {status}"
        except Exception:
            pass
    
    def toggle_monitoring(self):
        self.monitoring = self.toggle_switch.get()
        if self.monitoring:
            self.status_label.configure(text="Monitoring Active")
            self.detail_label.configure(text="Intelligent power switching")
        else:
            self.status_label.configure(text="Monitoring Paused")
            self.detail_label.configure(text="Click switch to resume")
    
    def edit_games(self):
        try:
            os.startfile(str(self.game_detector.game_list_path))
        except:
            messagebox.showerror("Error", "Could not open game list")
    
    def open_settings(self):
        try:
            if hasattr(self, 'settings_window'):
                try:
                    if self.settings_window and self.settings_window.winfo_exists():
                        self.settings_window.lift()
                        self.settings_window.focus()
                        return
                except:
                    self.settings_window = None
        except Exception:
            self.settings_window = None
        
        try:
            self.settings_window = ctk.CTkToplevel(self.root)
            self.settings_window.title("PowerSwitcher Settings")
            self.settings_window.geometry("450x500")
            self.settings_window.resizable(False, False)
            
            self.settings_window.update_idletasks()
            x = (self.settings_window.winfo_screenwidth() // 2) - (450 // 2)
            y = (self.settings_window.winfo_screenheight() // 2) - (500 // 2)
            self.settings_window.geometry(f"450x500+{x}+{y}")
            
            self.settings_window.transient(self.root)
            self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings_window)
            self.create_settings_ui()
        except Exception:
            self.settings_window = None
            messagebox.showerror("Error", "Failed to open settings")
    
    def close_settings_window(self):
        try:
            if hasattr(self, 'settings_window') and self.settings_window:
                self.settings_window.destroy()
            self.settings_window = None
        except Exception:
            self.settings_window = None
    
    def create_settings_ui(self):
        main_frame = ctk.CTkFrame(self.settings_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        title = ctk.CTkLabel(main_frame, text="⚙️ PowerSwitcher Settings", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(10, 30))
        theme_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        theme_frame.pack(fill="x", pady=10)
        theme_title = ctk.CTkLabel(theme_frame, text="🎨 Theme", font=ctk.CTkFont(size=16, weight="bold"))
        theme_title.pack(pady=(15, 10))
        theme_buttons = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_buttons.pack(pady=(0, 15))
        light_btn = ctk.CTkButton(theme_buttons, text="Light", width=120, command=lambda: self.change_theme("light"))
        light_btn.pack(side="left", padx=5)
        dark_btn = ctk.CTkButton(theme_buttons, text="Dark", width=120, command=lambda: self.change_theme("dark"))
        dark_btn.pack(side="left", padx=5)
        system_btn = ctk.CTkButton(theme_buttons, text="System", width=120, command=lambda: self.change_theme("system"))
        system_btn.pack(side="left", padx=5)
        games_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        games_frame.pack(fill="x", pady=10)
        games_title = ctk.CTkLabel(games_frame, text="🎮 Game Management", font=ctk.CTkFont(size=16, weight="bold"))
        games_title.pack(pady=(15, 10))
        edit_games_btn = ctk.CTkButton(games_frame, text="📝 Edit Game List", command=self.edit_games, width=200, height=40)
        edit_games_btn.pack(pady=(0, 15))
        power_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        power_frame.pack(fill="x", pady=10)
        power_title = ctk.CTkLabel(power_frame, text="⚡ Power Management", font=ctk.CTkFont(size=16, weight="bold"))
        power_title.pack(pady=(15, 10))
        power_buttons = ctk.CTkFrame(power_frame, fg_color="transparent")
        power_buttons.pack(pady=(0, 15))
        gaming_btn = ctk.CTkButton(power_buttons, text="🎮 Gaming Mode", command=self.force_gaming_mode, width=180)
        gaming_btn.pack(side="left", padx=5)
        balanced_btn = ctk.CTkButton(power_buttons, text="⚖️ Balanced Mode", command=self.force_balanced_mode, width=180)
        balanced_btn.pack(side="left", padx=5)
        about_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        about_frame.pack(fill="x", pady=10)
        about_title = ctk.CTkLabel(about_frame, text="ℹ️ About", font=ctk.CTkFont(size=16, weight="bold"))
        about_title.pack(pady=(15, 5))
        about_text = "PowerSwitcher Universal v2.0\nIntelligent Power Management"
        about_label = ctk.CTkLabel(about_frame, text=about_text, font=ctk.CTkFont(size=12))
        about_label.pack(pady=(0, 15))
        close_btn = ctk.CTkButton(main_frame, text="✅ Close Settings", command=self.close_settings_window, height=40, width=200)
        close_btn.pack(pady=20)
    
    def change_theme(self, theme_mode):
        try:
            ctk.set_appearance_mode(theme_mode)
            if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
                self.settings_window.destroy()
                self.settings_window = None
            self.root.after(100, self.refresh_theme_detection)
            self.show_notification("Settings", f"Theme changed to {theme_mode.title()}")
        except Exception:
            pass
    
    def refresh_theme_detection(self):
        try:
            self.theme_manager.refresh_theme()
            if hasattr(self, 'game_status') and hasattr(self, 'power_status'):
                current_game_text = self.game_status.cget("text")
                current_power_text = self.power_status.cget("text")
                if "detected" in current_game_text.lower():
                    self.update_game_display(current_game_text, "green", True)
                elif "error" in current_game_text.lower():
                    self.update_game_display(current_game_text, "red", False)
                else:
                    self.update_game_display(current_game_text, "gray", False)
                if "gaming" in current_power_text.lower():
                    self.update_power_display(current_power_text, "orange")
                elif "balanced" in current_power_text.lower():
                    self.update_power_display(current_power_text, "blue")
                else:
                    self.update_power_display(current_power_text, "gray")
        except Exception:
            pass
    
    def force_gaming_mode(self, icon=None, item=None):
        if self.power_manager.switch_to_gaming():
            self.show_notification("Power", "Switched to Gaming Mode")
        else:
            messagebox.showerror("Error", "Failed to switch to Gaming Mode")
    
    def force_balanced_mode(self, icon=None, item=None):
        if self.power_manager.switch_to_casual():
            self.show_notification("Power", "Switched to Balanced Mode")
        else:
            messagebox.showerror("Error", "Failed to switch to Balanced Mode")
    
    def exit_app(self, icon=None, item=None):
        self.monitoring = False
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.root.quit()
    
    def hide_window(self):
        self.root.withdraw()
        self.show_notification("PowerSwitcher", "Minimized to system tray")
    
    def show_notification(self, title, message):
        try:
            if self.tray_icon:
                self.tray_icon.notify(message, title)
        except Exception:
            pass
    
    def start_monitoring(self):
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def monitor_loop(self):
        while True:
            try:
                if self.monitoring:
                    self.update_status()
                    self.theme_check_counter += 1
                    if self.theme_check_counter >= 6:
                        self.theme_check_counter = 0
                        self.check_theme_changes()
                time.sleep(5)
            except Exception:
                break
    
    def check_theme_changes(self):
        try:
            old_is_dark = self.theme_manager.is_dark
            self.theme_manager.refresh_theme()
            if old_is_dark != self.theme_manager.is_dark:
                self.root.after(0, self.refresh_theme_detection)
        except Exception:
            pass
    
    def update_status(self):
        """Update status with enhanced visual feedback"""
        try:
            game_running, game_name = self.game_detector.is_game_running()
            current_plan = self.power_manager.get_current_plan()
            if game_running:
                if "balanced" in current_plan.lower():
                    self.power_manager.switch_to_gaming()
                    self.show_notification("PowerSwitcher", f"Switched to Gaming Mode for {game_name}")
                game_display_name = game_name.replace('.exe', '') if game_name.endswith('.exe') else game_name
                self.root.after(0, lambda: self.update_game_display(
                    f"🎮 Game detected: {game_display_name}!", 
                    "green", True))
                self.current_game = game_name
            else:
                if "gaming" in current_plan.lower() and self.current_game:
                    self.power_manager.switch_to_casual()
                    self.show_notification("PowerSwitcher", "Switched to Balanced Mode")
                
                self.scan_animation_state = (self.scan_animation_state + 1) % 4
                scan_dots = "." * (self.scan_animation_state + 1)
                scan_text = f"🔍 Scanning for games{scan_dots}"
                self.root.after(0, lambda: self.update_game_display(scan_text, "gray", False))
                self.current_game = None
            updated_plan = self.power_manager.get_current_plan()
            if "gaming" in updated_plan.lower():
                self.root.after(0, lambda: self.update_power_display(f"⚡ Current: {updated_plan}", "orange"))
                if game_running:
                    self.update_tray_tooltip(f"Gaming Mode - {game_display_name}")
            elif "balanced" in updated_plan.lower():
                self.root.after(0, lambda: self.update_power_display(f"⚖️ Current: {updated_plan}", "blue"))
                self.update_tray_tooltip("Balanced Mode - Monitoring")
            else:
                self.root.after(0, lambda: self.update_power_display(f"❓ Current: {updated_plan}", "gray"))
                self.update_tray_tooltip("Unknown Mode")
        except Exception as e:
            self.root.after(0, lambda: self.update_game_display("❌ Detection error", "red", False))
    def update_game_display(self, text, color, is_game_detected):
        """Update game status display with color and styling"""
        try:
            if self.theme_manager.is_dark:
                color_map = {
                    "green": "#4CAF50", "red": "#F44336", "orange": "#FF9800", 
                    "blue": "#2196F3", "gray": "#9E9E9E"
                }
            else:
                color_map = {
                    "green": "#2E7D32", "red": "#C62828", "orange": "#F57C00", 
                    "blue": "#1976D2", "gray": "#616161"
                }
            
            text_color = color_map.get(color, color_map["gray"])
            
           
            if is_game_detected:
                self.game_status.configure(text=text, text_color=text_color, 
                                         font=ctk.CTkFont(size=11, weight="bold"))
            else:
                self.game_status.configure(text=text, text_color=text_color,
                                         font=ctk.CTkFont(size=11))
        except Exception:
            pass
    
    def update_power_display(self, text, color):
        """Update power status display with color"""
        try:
            if self.theme_manager.is_dark:
                color_map = {"orange": "#FF9800", "blue": "#2196F3", "gray": "#9E9E9E"}
            else:
                color_map = {"orange": "#F57C00", "blue": "#1976D2", "gray": "#616161"}
            
            text_color = color_map.get(color, color_map["gray"])
            self.power_status.configure(text=text, text_color=text_color)
        except Exception:
            pass
    
    def run(self):
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            messagebox.showerror("Administrator Required", 
                               "PowerSwitcher requires administrator privileges.")
            return
        Path("C:/PowerSwitcher").mkdir(exist_ok=True)
        app = PowerSwitcherWorking()
        app.run()
    except Exception:
        messagebox.showerror("Error", "Failed to start")
if __name__ == "__main__":
    main()
