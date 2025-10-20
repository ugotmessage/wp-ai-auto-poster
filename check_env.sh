#!/bin/bash

# 環境變數檢查腳本
# 用於診斷 Unicode 編碼問題

echo "🔍 檢查環境變數設定..."
echo ""

if [ ! -f ".env" ]; then
    echo "❌ .env 檔案不存在"
    echo "請先複製 env.example 為 .env 並填入您的設定"
    exit 1
fi

echo "📋 載入環境變數..."
# 只載入沒有註解的行
export $(grep -v '^#' .env | grep -v '^$' | xargs)

echo ""
echo "🔍 檢查可能包含中文字元的環境變數:"
echo ""

# 檢查各個環境變數
check_var() {
    local var_name=$1
    local var_value=$2
    
    if [ -n "$var_value" ]; then
        # 檢查是否包含非 ASCII 字元
        if echo "$var_value" | grep -q '[^\x00-\x7F]'; then
            echo "⚠️  $var_name: $var_value (包含非 ASCII 字元)"
        else
            echo "✅ $var_name: $var_value"
        fi
    else
        echo "❌ $var_name: 未設定"
    fi
}

check_var "BRAND_NAME" "$BRAND_NAME"
check_var "SITE_NAME" "$SITE_NAME"
check_var "KEYWORDS" "$KEYWORDS"
check_var "TAGS" "$TAGS"

echo ""
echo "💡 建議:"
echo "   - 將 BRAND_NAME 改為英文，例如: MyBrand"
echo "   - 將 KEYWORDS 中的中文關鍵字改為英文，例如: health,nutrition,fitness"
echo "   - 將 TAGS 中的中文標籤改為英文，例如: health,lifestyle,wellness"
echo ""
echo "🔧 修正後請重新執行: ./run.sh run"
