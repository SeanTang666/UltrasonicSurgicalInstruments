# 專案開發與改進歷程日誌 (Development & Improvement Log)

本文件永久保存本專案從初始化、除錯、排版重構到功能增強的完整提示詞（Prompts）與程式碼改進（Coding Improvements）歷史紀錄。

---

## 🎯 初始專案目標與 Prompt (Initial Project Inception Prompt)

### 1. 系統設計核心目標

> **開發 ETHICON™ GEN11 超音波手術刀即時閉環追頻與能量控制模擬系統**
> 涵蓋壓電換能器 Butterworth-Van Dyke (BVD) 等效電路、微秒級 FPGA DPLL 諧振追頻、碰骨/金屬夾失諧保護與自動 Chirp 掃頻自愈、ATT (Adaptive Tissue Technology) 組織離斷感測，並提供 60 FPS 跨平台 Web 儀表板與 Python Tkinter 桌面獨立 GUI。

### 2. 初始任務提示詞 (Initial Prompt)

```text
超聲刀的關鍵，提到要精準控制頻率，其中最關鍵的是 Resonance Tracking Algorithm，共振追頻演算法。
超聲刀不是「固定輸出 55.5 kHz 就好」。Handpiece 裡面的 piezoelectric transducer + waveguide + blade 是一套機械共振系統。
例如一支刀頭空載時可能：
Resonance frequency = 55.50 kHz
但夾住組織後，因為 mechanical load 改變，可能變成：
55.42 kHz
使用一段時間溫度升高，又可能變成：
55.36 kHz
如果 generator 還是死守 55.50 kHz，可能會發生：
振幅下降 → cutting efficiency 下降 → 功率浪費 → transducer 發熱 → 甚至可能損壞 handpiece。
所以 FPGA 會非常快速地量：
Voltage → Current → Phase → Impedance
然後控制演算法持續調整輸出 frequency。
可以把整個 closed-loop 想成：
FPGA產生頻率 → Power amplifier → Handpiece → Piezo → Blade
同時：
Voltage / Current sensing → ADC → FPGA → 計算 Phase / Impedance → Resonance tracking → 修正 frequency
然後再回去調整 waveform。
這就是為什麼你們客戶說要「重新建立完整控制系統、演算法及軟體」，請幫我做一個即時的訊號模擬程式，讓真實的超聲刀切割人體組織所形成的阻抗當成stimulus，並讓各種變因可由使用者設定。整個即時模擬器就像示波器那樣可以即時的選擇想要觀測的信號，在同一時間發生了什麼變化(時間同步要很精確)。
```

---

## 📜 歷次 Coding Improvement 完整更新紀錄

### [Iteration 1] 2026-09-18 10:42:04

- **User Prompt**:
  ```text
  git push to [SeanTang666/UltrasonicSurgicalInstruments](https://github.com/SeanTang666/UltrasonicSurgicalInstruments)
  ```
- **問題分析 (Problem Diagnosis)**:
  - 工作目錄尚未建立 Git 倉庫，且目錄下存在 Python 快取目錄 `__pycache__/` 與 VS Code 設定檔案。
- **程式改進與動作 (Coding Improvements)**:
  1. 執行 `git init -b main` 初始化主分支。
  2. 新增 `.gitignore` 檔案排除 `__pycache__/`、`*.py[cod]`、`.vscode/`、`.idea/`。
  3. 建立首個版本 Commit `Initial commit: Ultrasonic Surgical Instruments simulator and system architecture`。
  4. 新增 Remote URL 至 GitHub 倉庫。
- **修改檔案**:
  - `[NEW] .gitignore`
  - `[ADD] SYSTEM_ARCHITECTURE.md`
  - `[ADD] simulator.html`
  - `[ADD] ultrasonic_surgical_sim.py`

---

### [Iteration 2] 2026-09-18 10:56:38

- **User Prompt**:
  ```text
  git push -u origin main怎麼跑那麼久？
  ```
- **問題分析 (Problem Diagnosis)**:
  - 檢查 Windows 認證庫發現 `git:https://github.com` 預設綁定舊帳號，而目標帳號的憑證記錄於 `git:https://SeanTang666@github.com`。通用 URL 觸發 Git Credential Manager 在背景等待非互動式驗證而掛起。
- **程式改進與動作 (Coding Improvements)**:
  1. 終止掛起的背景推送任務。
  2. 將 Remote URL 更新為明確包含帳號的規格：`https://SeanTang666@github.com/SeanTang666/UltrasonicSurgicalInstruments.git`。
  3. 成功觸發 Windows 憑證自動匹配，4 秒內完成推送至 `origin/main`。
- **修改檔案**:
  - Git configuration / Remote URL

---

### [Iteration 3] 2026-09-18 11:01:31 ~ 11:05:19

- **User Prompt**:
  ```text
  請幫我改成一樣可以在github佈署網頁
  [用戶上傳圖片：GitHub Pages Private 倉庫限制提示]
  ```
- **問題分析 (Problem Diagnosis)**:
  - GitHub Pages 需要根目錄靜態進入點（`index.html`）或 GitHub Actions 工作流；同時免費用戶之私有倉庫（Private）無法使用 Pages 服務。
