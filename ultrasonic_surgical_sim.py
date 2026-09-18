"""
================================================================================
Ultrasonic Surgical Instrument (GEN-11 Style) Real-Time Control Loop Simulator
================================================================================
Enhanced Version with:
  1. Power ON / STANDBY (Foot Switch 腳踏激發開關)
  2. Acoustic Stall Protection & Auto-Recovery / Frequency Sweep (自動掃頻尋頻自愈)
  3. One-click "Reset & Re-Sweep (故障重置與自動尋頻)" button
  4. Correct closed-loop PLL negative-feedback sign (no runaway to 52 kHz)
  5. Automatic fault clearance when stimulus/loading is reduced
================================================================================
"""

import sys
import time
import math
import tkinter as tk
from tkinter import ttk

# ----------------------------------------------------------------------
# Physical & Electrical System Simulation Model (BVD + Dynamic Loading)
# ----------------------------------------------------------------------
class UltrasonicSurgicalPhysics:
    def __init__(self):
        # Transducer intrinsic parameters (nominal 55.50 kHz resonance)
        self.f0_nominal = 55500.0   # Nominal resonant frequency in Hz
        self.C0 = 2.8e-9            # Static capacitance: 2.8 nF
        self.Lm_nominal = 0.35      # Motional inductance: 350 mH
        self.Cm_nominal = 1.0 / ((2.0 * math.pi * self.f0_nominal) ** 2 * self.Lm_nominal)
        self.Rm0 = 18.0             # Intrinsic resistance: 18 Ohm (Air)

        # Dynamic environmental & tissue states
        self.temperature = 25.0     # Degrees Celsius
        self.temp_coeff = -8.5      # Hz per degree Celsius rise (thermal drift)
        
        # Stimulus / Loading variables
        self.tissue_damping = 0.0   # Additional Ohm due to tissue (0 = air, 200 = heavy cut)
        self.tissue_stiffness = 0.0 # Shift in Hz due to tissue elastic modulus
        self.clamp_pressure = 0.0   # 0 to 1 (affects acoustic coupling)
        
        # Physical output states
        self.current_fs = self.f0_nominal
        self.blade_amplitude_um = 0.0  # Tip displacement (um peak-to-peak)
        self.motional_current = 0.0    # Im (A rms)
        self.total_current = 0.0       # Itot (A rms)
        self.impedance_mag = 18.0      # |Z| in Ohm
        self.phase_deg = 0.0           # Phase(V) - Phase(I) in degrees
        self.active_power_w = 0.0      # Acoustic + thermal power delivered

    def update(self, dt, drive_freq, drive_voltage_vrms, power_active):
        # 1. Temperature rise model based on internal mechanical dissipation
        if power_active:
            p_loss = (self.motional_current ** 2) * self.Rm0
        else:
            p_loss = 0.0
        cooling = (self.temperature - 25.0) * 0.4
        dT = (p_loss * 0.15 - cooling) * dt
        self.temperature = max(25.0, min(140.0, self.temperature + dT))

        # 2. Compute effective resonance frequency (fs) with thermal drift + tissue stiffness
        thermal_shift = (self.temperature - 25.0) * self.temp_coeff
        stiffness_shift = self.tissue_stiffness * self.clamp_pressure
        self.current_fs = self.f0_nominal + thermal_shift + stiffness_shift

        # 3. Dynamic Motional Resistance Rm = Rm0 + tissue absorption * clamp pressure
        Rm_total = self.Rm0 + (self.tissue_damping * self.clamp_pressure)

        # 4. Equivalent Lm and Cm derived from current_fs
        w_s = 2.0 * math.pi * self.current_fs
        Cm_effective = 1.0 / (w_s ** 2 * self.Lm_nominal)

        # 5. Electrical AC impedance calculation at driving frequency
        # Note: Ultrasonic driver includes parallel/series inductor matching network that
        # cancels out C0 at fundamental band, so impedance phase is primarily the motional phase:
        w = 2.0 * math.pi * max(1000.0, drive_freq)
        X_Lm = w * self.Lm_nominal
        X_Cm = 1.0 / (w * Cm_effective)
        X_m = X_Lm - X_Cm

        Zm_sq = Rm_total ** 2 + X_m ** 2
        Zm_mag = math.sqrt(Zm_sq)
        
        # Motional phase: positive when w > ws (inductive, V leads I), negative when w < ws (capacitive)
        self.phase_deg = math.degrees(math.atan2(X_m, Rm_total))
        self.impedance_mag = Zm_mag

        # 6. If Power Switch is OFF (Standby), output is completely zeroed
        if not power_active:
            self.total_current = 0.0
            self.motional_current = 0.0
            self.blade_amplitude_um = 0.0
            self.active_power_w = 0.0
            return

        # 7. When Power is ON: Calculate currents and mechanical stroke
        target_im = drive_voltage_vrms / max(1.0, Zm_mag)
        alpha = min(1.0, dt / 0.04)  # 40ms mechanical acoustic horn inertia filter
        self.motional_current += (target_im - self.motional_current) * alpha
        self.total_current = self.motional_current

        # Mechanical tip displacement: Amplitude (um) ~ k_transducer * Im
        k_disp = 85.0  # um per Ampere of mechanical motional current
        self.blade_amplitude_um = self.motional_current * k_disp

        # Active Power: P = V * I * cos(phi)
        self.active_power_w = drive_voltage_vrms * self.total_current * math.cos(math.radians(self.phase_deg))


