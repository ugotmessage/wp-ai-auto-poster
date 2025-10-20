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

3. **執行應用程式**

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

### 注意事項

1. 確保 `used_refs.json` 檔案有適當的權限，讓容器可以讀寫
2. 如果需要定時執行，可以修改 `docker-compose.yml` 中的排程設定
3. 建議先在測試環境中驗證設定是否正確

### 故障排除

如果遇到權限問題：
```bash
sudo chown -R $USER:$USER used_refs.json
```

如果遇到 API 限制：
- 檢查 Google API 配額
- 確認 API 金鑰權限設定正確
