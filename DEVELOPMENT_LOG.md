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


