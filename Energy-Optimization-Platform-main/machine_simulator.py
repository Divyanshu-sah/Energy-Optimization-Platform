"""
EnergiX Copilot - Digital Twin Industrial Machine Simulator
Simulates a real industrial compressor machine with realistic telemetry
"""

import time
import random
import json
import requests
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np

# For colored terminal output
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Fallback color codes
    class Fore:
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        RESET = '\033[0m'
        BLACK = '\033[30m'
    
    class Back:
        RED = '\033[101m'
        GREEN = '\033[102m'
        YELLOW = '\033[103m'
        BLUE = '\033[104m'
        MAGENTA = '\033[105m'
        CYAN = '\033[106m'
        WHITE = '\033[107m'
        RESET = '\033[0m'
    
    class Style:
        BRIGHT = '\033[1m'
        DIM = '\033[2m'
        NORMAL = '\033[22m'
        RESET_ALL = '\033[0m'

# CONFIGURATION
API_URL = "http://localhost:8002"  # FastAPI backend URL
INGEST_ENDPOINT = f"{API_URL}/api/telemetry/ingest"
SIMULATION_INTERVAL_SECONDS = 2  # Send data every 2 seconds

# Machine configuration
MACHINE_CONFIG = {
    "machine_id": "SIM_COMP_001",
    "machine_type": "compressor",
    "plant_id": "P01",
    "zone_id": "Z01",
    "rated_power_kw": 150.0,
    "normal_power_range": (60, 120),  # kW
    "normal_load_range": (55, 85),  # percent
    "normal_temp_range": (35, 45),  # Celsius
    "normal_vibration_range": (1.5, 3.0),  # mm/s
    "normal_output_range": (45, 75),  # units
}

# SCENARIO DEFINITIONS

@dataclass
class Scenario:
    """Base scenario configuration"""
    name: str
    description: str
    color: str = Fore.WHITE

    def generate_telemetry(self, base_data: Dict, step: int) -> Dict:
        """Generate telemetry for this scenario"""
        raise NotImplementedError


class NormalScenario(Scenario):
    """Normal operation - stable values within normal ranges"""

    def __init__(self):
        super().__init__(
            name="normal",
            description="Normal operation - Stable performance within optimal ranges",
            color=Fore.GREEN
        )

    def generate_telemetry(self, base_data: Dict, step: int) -> Dict:
        data = base_data.copy()

        data["power_kw"] = np.random.uniform(
            MACHINE_CONFIG["normal_power_range"][0],
            MACHINE_CONFIG["normal_power_range"][1],
        )
        data["load_percent"] = np.random.uniform(
            MACHINE_CONFIG["normal_load_range"][0],
            MACHINE_CONFIG["normal_load_range"][1],
        )
        data["temperature_c"] = np.random.uniform(
            MACHINE_CONFIG["normal_temp_range"][0],
            MACHINE_CONFIG["normal_temp_range"][1],
        )
        data["vibration_mm_s"] = np.random.uniform(
            MACHINE_CONFIG["normal_vibration_range"][0],
            MACHINE_CONFIG["normal_vibration_range"][1],
        )

        data["output_units"] = data["load_percent"] * 0.85 + np.random.uniform(-2, 2)
        data["utilization_percent"] = data["load_percent"] * 0.95
        data["runtime_state"] = "active"

        return data


class IdleWasteScenario(Scenario):
    """Idle waste - Machine idle but consuming significant power"""

    def __init__(self):
        super().__init__(
            name="idle_waste",
            description="Idle Waste - Machine idle but consuming abnormal power",
            color=Fore.YELLOW
        )
        self.idle_power_base = 25.0

    def generate_telemetry(self, base_data: Dict, step: int) -> Dict:
        data = base_data.copy()

        data["load_percent"] = np.random.uniform(5, 15)
        data["power_kw"] = self.idle_power_base + np.random.uniform(-3, 5)
        data["temperature_c"] = np.random.uniform(30, 38)
        data["vibration_mm_s"] = np.random.uniform(1.0, 2.0)
        data["output_units"] = np.random.uniform(2, 8)
        data["utilization_percent"] = 15.0
        data["runtime_state"] = "idle"

        return data


