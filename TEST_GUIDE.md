# 測試模式使用指南

## 為什麼需要測試模式？

在正式推送文章到 WordPress 之前，使用測試模式可以：
1. 檢查生成的文章是否包含不安全的連結
2. 驗證文章內容質量
3. 避免推送有問題的文章到線上環境

## 如何使用測試模式

### 方法 1: 使用環境變數

在 `.env` 文件中添加：
```bash
TEST_MODE=true
```

然後運行：
```bash
python app.py
```

### 方法 2: 使用 Docker

修改 `docker-compose.yml` 或在運行時指定：
```bash
TEST_MODE=true docker-compose up
```

或者直接在 `docker-compose.yml` 的環境變數中添加：
```yaml
environment:
  - TEST_MODE=true
```

## 測試結果

測試模式運行後，會在 `test_output/` 目錄下生成測試文件，文件名格式：
```
test_output/test_YYYYMMDD_HHMMSS_[關鍵字].txt
```

每個測試文件包含：
- 測試時間和關鍵字
- SEO 標題、描述和關鍵字
- **連結檢查結果**：
  - ✅ 沒有發現任何連結
  - ⚠️ 發現連結（會列出具體連結內容）
- 完整的文章內容

## 查看結果

```bash
# 列出所有測試文件
ls -lh test_output/

# 查看最新的測試文件
ls -t test_output/ | head -1 | xargs cat

# 查找包含連結的測試文件
grep -l "發現連結" test_output/*.txt
```

## 清理測試文件

```bash
# 刪除所有測試文件
rm -rf test_output/*.txt
```

## 下一步

1. 運行測試模式：`TEST_MODE=true python app.py`
2. 檢查 `test_output/` 目錄下的文件
3. 確認沒有發現任何連結（應該顯示 "✅ 沒有發現任何連結"）
4. 如果確認無誤，關閉測試模式：`TEST_MODE=false` 或刪除 `TEST_MODE` 環境變數
5. 正式推送文章到 WordPress

## 注意事項

- 測試模式**不會**推送到 WordPress
- 測試模式會使用環境變數中的關鍵字，不會連接 WordPress 獲取標籤
- 測試輸出保存在本地 `test_output/` 目錄
- 測試輸出不會被提交到 Git（已加入 .gitignore）

