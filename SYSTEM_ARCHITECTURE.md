# ETHICON™ GEN11 超音波手術系統閉環控制架構與共振追頻演算法解析

本文件詳細闡述超音波手術刀（如 Ethicon Harmonic ACE+7、Olympus Thunderbeat）在換能器聲學、電力電子、FPGA 數位訊號處理與人體組織相互作用中的核心控制原理與故障自愈機制。

---

## 一、 超音波控制在手術器械上的關鍵重要性

超音波手術系統並非單純的「高頻交流電源」，而是一套**高 Q 值（品質因數）的微米級機電諧振系統**。

### 1. 為何不能使用「固定頻率 (Fixed 55.5 kHz)」？
- **極窄的諧振頻寬**：壓電換能器（PZT）與鈦合金聲學變幅桿（Waveguide / Horn）系統的機械 $Q$ 值通常在 $500 \sim 1500$。這意味著共振峰的半功率頻寬（$3\text{ dB Bandwidth}$）只有：
  $$\Delta f = \frac{f_s}{Q} \approx \frac{55500\text{ Hz}}{800} \approx 69\text{ Hz}$$
- **頻率偏離 50 Hz 的災難性後果**：
  - 若驅動頻率偏離固有諧振頻率 $f_s$ 超過 $50 \sim 100\text{ Hz}$，系統的電抗（Reactance）暴增數倍，換能器動態臂電流驟降。
  - **刀尖振幅驟降（Displacement Collapse）**：機械位移從 $80\ \mu m$ 跌落至 $<20\ \mu m$，手術刀在人體組織上無法有效產生空化切除與凝固摩擦熱，造成「切不動、死卡組織」。
  - **發熱損耗與器件燒毀**：未轉化為有效機械聲能的電能，全數轉為無功功率與壓電陶瓷的介電損耗（Dielectric Loss），換能器急遽升溫，壓電陶瓷若超過居里溫度（Curie Temperature, 約 $300^\circ\text{C}$，局部熱應力甚至在 $150^\circ\text{C}$ 就會使極化退化），造成換能器永久性退極化報廢。

---

## 二、 物理等效模型：Butterworth-Van Dyke (BVD) 網絡

壓電換能器在諧振點附近的電氣特性，完美遵循 **BVD 等效電路**：

```
           +---[ Static Cap: C0 ]---+
       o---|                        |---o
           +---[ Lm ]---[ Cm ]---[ Rm ]-+
                    (Motional Arm)
```

1. **靜態電容 $C_0$（Clamping Capacitance）**：
   - 壓電陶瓷片正負電極形成的物理電容，通常約 $2.0 \sim 3.5\text{ nF}$。
   - 產生與頻率成正比的容性無功電流，需在驅動板上透過 LC 匹配電感進行補償。
2. **動態臂（Motional Arm，真實機械運動的電氣映射）**：
   - **動態電感 $L_m$**：等效於換能器與金屬刀桿的**有效振動質量（Effective Mass / Inertia）**，約 $0.2 \sim 0.5\text{ H}$。
   - **動態電容 $C_m$**：等效於波導材料的**彈性柔度（Mechanical Compliance / 1/Stiffness）**，約 $20 \sim 40\text{ fF}$。
   - **動態電阻 $R_m$**：等效於**系統的內部機械摩擦損耗 + 刀尖聲學負載阻尼**。
     - **空載（Air Idle）**：$R_m \approx 15 \sim 30\ \Omega$（超低阻抗，大電流，高 Q 值）。
     - **夾緊軟組織/脂肪（Fat Tissue）**：$R_m \approx 60 \sim 120\ \Omega$。
     - **緊握厚血管/肌肉切除（Muscle / Coagulation）**：$R_m \approx 150 \sim 350\ \Omega$。
     - **碰骨/器械金屬夾失諧（Stall / Jamming）**：$R_m > 260\ \Omega$，彈性模量急變使諧振頻偏 $>300\text{ Hz}$。

3. **串聯諧振頻率公式**：
   $$f_s = \frac{1}{2\pi \sqrt{L_m C_m}}$$
   在 $f_s$ 頻率下，動態臂電感抗與電容抗抵消：$j\omega L_m + \frac{1}{j\omega C_m} = 0$，此時動態臂純粹呈現純電阻 $R_m$。