class OverloadScenario(Scenario):
    """Overload - Machine running beyond rated capacity"""

    def __init__(self):
        super().__init__(
            name="overload",
            description="Overload - Machine running above rated capacity",
            color=Fore.RED
        )
        self.overload_start_time = None

    def generate_telemetry(self, base_data: Dict, step: int) -> Dict:
        data = base_data.copy()

        if self.overload_start_time is None:
            self.overload_start_time = step

        overload_duration = step - self.overload_start_time
        overload_factor = min(1.0 + (overload_duration * 0.01), 1.5)

        data["load_percent"] = min(120, 95 + overload_duration * 0.5)
        data["power_kw"] = (
            MACHINE_CONFIG["rated_power_kw"]
            * (data["load_percent"] / 100)
            * overload_factor
        )
        data["temperature_c"] = 45 + overload_duration * 0.3 + np.random.uniform(-2, 2)
        data["vibration_mm_s"] = (
            3.5 + overload_duration * 0.1 + np.random.uniform(-0.5, 0.5)
        )
        data["output_units"] = data["load_percent"] * 0.9
        data["utilization_percent"] = min(100, data["load_percent"])
        data["runtime_state"] = "overload"

        return data


class GradualDegradationScenario(Scenario):
    """Gradual degradation - Slow increase in power consumption and temperature"""

    def __init__(self):
        super().__init__(
            name="gradual_degradation",
            description="Gradual Degradation - Slowly increasing inefficiency over time",
            color=Fore.MAGENTA
        )
        self.degradation_start_time = None
        self.baseline_power = 85.0

    def generate_telemetry(self, base_data: Dict, step: int) -> Dict:
        data = base_data.copy()

        if self.degradation_start_time is None:
            self.degradation_start_time = step

        degradation_duration = step - self.degradation_start_time
        degradation_factor = min(1.0 + (degradation_duration * 0.005), 1.3)

        data["load_percent"] = np.random.uniform(60, 75)
        data["power_kw"] = self.baseline_power * degradation_factor + np.random.uniform(-2, 2)
        data["temperature_c"] = 38 + degradation_duration * 0.15 + np.random.uniform(-1, 1)
        data["vibration_mm_s"] = 2.0 + degradation_duration * 0.05 + np.random.uniform(-0.3, 0.3)
        data["output_units"] = data["load_percent"] * 0.8 * (1 - degradation_factor * 0.1)
        data["utilization_percent"] = data["load_percent"] * (1 - degradation_factor * 0.05)
        data["runtime_state"] = "active"

        return data


# DIGITAL TWIN SIMULATOR