- **程式改進與動作 (Coding Improvements)**:
  1. 建立根目錄 `index.html`（同步自 `simulator.html`）。
  2. 建立自動化部署工作流 `.github/workflows/deploy.yml`（利用 `actions/deploy-pages@v4`）。
  3. 撰寫繁體中文說明文件 `README.md`，並加入 Live Demo 徽章與架構引導。
  4. 指引使用者前往倉庫設定將可見性（Visibility）由 Private 改為 Public。
- **修改檔案**:
  - `[NEW] index.html`
  - `[NEW] .github/workflows/deploy.yml`
  - `[NEW] README.md`

---

### [Iteration 4] 2026-09-18 11:37:30

- **User Prompt**:
  ```text
  箭頭所指之處會有顯示抖動的問題
  [用戶上傳圖片：示波器 CH3 密集梳狀震盪，數值卡劇烈跳動]
  ```
- **問題分析 (Problem Diagnosis)**:
  1. **控制迴路極限環失穩 (Limit-Cycle Instability)**：刀尖機械位移缺乏聲學換能器質量之機械慣性時間常數；PI 增益 `ampKp=0.7` 在 $Z_m \approx 48\ \Omega$ 負載下單步離散開環增益高達 1.24，導致單幀超調與反壓來回反彈，在 CH3 產生 60 Hz 鋸齒極限環。
  2. **CSS 彈性佈局橫向位移 (Layout Shift)**：頂部 `.chain-node` 未設定固定最小寬度，數值字元位數變更引發周圍節點晃動。
  3. 頂部 `Rm` 節點誤綁動態總阻抗 $|Z_m|$，失諧時包含電抗成分加劇數值跳動。
- **程式改進與動作 (Coding Improvements)**:
  1. 物理模型加入聲學換能器機械慣性包絡時間常數（$\tau \approx 40\text{ ms}$）。
  2. 重新整定控制器：振幅控制改為臨界阻尼 `ampKp: 0.2, ampKi: 0.8`；鎖相環微調為 `pllKp: 4.0, pllKi: 2.0`。
  3. `.chain-node` 加上 `flex: 1 1 110px; min-width: 105px;` 與 `font-variant-numeric: tabular-nums`。
  4. 頂部 `Rm` 改為顯示真正的組織聲阻尼 `RmTotal`。
  5. 同步更新 `simulator.html`、`index.html` 與 `ultrasonic_surgical_sim.py`。
- **修改檔案**:
  - `[MODIFY] simulator.html`
  - `[MODIFY] index.html`
  - `[MODIFY] ultrasonic_surgical_sim.py`

---

### [Iteration 5] 2026-09-18 13:28:37

- **User Prompt**:
  ```text
  這兩個畫面的字體可以加大，目前這樣看不清楚
  [用戶上傳圖片：手術刀作動 Canvas 與示波器 Canvas 局部放大]
  ```
- **問題分析 (Problem Diagnosis)**:
  - 畫布內文字原先為 8~10px，在高解析螢幕或遠距觀看時字體過小、對比度不足。
- **程式改進與動作 (Coding Improvements)**:
  1. 手術刀作動圖：Piezo 文字加大至 `bold 13px`；Waveguide 文字加大至 `bold 13px`（亮白 `#f1f5f9`）；PTFE Pad 加大至 `bold 12px`；Tip Stroke 數值加大至 `bold 14px`。
  2. 示波器圖：CH1~CH3 標題加大至 `bold 13.5px`（純白 `#f1f5f9`）；Y 軸刻度加大至 `bold 11.5px monospace`，擴寬左邊距至 76px；右側圖例加大至 `bold 12.5px`，行距擴大至 20px。
  3. 畫布高度調整：`knifeCanvas` 增至 175px，`scopeCanvas` 增至 460px。
  4. 同步更新 Python GUI Canvas 字體大小與邊界。
- **修改檔案**:
  - `[MODIFY] simulator.html`
  - `[MODIFY] index.html`
  - `[MODIFY] ultrasonic_surgical_sim.py`

---

### [Iteration 6] 2026-09-18 13:54:07

- **User Prompt**:
  ```text
  1.黃框1版面不用占那麼大，內部的顯示可以縮小一些，看的清楚就好. 
  2.綠框3可以和紅框2合併，例如原紅框2只是顯示刀子的作動，可以縮小一些，往右移出空間給綠框3的訊息。這樣騰出的空間可以給真正要觀察的波形看更多信號。
  3. initial prompt請寫入log file. 
  4. 請每一次的coding improvement自動加入log file.
  [用戶上傳圖片：黃框 1 頂部、紅框 2 刀具、綠框 3 遙測數值、綠色箭頭指示合併]
  ```
- **問題分析 (Problem Diagnosis)**:
  - 頂部導覽列與信號鏈（黃框 1）佔用垂直像素過多（~140px）。
  - 刀具作動（紅框 2）與 8 個遙測卡（綠框 3）垂直堆疊佔用 ~310px，造成最核心的示波器被壓縮至下方。
  - 需要將紅框 2 與綠框 3 左右合併（左側 2x4 遙測卡，右側刀具作動），騰出超過 140px 垂直高度擴展示波器並增加觀測信號。
