# Cron 排程時間設定說明

## 🕒 常用排程時間範例

### 每天執行
```bash
# 每天上午 9 點
0 9 * * *

# 每天下午 2 點
0 14 * * *

# 每天晚上 8 點
0 20 * * *
```

### 每週執行
```bash
# 每週一上午 9 點
0 9 * * 1

# 每週五下午 2 點
0 14 * * 5
```

### 每月執行
```bash
# 每月 1 號上午 9 點
0 9 1 * *

# 每月 15 號下午 2 點
0 14 15 * *
```

## 🔧 修改排程時間

### 方法 1：修改 Docker Compose（推薦）
編輯 `docker-compose.yml` 第 30 行：
```yaml
echo '0 9 * * * python /app/app.py' | crontab - &&
```
改為您想要的時間，例如：
```yaml
echo '0 14 * * * python /app/app.py' | crontab - &&
```

### 方法 2：使用系統 cron
```bash
# 編輯 crontab
crontab -e

# 新增這行（每天下午 2 點執行）
0 14 * * * cd /Users/HTLin/Desktop/DockerApp/wp-article && ./run.sh run
```

## 📋 Cron 時間格式說明
```
* * * * *
│ │ │ │ │
│ │ │ │ └── 星期幾 (0-7, 0 和 7 都代表星期日)
│ │ │ └──── 月份 (1-12)
│ │ └────── 日期 (1-31)
│ └──────── 小時 (0-23)
└────────── 分鐘 (0-59)
```

## 🚀 啟動排程服務
```bash
# 啟動定時排程
./run.sh start

# 查看服務狀態
./run.sh status

# 查看日誌
./run.sh local-logs
```
