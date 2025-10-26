#!/bin/bash

# 測試模式腳本
# 用於測試文章生成功能，不會推送文章到 WordPress

echo "🧪 啟動測試模式..."
echo "========================================="
echo ""
echo "測試模式將："
echo "  ✅ 生成文章"
echo "  ✅ 檢查是否有連結"
echo "  ✅ 保存到 test_output/ 目錄"
echo "  ❌ 不會推送到 WordPress"
echo ""
echo "========================================="
echo ""

# 設置測試模式
export TEST_MODE=true

# 運行 Python 腳本
python app.py

echo ""
echo "========================================="
echo "🎉 測試完成！請檢查 test_output/ 目錄"
echo "========================================="