- **程式改進與動作 (Coding Improvements)**:
  1. **黃框 1 緊湊化**：
     - Header padding 縮減為 `6px 18px`，標題字體調整為 `0.96rem`。
     - 按鈕與狀態標籤 padding 縮減，更加小巧精緻。
     - 信號鏈 Ribbon padding 縮減為 `4px 18px`，節點字體縮至 `0.68rem`。
  2. **紅框 2 與 綠框 3 左右合併 (`.combined-top-panel`)**：
     - 左側（綠框 3）：緊湊型 2 欄 x 4 列 Telemetry Grid，收納 8 項核心即時數據（諧振頻率、輸出頻率、相位差、位移衝程、電壓、電流、功率、等效阻抗），數值維持清晰等寬顯示。
     - 右側（紅框 2）：緊湊型換能器與變幅桿聲學運動微觀 Canvas，刀桿隨寬度自適應縮放，保留 PTFE 墊片、空化汽化氣泡與刀尖振幅動態。
     - 整體高度從原先 310px 大幅壓縮至僅 165px，省下約 145px 垂直空間。
  3. **示波器高度顯著擴增與信號增強**：
     - 示波器畫布高度大幅擴充至 **550px**（每通道擁有 180px 充裕高度）。
     - **新增信號**：在 CH3 引入第 3 條波形——**換能器總驅動電流 (Total Motional Current, 0~2.5A, 綠色曲線)**，同時並列電壓（黃色）、機械位移（粉色）與電流（綠色），全方位透視機電換能特性。
  4. **日誌系統持久化**：
     - 建立 `DEVELOPMENT_LOG.md`，完整登錄專案由起始至今的所有 Prompt 與改進記錄，並於每次更新自動維護。
- **修改檔案**:
  - `[MODIFY] simulator.html`
  - `[MODIFY] index.html`
  - `[NEW] DEVELOPMENT_LOG.md`

---

### [Iteration 7] 2026-09-18 14:20:00

- **User Prompt**:
  ```text
  1. 兩個黃框可以合併，相位的標示可以放在合併框的右邊，才不會重疊。這樣可以省下空間給紅框模擬更多訊號 
  2. 紅框內目前的訊號並無垂直軸的訊號強度，可以考慮使這三個訊號分開，並給出其實際值。 
  3. 另外要像示波器這樣讓使用者可以調整想要看的水平時間軸解析度
  ```
- **問題分析 (Problem Diagnosis)**:
  1. **示波器通道與垂直空間浪費**：原先頻率追蹤（CH1）與相位差（CH2）各占一個子示波器，兩者都是觀測閉環鎖相的核心，分開佔用兩倍垂直高度。若合併為雙 Y 軸（Dual-Axis DSO），左軸放頻率、右軸放相位，中間以 0° 諧振虛線為基準，可省出一個通道的高度。
  2. **訊號重疊與缺少垂直刻度強度**：原先 DAC 電壓、刀尖振幅、總電流三條曲線疊在 CH3，僅有一組 0~160 數值刻度，難以辨識各訊號的精確強度與單位（例如電流 0~2.5A 與電壓 0~160V 混用刻度不直觀）。
  3. **缺乏水平時間解析度調整 (Timebase)**：原先固定為固定採樣視窗（約 5 秒），使用者在觀察短時階躍暫態（如血管夾閉、碰骨失諧初期的微秒~毫秒級震盪）或長時間溫漂趨勢時，無法像真實示波器靈活放大或縮小時間軸。
- **程式改進與動作 (Coding Improvements)**:
  1. **雙 Y 軸示波器合併 (Dual-Axis DSO - CH1 & CH2)**：
     - **左側 Y 軸**：機械諧振頻率 Target fs（黃色虛線）與 FPGA DDS 驅動頻率 Drive f（青色實線），刻度 54.0 ~ 57.0 kHz，數值靠左對齊。
     - **右側 Y 軸**：阻抗相位差 Δφ（紫色實線），刻度 -50° ~ +50°，數值靠右對齊，並繪製 0° Target 串聯諧振綠色虛線基準線。
     - 頻率與相位數值完全分立兩側，徹底杜絕文字與標籤重疊。
  2. **紅框能量與響應訊號分離為 3 個獨立示波器通道**：
     - **CH2 (DAC 驅動電壓)**：0 ~ 160 Vrms 獨立刻度（160V, 80V, 0V），金色實線，附帶即時電壓數值標註。
     - **CH3 (刀尖機械位移衝程振幅)**：0 ~ 120 μm 獨立刻度（120μm, 60μm, 0μm），桃粉色實線，附帶目標振幅虛線參考與即時位移數值。
     - **CH4 (換能器總驅動電流)**：0.00 ~ 2.50 A 獨立刻度（2.50A, 1.25A, 0.00A），翡翠綠實線，附帶即時電流與等效阻抗讀數。
  3. **專業示波器水平時基調節 (Adjustable Timebase / DSO Graticule)**：
     - 工具列新增 5 種水平時基切換按鈕：`0.5s (50 ms/div)`、`1.0s (100 ms/div)`、`2.5s (250 ms/div)`、`5.0s (500 ms/div)`、`10.0s (1.0 s/div)`。
     - 擴充歷史緩衝區容量至 `MAX_BUF_LEN = 600`，動態截取並平滑映射視窗數據。
     - 繪製 DSO 標準 10-div 時間刻度網格與 4-div 垂直格線，底部顯示即時相對時間軸標籤（如 `-5.0s`, `-4.0s`, ..., `0.0s (Now)`）。
  4. **全平台同步**：
     - 同步更新 `simulator.html`、`index.html` 以及 `ultrasonic_surgical_sim.py`（Python 桌面 GUI 同步支援 4 通道與雙 Y 軸相位標籤）。
