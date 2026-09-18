# 專案開發與改進歷程日誌 (Development & Improvement Log)

本文件永久保存本專案從初始化、除錯、排版重構到功能增強的完整提示詞（Prompts）與程式碼改進（Coding Improvements）歷史紀錄。

---

## 🎯 初始專案目標與 Prompt (Initial Project Inception Prompt)

### 1. 系統設計核心目標
> **開發 ETHICON™ GEN11 超音波手術刀即時閉環追頻與能量控制模擬系統**  
> 涵蓋壓電換能器 Butterworth-Van Dyke (BVD) 等效電路、微秒級 FPGA DPLL 諧振追頻、碰骨/金屬夾失諧保護與自動 Chirp 掃頻自愈、ATT (Adaptive Tissue Technology) 組織離斷感測，並提供 60 FPS 跨平台 Web 儀表板與 Python Tkinter 桌面獨立 GUI。

### 2. 初始任務提示詞 (Initial Prompt)
```text
git push to [SeanTang666/UltrasonicSurgicalInstruments](https://github.com/SeanTang666/UltrasonicSurgicalInstruments)
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
  2. 將 Remote URL 更新為明確包含帳號的規格：  
     `https://SeanTang666@github.com/SeanTang666/UltrasonicSurgicalInstruments.git`。
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