class DigitalTwinSimulator:
    """Main simulator class for industrial machine"""

    def __init__(self, api_url: str = API_URL):
        self.api_url = api_url
        self.is_running = False
        self.current_scenario = NormalScenario()
        self.step_count = 0
        self.telemetry_buffer = []

        self.scenarios = {
            "normal": NormalScenario(),
            "idle_waste": IdleWasteScenario(),
            "overload": OverloadScenario(),
            "gradual_degradation": GradualDegradationScenario(),
        }

        self.stats = {
            "total_telemetry_sent": 0,
            "successful_posts": 0,
            "failed_posts": 0,
            "start_time": None,
        }

        self.print_banner()

    def print_banner(self):
        """Print colored banner"""
        if COLORS_AVAILABLE:
            print(Fore.CYAN + Style.BRIGHT + "=" * 70)
            print(Fore.CYAN + Style.BRIGHT + "🤖 ENERGY OPTIMIZATION PLATFORM - DIGITAL TWIN SIMULATOR")
            print(Fore.CYAN + Style.BRIGHT + "=" * 70)
            print(f"{Fore.GREEN}✅ Simulator Initialized")
            print(f"   {Fore.YELLOW}Machine: {Style.BRIGHT}{MACHINE_CONFIG['machine_id']} {Fore.WHITE}({MACHINE_CONFIG['machine_type']})")
            print(f"   {Fore.BLUE}API Endpoint: {INGEST_ENDPOINT}")
            print(Fore.CYAN + "=" * 70 + Fore.RESET)
        else:
            print("=" * 70)
            print("🤖 ENERGY OPTIMIZATION PLATFORM - DIGITAL TWIN SIMULATOR")
            print("=" * 70)
            print(f"✅ Simulator Initialized")
            print(f"   Machine: {MACHINE_CONFIG['machine_id']} ({MACHINE_CONFIG['machine_type']})")
            print(f"   API Endpoint: {INGEST_ENDPOINT}")
            print("=" * 70)

    def generate_base_telemetry(self) -> Dict:
        """Generate base telemetry structure"""
        return {
            "machine_id": MACHINE_CONFIG["machine_id"],
            "machine_type": MACHINE_CONFIG["machine_type"],
            "plant_id": MACHINE_CONFIG["plant_id"],
            "zone_id": MACHINE_CONFIG["zone_id"],
            "timestamp": datetime.now().isoformat(),
            "shift_id": self.get_shift_id(),
            "power_kw": 0.0,
            "load_percent": 0.0,
            "temperature_c": 0.0,
            "vibration_mm_s": 0.0,
            "utilization_percent": 0.0,
            "output_units": 0.0,
            "runtime_state": "unknown",
            "scenario": self.current_scenario.name,
        }

    def get_shift_id(self) -> str:
        """Determine shift based on current hour"""
        hour = datetime.now().hour
        if 6 <= hour < 14:
            return "morning"
        elif 14 <= hour < 22:
            return "evening"
        else:
            return "night"

    def generate_telemetry(self) -> Dict:
        """Generate complete telemetry using current scenario"""
        base_data = self.generate_base_telemetry()
        telemetry = self.current_scenario.generate_telemetry(base_data, self.step_count)
        
        telemetry["energy_kwh_interval"] = telemetry["power_kw"] * (SIMULATION_INTERVAL_SECONDS / 3600)
        telemetry["power_factor"] = np.random.uniform(0.85, 0.95)
        telemetry["voltage_v"] = np.random.normal(400, 5)
        telemetry["current_a"] = telemetry["power_kw"] * 1000 / (400 * 0.9)

        return telemetry

    def get_status_icon(self, value, thresholds):
        """Get status icon based on value thresholds"""
        if value >= thresholds.get('critical', float('inf')):
            return "🔴"
        elif value >= thresholds.get('warning', float('inf')):
            return "🟡"
        elif value <= thresholds.get('low', -float('inf')):
            return "🔵"
        else:
            return "🟢"

    def send_telemetry(self, telemetry: Dict) -> bool:
        """Send telemetry to API endpoint"""
        try:
            response = requests.post(
                INGEST_ENDPOINT,
                json=telemetry,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )

            if response.status_code == 200:
                self.stats["successful_posts"] += 1
                return True
            else:
                self.stats["failed_posts"] += 1
                if COLORS_AVAILABLE:
                    print(f"{Fore.RED}⚠️ API returned {response.status_code}: {response.text[:100]}{Fore.RESET}")
                else:
                    print(f"⚠️ API returned {response.status_code}: {response.text[:100]}")
                return False

        except requests.exceptions.ConnectionError:
            self.stats["failed_posts"] += 1
            if COLORS_AVAILABLE:
                print(f"{Fore.RED}❌ Cannot connect to API at {INGEST_ENDPOINT}{Fore.RESET}")
                print(f"{Fore.YELLOW}   Make sure the FastAPI backend is running on port 8002!{Fore.RESET}")
            else:
                print(f"❌ Cannot connect to API at {INGEST_ENDPOINT}")
                print("   Make sure the FastAPI backend is running on port 8002!")
            return False
        except Exception as e:
            self.stats["failed_posts"] += 1
            if COLORS_AVAILABLE:
                print(f"{Fore.RED}❌ Error sending telemetry: {e}{Fore.RESET}")
            else:
                print(f"❌ Error sending telemetry: {e}")
            return False

    def run_simulation_step(self):
        """Execute one simulation step"""
        if not self.is_running:
            return

        telemetry = self.generate_telemetry()
        success = self.send_telemetry(telemetry)
        self.stats["total_telemetry_sent"] += 1

        # Colorful console output
        status_icon = "✅" if success else "❌"
        
        # Determine colors based on values
        power_icon = self.get_status_icon(telemetry['power_kw'], {'warning': 110, 'critical': 130})
        temp_icon = self.get_status_icon(telemetry['temperature_c'], {'warning': 55, 'critical': 65})
        vib_icon = self.get_status_icon(telemetry['vibration_mm_s'], {'warning': 3.5, 'critical': 5.0})
        
        if COLORS_AVAILABLE:
            scenario_color = self.current_scenario.color
            print(f"\n{Fore.CYAN}{'─' * 70}{Fore.RESET}")
            print(f"{status_icon} {Style.BRIGHT}[Step {self.step_count:04d}]{Style.NORMAL} "
                  f"{scenario_color}{self.current_scenario.name.upper()}{Fore.RESET} "
                  f"| {Fore.WHITE}Time: {datetime.now().strftime('%H:%M:%S')}{Fore.RESET}")
            print(f"   {power_icon} {Fore.CYAN}Power:{Fore.RESET} {Fore.YELLOW}{telemetry['power_kw']:6.1f} kW{Fore.RESET} "
                  f"| {temp_icon} {Fore.CYAN}Temp:{Fore.RESET} {Fore.YELLOW}{telemetry['temperature_c']:5.1f}°C{Fore.RESET} "
                  f"| {vib_icon} {Fore.CYAN}Vibration:{Fore.RESET} {Fore.YELLOW}{telemetry['vibration_mm_s']:4.2f} mm/s{Fore.RESET}")
            print(f"   📊 {Fore.CYAN}Load:{Fore.RESET} {Fore.GREEN}{telemetry['load_percent']:5.1f}%{Fore.RESET} "
                  f"| 🏭 {Fore.CYAN}Output:{Fore.RESET} {Fore.GREEN}{telemetry['output_units']:6.1f} units{Fore.RESET} "
                  f"| 📈 {Fore.CYAN}Utilization:{Fore.RESET} {Fore.GREEN}{telemetry['utilization_percent']:5.1f}%{Fore.RESET}")
            print(f"{Fore.CYAN}{'─' * 70}{Fore.RESET}")
        else:
            print(f"\n{'─' * 70}")
            print(f"{status_icon} [Step {self.step_count:04d}] {self.current_scenario.name.upper()} | Time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"   {power_icon} Power: {telemetry['power_kw']:6.1f} kW | {temp_icon} Temp: {telemetry['temperature_c']:5.1f}°C | {vib_icon} Vibration: {telemetry['vibration_mm_s']:4.2f} mm/s")
            print(f"   📊 Load: {telemetry['load_percent']:5.1f}% | 🏭 Output: {telemetry['output_units']:6.1f} units | 📈 Utilization: {telemetry['utilization_percent']:5.1f}%")
            print(f"{'─' * 70}")

        self.step_count += 1

    def start(self):
        """Start the simulator"""
        self.is_running = True
        self.stats["start_time"] = datetime.now()
        
        if COLORS_AVAILABLE:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}🚀 SIMULATION STARTED{Style.NORMAL} at {self.stats['start_time'].strftime('%H:%M:%S')}{Fore.RESET}")
            print(f"   {Fore.CYAN}Scenario:{Fore.RESET} {self.current_scenario.color}{self.current_scenario.name}{Fore.RESET}")
            print(f"   {Fore.CYAN}Interval:{Fore.RESET} {SIMULATION_INTERVAL_SECONDS} seconds\n")
        else:
            print(f"\n🚀 SIMULATION STARTED at {self.stats['start_time'].strftime('%H:%M:%S')}")
            print(f"   Scenario: {self.current_scenario.name}")
            print(f"   Interval: {SIMULATION_INTERVAL_SECONDS} seconds\n")

        while self.is_running:
            self.run_simulation_step()
            time.sleep(SIMULATION_INTERVAL_SECONDS)

    def stop(self):
        """Stop the simulator"""
        self.is_running = False
        duration = ((datetime.now() - self.stats["start_time"]).total_seconds() if self.stats["start_time"] else 0)
        
        success_rate = (self.stats['successful_posts'] / self.stats['total_telemetry_sent'] * 100) if self.stats['total_telemetry_sent'] > 0 else 0
        
        if COLORS_AVAILABLE:
            print(f"\n{Fore.RED}{Style.BRIGHT}🛑 SIMULATION STOPPED{Style.NORMAL}{Fore.RESET}")
            print(f"   {Fore.CYAN}Duration:{Fore.RESET} {duration:.1f} seconds")
            print(f"   {Fore.CYAN}Telemetry sent:{Fore.RESET} {self.stats['total_telemetry_sent']}")
            print(f"   {Fore.GREEN}Successful:{Fore.RESET} {self.stats['successful_posts']}")
            print(f"   {Fore.RED}Failed:{Fore.RESET} {self.stats['failed_posts']}")
            
            if success_rate >= 90:
                rate_color = Fore.GREEN
            elif success_rate >= 70:
                rate_color = Fore.YELLOW
            else:
                rate_color = Fore.RED
            print(f"   {Fore.CYAN}Success Rate:{Fore.RESET} {rate_color}{success_rate:.1f}%{Fore.RESET}")
        else:
            print(f"\n🛑 SIMULATION STOPPED")
            print(f"   Duration: {duration:.1f} seconds")
            print(f"   Telemetry sent: {self.stats['total_telemetry_sent']}")
            print(f"   Successful: {self.stats['successful_posts']}")
            print(f"   Failed: {self.stats['failed_posts']}")
            print(f"   Success Rate: {success_rate:.1f}%")

    def switch_scenario(self, scenario_name: str):
        """Switch to a different scenario"""
        if scenario_name in self.scenarios:
            old_scenario = self.current_scenario.name
            self.current_scenario = self.scenarios[scenario_name]

            if scenario_name == "overload":
                self.scenarios["overload"].overload_start_time = None
            elif scenario_name == "gradual_degradation":
                self.scenarios["gradual_degradation"].degradation_start_time = None

            if COLORS_AVAILABLE:
                print(f"\n{Fore.CYAN}{'─' * 50}{Fore.RESET}")
                print(f"{Fore.YELLOW}🔄 Scenario Switched{Fore.RESET}")
                print(f"   {Fore.RED}From:{Fore.RESET} {old_scenario}")
                print(f"   {Fore.GREEN}To:{Fore.RESET} {self.current_scenario.color}{self.current_scenario.name}{Fore.RESET}")
                print(f"   {Fore.CYAN}Description:{Fore.RESET} {self.current_scenario.description}")
                print(f"{Fore.CYAN}{'─' * 50}{Fore.RESET}\n")
            else:
                print(f"\n{'─' * 50}")
                print(f"🔄 Scenario Switched: {old_scenario} → {self.current_scenario.name}")
                print(f"   {self.current_scenario.description}")
                print(f"{'─' * 50}\n")
            return True
        else:
            if COLORS_AVAILABLE:
                print(f"{Fore.RED}❌ Unknown scenario: {scenario_name}{Fore.RESET}")
            else:
                print(f"❌ Unknown scenario: {scenario_name}")
            return False