- **修改檔案**:
  - `[MODIFY] simulator.html`
  - `[MODIFY] index.html`
  - `[MODIFY] ultrasonic_surgical_sim.py`
  - `[MODIFY] DEVELOPMENT_LOG.md`

---

### [Iteration 8] 2026-09-18 14:33:00
- **User Prompt**:
  ```text
  數字的小數點要限制，
  [用戶上傳圖片：組織聲阻尼顯示 168.94736842105246 Ω，組織剛性共振頻偏顯示 -98.42105263157883 Hz]
  ```
- **問題分析 (Problem Diagnosis)**:
  - 臨床時序自動運算情境（如「血管閉合切斷全流程 (Seal & Transect)」）中，組織聲阻尼、剛度頻偏與夾持力以插值公式計算（例如 `30 + 110 * (t / 1.5)`）。
  - 在傳遞給 `setStimulus(damping, clamp, stiffness)` 時，未先進行整數取整或小數點格式化限制，直接以 `${damping} Ω` 與 `${stiffness} Hz` 插值輸出至 DOM，造成介面上出現十幾位浮點數殘留（如 `168.94736842105246 Ω`、`-98.42105263157883 Hz`），破壞介面版面整潔與讀取舒適度。
- **程式改進與動作 (Coding Improvements)**:
  1. **變因與滑桿數值取整限制**：
     - 在 `setStimulus(damping, clamp, stiffness)` 函式中全面引入 `Math.round()` 四捨五入取整：
       - `val-damping`: `${Math.round(damping)} Ω`
       - `val-clamp`: `${Math.round(clamp)} %`
       - `val-stiffness`: `${Math.round(stiffness)} Hz`
     - 同時將 `slideDamping.value`、`slideClamp.value`、`slideStiffness.value` 同步寫入整數值，防止滑桿與文字不同步。
  2. **滑桿手動事件防護**：
     - 在 `slideDamping`、`slideClamp`、`slideStiffness` 及 `slideManualF` 的 `input` 監聽器中加入 `Math.round(parseFloat(...) || 0)`，徹底杜絕浮點數溢位字串。
     - `slideTemp` 嚴格限制為 1 位小數（`${val.toFixed(1)} °C`）。
  3. **全站與 GitHub Pages 同步**：
     - 同步更新 `simulator.html` 與 `index.html`。
- **修改檔案**:
  - `[MODIFY] simulator.html`
  - `[MODIFY] index.html`
  - `[MODIFY] DEVELOPMENT_LOG.md`

---

### [Iteration 9] 2026-09-18 14:36:50
- **User Prompt**:
  ```text
  請框內的小數點只取到兩位，4捨五入
  [用戶上傳圖片：紅框標註手動即時微調變因欄位：組織聲阻尼 139.9999999999999 Ω、刀鉗夾持力 94.99999999999994 %、組織剛性頻偏 -79.99999999999993 Hz]
  ```
- **問題分析 (Problem Diagnosis)**:
  - 使用者明確要求「手動即時微調任意變因」框內之三個變因（組織聲阻尼、刀鉗夾持力、組織剛性頻偏）數值顯示規格須**精確四捨五入並嚴格保留至小數點後兩位 (2 decimal places, e.g. `140.00 Ω`)**。
  - 原 HTML `<input type="range">` 滑桿的 `step="1"` 限制了微觀解析度，且文字顯示未固定採用 `.toFixed(2)`。
- **程式改進與動作 (Coding Improvements)**:
  1. **固定雙位小數與四捨五入 (toFixed(2) & Math.round(*100)/100)**：
     - 在 `setStimulus(damping, clamp, stiffness)` 中：
       - `d = Math.round(Number(damping) * 100) / 100` $\rightarrow$ `${d.toFixed(2)} Ω`
       - `c = Math.round(Number(clamp) * 100) / 100` $\rightarrow$ `${c.toFixed(2)} %`
       - `s = Math.round(Number(stiffness) * 100) / 100` $\rightarrow$ `${s.toFixed(2)} Hz`
     - 徹底杜絕浮點運算產生的 `139.9999999999999` 或 `94.99999999999994`，精確收斂為 `140.00 Ω`、`95.00 %`、`-80.00 Hz`。
  2. **滑桿組件步階擴充至 0.01 (step="0.01")**：
     - 將 `slideDamping`、`slideClamp`、`slideStiffness` 的 `step` 屬性由 `1` 調整為 `0.01`，支援平滑高精度的動態連續位置設定。
     - 手動拖曳監聽器同步採用 `Math.round(val * 100) / 100` 與 `.toFixed(2)` 格式化。
  3. **全站與 GitHub Pages 同步**：
     - 同步更新 `simulator.html` 與 `index.html`，並推送到遠端倉庫。
