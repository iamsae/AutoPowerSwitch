# AutoPowerSwitcher

AutoPowerSwitcher is a lightweight, battery-aware power plan manager for Windows. It automatically switches between custom power plans based on battery status and running games, helping you optimize performance and battery life.

## Features
- 🧠 Battery-aware switching
- 🎮 Game detection via process scan
- 🖼️ Tray icon with pause/resume, edit list, exit
- 🔁 Persistent via Task Scheduler
- 🛠️ Fully configurable game list and power plans

## Getting Started
1. Clone the repo
2. Edit `GameList.txt` with your game executables
3. Set up your custom power plans and grab their GUIDs
4. Run `AutoPowerTray.ps1` or convert to `.exe` using `ps2exe`

## Power Plan Setup
Use `powercfg /list` to find your GUIDs. Create two plans:
- **Gaming Cool**: capped GHz, Turbo Boost on
- **Casual**: full performance

## Convert to EXE
```powershell
Install-Module -Name ps2exe -Scope CurrentUser
```
```powershell
Invoke-PS2EXE -InputFile .\src\AutoPowerTray.ps1 -OutputFile .\AutoPowerTray.exe -noConsole
```
