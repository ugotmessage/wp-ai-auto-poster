#!/bin/bash

# WordPress 文章自動生成器 - 執行腳本
# 作者: AI Assistant
# 用途: 簡化 Docker Compose 操作

set -e  # 遇到錯誤就停止

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 顯示使用說明
show_help() {
    echo -e "${BLUE}WordPress 文章自動生成器 - 執行腳本${NC}"
    echo ""
    echo "使用方法:"
    echo "  $0 [選項]"
    echo ""
    echo "選項:"
    echo "  run      - 手動執行一次（執行完就關閉）"
    echo "  start    - 啟動定時排程服務（每天上午9點執行）"
    echo "  stop     - 停止所有服務"
    echo "  restart  - 重新啟動排程服務"
    echo "  logs     - 查看服務日誌"
    echo "  local-logs - 查看本地日誌檔案"
    echo "  status   - 查看服務狀態"
    echo "  build    - 重新建構映像檔"
    echo "  clean    - 清理容器和映像檔"
    echo "  help     - 顯示此說明"
    echo ""
    echo "範例:"
    echo "  $0 run        # 執行一次文章生成"
    echo "  $0 start      # 啟動定時排程"
    echo "  $0 logs       # 查看服務日誌"
    echo "  $0 local-logs # 查看本地日誌檔案"
}

# 檢查 Docker 和 Docker Compose
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}錯誤: Docker 未安裝或不在 PATH 中${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}錯誤: Docker Compose 未安裝或不在 PATH 中${NC}"
        exit 1
    fi
}

# 檢查環境變數檔案
check_env_file() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}警告: .env 檔案不存在${NC}"
        if [ -f "env.example" ]; then
            echo -e "${YELLOW}請複製 env.example 為 .env 並填入您的設定:${NC}"
            echo -e "${BLUE}cp env.example .env${NC}"
        fi
        exit 1
    fi
}

# 手動執行一次
run_once() {
    echo -e "${GREEN}🚀 開始執行文章生成...${NC}"
    docker-compose run --rm wp-article-generator
    echo -e "${GREEN}✅ 執行完成！${NC}"
}

# 啟動排程服務
start_scheduler() {
    echo -e "${GREEN}🚀 啟動定時排程服務...${NC}"
    docker-compose up -d wp-article-scheduler
    echo -e "${GREEN}✅ 排程服務已啟動！${NC}"
    echo -e "${BLUE}💡 使用 '$0 logs' 查看日誌${NC}"
}

# 停止服務
stop_services() {
    echo -e "${YELLOW}🛑 停止所有服務...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ 服務已停止！${NC}"
}

# 重新啟動服務
restart_services() {
    echo -e "${YELLOW}🔄 重新啟動排程服務...${NC}"
    docker-compose restart wp-article-scheduler
    echo -e "${GREEN}✅ 服務已重新啟動！${NC}"
}

# 查看日誌
show_logs() {
    echo -e "${BLUE}📋 顯示服務日誌...${NC}"
    docker-compose logs -f wp-article-scheduler
}

# 查看本地日誌檔案
show_local_logs() {
    echo -e "${BLUE}📋 顯示本地日誌檔案...${NC}"
    if [ -f "wp_article_generator.log" ]; then
        echo -e "${GREEN}最新的日誌內容:${NC}"
        tail -50 wp_article_generator.log
        echo ""
        echo -e "${BLUE}💡 使用 'tail -f wp_article_generator.log' 即時查看日誌${NC}"
    else
        echo -e "${YELLOW}日誌檔案不存在，請先執行一次程式${NC}"
    fi
}

# 查看狀態
show_status() {
    echo -e "${BLUE}📊 服務狀態:${NC}"
    docker-compose ps
}

# 建構映像檔
build_images() {
    echo -e "${GREEN}🔨 建構 Docker 映像檔...${NC}"
    docker-compose build
    echo -e "${GREEN}✅ 映像檔建構完成！${NC}"
}

# 清理容器和映像檔
clean_up() {
    echo -e "${YELLOW}🧹 清理容器和映像檔...${NC}"
    docker-compose down --rmi all --volumes --remove-orphans
    echo -e "${GREEN}✅ 清理完成！${NC}"
}

# 主程式
main() {
    # 檢查依賴
    check_dependencies
    
    # 檢查參數
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    case "$1" in
        "run")
            check_env_file
            run_once
            ;;
        "start")
            check_env_file
            start_scheduler
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "logs")
            show_logs
            ;;
        "local-logs")
            show_local_logs
            ;;
        "status")
            show_status
            ;;
        "build")
            build_images
            ;;
        "clean")
            clean_up
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}錯誤: 未知的選項 '$1'${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 執行主程式
main "$@"