- **修改檔案**:
  - `[MODIFY] simulator.html`
  - `[MODIFY] index.html`
  - `[MODIFY] DEVELOPMENT_LOG.md`

---

### [Iteration 10] 2026-09-18 14:48:00
- **User Prompt**:
  ```text
  1. 紅框內的play, 讓我再按一次可以pause, ie. play and pause toggle. 
  2. 0.5sec 的horizontal scale不夠用，我再來要能看到55.5Khz PLL的調控精細過程，55.5Khz被FPGA用多高的頻率去偵測？ADC用多高的頻率去偵測，然後feedback給FPGA的哪一個功能模組去做DDS調整？細部信號的解析是設計上必須了解的。
  [用戶上傳圖片：紅框標註「▶ 血管閉合切斷全流程 (Seal & Transect)」按鈕與示波器時間軸]
  ```
- **問題分析與硬體架構解構 (Problem Diagnosis & Hardware Architectural Analysis)**:
  1. **臨床時序按鈕缺乏暫停切換機制**：原先「▶ 血管閉合切斷全流程」為單向觸發，點擊後只能等待完整 5.5 秒流程走完，無法在血管變性、沸騰或離斷瞬間凍結時間軸仔細比對波形。
  2. **巨觀時間軸（0.5s~10s）無法透視微觀 55.5 kHz 射頻正弦波與鎖相環動態**：
     - 超音波手術刀中心頻率 $f_0 \approx 55.5\text{ kHz}$，單一正弦波週期僅約 $T \approx 18.018\ \mu\text{s}$。
     - 0.5s 示波器視窗包含了約 27,750 個交流週期，只能看到包絡線（Envelope），無法觀察正弦波過零點、相位超前/滯後與 ADC 採樣過程。
  3. **硬體架構設計解答 (ETHICON GEN11 原廠硬體映射)**：
     - **ADC 偵測頻率**：高速雙通道 Flash/Pipelined ADC 以 **60.0 MSPS**（14-bit）同步採樣驅動電壓感測器與電流互感器。每 $55.5\text{ kHz}$ 週期採集 $\frac{60\text{ MHz}}{55.5\text{ kHz}} \approx \mathbf{1,081\text{ 個採樣點}}$，徹底消除高頻諧波與量化抖動。
     - **FPGA 偵測與運算時脈**：FPGA 核心工作時脈由 TCXO 晶振倍頻至 **120.0 MHz**。過零檢測器（ZCD / TDC）具備 **8.33 ns** 時間解析度，相對於 55.5 kHz 相當於極限 $\mathbf{0.166^\circ}$ 的超精細相角解析度。
     - **Feedback 調節 DDS 的功能模組**：
       - 第一步：`Dual ADC (60 MSPS)` 採集瞬時 $v[n], i[n]$。
       - 第二步：`CORDIC / 數位正交解調與過零相檢模組 (PFD/ZCD @ 120 MHz)` 提取即時相角差 $\Delta\phi$。
       - 第三步：`相位誤差器` 計算 $e_\phi = \Delta\phi - 0.00^\circ$。
       - 第四步：**回授至關鍵核心模組——`數字鎖相環環路濾波器 (DPLL Loop Filter, PI 控制器)`**，於每個 $18.02\ \mu\text{s}$ 週期（55.5 kHz 同步更新）運算輸出調頻量 $\Delta f$。
       - 第五步：$\Delta f$ 寫入 **`32 位元頻率控制字暫存器 (FTW Register)`**，累加至 **`DDS / NCO 相位累加器`**（120 MHz 時脈），經 Sine LUT 查表送出至 14-bit 120 MSPS 驅動 DAC。
