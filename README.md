# WordPress 文章自動生成器

這是一個使用 Google Gemini AI 和 Google Custom Search API 自動生成 WordPress 文章的 Python 應用程式。

## 功能特色

- 使用 Google Gemini AI 生成文章內容
- 透過 Google Custom Search API 搜尋相關參考連結
- 自動發佈到 WordPress 網站
- 支援 SEO 優化（標題、描述、標籤）
- 避免重複使用相同的參考連結

## Docker Compose 設定

### 前置需求

1. Docker 和 Docker Compose
2. Google API 金鑰
3. WordPress 應用程式密碼
4. WordPress 網站需安裝 Yoast SEO 外掛（如需 SEO 功能）

### 設定步驟

1. **複製環境變數範本**
   ```bash
   cp env.sample .env
   ```

2. **編輯 `.env` 檔案**
   填入您的實際設定值：
   - `WP_URL`: WordPress REST API 端點
   - `WP_USER`: WordPress 使用者名稱
   - `WP_APP_PASS`: WordPress 應用程式密碼
   - `GOOGLE_API_KEY`: Google API 金鑰
   - `GOOGLE_CSE_ID`: Google Custom Search Engine ID
   - 其他品牌和內容設定

3. **WordPress SEO 設定（可選）**
   
   如果您想要 AI 自動設定 SEO 標題、描述和焦點關鍵字，需要將以下程式碼加入 WordPress：
   
   **方法 1：加入主題的 functions.php（推薦）**
   1. 登入 WordPress 管理後台
   2. 前往「外觀」→「主題編輯器」
   3. 選擇「functions.php」
   4. 將 `wordpress-yoast-setup.php` 檔案的內容複製貼到 `functions.php` 的最底部
   
   **方法 2：建立為外掛檔案**
   1. 將 `wordpress-yoast-setup.php` 檔案上傳到 `/wp-content/plugins/` 目錄
   2. 在 WordPress 管理後台啟用此外掛
   
   ⚠️ **重要提醒**：
   - 必須安裝 Yoast SEO 外掛
   - 需要 WordPress 應用程式密碼
   - 建議先在測試環境驗證設定

4. **執行應用程式**

   **手動執行一次（執行完就關閉）：**
   ```bash
   docker-compose run --rm wp-article-generator
   ```

   **啟動定時排程服務（每天上午9點自動執行）：**
   ```bash
   docker-compose up -d wp-article-scheduler
   ```

   **查看排程服務日誌：**
   ```bash
   docker-compose logs -f wp-article-scheduler
   ```

   **停止所有服務：**
   ```bash
   docker-compose down
   ```

### 檔案說明

- `Dockerfile`: 定義 Python 應用程式的容器映像檔
- `docker-compose.yml`: 定義服務和容器配置
- `requirements.txt`: Python 依賴套件清單
- `env.sample`: 環境變數範本
- `used_refs.json`: 記錄已使用的參考連結（自動生成）
- `used_refs.json.template`: 參考連結樣板檔案
- `wordpress-yoast-setup.php`: WordPress Yoast SEO 設定檔案
- `CRON_GUIDE.md`: Cron 排程時間設定說明

### 注意事項

1. **動態檔案會自動建立**：`used_refs.json` 和 `wp_article_generator.log` 會在程式執行時自動建立
2. **部署時無需手動建立**：程式會檢查檔案是否存在，不存在時會自動建立
3. **檔案權限**：Docker 容器會自動處理檔案權限
4. **建議先在測試環境中驗證設定是否正確**

### 故障排除

如果遇到權限問題：
```bash
sudo chown -R $USER:$USER used_refs.json
```

如果遇到 API 限制：
- 檢查 Google API 配額
- 確認 API 金鑰權限設定正確