4. **阻抗相位角與 S-Curve 負反饋**：
   $$\Delta\phi = \text{Phase}(V_{drive}) - \text{Phase}(I_{motional}) = \arctan\left(\frac{\omega L_m - \frac{1}{\omega C_m}}{R_m}\right)$$
   - 當 $f < f_s$：$\Delta\phi < 0$（容性）。欲回到 $f_s$，頻率必須**增加**（$\Delta f > 0$）。
   - 當 $f > f_s$：$\Delta\phi > 0$（感性）。欲回到 $f_s$，頻率必須**減少**（$\Delta f < 0$）。
   - 因此 PLL 環路濾波器必須為**嚴格的負反饋**：
     $$\Delta f = - (K_p \cdot \Delta\phi + K_i \int \Delta\phi \, dt)$$

---

## 三、 超音波控制系統四大關鍵機制與安全保護

### 1. 快速共振追頻演算法 (Resonance Tracking / Digital PLL)
- **目標**：以百微秒（$\mu s$）級的即時閉環，讓 $\Delta\phi \to 0^\circ$。
- **實現方式**：
  1. 高速雙通道 ADC 採樣電流互感器（CT）與電壓感測信號。
  2. FPGA 內部進行正交解調提取 $\Delta\phi$。
  3. PLL 環路濾波器（PI 控制器）輸出頻率修正量。
  4. 調整 DDS 的頻率控制字（FTW），即時修正 PWM 輸出頻率。

### 2. 碰骨/金屬鉗失諧保護與自動尋頻自愈 (Acoustic Stall & Auto-Sweep)
- **臨床現象**：當刀頭在體腔內意外碰觸骨骼或金屬止血夾時，阻抗極速飆升，刀尖幾乎被完全卡死（Mechanical Clamping），引發 Acoustic Stall。
- **GEN11 防護機制**：
  1. **輸出箝位保護**：限制最大輸出電壓，防止大電流衝擊擊穿壓電陶瓷。
  2. **自動掃頻自愈（Auto Frequency Sweep）**：
     當外科醫師將刀頭移開骨骼、釋放夾持力，或經過短暫延時，FPGA 會以低能小信號在 $53.0 \sim 57.0\text{ kHz}$ 頻段進行毫秒級 Chirp 掃頻，直接偵測當前阻抗極小值點 $|Z|_{min}$，瞬時將 DDS 頻率對齊至新共振點並重置積分器，徹底避免失諧卡死。
  3. **手動重置按鈕（Reset & Re-Sweep）**：面板提供手動一鍵復歸。

### 3. 主機電源激發開關 (Generator Power ON/OFF / Foot Switch)
- 模擬實際手術室中的**腳踏開關（Foot Switch）或手柄激發按鈕**：
  - **STANDBY（待機，腳踏未踩）**：輸出電壓為 0V，電流 0A，刀尖靜止，面板呈現黃色待機標誌。
  - **ACTIVE（激發，腳踏踩下）**：電壓軟啟動（Soft-Start），PLL 閉環追頻，刀尖高頻振動。

### 4. 自適應組織切斷感測技術 (Adaptive Tissue Technology / ATT)
- **組織離斷瞬間特徵**：血管切斷離斷的瞬間，動態阻抗會發生急遽陡降（$\frac{dR_m}{dt} \ll 0$ 且 $f_s$ 回彈）。
- 捕獲此跳變後發出切斷完成提示音（Transection Alert），並自動降載，防止空轉燒蝕上鉗口的鐵氟龍墊片（PTFE Pad）。

---

## 四、 模擬器操作指引

### 1. Python 桌面獨立 GUI 模擬器 (`ultrasonic_surgical_sim.py`)
```powershell
python ultrasonic_surgical_sim.py
```
- **頂部工具列**：
  - `⚡ 腳踏開關: 激發中 (ACTIVE: ON)`：點擊可切換「待機 (STANDBY)」與「激發 (ACTIVE)」。
  - `🔄 故障重置與自動尋頻 (Reset & Re-Sweep)`：碰骨失諧後一鍵瞬間重置並重新鎖頻。
- **情境觸發與自動自愈**：
  - 點擊「⚠ 碰骨/金屬鉗失諧 (Stall)」：可觀察到阻抗飆升、發出過載警報、電壓受保護箝位。
  - 移開骨頭（點擊「空載運轉」或「切脂肪」）：系統會在幾十毫秒內自動偵測並自愈恢復共振！

### 2. 跨平台 60 FPS Web 互動式儀表板 (`simulator.html`)
```powershell
start simulator.html
```
- 包含與 Python 版完全同步的：
  - 腳踏激發開關（ACTIVE / STANDBY 切換）
  - 故障重置與自動尋頻按鈕（Reset & Re-Sweep）
  - 碰骨過載保護旗標與自動自愈機制
  - 負反饋 PLL 閉環防止頻率滑向邊界