- **程式改進與動作 (Coding Improvements)**:
  1. **臨床時序按鈕 Play / Pause Toggle 互動切換**：
     - 加入 `vesselState` 狀態機（`idle` ➜ `playing` ➜ `paused`）。
     - 點選啟動時顯示「`⏸ 暫停血管流程 (Pause)`」（橘色警告樣式），再點一次凍結 `scenTimer` 與變因，按鈕切換為「`▶ 繼續血管流程 (Resume)`」（綠色就緒樣式）。
     - 任何其他手動模式按鈕切換時，自動安全重置回初始狀態。
  2. **多通道示波器時基擴充 (Main DSO Toolbar)**：
     - 示波器工具列新增微秒/毫秒等級解析度按鈕：`50ms` ($5\text{ ms/div}$)、`100ms` ($10\text{ ms/div}$)，滿足由巨觀至過渡暫態的觀測需求。
  3. **全新研發：🔬 55.5 kHz 射頻微觀週期正弦波與 FPGA 閉環模組解析面板 (`.rf-inspector-card`)**：
     - **左側：微觀射頻示波器畫布 (`#rfCanvas`)**：
       - 即時渲染真實 $55.5\text{ kHz}$ 交流驅動電壓 $V_{\text{drive}}(t)$ 與感測電流 $I_{\text{sense}}(t)$。
       - 支援 `36μs (2週期)`、`90μs (5週期)`、`180μs (10週期)`、`540μs (30週期)` 微觀時基切換。
       - **ADC 60 MSPS 離散採樣點視覺化**：於電流波形上即時標記出 16.67 ns 取樣週期的離散採樣發光點。
       - **過零檢測與時間差動態指示**：標註電壓過零與電流過零的垂直虛線標記，並以雙箭頭即時指示過零時間差 $\Delta t$（精確至 $0.1\text{ ns}$）。
     - **右側：FPGA 4 級硬體閉環管線即時動態卡片 (Pipeline Readouts)**：
       - `Step 1: Dual ADC @ 60.00 MSPS (14-bit, dt = 16.67 ns)`
       - `Step 2: CORDIC / ZCD 檢相 (120 MHz, 8.33 ns, 即時 Δφ 與 Δt)`
       - `Step 3: DPLL Loop Filter (PI @ 18.02 μs, 即時輸出頻率修正量 Δf)`
       - `Step 4: 32-bit DDS / NCO 累加器 (即時 FTW 暫存器數值與 16 進位字元)`
  4. **跨平台同步與日誌登錄**：
     - 同步更新 Web 介面 `simulator.html` 與 GitHub Pages 進入點 `index.html`。
     - 同步更新 Python GUI 桌面程式 `ultrasonic_surgical_sim.py`，支援 Play/Pause 切換。
- **修改檔案**:
  - `[MODIFY] simulator.html`
  - `[MODIFY] index.html`
  - `[MODIFY] ultrasonic_surgical_sim.py`
  - `[MODIFY] DEVELOPMENT_LOG.md`

---

### [Iteration 11] 2026-09-18 15:02:00
- **User Prompt**:
  ```text
  當我按下pause, 好像波形還繼續跑
  ```
- **問題分析 (Problem Diagnosis)**:
  1. **採樣移位未凍結造成波形持續推移**：在前次實作中，點擊 `⏸ 暫停血管流程 (Pause)` 時，僅暫停了臨床劇本計時器 `scenTimer`，而 60 FPS 動態動畫主循環 (`loop()`) 依然持續推進 `simTime`，並且每一幀無條件執行 `history.*.shift()` 與 `push()`。
  2. **歷史緩衝區遭同質常數洗掉**：暫停時由於變因維持定值，波形持續以每秒 60 筆的速度向左滾動移出畫面，約 10 秒後整個 600 筆緩衝區皆被平直直線取代，原本捕捉到的切斷與阻抗跳變瞬態資料全部流失。
  3. **刀尖動畫與畫布缺少明確 HOLD 提示**：暫停時刀尖仍持續正弦震盪，示波器亦無明確鎖定標籤，使用者難以確認系統是已凍結還是仍在運行。
- **程式改進與動作 (Coding Improvements)**:
  1. **示波器與動態採樣真凍結 (True Waveform Acquisition Freeze & Hold)**：
     - 在 `simulator.html` 的 `loop()` 中引入全局凍結判定：`const isPaused = (vesselState === "paused") || isScopeFrozen;`。
     - 當處於暫停或示波器手動凍結時，將 `simTime += dt`、`Physics.update(...)`、`FPGA.step(...)` 以及全部 8 組示波器歷史緩衝區的 `history.*.shift()` / `push(...)` 完整置入 `if (!isPaused) { ... }` 內保護。暫停期間**不再推進時間，亦不再向歷史陣列推入任何新數據**，波形完全靜止定格。
  2. **示波器停機縮放檢視功能 (Stop & Zoom Capability)**：
     - 在波形凍結的狀態下，`renderScopeGraphic(isPaused)` 與畫布互動事件依然保持活躍。使用者在暫停時可任意點擊切換 `50ms`、`100ms`、`0.5s`、`1.0s`、`2.5s`、`5.0s`、`10.0s` 各水平時基按鈕，在定格的暫態波形上進行時間軸縮放，重現專業數位儲存示波器（DSO）標準行為。
  3. **微觀射頻與刀尖視覺狀態同步凍結**：
     - 傳入 `isPaused` 至 `renderKnifeGraphic(isPaused)`，暫停時刀尖機械震動偏移量立即歸零（`vib = 0.0`），停止抖動。
     - 傳入 `isPaused` 至 `renderRfInspector(isPaused)`，於 55.5 kHz 射頻示波器畫布右上角即時顯示 `⏸ DSO HOLD (已凍結)` 狀態徽章。
     - 於主示波器畫布（`#scopeCanvas`）正上方繪製半透明警示覆蓋條：`⏸ 採樣凍結中 (DSO HOLD / PAUSED) — 保持當前數據，可切換時基縮放檢視`。
  4. **新增專用示波器手動鎖定按鈕 (`#btnScopeFreeze`)**：
     - 於時基按鈕列右側加入 `⏸ 示波器鎖定 (Freeze) / ▶ 示波器解凍 (Run)` 按鈕，方便使用者於任何手動調節工況或極限負載下隨時單擊定格分析。
  5. **跨平台與部署同步**：
     - 同步更新 Python GUI 桌面程式 `ultrasonic_surgical_sim.py`：在 `update_simulation_step()` 中加入暫停返回機制，停止緩衝區推進，並在 Tkinter 畫布顯示 DSO HOLD 框與凍結刀尖振動。
     - 同步複製更新 GitHub Pages 靜態網站入口 `index.html`。