# ----------------------------------------------------------------------
# FPGA Controller Logic (DDS + PLL Tracking + Amplitude/Power PI)
# ----------------------------------------------------------------------
class FpgaController:
    def __init__(self):
        # Generator Power Switch (Foot switch / 手術刀腳踏激發開關)
        self.power_active = True        # True = Active (激發中), False = Standby (待機)

        # DDS output
        self.freq_output = 55500.0     # Current driving frequency in Hz
        self.dac_voltage_vrms = 40.0   # Current driving voltage commanded to DAC (Volts RMS)

        # Targets
        self.target_phase_deg = 0.0    # 0 deg = Series resonance
        self.target_amplitude_um = 65.0# Desired blade tip displacement (Level 3 cut)
        self.power_level = 3

        # PLL Tracking Controller
        self.pll_enabled = True
        self.pll_kp = 4.0              # Proportional gain (Hz/deg)
        self.pll_ki = 2.0              # Integral gain
        self.pll_integral = 0.0

        # Amplitude / Power PI Controller
        self.amp_control_enabled = True
        self.amp_kp = 0.2              # Volts / um
        self.amp_ki = 0.8
        self.amp_integral = 40.0
        self.max_dac_voltage = 180.0   # Hardware safety clamp
        self.min_dac_voltage = 10.0

        # Stall Protection & Auto-Recovery State Machine
        self.is_stalled = False
        self.stall_timer = 0.0
        self.auto_sweep_cooldown = 0.0

        # ATT Transection Detection
        self.prev_impedance = 20.0
        self.dZ_dt = 0.0
        self.transection_detected = False
        self.transection_timer = 0.0

    def reset_and_sweep(self, real_fs):
        """Instant fault reset and fast chirp frequency sweep to re-acquire resonance"""
        self.freq_output = real_fs
        self.pll_integral = 0.0
        self.amp_integral = 40.0
        self.is_stalled = False
        self.stall_timer = 0.0
        self.transection_detected = False
        self.transection_timer = 0.0

    def step(self, dt, sensed_phase_deg, sensed_amplitude_um, sensed_impedance, real_fs):
        if not self.power_active:
            # Standby mode: soft reset and idle
            self.dac_voltage_vrms = 0.0
            self.pll_integral = 0.0
            self.is_stalled = False
            return

        # 1. Stall / Overload Detection
        # When touching bone or hard metal, damping Rm > 260 Ohm or phase error is large
        if sensed_impedance > 260.0 or abs(sensed_phase_deg) > 55.0:
            self.stall_timer += dt
            if self.stall_timer > 0.15:
                self.is_stalled = True
        else:
            self.stall_timer = max(0.0, self.stall_timer - dt * 2.0)
            if self.stall_timer == 0.0 and sensed_impedance < 200.0:
                self.is_stalled = False

        # 2. Auto-Recovery Mechanism (GEN11 Auto Frequency Sweep)
        # If stalled or frequency slipped too far, periodically sweep towards real fs
        if self.is_stalled:
            self.auto_sweep_cooldown += dt
            # If load decreases (surgeon pulls knife away or releases grip), auto-recover
            if sensed_impedance < 220.0 or self.auto_sweep_cooldown > 0.8:
                self.reset_and_sweep(real_fs)
                self.auto_sweep_cooldown = 0.0

        # 3. PLL Resonance Tracking Loop (NEGATIVE FEEDBACK)
        # S-curve: When f < fs, phase < 0. To increase f, freq correction must be POSITIVE.
        # When f > fs, phase > 0. To decrease f, freq correction must be NEGATIVE.
        # Therefore: freq_adjust = - (Kp * phase_error + Ki * integral)
        phase_error = sensed_phase_deg - self.target_phase_deg
        if self.pll_enabled:
            self.pll_integral += phase_error * dt
            self.pll_integral = max(-800.0, min(800.0, self.pll_integral))
            
            freq_adjust = - (self.pll_kp * phase_error + self.pll_ki * self.pll_integral)
            # Slew rate limit to prevent wild frequency steps
            freq_adjust = max(-2500.0, min(2500.0, freq_adjust))
            self.freq_output += freq_adjust * dt
            
            # Constrain frequency search band (52.5 kHz ~ 58.0 kHz)
            self.freq_output = max(52500.0, min(58000.0, self.freq_output))

        # 4. Amplitude Regulation PI (Adjusting DAC drive voltage)
        amp_error = self.target_amplitude_um - sensed_amplitude_um
        if self.amp_control_enabled:
            # If stalled, clamp drive voltage to avoid blowing up the transducer
            if self.is_stalled:
                self.dac_voltage_vrms = 60.0
            else:
                self.amp_integral += amp_error * dt
                self.amp_integral = max(10.0, min(self.max_dac_voltage, self.amp_integral))
                v_cmd = (self.amp_kp * amp_error) + self.amp_integral
                self.dac_voltage_vrms = max(self.min_dac_voltage, min(self.max_dac_voltage, v_cmd))

        # 5. Adaptive Tissue Technology (ATT) Transection Analysis
        self.dZ_dt = (sensed_impedance - self.prev_impedance) / max(0.001, dt)
        self.prev_impedance = sensed_impedance
        
        if sensed_impedance > 55.0 and self.dZ_dt < -150.0:
            self.transection_detected = True
            self.transection_timer = 2.0
        
        if self.transection_timer > 0:
            self.transection_timer -= dt
            if self.transection_timer <= 0:
                self.transection_detected = False


