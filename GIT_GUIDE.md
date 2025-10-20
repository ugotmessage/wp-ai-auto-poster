# Git 使用指南

## 📁 專案結構

### ✅ 已上傳到 Git 的檔案
- `app.py` - 主要程式檔案
- `Dockerfile` - Docker 映像檔定義
- `docker-compose.yml` - Docker Compose 配置
- `requirements.txt` - Python 依賴清單
- `env.example` - 環境變數範本
- `run.sh` - 執行腳本
- `check_env.sh` - 環境檢查腳本
- `README.md` - 專案說明文件
- `.gitignore` - Git 忽略檔案清單

### 🚫 被忽略的檔案（不會上傳）
- `.env` - 包含 API 金鑰等敏感資訊
- `.env.backup` - 環境變數備份
- `used_refs.json` - 動態資料檔案
- `wp_article_generator.log` - 日誌檔案
- `__pycache__/` - Python 快取檔案
- `.DS_Store` - macOS 系統檔案

## 🔧 Git 基本操作

### 查看狀態
```bash
git status
```

### 查看被忽略的檔案
```bash
git status --ignored
```

### 新增檔案到 Git
```bash
git add <檔案名>
git add .  # 新增所有變更
```

### 提交變更
```bash
git commit -m "提交訊息"
```

### 查看提交歷史
```bash
git log --oneline
```

## 🚀 推送到遠端倉庫

### 連接到 GitHub/GitLab
```bash
# 新增遠端倉庫
git remote add origin <倉庫URL>

# 推送到遠端
git push -u origin main
```

### 後續推送
```bash
git push
```

## ⚠️ 注意事項

1. **永遠不要提交 `.env` 檔案** - 包含敏感資訊
2. **定期備份 `used_refs.json`** - 如果需要的話
3. **日誌檔案會自動忽略** - 不需要手動處理
4. **使用 `env.example` 作為環境變數範本**

## 📋 建議的 Git 工作流程

1. 修改程式碼
2. 測試功能
3. 檢查 `git status`
4. 新增變更：`git add .`
5. 提交變更：`git commit -m "描述變更"`
6. 推送到遠端：`git push`