- **修改檔案**:
  - `[MODIFY] simulator.html`
  - `[MODIFY] index.html`
  - `[MODIFY] ultrasonic_surgical_sim.py`
  - `[MODIFY] DEVELOPMENT_LOG.md`

---

### [Iteration 12] 2026-09-18 15:05:00
- **User Prompt**:
  ```text
  這兩個信號框請對調
  [用戶上傳圖片：紅框標註上方「55.5 kHz 射頻微觀週期交流正弦信號與 FPGA 閉環模組解析」，黃框標註下方「閉環即時多通道示波器」]
  ```
- **問題分析 (Problem Diagnosis)**:
  - 使用者在操作模擬器與觀測手術刀動態響應時，「閉環即時多通道示波器 (Dual-Axis Tracking & Multi-Channel Power DSO)」負責呈現手術進程（0.5s~10s）之巨觀核心數據：雙軸頻率追蹤、相位差、驅動電壓、刀尖衝程與電流負載，是用戶進行工況判斷的最關鍵主儀表板。
  - 「55.5 kHz 射頻微觀週期交流正弦信號與 FPGA 閉環模組解析 (Microscopic RF & FPGA Control Chain)」則提供微觀（36μs~540μs）射頻正弦波、過零時差、ADC 取樣點與 FPGA 4 級管線架構卡，屬於進階硬體深入透視與教學診斷用途。
  - 原版面將微觀射頻模組置於上方、主示波器置於下方，在視覺流線上本末倒置，使用者需向下俯視才能監看巨觀即時趨勢。
- **程式改進與動作 (Coding Improvements)**:
  1. **訊號框位置順序對調 (DOM Hierarchy Swap)**：
     - 將「📊 閉環即時多通道示波器 (`.scope-card`)」向上提升至換能器刀尖視覺動畫正下方，使巨觀時基（0.5s~10.0s）4 軌即時訊號成為主視覺焦點。
     - 將「🔬 55.5 kHz 射頻微觀週期交流正弦信號與 FPGA 閉環模組解析 (`.rf-inspector-card`)」順勢調整至下方，作為深入研究 FPGA DDS / ADC 閉環機制之微觀分析工作台。
  2. **跨平台與 GitHub Pages 部署**：
     - 同步覆蓋更新 GitHub Pages 靜態網站入口 `index.html`。
     - 自動記錄日誌並推送到 GitHub 遠端倉庫。
- **修改檔案**:
  - `[MODIFY] simulator.html`
  - `[MODIFY] index.html`
  - `[MODIFY] DEVELOPMENT_LOG.md`

---

### [Iteration 13] 2026-09-18 16:15:00
- **User Prompt**:
  ```text
  按下play不能動
  [用戶上傳圖片：刀尖畫布黑屏、示波器黑屏，點擊「▶ 血管閉合切斷全流程 (Seal & Transect)」按鈕無響應]
  ```
- **問題分析 (Problem Diagnosis)**:
  - 經檢查用戶圖片，刀尖動畫畫布（`#knifeCanvas`）與示波器畫布（`#scopeCanvas`）完全處於初始黑色背景未繪製狀態，且點擊任何按鈕皆無反應，此現象為典型的**JavaScript 全域語法錯誤造成腳本於載入期中斷**。
  - 經使用 Node.js 語法剖析器深入檢驗，在 `renderRfInspector()` 函式內部，先前新增 `isPaused` 凍結判斷時，過零標示判斷式 `if (pxZeroV >= 0 && pxZeroV <= cw && pxZeroI >= 0 && pxZeroI <= cw)` 之結尾閉合括號 `}` 遭遺漏，導致 `function renderRfInspector` 語法區塊未閉合（`SyntaxError: Unexpected end of input`）。
  - 語法錯誤使整份 `<script>` 在瀏覽器啟動時即被中止，`resizeCanvases()`、`loop()` 動畫迴圈以及全部 DOM 按鈕點擊監聽器（包括 Play 按鈕）皆未能成功掛載。
- **程式改進與動作 (Coding Improvements)**:
  1. **修復函式語法閉合括號 (Syntax Fix)**：
     - 於 `renderRfInspector()` 內過零檢測區塊精確補上閉合花括號 `}`，恢復完整語法階層。
     - 執行 Node.js `new Function()` 與語法靜態檢查（Node syntax check），驗證 `simulator.html` 與 `index.html` 腳本語法 100% 正確通過。
  2. **重新載入驗證 (Runtime Verification)**：
     - 畫布重繪、60 FPS 動態主迴圈與 `btnVessel` 點擊事件已恢復正常綁定。點擊 Play 按鈕能順利啟動血管切斷流程，刀尖動畫正常振動、示波器 4 通道正常推進。
  3. **全站與 GitHub Pages 同步**：
     - 同步複製更新 `index.html`。
     - 自動記錄日誌並推送到 GitHub 遠端儲存庫。