# TKINTER GUI WITH IMPROVED STYLING

class ModernSimulatorGUI:
    """Enhanced Tkinter GUI with modern styling"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EnergiX Copilot - Digital Twin Simulator")
        self.root.geometry("900x700")
        
        # Modern color scheme
        self.colors = {
            'bg_dark': '#1a1a2e',
            'bg_medium': '#16213e',
            'bg_light': '#0f3460',
            'accent': '#e94560',
            'success': '#4caf50',
            'warning': '#ff9800',
            'danger': '#f44336',
            'info': '#2196f3',
            'text': '#eeeeee',
            'text_secondary': '#b0b0b0'
        }
        
        self.root.configure(bg=self.colors['bg_dark'])
        
        self.simulator = None
        self.simulation_thread = None
        self.is_running = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the enhanced GUI interface"""
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Modern.TButton', 
                       font=('Segoe UI', 10, 'bold'),
                       padding=10,
                       background=self.colors['accent'],
                       foreground='white')
        
        style.configure('Success.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=10,
                       background=self.colors['success'])
        
        style.configure('Danger.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=10,
                       background=self.colors['danger'])
        
        style.configure('Modern.TLabel',
                       font=('Segoe UI', 10),
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text'])
        
        style.configure('Header.TLabel',
                       font=('Segoe UI', 16, 'bold'),
                       background=self.colors['bg_dark'],
                       foreground=self.colors['accent'])
        
        style.configure('Title.TLabel',
                       font=('Segoe UI', 12, 'bold'),
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text'])
        
        style.configure('Value.TLabel',
                       font=('Segoe UI', 14, 'bold'),
                       background=self.colors['bg_medium'],
                       foreground=self.colors['accent'])
        
        style.configure('Modern.TLabelframe',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text'])
        
        style.configure('Modern.TLabelframe.Label',
                       font=('Segoe UI', 11, 'bold'),
                       background=self.colors['bg_dark'],
                       foreground=self.colors['accent'])
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.configure(style='Modern.TFrame')
        
        # Header with icon
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, 
                               text="🤖 INDUSTRIAL MACHINE DIGITAL TWIN", 
                               style='Header.TLabel')
        title_label.grid(row=0, column=0)
        
        subtitle_label = ttk.Label(header_frame,
                                  text="Real-time Simulation & Monitoring Platform",
                                  style='Modern.TLabel')
        subtitle_label.grid(row=1, column=0)
        
        # Machine info card
        info_frame = ttk.LabelFrame(main_frame, text="Machine Configuration", style='Modern.TLabelframe')
        info_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Create info grid with better layout
        info_grid = ttk.Frame(info_frame)
        info_grid.grid(row=0, column=0, padx=10, pady=10)
        
        info_items = [
            ("🆔 Machine ID:", MACHINE_CONFIG["machine_id"]),
            ("🔧 Type:", MACHINE_CONFIG["machine_type"].title()),
            ("🏭 Plant/Zone:", f"{MACHINE_CONFIG['plant_id']} / {MACHINE_CONFIG['zone_id']}"),
            ("⚡ Rated Power:", f"{MACHINE_CONFIG['rated_power_kw']} kW"),
            ("📡 API Endpoint:", "http://localhost:8002")
        ]
        
        for i, (label, value) in enumerate(info_items):
            ttk.Label(info_grid, text=label, style='Modern.TLabel').grid(row=i, column=0, sticky=tk.W, pady=5)
            ttk.Label(info_grid, text=value, style='Title.TLabel').grid(row=i, column=1, sticky=tk.W, padx=20, pady=5)
        
        # Scenario selection card
        scenario_frame = ttk.LabelFrame(main_frame, text="Scenario Control", style='Modern.TLabelframe')
        scenario_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.scenario_var = tk.StringVar(value="normal")
        
        scenarios = [
            ("✅ Normal Operation", "normal", self.colors['success']),
            ("💤 Idle Waste", "idle_waste", self.colors['warning']),
            ("⚠️ Overload Condition", "overload", self.colors['danger']),
            ("📉 Gradual Degradation", "gradual_degradation", self.colors['info']),
        ]
        
        for i, (text, value, color) in enumerate(scenarios):
            rb = tk.Radiobutton(
                scenario_frame, 
                text=text, 
                value=value, 
                variable=self.scenario_var,
                bg=self.colors['bg_medium'],
                fg=self.colors['text'],
                selectcolor=self.colors['bg_dark'],
                font=('Segoe UI', 10),
                activebackground=self.colors['accent'],
                activeforeground='white'
            )
            rb.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=20, pady=10)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        self.start_button = tk.Button(
            control_frame,
            text="▶ START SIMULATION",
            command=self.start_simulation,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.start_button.grid(row=0, column=0, padx=10)
        
        self.stop_button = tk.Button(
            control_frame,
            text="⏹ STOP SIMULATION",
            command=self.stop_simulation,
            bg=self.colors['danger'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            state='disabled'
        )
        self.stop_button.grid(row=0, column=1, padx=10)
        
        self.switch_button = tk.Button(
            control_frame,
            text="🔄 SWITCH SCENARIO",
            command=self.switch_scenario,
            bg=self.colors['info'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            state='disabled'
        )
        self.switch_button.grid(row=0, column=2, padx=10)
        
        # Telemetry display card
        telemetry_frame = ttk.LabelFrame(main_frame, text="Live Telemetry", style='Modern.TLabelframe')
        telemetry_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Create telemetry display with cards
        metrics_frame = ttk.Frame(telemetry_frame)
        metrics_frame.grid(row=0, column=0, padx=10, pady=10)
        
        self.telemetry_vars = {}
        metrics = [
            ("⚡ Power", "power", "kW"),
            ("📊 Load", "load", "%"),
            ("🌡️ Temperature", "temp", "°C"),
            ("📳 Vibration", "vib", "mm/s"),
            ("🏭 Output", "output", "units"),
            ("📈 Utilization", "util", "%"),
        ]
        
        for i, (label, key, unit) in enumerate(metrics):
            # Card frame
            card = tk.Frame(metrics_frame, bg=self.colors['bg_medium'], relief=tk.RAISED, bd=0)
            card.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky='nsew')
            
            # Label
            tk.Label(card, text=label, font=('Segoe UI', 11),
                    bg=self.colors['bg_medium'], fg=self.colors['text_secondary']).pack(pady=(10,5))
            
            # Value
            self.telemetry_vars[key] = tk.StringVar(value="--")
            tk.Label(card, textvariable=self.telemetry_vars[key], 
                    font=('Segoe UI', 20, 'bold'),
                    bg=self.colors['bg_medium'], fg=self.colors['accent']).pack()
            
            # Unit
            tk.Label(card, text=unit, font=('Segoe UI', 10),
                    bg=self.colors['bg_medium'], fg=self.colors['text_secondary']).pack(pady=(0,10))
            
            # Configure card size
            card.configure(width=180, height=120)
            card.pack_propagate(False)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg=self.colors['bg_medium'], height=40)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.status_var = tk.StringVar(value="✅ Ready to start simulation")
        status_label = tk.Label(status_frame, textvariable=self.status_var,
                               bg=self.colors['bg_medium'], fg=self.colors['text'],
                               font=('Segoe UI', 10), anchor=tk.W)
        status_label.pack(fill=tk.BOTH, padx=15, pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def update_telemetry_display(self, telemetry: Dict):
        """Update the live telemetry display with color coding"""
        power = telemetry.get('power_kw', 0)
        temp = telemetry.get('temperature_c', 0)
        vib = telemetry.get('vibration_mm_s', 0)
        
        # Color coding based on values
        power_color = self.colors['danger'] if power > 110 else (self.colors['warning'] if power > 90 else self.colors['success'])
        temp_color = self.colors['danger'] if temp > 55 else (self.colors['warning'] if temp > 45 else self.colors['success'])
        vib_color = self.colors['danger'] if vib > 3.5 else (self.colors['warning'] if vib > 2.5 else self.colors['success'])
        
        self.telemetry_vars["power"].set(f"{power:.1f}")
        self.telemetry_vars["load"].set(f"{telemetry.get('load_percent', 0):.0f}")
        self.telemetry_vars["temp"].set(f"{temp:.1f}")
        self.telemetry_vars["vib"].set(f"{vib:.2f}")
        self.telemetry_vars["output"].set(f"{telemetry.get('output_units', 0):.1f}")
        self.telemetry_vars["util"].set(f"{telemetry.get('utilization_percent', 0):.0f}")
    
    def simulation_worker(self):
        """Worker function for simulation thread"""
        self.simulator = DigitalTwinSimulator()
        
        original_send = self.simulator.send_telemetry
        
        def send_with_gui(telemetry):
            self.root.after(0, self.update_telemetry_display, telemetry)
            return original_send(telemetry)
        
        self.simulator.send_telemetry = send_with_gui
        self.simulator.start()
    
    def start_simulation(self):
        """Start the simulation in a separate thread"""
        self.is_running = True
        self.simulation_thread = threading.Thread(target=self.simulation_worker, daemon=True)
        self.simulation_thread.start()
        
        self.start_button.config(state='disabled', bg=self.colors['text_secondary'])
        self.stop_button.config(state='normal', bg=self.colors['danger'])
        self.switch_button.config(state='normal', bg=self.colors['info'])
        self.status_var.set("🚀 Simulation running - Sending telemetry data...")
    
    def stop_simulation(self):
        """Stop the simulation"""
        if self.simulator:
            self.simulator.stop()
        
        self.is_running = False
        self.start_button.config(state='normal', bg=self.colors['success'])
        self.stop_button.config(state='disabled', bg=self.colors['text_secondary'])
        self.switch_button.config(state='disabled', bg=self.colors['text_secondary'])
        self.status_var.set("⏹️ Simulation stopped")
    
    def switch_scenario(self):
        """Switch to selected scenario"""
        if self.simulator and self.is_running:
            scenario_name = self.scenario_var.get()
            if self.simulator.switch_scenario(scenario_name):
                scenario_names = {
                    "normal": "Normal Operation",
                    "idle_waste": "Idle Waste",
                    "overload": "Overload Condition",
                    "gradual_degradation": "Gradual Degradation"
                }
                self.status_var.set(f"🔄 Switched to {scenario_names.get(scenario_name, scenario_name)} scenario")
    
    def run(self):
        """Run the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            self.stop_simulation()
        self.root.destroy()


# COMMAND LINE VERSION WITH ENHANCED COLORS

def run_cli_version():
    """Run simulator without GUI with enhanced colored output"""
    if COLORS_AVAILABLE:
        print(Fore.CYAN + Style.BRIGHT + "=" * 70)
        print(Fore.CYAN + Style.BRIGHT + "🤖 ENERGY OPTIMIZATION PLATFORM - DIGITAL TWIN SIMULATOR (CLI MODE)")
        print(Fore.CYAN + Style.BRIGHT + "=" * 70 + Fore.RESET)
    else:
        print("=" * 70)
        print("🤖 ENERGY OPTIMIZATION PLATFORM - DIGITAL TWIN SIMULATOR (CLI MODE)")
        print("=" * 70)

    simulator = DigitalTwinSimulator()

    print(f"\n{Fore.CYAN}Available Scenarios:{Fore.RESET}")
    print(f"  {Fore.GREEN}1. normal{Fore.RESET} - Normal operation")
    print(f"  {Fore.YELLOW}2. idle_waste{Fore.RESET} - Idle waste scenario")
    print(f"  {Fore.RED}3. overload{Fore.RESET} - Overload condition")
    print(f"  {Fore.MAGENTA}4. gradual_degradation{Fore.RESET} - Gradual degradation")
    
    print(f"\n{Fore.CYAN}Commands:{Fore.RESET}")
    print(f"  {Fore.YELLOW}switch <scenario>{Fore.RESET} - Change scenario")
    print(f"  {Fore.YELLOW}status{Fore.RESET} - Show current status")
    print(f"  {Fore.YELLOW}stop{Fore.RESET} - Stop simulation")
    print(f"  {Fore.YELLOW}help{Fore.RESET} - Show this help")

    # Start simulator in a thread
    sim_thread = threading.Thread(target=simulator.start, daemon=True)
    sim_thread.start()

    # Command loop
    while simulator.is_running:
        try:
            cmd = input(f"\n{Fore.CYAN}> {Fore.RESET}").strip().lower()

            if cmd.startswith("switch"):
                parts = cmd.split()
                if len(parts) == 2:
                    simulator.switch_scenario(parts[1])
                else:
                    print(f"{Fore.RED}Usage: switch <scenario_name>{Fore.RESET}")

            elif cmd == "status":
                print(f"\n{Fore.CYAN}Current Status:{Fore.RESET}")
                print(f"  {Fore.YELLOW}Scenario:{Fore.RESET} {simulator.current_scenario.color}{simulator.current_scenario.name}{Fore.RESET}")
                print(f"  {Fore.YELLOW}Step count:{Fore.RESET} {simulator.step_count}")
                print(f"  {Fore.YELLOW}Telemetry sent:{Fore.RESET} {simulator.stats['total_telemetry_sent']}")
                success_rate = (simulator.stats['successful_posts'] / simulator.stats['total_telemetry_sent'] * 100) if simulator.stats['total_telemetry_sent'] > 0 else 0
                rate_color = Fore.GREEN if success_rate >= 90 else (Fore.YELLOW if success_rate >= 70 else Fore.RED)
                print(f"  {Fore.YELLOW}Success Rate:{Fore.RESET} {rate_color}{success_rate:.1f}%{Fore.RESET}")

            elif cmd == "stop":
                simulator.stop()
                break

            elif cmd == "help":
                print(f"\n{Fore.CYAN}Available Commands:{Fore.RESET}")
                print(f"  {Fore.GREEN}switch normal{Fore.RESET} - Switch to normal scenario")
                print(f"  {Fore.YELLOW}switch idle_waste{Fore.RESET} - Switch to idle waste scenario")
                print(f"  {Fore.RED}switch overload{Fore.RESET} - Switch to overload scenario")
                print(f"  {Fore.MAGENTA}switch gradual_degradation{Fore.RESET} - Switch to degradation scenario")
                print(f"  {Fore.CYAN}status{Fore.RESET} - Show current status")
                print(f"  {Fore.CYAN}stop{Fore.RESET} - Stop simulation")
                print(f"  {Fore.CYAN}help{Fore.RESET} - Show this help")

            else:
                print(f"{Fore.RED}Unknown command. Type 'help' for available commands.{Fore.RESET}")

        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Stopping simulation...{Fore.RESET}")
            simulator.stop()
            break
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Fore.RESET}")


# MAIN ENTRY POINT

def main():
    """Main entry point - choose between GUI and CLI"""
    import sys

    # Check for colorama and install if needed
    try:
        import colorama
        colorama.init(autoreset=True)
    except ImportError:
        print("Note: For better colors, install colorama: pip install colorama")
    
    if COLORS_AVAILABLE:
        print(Fore.CYAN + Style.BRIGHT + "=" * 60)
        print(Fore.CYAN + Style.BRIGHT + "🤖 ENERGY OPTIMIZATION PLATFORM - DIGITAL TWIN SIMULATOR")
        print(Fore.CYAN + Style.BRIGHT + "=" * 60 + Fore.RESET)
    else:
        print("=" * 60)
        print("🤖 ENERGY OPTIMIZATION PLATFORM - DIGITAL TWIN SIMULATOR")
        print("=" * 60)
    
    print(f"\n{Fore.CYAN}Select Mode:{Fore.RESET}")
    print(f"  {Fore.GREEN}1. GUI Mode{Fore.RESET} (Enhanced visual interface)")
    print(f"  {Fore.YELLOW}2. CLI Mode{Fore.RESET} (Command line with colors)")

    try:
        choice = input(f"\n{Fore.CYAN}Enter choice (1 or 2): {Fore.RESET}").strip()

        if choice == "2":
            run_cli_version()
        else:
            print(f"\n{Fore.GREEN}🚀 Starting GUI Mode...{Fore.RESET}")
            app = ModernSimulatorGUI()
            app.run()

    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}👋 Simulator stopped{Fore.RESET}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}{Fore.RESET}")
        print(f"\n{Fore.YELLOW}Make sure tkinter is installed:{Fore.RESET}")
        print("  Windows: Included with Python")
        print("  Linux: sudo apt-get install python3-tk")
        print("  Mac: brew install python-tk")


if __name__ == "__main__":
    main()