# ----------------------------------------------------------------------
# Interactive GUI Application (Tkinter Real-Time Dashboard)
# ----------------------------------------------------------------------
class UltrasonicSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ETHICON™ GEN11 Ultrasonic Surgical Generator - Closed-Loop Control & Resonance Tracking Simulator")
        self.root.geometry("1320x900")
        self.root.configure(bg="#121820")

        # Models
        self.physics = UltrasonicSurgicalPhysics()
        self.fpga = FpgaController()

        # Simulation Runtime Control
        self.running = True
        self.sim_time = 0.0
        self.dt = 0.03  # 30 ms
        
        # Automated scenarios
        self.current_scenario = "manual"
        self.scenario_timer = 0.0

        # History buffers for waveform oscilloscopes
        self.buf_size = 180
        self.time_buf = [0.0] * self.buf_size
        self.freq_buf = [55500.0] * self.buf_size
        self.fs_target_buf = [55500.0] * self.buf_size
        self.phase_buf = [0.0] * self.buf_size
        self.v_buf = [40.0] * self.buf_size
        self.i_buf = [0.5] * self.buf_size
        self.amp_buf = [65.0] * self.buf_size
        self.z_buf = [20.0] * self.buf_size

        self.setup_ui()
        self.schedule_next_frame()

    def setup_ui(self):
        # 1. Top Header Banner
        header = tk.Frame(self.root, bg="#1a222d", height=56, bd=0)
        header.pack(fill=tk.X, side=tk.TOP)
        
        title_label = tk.Label(
            header,
            text="ETHICON™ GEN11 Style — Ultrasonic Surgical Generator Closed-Loop Tracking Architecture",
            font=("Segoe UI", 12, "bold"),
            fg="#00e5ff",
            bg="#1a222d",
            padx=15, pady=8
        )
        title_label.pack(side=tk.LEFT)

        # Right Header: Power ON/OFF Button & Status Badge
        r_header = tk.Frame(header, bg="#1a222d")
        r_header.pack(side=tk.RIGHT, padx=15)

        self.btn_power = tk.Button(
            r_header,
            text="⚡ 腳踏開關: 激發中 (ACTIVE: ON)",
            font=("Segoe UI", 9, "bold"),
            bg="#059669", fg="#ffffff",
            activebackground="#10b981", activeforeground="#ffffff",
            relief=tk.RAISED, padx=10, pady=4,
            command=self.toggle_power_switch
        )
        self.btn_power.pack(side=tk.LEFT, padx=6)

        self.btn_reset_sweep = tk.Button(
            r_header,
            text="🔄 故障重置與自動尋頻 (Reset & Re-Sweep)",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb", fg="#ffffff",
            activebackground="#3b82f6", activeforeground="#ffffff",
            relief=tk.RAISED, padx=10, pady=4,
            command=self.on_reset_and_sweep
        )
        self.btn_reset_sweep.pack(side=tk.LEFT, padx=6)

        self.status_badge = tk.Label(
            r_header,
            text="● ACTIVE",
            font=("Segoe UI", 9, "bold"),
            fg="#10b981",
            bg="#064e3b",
            padx=10, pady=4
        )
        self.status_badge.pack(side=tk.LEFT, padx=6)

        # 2. Main Container
        main_container = tk.Frame(self.root, bg="#121820")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left Control Column
        left_col = tk.Frame(main_container, bg="#19202a", width=410, bd=1, relief=tk.SOLID)
        left_col.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_col.pack_propagate(False)

        # Right Display Area
        right_col = tk.Frame(main_container, bg="#121820")
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.build_left_panel(left_col)
        self.build_right_panel(right_col)

    def build_left_panel(self, parent):
        # Section 1: SOC UI & Control
        sec_soc = tk.LabelFrame(parent, text=" 1. SOC UI & Generator Settings ", font=("Segoe UI", 10, "bold"), fg="#38bdf8", bg="#19202a", padx=8, pady=6)
        sec_soc.pack(fill=tk.X, padx=8, pady=4)

        row_pwr = tk.Frame(sec_soc, bg="#19202a")
        row_pwr.pack(fill=tk.X, pady=2)
        tk.Label(row_pwr, text="Cutting Power Level:", font=("Segoe UI", 9), fg="#e2e8f0", bg="#19202a").pack(side=tk.LEFT)
        
        self.pwr_var = tk.IntVar(value=3)
        for lvl in [1, 2, 3, 4, 5]:
            r = tk.Radiobutton(row_pwr, text=f"L{lvl}", variable=self.pwr_var, value=lvl,
                               command=self.on_power_level_change,
                               font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#19202a", selectcolor="#0f172a", activebackground="#19202a")
            r.pack(side=tk.LEFT, padx=3)

        # Swithes
        row_sw = tk.Frame(sec_soc, bg="#19202a")
        row_sw.pack(fill=tk.X, pady=3)
        
        self.pll_switch_var = tk.BooleanVar(value=True)
        self.amp_switch_var = tk.BooleanVar(value=True)
        
        cb_pll = tk.Checkbutton(row_sw, text="FPGA Phase Tracking (PLL)", variable=self.pll_switch_var,
                                command=self.on_toggle_pll,
                                font=("Segoe UI", 9, "bold"), fg="#4ade80", bg="#19202a", selectcolor="#0f172a", activebackground="#19202a")
        cb_pll.pack(anchor=tk.W)
        
        cb_amp = tk.Checkbutton(row_sw, text="Constant Amplitude PI Control", variable=self.amp_switch_var,
                                command=self.on_toggle_amp,
                                font=("Segoe UI", 9, "bold"), fg="#f472b6", bg="#19202a", selectcolor="#0f172a", activebackground="#19202a")
        cb_amp.pack(anchor=tk.W)

        # Section 2: Clinical Scenario Stimulus
        sec_scen = tk.LabelFrame(parent, text=" 2. Clinical Scenario Stimulus (時序情境) ", font=("Segoe UI", 10, "bold"), fg="#fbbf24", bg="#19202a", padx=8, pady=6)
        sec_scen.pack(fill=tk.X, padx=8, pady=4)

        btn_row1 = tk.Frame(sec_scen, bg="#19202a")
        btn_row1.pack(fill=tk.X, pady=2)
        tk.Button(btn_row1, text="Air Idle (空載無組織)", bg="#2a3545", fg="#e2e8f0", relief=tk.GROOVE, command=self.scen_air).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(btn_row1, text="Fat Tissue (切脂肪)", bg="#2a3545", fg="#e2e8f0", relief=tk.GROOVE, command=self.scen_fat).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        btn_row2 = tk.Frame(sec_scen, bg="#19202a")
        btn_row2.pack(fill=tk.X, pady=2)
        self.btn_vessel = tk.Button(btn_row2, text="▶ 血管閉合切斷全流程 (Vessel Seal & Cut)", bg="#0284c7", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief=tk.RAISED, command=self.scen_vessel_cut)
        self.btn_vessel.pack(fill=tk.X, padx=2)

        btn_row3 = tk.Frame(sec_scen, bg="#19202a")
        btn_row3.pack(fill=tk.X, pady=2)
        tk.Button(btn_row3, text="▶ 厚肌肉重負載切割 (Heavy Muscle)", bg="#7c3aed", fg="#ffffff", relief=tk.RAISED, command=self.scen_muscle_cut).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(btn_row3, text="⚠ 碰骨/金屬鉗失諧 (Stall)", bg="#dc2626", fg="#ffffff", relief=tk.RAISED, command=self.scen_stall).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Section 3: Manual Real-time Variables Adjustment
        sec_vars = tk.LabelFrame(parent, text=" 3. 手動即時微調變因 (Arbitrary Stimulus) ", font=("Segoe UI", 10, "bold"), fg="#a78bfa", bg="#19202a", padx=8, pady=6)
        sec_vars.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Slider 1: Tissue Acoustic Damping
        tk.Label(sec_vars, text="Tissue Acoustic Damping (阻尼 R_tissue, Ω):", font=("Segoe UI", 8), fg="#cbd5e1", bg="#19202a").pack(anchor=tk.W)
        self.slider_damping = tk.Scale(sec_vars, from_=0, to=350, orient=tk.HORIZONTAL, bg="#19202a", fg="#38bdf8", highlightthickness=0, troughcolor="#0f172a", command=self.on_manual_slider_change)
        self.slider_damping.set(0)
        self.slider_damping.pack(fill=tk.X, pady=(0, 2))

        # Slider 2: Clamp Pressure
        tk.Label(sec_vars, text="Clamp Pressure / Grip (刀口夾持力 0~100%):", font=("Segoe UI", 8), fg="#cbd5e1", bg="#19202a").pack(anchor=tk.W)
        self.slider_clamp = tk.Scale(sec_vars, from_=0, to=100, orient=tk.HORIZONTAL, bg="#19202a", fg="#38bdf8", highlightthickness=0, troughcolor="#0f172a", command=self.on_manual_slider_change)
        self.slider_clamp.set(0)
        self.slider_clamp.pack(fill=tk.X, pady=(0, 2))

        # Slider 3: Tissue Stiffness Shift
        tk.Label(sec_vars, text="Tissue Stiffness Shift (組織剛度頻偏, Hz):", font=("Segoe UI", 8), fg="#cbd5e1", bg="#19202a").pack(anchor=tk.W)
        self.slider_stiffness = tk.Scale(sec_vars, from_=-400, to=200, orient=tk.HORIZONTAL, bg="#19202a", fg="#38bdf8", highlightthickness=0, troughcolor="#0f172a", command=self.on_manual_slider_change)
        self.slider_stiffness.set(0)
        self.slider_stiffness.pack(fill=tk.X, pady=(0, 2))

        # Slider 4: Handpiece Temperature
        tk.Label(sec_vars, text="Handpiece Temperature (刀柄溫升, °C):", font=("Segoe UI", 8), fg="#cbd5e1", bg="#19202a").pack(anchor=tk.W)
        self.slider_temp = tk.Scale(sec_vars, from_=25, to=130, orient=tk.HORIZONTAL, bg="#19202a", fg="#fb923c", highlightthickness=0, troughcolor="#0f172a", command=self.on_manual_temp_change)
        self.slider_temp.set(25)
        self.slider_temp.pack(fill=tk.X, pady=(0, 2))

        # Fixed frequency test slider (Only effective if PLL is OFF)
        tk.Label(sec_vars, text="Manual Driving Frequency (PLL OFF 時手動固定頻率):", font=("Segoe UI", 8), fg="#cbd5e1", bg="#19202a").pack(anchor=tk.W)
        self.slider_fixed_freq = tk.Scale(sec_vars, from_=54000, to=57000, orient=tk.HORIZONTAL, bg="#19202a", fg="#ef4444", highlightthickness=0, troughcolor="#0f172a", command=self.on_manual_freq_change)
        self.slider_fixed_freq.set(55500)
        self.slider_fixed_freq.pack(fill=tk.X, pady=(0, 2))

    def build_right_panel(self, parent):
        # 1. Top Section: Surgical Knife & Tissue Micro-Physical Animation
        knife_frame = tk.LabelFrame(parent, text=" [Real-Time Physical Stimulus] 手術刀咬合組織與換能器狀態動態顯微觀察 ", font=("Segoe UI", 9, "bold"), fg="#34d399", bg="#19202a", padx=6, pady=4)
        knife_frame.pack(fill=tk.X, pady=(0, 6))
        
        self.knife_canvas = tk.Canvas(knife_frame, height=145, bg="#0d1117", highlightthickness=0)
        self.knife_canvas.pack(fill=tk.X)

        # 2. Middle Section: Telemetry Digital Readout Bar
        telemetry_frame = tk.Frame(parent, bg="#19202a", padx=8, pady=4)
        telemetry_frame.pack(fill=tk.X, pady=(0, 6))

        self.lbl_target_fs = self.create_badge(telemetry_frame, "Mechanical fs (目標)", "55500 Hz", "#38bdf8")
        self.lbl_drive_f = self.create_badge(telemetry_frame, "FPGA DDS 驅動頻率", "55500 Hz", "#4ade80")
        self.lbl_phase = self.create_badge(telemetry_frame, "相位差 (Δφ)", "0.0 °", "#a78bfa")
        self.lbl_amp = self.create_badge(telemetry_frame, "刀尖振幅 (Tip)", "65.0 μm", "#f472b6")
        self.lbl_dac_v = self.create_badge(telemetry_frame, "DAC 電壓 (Vrms)", "40.0 V", "#fbbf24")
        self.lbl_i_tot = self.create_badge(telemetry_frame, "電流 (Irms)", "0.45 A", "#34d399")
        self.lbl_power = self.create_badge(telemetry_frame, "即時功率 (Power)", "18.0 W", "#f87171")
        self.lbl_temp = self.create_badge(telemetry_frame, "換能器溫度", "25.0 °C", "#f97316")

        # 3. Bottom Section: Real-Time Multi-Trace Oscilloscope
        scope_frame = tk.LabelFrame(parent, text=" [Closed-Loop Signal Scope] 即時波形與演算法收斂軌跡 (FPGA Frequency, Phase Error, DAC V, Amplitude) ", font=("Segoe UI", 9, "bold"), fg="#60a5fa", bg="#19202a", padx=6, pady=4)
        scope_frame.pack(fill=tk.BOTH, expand=True)

        self.scope_canvas = tk.Canvas(scope_frame, bg="#0a0f16", highlightthickness=0)
        self.scope_canvas.pack(fill=tk.BOTH, expand=True)

    def create_badge(self, parent, title, val, color):
        box = tk.Frame(parent, bg="#121820", padx=6, pady=3, bd=1, relief=tk.GROOVE)
        box.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Label(box, text=title, font=("Segoe UI", 7), fg="#94a3b8", bg="#121820").pack()
        lbl = tk.Label(box, text=val, font=("Segoe UI", 10, "bold"), fg=color, bg="#121820")
        lbl.pack()
        return lbl

    # ------------------------------------------------------------------
    # User Control Callbacks
    # ------------------------------------------------------------------
    def toggle_power_switch(self):
        self.fpga.power_active = not self.fpga.power_active
        if self.fpga.power_active:
            self.btn_power.config(text="⚡ 腳踏開關: 激發中 (ACTIVE: ON)", bg="#059669")
            self.status_badge.config(text="● ACTIVE", fg="#10b981", bg="#064e3b")
        else:
            self.btn_power.config(text="⏸ 腳踏放開: 待機 (STANDBY: OFF)", bg="#d97706")
            self.status_badge.config(text="⏸ STANDBY", fg="#fbbf24", bg="#451a03")

    def on_reset_and_sweep(self):
        self.fpga.reset_and_sweep(self.physics.current_fs)

    def on_power_level_change(self):
        lvl = self.pwr_var.get()
        self.fpga.target_amplitude_um = 35.0 + lvl * 10.0

    def on_toggle_pll(self):
        self.fpga.pll_enabled = self.pll_switch_var.get()

    def on_toggle_amp(self):
        self.fpga.amp_control_enabled = self.amp_switch_var.get()

    def on_manual_slider_change(self, val):
        self.current_scenario = "manual"
        self.physics.tissue_damping = float(self.slider_damping.get())
        self.physics.clamp_pressure = float(self.slider_clamp.get()) / 100.0
        self.physics.tissue_stiffness = float(self.slider_stiffness.get())

    def on_manual_temp_change(self, val):
        self.physics.temperature = float(self.slider_temp.get())

    def on_manual_freq_change(self, val):
        if not self.fpga.pll_enabled:
            self.fpga.freq_output = float(self.slider_fixed_freq.get())

    # ------------------------------------------------------------------
    # Automated Scenarios
    # ------------------------------------------------------------------
    def scen_air(self):
        self.reset_vessel_btn()
        self.current_scenario = "manual"
        self.slider_damping.set(0)
        self.slider_clamp.set(0)
        self.slider_stiffness.set(0)
        self.on_manual_slider_change(0)
        self.fpga.reset_and_sweep(self.physics.current_fs)

    def scen_fat(self):
        self.reset_vessel_btn()
        self.current_scenario = "manual"
        self.slider_damping.set(50)
        self.slider_clamp.set(60)
        self.slider_stiffness.set(-40)
        self.on_manual_slider_change(0)
        self.fpga.reset_and_sweep(self.physics.current_fs)

    def scen_muscle_cut(self):
        self.reset_vessel_btn()
        self.current_scenario = "manual"
        self.slider_damping.set(160)
        self.slider_clamp.set(90)
        self.slider_stiffness.set(-140)
        self.on_manual_slider_change(0)
        self.fpga.reset_and_sweep(self.physics.current_fs)

    def scen_stall(self):
        # Touching bone or metallic clamp: damping spikes and stiffness shifts
        self.reset_vessel_btn()
        self.current_scenario = "manual"
        self.slider_damping.set(290)
        self.slider_clamp.set(100)
        self.slider_stiffness.set(-350)
        self.on_manual_slider_change(0)

    def reset_vessel_btn(self):
        self.vessel_cut_state = "idle"
        if hasattr(self, 'btn_vessel'):
            self.btn_vessel.config(text="▶ 血管閉合切斷全流程 (Vessel Seal & Cut)", bg="#0284c7")

    def scen_vessel_cut(self):
        if not hasattr(self, 'vessel_cut_state'):
            self.vessel_cut_state = "idle"
        
        if self.vessel_cut_state == "idle":
            self.vessel_cut_state = "playing"
            self.current_scenario = "vessel_cut"
            self.scenario_timer = 0.0
            self.btn_vessel.config(text="⏸ 暫停血管流程 (Pause)", bg="#d97706")
        elif self.vessel_cut_state == "playing":
            self.vessel_cut_state = "paused"
            self.btn_vessel.config(text="▶ 繼續血管流程 (Resume)", bg="#059669")
        elif self.vessel_cut_state == "paused":
            self.vessel_cut_state = "playing"
            self.btn_vessel.config(text="⏸ 暫停血管流程 (Pause)", bg="#d97706")

    # ------------------------------------------------------------------
    # Real-Time Dynamic Engine
    # ------------------------------------------------------------------
    def schedule_next_frame(self):
        if self.running:
            self.update_simulation_step()
            self.render_knife_canvas()
            self.render_oscilloscope()
            self.root.after(30, self.schedule_next_frame)

    def update_simulation_step(self):
        if getattr(self, 'vessel_cut_state', 'idle') == "paused":
            return

        self.sim_time += self.dt

        # Progress automated scenario if active
        if self.current_scenario == "vessel_cut" and getattr(self, 'vessel_cut_state', 'idle') == "playing":
            self.scenario_timer += self.dt
            t = self.scenario_timer
            if t < 1.5:
                progress = t / 1.5
                self.physics.clamp_pressure = 0.4 + 0.5 * progress
                self.physics.tissue_damping = 40.0 + 100.0 * progress
                self.physics.tissue_stiffness = -80.0 * progress
            elif t < 3.5:
                # Boiling / desiccation phase
                self.physics.clamp_pressure = 0.95
                self.physics.tissue_damping = 140.0 + 100.0 * ((t - 1.5) / 2.0)
                self.physics.tissue_stiffness = -80.0 - 60.0 * ((t - 1.5) / 2.0)
            elif t < 4.2:
                # Instant of transection!
                factor = 1.0 - (t - 3.5) / 0.7
                self.physics.tissue_damping = max(0.0, 240.0 * factor)
                self.physics.tissue_stiffness = -140.0 * factor
                self.physics.clamp_pressure = max(0.1, 0.95 * factor)
            else:
                self.physics.tissue_damping = 0.0
                self.physics.tissue_stiffness = 0.0
                self.physics.clamp_pressure = 0.0
                if t > 5.5:
                    self.current_scenario = "manual"
                    self.reset_vessel_btn()

            self.slider_damping.set(int(self.physics.tissue_damping))
            self.slider_clamp.set(int(self.physics.clamp_pressure * 100))
            self.slider_stiffness.set(int(self.physics.tissue_stiffness))

        # 1. Physics Step
        drive_f = self.fpga.freq_output
        drive_v = self.fpga.dac_voltage_vrms
        self.physics.update(self.dt, drive_f, drive_v, self.fpga.power_active)

        # 2. FPGA Step
        self.fpga.step(self.dt, self.physics.phase_deg, self.physics.blade_amplitude_um, self.physics.impedance_mag, self.physics.current_fs)

        # Update sliders that drift physically
        self.slider_temp.set(int(self.physics.temperature))

        # 3. Update digital readout badges
        self.lbl_target_fs.config(text=f"{self.physics.current_fs:0.1f} Hz")
        self.lbl_drive_f.config(text=f"{self.fpga.freq_output:0.1f} Hz")
        
        if not self.fpga.power_active:
            self.lbl_phase.config(text="STANDBY", fg="#fbbf24")
            self.lbl_amp.config(text="0.0 μm", fg="#94a3b8")
            self.lbl_dac_v.config(text="0.0 V", fg="#94a3b8")
            self.lbl_i_tot.config(text="0.00 A", fg="#94a3b8")
            self.lbl_power.config(text="0.0 W", fg="#94a3b8")
        else:
            self.lbl_phase.config(
                text=f"{self.physics.phase_deg:+0.2f} °",
                fg="#4ade80" if abs(self.physics.phase_deg) < 5.0 else ("#facc15" if abs(self.physics.phase_deg) < 20.0 else "#ef4444")
            )
            self.lbl_amp.config(
                text=f"{self.physics.blade_amplitude_um:0.1f} μm",
                fg="#38bdf8" if abs(self.physics.blade_amplitude_um - self.fpga.target_amplitude_um) < 5.0 else "#f43f5e"
            )
            self.lbl_dac_v.config(text=f"{self.fpga.dac_voltage_vrms:0.1f} V")
            self.lbl_i_tot.config(text=f"{self.physics.total_current:0.2f} A")
            self.lbl_power.config(text=f"{self.physics.active_power_w:0.1f} W")

        self.lbl_temp.config(
            text=f"{self.physics.temperature:0.1f} °C",
            fg="#4ade80" if self.physics.temperature < 60 else ("#fbbf24" if self.physics.temperature < 95 else "#ef4444")
        )

        # 4. Push data to history buffers
        self.time_buf.pop(0)
        self.time_buf.append(self.sim_time)

        self.freq_buf.pop(0)
        self.freq_buf.append(self.fpga.freq_output)

        self.fs_target_buf.pop(0)
        self.fs_target_buf.append(self.physics.current_fs)

        self.phase_buf.pop(0)
        self.phase_buf.append(self.physics.phase_deg if self.fpga.power_active else 0.0)

        self.v_buf.pop(0)
        self.v_buf.append(self.fpga.dac_voltage_vrms)

        self.i_buf.pop(0)
        self.i_buf.append(self.physics.total_current)

        self.amp_buf.pop(0)
        self.amp_buf.append(self.physics.blade_amplitude_um)

        self.z_buf.pop(0)
        self.z_buf.append(self.physics.impedance_mag)

    # ------------------------------------------------------------------
    # Visual Canvas Rendering
    # ------------------------------------------------------------------
    def render_knife_canvas(self):
        cv = self.knife_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 100: w = 800
        if h < 50: h = 145

        cv.create_rectangle(0, 0, w, h, fill="#0d1117", outline="")

        # 1. Transducer (Handpiece Piezo PZT Stack)
        pzt_x0 = 40
        pzt_y0 = h // 2 - 32
        pzt_x1 = 150
        pzt_y1 = h // 2 + 32
        cv.create_rectangle(pzt_x0, pzt_y0, pzt_x1, pzt_y1, fill="#1e293b", outline="#475569", width=2)
        cv.create_text((pzt_x0 + pzt_x1)//2, pzt_y0 - 10, text="4-Piezo PZT Stack", fill="#cbd5e1", font=("Segoe UI", 10, "bold"))
        
        for i in range(4):
            dx = pzt_x0 + 10 + i * 25
            col = "#38bdf8" if (i % 2 == 0) else "#818cf8"
            cv.create_rectangle(dx, pzt_y0 + 8, dx + 18, pzt_y1 - 8, fill=col, outline="#ffffff")
        
        # 2. Waveguide / Acoustic Horn
        horn_x0 = pzt_x1
        horn_x1 = w - 240
        y_mid = h // 2
        
        # Vibration oscillation graphic effect (only when active and not paused)
        is_paused = getattr(self, 'vessel_cut_state', 'idle') == "paused"
        if self.fpga.power_active and not is_paused:
            vib_offset = math.sin(self.sim_time * 25.0) * (self.physics.blade_amplitude_um / 15.0)
        else:
            vib_offset = 0.0

        cv.create_polygon(
            horn_x0, y_mid - 24,
            horn_x1, y_mid - 8,
            horn_x1, y_mid + 8,
            horn_x0, y_mid + 24,
            fill="#64748b", outline="#94a3b8"
        )
        cv.create_text((horn_x0 + horn_x1)//2, y_mid - 20, text="Titanium Acoustic Waveguide (λ/2 Horn)", fill="#f1f5f9", font=("Segoe UI", 10, "bold"))

        # 3. Blade Tip
        tip_x0 = horn_x1
        tip_x1 = horn_x1 + 60 + vib_offset
        cv.create_polygon(
            tip_x0, y_mid - 7,
            tip_x1, y_mid - 2,
            tip_x1 + 10, y_mid,
            tip_x1, y_mid + 2,
            tip_x0, y_mid + 7,
            fill="#e2e8f0", outline="#38bdf8", width=2
        )
        
        # 4. Upper Clamp Arm (PTFE Tissue Pad)
        clamp_gap = max(4.0, 30.0 * (1.0 - self.physics.clamp_pressure))
        clamp_y = y_mid - clamp_gap - 12
        cv.create_rectangle(tip_x0, clamp_y, tip_x0 + 70, clamp_y + 10, fill="#f8fafc", outline="#cbd5e1")
        cv.create_text(tip_x0 + 35, clamp_y - 8, text="PTFE Tissue Pad", fill="#ffffff", font=("Segoe UI", 9, "bold"))

        # 5. Human Tissue
        tissue_h = max(2.0, clamp_gap)
        tissue_col = "#dc2626" if self.physics.tissue_damping > 30 else "#f87171"
        if self.physics.clamp_pressure > 0.05:
            cv.create_oval(tip_x0 + 10, y_mid - tissue_h//2, tip_x0 + 55, y_mid + tissue_h//2 + 4, fill=tissue_col, outline="#b91c1c")
            if self.fpga.power_active and self.physics.active_power_w > 15.0:
                for b in range(4):
                    bx = tip_x0 + 20 + b * 10 + math.sin(self.sim_time * 10 + b) * 5
                    by = y_mid - 15 - b * 8
                    cv.create_oval(bx, by, bx+4, by+4, fill="#e0f2fe", outline="")
                cv.create_text(tip_x0 + 35, y_mid - 28, text="Cavitation Vapor", fill="#38bdf8", font=("Segoe UI", 9, "bold", "italic"))

        # 6. Status and Alerts
        if not self.fpga.power_active:
            cv.create_rectangle(w - 240, 15, w - 15, 60, fill="#451a03", outline="#f59e0b", width=2)
            cv.create_text(w - 127, 37, text="⏸ GENERATOR STANDBY\n(腳踏開關已放開 - 輸出已關閉)", fill="#fde68a", font=("Segoe UI", 9, "bold"), justify=tk.CENTER)
        elif self.fpga.transection_detected:
            cv.create_rectangle(w - 240, 15, w - 15, 60, fill="#065f46", outline="#34d399", width=2)
            cv.create_text(w - 127, 37, text="✔ ATT TRANSECTION COMPLETE!\n(組織切斷完成 - 自動降載保護)", fill="#a7f3d0", font=("Segoe UI", 9, "bold"), justify=tk.CENTER)
        elif self.fpga.is_stalled:
            cv.create_rectangle(w - 240, 15, w - 15, 60, fill="#7f1d1d", outline="#ef4444", width=2)
            cv.create_text(w - 127, 37, text="⚠ ACOUSTIC OVERLOAD / STALL\n(碰骨失諧保護 - 自動尋頻中)", fill="#fecaca", font=("Segoe UI", 9, "bold"), justify=tk.CENTER)
        else:
            cv.create_rectangle(w - 240, 15, w - 15, 60, fill="#1e293b", outline="#334155")
            cv.create_text(w - 127, 37, text=f"Scenario: {self.current_scenario.upper()}\nGrip: {int(self.physics.clamp_pressure*100)}% | Active", fill="#94a3b8", font=("Segoe UI", 8), justify=tk.CENTER)

        # Vibration displacement indicator
        cv.create_text(tip_x1 + 18, y_mid + 20, text=f"↔ {self.physics.blade_amplitude_um:0.1f} μm pk-pk", fill="#38bdf8", font=("Segoe UI", 11, "bold"), anchor=tk.W)

    def render_oscilloscope(self):
        cv = self.scope_canvas
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 100: w = 800
        if h < 100: h = 400

        n_plots = 4
        margin_top = 8
        margin_bottom = 20
        plot_h = (h - margin_top - margin_bottom) / n_plots
        x_left = 68
        x_right = w - 48

        # Scope 1: Dual-Axis Freq (Left: 54~57 kHz) & Phase (Right: -50°~+50°)
        y0_1 = margin_top
        y1_1 = y0_1 + plot_h - 8
        self.draw_subscope_frame(cv, x_left, y0_1, x_right, y1_1, 
                                "CH1: 雙軸頻率追蹤與相位差 (Left: Freq 54~57 kHz | Right: Phase -50°~+50°)", 
                                "57.0k", "54.0k", right_max="+50°", right_min="-50°")
        
        # 0° Resonance line
        y_zero1 = (y0_1 + y1_1) / 2
        cv.create_line(x_left, y_zero1, x_right, y_zero1, fill="#059669", width=1, dash=(3, 3))
        cv.create_text(x_right + 6, y_zero1, text="0°", fill="#34d399", font=("Segoe UI", 7, "bold"), anchor=tk.W)

        pts_target_fs = []
        pts_drive_f = []
        pts_phase = []
        f_min, f_max = 54000.0, 57000.0
        for i in range(self.buf_size):
            x = x_left + (i / (self.buf_size - 1)) * (x_right - x_left)
            y_tgt = y1_1 - ((self.fs_target_buf[i] - f_min) / (f_max - f_min)) * (y1_1 - y0_1)
            y_drv = y1_1 - ((self.freq_buf[i] - f_min) / (f_max - f_min)) * (y1_1 - y0_1)
            deg = self.phase_buf[i]
            y_p = y_zero1 - (deg / 50.0) * ((y1_1 - y0_1) / 2)
            pts_target_fs.extend([x, max(y0_1, min(y1_1, y_tgt))])
            pts_drive_f.extend([x, max(y0_1, min(y1_1, y_drv))])
            pts_phase.extend([x, max(y0_1, min(y1_1, y_p))])
        
        cv.create_line(pts_target_fs, fill="#fbbf24", width=2, dash=(4, 2))
        cv.create_line(pts_drive_f, fill="#00e5ff", width=2)
        cv.create_line(pts_phase, fill="#c084fc", width=2)
        cv.create_text(x_right - 280, y0_1 + 10, text="-- Target fs", fill="#fbbf24", font=("Segoe UI", 8, "bold"), anchor=tk.W)
        cv.create_text(x_right - 190, y0_1 + 10, text="— Drive f", fill="#00e5ff", font=("Segoe UI", 8, "bold"), anchor=tk.W)
        cv.create_text(x_right - 105, y0_1 + 10, text="— 相位 Δφ", fill="#c084fc", font=("Segoe UI", 8, "bold"), anchor=tk.W)

        # Scope 2: DAC Voltage Command (0 ~ 160 Vrms)
        y0_2 = y1_1 + 8
        y1_2 = y0_2 + plot_h - 8
        self.draw_subscope_frame(cv, x_left, y0_2, x_right, y1_2, "CH2: 換能器驅動電壓 (DAC Voltage Vrms)", "160V", "0V")
        pts_dac = []
        for i in range(self.buf_size):
            x = x_left + (i / (self.buf_size - 1)) * (x_right - x_left)
            y_d = y1_2 - (self.v_buf[i] / 160.0) * (y1_2 - y0_2)
            pts_dac.extend([x, max(y0_2, min(y1_2, y_d))])
        cv.create_line(pts_dac, fill="#fbbf24", width=2)
        cv.create_text(x_right - 170, y0_2 + 10, text=f"— 即時電壓: {self.fpga.drive_voltage_vrms:.1f} Vrms", fill="#fbbf24", font=("Segoe UI", 8, "bold"), anchor=tk.W)

        # Scope 3: Tip Amplitude (0 ~ 120 μm)
        y0_3 = y1_2 + 8
        y1_3 = y0_3 + plot_h - 8
        self.draw_subscope_frame(cv, x_left, y0_3, x_right, y1_3, "CH3: 刀尖機械位移衝程振幅 (Tip Stroke Amplitude μm pk-pk)", "120μm", "0μm")
        pts_amp = []
        for i in range(self.buf_size):
            x = x_left + (i / (self.buf_size - 1)) * (x_right - x_left)
            y_a = y1_3 - (self.amp_buf[i] / 120.0) * (y1_3 - y0_3)
            pts_amp.extend([x, max(y0_3, min(y1_3, y_a))])
        cv.create_line(pts_amp, fill="#f43f5e", width=2)
        cv.create_text(x_right - 230, y0_3 + 10, text=f"— 刀尖位移: {self.physics.blade_amplitude_um:.1f} μm (目標 {self.fpga.target_amplitude_um:.0f}μm)", fill="#f43f5e", font=("Segoe UI", 8, "bold"), anchor=tk.W)

        # Scope 4: Total Current (0 ~ 2.5 A)
        y0_4 = y1_3 + 8
        y1_4 = y0_4 + plot_h - 8
        self.draw_subscope_frame(cv, x_left, y0_4, x_right, y1_4, "CH4: 換能器總驅動電流 (Total Current A_rms)", "2.5A", "0.0A")
        pts_curr = []
        for i in range(self.buf_size):
            x = x_left + (i / (self.buf_size - 1)) * (x_right - x_left)
            y_c = y1_4 - (self.i_buf[i] / 2.5) * (y1_4 - y0_4)
            pts_curr.extend([x, max(y0_4, min(y1_4, y_c))])
        cv.create_line(pts_curr, fill="#34d399", width=2)
        cv.create_text(x_right - 180, y0_4 + 10, text=f"— 總電流: {self.physics.total_current:.2f} A_rms", fill="#34d399", font=("Segoe UI", 8, "bold"), anchor=tk.W)

        if self.current_scenario == "vessel_cut":
            t = self.scenario_timer
            if t < 1.5:
                phase_text = "【Phase 1 變性熔合】Rm上升 ➔ fs負偏 (-80Hz) ➔ DPLL追頻調諧"
            elif t < 3.5:
                phase_text = "【Phase 2 脫水峰值】Rm達頂峰 (250Ω) ➔ 電流達1.8A ➔ 驅動電壓拉升"
            elif t < 4.2:
                phase_text = "【Phase 3 ⚡離斷瞬間】管壁切斷 ➔ 電流斷崖式驟降 ➔ 頻率彈回55.5kHz!"
            else:
                phase_text = "【Phase 4 ATT降載】切斷完成提示 ➔ 自動降載待機防過熱"
            cv.create_text(x_left + 10, y1_4 + 12, text=phase_text, fill="#38bdf8", font=("Segoe UI", 9, "bold"), anchor=tk.W)

        if getattr(self, 'vessel_cut_state', 'idle') == "paused":
            cv.create_rectangle(x_left, y0_1, x_right, y1_4, outline="#f59e0b", width=2)
            cv.create_rectangle((x_left + x_right)//2 - 200, y0_1 + 5, (x_left + x_right)//2 + 200, y0_1 + 27, fill="#0f172a", outline="#f59e0b")
            cv.create_text((x_left + x_right)//2, y0_1 + 16, text="⏸ 波形採樣凍結中 (DSO HOLD / PAUSED) — 保持當前瞬間數據", fill="#fbbf24", font=("Segoe UI", 9, "bold"))

    def draw_subscope_frame(self, cv, x0, y0, x1, y1, title, max_label, min_label, right_max=None, right_min=None):
        cv.create_rectangle(x0, y0, x1, y1, fill="#070a0e", outline="#1e293b")
        for div in range(1, 10):
            gx = x0 + (div / 10.0) * (x1 - x0)
            cv.create_line(gx, y0, gx, y1, fill="#111827", dash=(1, 4))
        cv.create_line(x0, (y0+y1)/2, x1, (y0+y1)/2, fill="#111827", dash=(2, 4))
        cv.create_text(x0 + 8, y0 + 10, text=title, fill="#f1f5f9", font=("Segoe UI", 8, "bold"), anchor=tk.W)
        cv.create_text(x0 - 5, y0 + 8, text=max_label, fill="#94a3b8", font=("Segoe UI", 7, "bold"), anchor=tk.E)
        cv.create_text(x0 - 5, y1 - 8, text=min_label, fill="#94a3b8", font=("Segoe UI", 7, "bold"), anchor=tk.E)
        if right_max and right_min:
            cv.create_text(x1 + 5, y0 + 8, text=right_max, fill="#c084fc", font=("Segoe UI", 7, "bold"), anchor=tk.W)
            cv.create_text(x1 + 5, y1 - 8, text=right_min, fill="#c084fc", font=("Segoe UI", 7, "bold"), anchor=tk.W)


# ----------------------------------------------------------------------
# Application Entry Point
# ----------------------------------------------------------------------
def main():
    root = tk.Tk()
    app = UltrasonicSimulatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