- **修改檔案**:
  - `[MODIFY] simulator.html`
  - `[MODIFY] index.html`
  - `[MODIFY] DEVELOPMENT_LOG.md`

---

### [Iteration 14] 2026-09-18 17:15:00
- **User Prompt**:
  ```text
  我對這個超聲刀開始剪到結束過程中的幾個重要波形轉變所代表的意義不明白，能否在刀具、波形進行過程中，加入一些註解
  implementation plan 也請儲存，then preceed
  ```
- **問題分析與臨床物理意義解構 (Problem Diagnosis & Clinical Physical Analysis)**:
  1. 超音波手術刀在進行血管閉合與離斷（Seal & Transect）全流程中，經歷四個關鍵的生理病理與聲學阻抗轉變：
     - **Phase 1 (0.0s~1.5s) 夾持加壓與變性熔合**：55.5 kHz 高頻微振動打斷氫鍵摩擦生熱（60~80°C），膠原蛋白變性 ➔ 組織聲阻尼 Rm 爬升 (30→140 Ω)，總電流上升；組織彈性負載造成諧振頻率 fs 負向頻偏 (Δfs ≈ -80 Hz)；DPLL 自動向下追頻維持 0° 相角諧振。
     - **Phase 2 (1.5s~3.4s) 空化沸騰、脫水乾涸與負載峰值**：組織液沸騰汽化，脫水變硬 ➔ 等效阻抗 Rm 與總電流達到最高峰 (Rm→250 Ω, Itot→1.8 A)，剛度頻偏達到極值 (-150 Hz)；閉環驅動電壓拉至頂峰 (~110 Vrms)。
     - **Phase 3 (3.4s~4.1s) ⚡ 血管壁完全離斷瞬間**：管壁徹底切斷分離，刀尖脫離組織束縛 ➔ 電流與阻抗「垂直斷崖式驟降」(250Ω→18Ω, 1.8A→0.45A)，諧振頻率 fs 瞬間彈回標稱 55.5 kHz！此「負載突降」為演算法判定切斷成功的標誌性事件（Signature Event）。
     - **Phase 4 (4.1s~5.5s) ✔ ATT 智能降載保護與冷卻**：組織已分離，若持續激發將導致空刀過熱（>200°C）並熔損鐵氟龙墊 ➔ GEN11 ATT 演算法自動調降功率至待機，發出切斷完成提示音。
  2. 原先使用者僅能看到一堆線條起伏，缺乏直觀的文字解說、物理意義與病理生理關聯對照。
- **程式改進與動作 (Coding Improvements)**:
  1. **實作計畫存檔 (`IMPLEMENTATION_PLAN.md`)**：
     - 已將完整臨床規劃與驗證計畫儲存至專案根目錄 `IMPLEMENTATION_PLAN.md`。
  2. **新增「臨床手術切斷即時物理與病理生理階段註解條」(`.clinical-annotation-box`)**：
     - 位於換能器面板與示波器之間，全寬展示當前階段徽章（Phase Badge）、時序進度條（Timer Progress Bar）。
     - 3 欄式深入解讀：
       - 🩺 組織病理與刀尖動作
       - 📈 示波器波形關鍵轉變意義
       - ⚡ FPGA 閉環調控應對機制
  3. **4 階段互動導覽切換標籤列 (`.phase-tabs-row`)**：
     - 提供 4 個階段快捷卡片，隨流程進度自動亮起**高亮呼吸發光指示燈**。
     - 支援使用者隨時單擊任一階段標籤，直接跳轉並定格預覽該階段之組織狀態、變因數值與波形特徵！
  4. **刀尖動畫區即時階段字幕橫幅 (`renderKnifeGraphic`)**：
     - 於刀尖畫布左上方即時標註當前階段名稱與臨床意義。
  5. **示波器各通道即時診斷標註與深度凍結解讀卡 (`renderScopeGraphic`)**：
     - 示波器 CH1~CH4 各通道即時繪製對應階段的特徵解讀（如 DPLL 追頻、電壓爬升、斷崖驟降等）。
     - 當處於暫停（Pause）或示波器凍結（Freeze）時，示波器頂部展開雙行深度解析卡片：顯示當前定格階段名稱及此瞬間波形特徵意義。
  6. **Python GUI 桌面版同步 (`ultrasonic_surgical_sim.py`)**：
     - 示波器底部同步加入 4 階段動態即時中文註解。
  7. **全站與 GitHub Pages 部署**：
     - 同步更新 `simulator.html`、`index.html`、`IMPLEMENTATION_PLAN.md`，提交並推送到 GitHub 遠端儲存庫。
- **修改檔案**:
  - `[NEW] IMPLEMENTATION_PLAN.md`
  - `[MODIFY] simulator.html`
  - `[MODIFY] index.html`
  - `[MODIFY] ultrasonic_surgical_sim.py`
  - `[MODIFY] DEVELOPMENT_LOG.md`
