# 超音波手術刀即時閉環追頻與能量控制模擬系統
### Real-Time Resonance Tracking & Closed-Loop Energy Control Simulation

[![GitHub Pages](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-brightgreen?style=for-the-badge&logo=github)](https://seantang666.github.io/UltrasonicSurgicalInstruments/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

本專案高精度模擬外科能量器械（如 **Ethicon Harmonic ACE+7 / GEN11 主機**、**Olympus Thunderbeat**）之壓電換能器聲學、電力電子、FPGA 數位訊號處理（DPLL）與人體組織相互作用的核心控制原理。

---

## 🌐 線上即時展示 (Live Demo)

👉 **立即在瀏覽器中體驗：[https://seantang666.github.io/UltrasonicSurgicalInstruments/](https://seantang666.github.io/UltrasonicSurgicalInstruments/)**

---

## 🔬 核心模擬機制與特色

1. **壓電換能器 BVD (Butterworth-Van Dyke) 物理等效模型**
   - 包含靜態箝位電容 $C_0$、動態臂質量電感 $L_m$、彈性柔度電容 $C_m$ 與機械負載阻尼 $R_m$。
   - 真實呈現串聯諧振點 $f_s \approx 55.5\text{ kHz}$ 與阻抗相位 $S\text{-Curve}$ 特性。

2. **微秒級數位閉環追頻 (Digital PLL / Phase Locked Loop)**
   - 模擬雙通道 ADC 採樣與 FPGA 乘法正交相敏檢波（Phase Detector）。
   - 環路濾波器（PI 控制器）即時修正 DDS 頻率控制字（FTW），將電壓與電流相位差箝制於 $0^\circ$。

3. **臨床負載情境與失諧保護自愈 (Acoustic Stall & Auto-Sweep)**
   - 支援空載、夾持脂肪、厚血管離斷、碰骨/金屬鉗失諧（Stall）等臨床情境。
   - 當發生失諧卡死時，觸發輸出電壓箝位保護，並在釋放後進行自動小信號掃頻（Auto Frequency Sweep）自愈復歸。

4. **ATT (Adaptive Tissue Technology) 組織離斷感測**
   - 實時監測 $\frac{dR_m}{dt}$ 阻抗跳變，捕捉組織切斷瞬間並發出提示音與自動降載。

---

## 🚀 快速開始

### 1. Web 版互動儀表板
直接開啟 [index.html](index.html) 或造訪 [GitHub Pages 線上展示](https://seantang666.github.io/UltrasonicSurgicalInstruments/)。

### 2. Python 桌面獨立 GUI 版
具備完整多線程物理引擎與 Matplotlib 示波器圖表：

```bash
# 建議使用 Python 3.8 或以上版本
python ultrasonic_surgical_sim.py
```

---

## 📖 系統架構與演算法文檔

深入了解壓電換能器數理推導、BVD 網絡推導、閉環穩定性分析與保護邏輯，請參閱：
👉 **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)**

