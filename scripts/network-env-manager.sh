#!/bin/bash

# 网络环境管理脚本
# 用于在公司和家庭环境之间快速切换网络配置

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.network-configs"
CURRENT_ENV_FILE="$CONFIG_DIR/current-env"

# 创建配置目录
mkdir -p "$CONFIG_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE}    网络环境管理器 v1.0${NC}"
    echo -e "${BLUE}=====================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# 检测当前网络环境
detect_environment() {
    print_info "检测网络环境..."
    
    # 检查是否能访问公司代理
    if curl -s --connect-timeout 3 --max-time 5 http://127.0.0.1:1080 >/dev/null 2>&1; then
        echo "office"
    elif ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
        echo "home"
    else
        echo "unknown"
    fi
}

# 获取当前环境
get_current_env() {
    if [[ -f "$CURRENT_ENV_FILE" ]]; then
        cat "$CURRENT_ENV_FILE"
    else
        echo "unknown"
    fi
}

# 设置当前环境
set_current_env() {
    echo "$1" > "$CURRENT_ENV_FILE"
}

# 配置公司环境
setup_office() {
    print_info "配置公司网络环境..."
    
    # 设置代理环境变量
    export http_proxy=http://127.0.0.1:1080
    export HTTP_PROXY=http://127.0.0.1:1080
    export https_proxy=http://127.0.0.1:1080
    export HTTPS_PROXY=http://127.0.0.1:1080
    export no_proxy=localhost,127.0.0.1,::1,0.0.0.0
    export NO_PROXY=localhost,127.0.0.1,::1,0.0.0.0
    
    # 保存到配置文件
    cat > "$CONFIG_DIR/office.env" << EOF
export http_proxy=http://127.0.0.1:1080
export HTTP_PROXY=http://127.0.0.1:1080
export https_proxy=http://127.0.0.1:1080
export HTTPS_PROXY=http://127.0.0.1:1080
export no_proxy=localhost,127.0.0.1,::1,0.0.0.0
export NO_PROXY=localhost,127.0.0.1,::1,0.0.0.0
EOF

    # npm代理配置
    npm config set proxy http://127.0.0.1:1080
    npm config set https-proxy http://127.0.0.1:1080
    npm config set registry https://registry.npmmirror.com/
    
    # git代理配置
    git config --global http.proxy http://127.0.0.1:1080
    git config --global https.proxy http://127.0.0.1:1080
    
    set_current_env "office"
    print_success "公司环境配置完成"
}

# 配置家庭环境
setup_home() {
    print_info "配置家庭网络环境..."
    
    # 清除代理环境变量
    unset http_proxy HTTP_PROXY https_proxy HTTPS_PROXY
    unset no_proxy NO_PROXY
    
    # 保存到配置文件
    cat > "$CONFIG_DIR/home.env" << EOF
unset http_proxy
unset HTTP_PROXY
unset https_proxy
unset HTTPS_PROXY
unset no_proxy
unset NO_PROXY
EOF

    # 清除npm代理配置
    npm config delete proxy >/dev/null 2>&1
    npm config delete https-proxy >/dev/null 2>&1
    npm config set registry https://registry.npmjs.org/
    
    # 清除git代理配置
    git config --global --unset http.proxy >/dev/null 2>&1
    git config --global --unset https.proxy >/dev/null 2>&1
    
    set_current_env "home"
    print_success "家庭环境配置完成"
}

# 应用配置到当前shell
apply_config() {
    local env_type="$1"
    if [[ -f "$CONFIG_DIR/${env_type}.env" ]]; then
        source "$CONFIG_DIR/${env_type}.env"
        print_success "已应用 ${env_type} 环境配置到当前shell"
    fi
}

# 测试网络连通性
test_connectivity() {
    local env_type="$1"
    print_info "测试网络连通性..."
    
    # 测试基本网络
    if curl -s --connect-timeout 5 --max-time 10 http://www.baidu.com >/dev/null 2>&1; then
        print_success "网络连接正常"
    else
        print_error "网络连接失败"
        return 1
    fi
    
    # 测试本地API
    if curl -s --connect-timeout 3 --max-time 5 http://127.0.0.1:8000 >/dev/null 2>&1; then
        print_success "本地后端API可访问"
    else
        print_warning "本地后端API不可访问（可能未启动）"
    fi
    
    return 0
}

# 显示当前状态
show_status() {
    print_header
    
    local current_env=$(get_current_env)
    local detected_env=$(detect_environment)
    
    echo -e "${BLUE}当前配置环境:${NC} $current_env"
    echo -e "${BLUE}检测到的环境:${NC} $detected_env"
    echo
    
    if [[ "$current_env" != "$detected_env" && "$detected_env" != "unknown" ]]; then
        print_warning "环境不匹配，建议重新配置"
    fi
    
    echo -e "${BLUE}环境变量状态:${NC}"
    echo "  http_proxy: ${http_proxy:-未设置}"
    echo "  npm proxy: $(npm config get proxy 2>/dev/null || echo '未设置')"
    echo "  git proxy: $(git config --global --get http.proxy 2>/dev/null || echo '未设置')"
    echo
}

# 自动配置
auto_configure() {
    print_info "自动检测并配置网络环境..."
    
    local detected_env=$(detect_environment)
    
    case $detected_env in
        "office")
            print_info "检测到公司环境"
            setup_office
            apply_config "office"
            ;;
        "home")
            print_info "检测到家庭环境"
            setup_home
            apply_config "home"
            ;;
        "unknown")
            print_error "无法检测网络环境，请手动选择"
            return 1
            ;;
    esac
    
    test_connectivity "$detected_env"
}

# 重启开发服务
restart_dev_services() {
    print_info "重启开发服务..."
    
    # 查找并杀死现有进程
    local pids=$(ps aux | grep -E "(uvicorn|npm.*start)" | grep -v grep | awk '{print $2}')
    if [[ -n "$pids" ]]; then
        echo "$pids" | xargs kill -9 >/dev/null 2>&1
        print_success "已停止现有服务"
        sleep 2
    fi
    
    # 重启后端
    cd "$(dirname "$SCRIPT_DIR")/backend"
    if [[ -f "app/main.py" ]]; then
        print_info "启动后端服务..."
        nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
        print_success "后端服务已启动"
    fi
    
    # 重启前端
    cd "$(dirname "$SCRIPT_DIR")/frontend/chip-quotation-frontend"
    if [[ -f "package.json" ]]; then
        print_info "启动前端服务..."
        nohup npm start > frontend.log 2>&1 &
        print_success "前端服务已启动"
    fi
    
    print_info "等待服务启动..."
    sleep 5
    
    # 测试服务
    if curl -s http://127.0.0.1:8000 >/dev/null 2>&1; then
        print_success "后端服务运行正常"
    else
        print_warning "后端服务可能未正常启动"
    fi
}

# 显示帮助信息
show_help() {
    print_header
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help          显示此帮助信息"
    echo "  -s, --status        显示当前网络环境状态"
    echo "  -a, --auto          自动检测并配置网络环境"
    echo "  -o, --office        手动配置为公司环境"
    echo "  -H, --home          手动配置为家庭环境"
    echo "  -t, --test          测试网络连通性"
    echo "  -r, --restart       重启开发服务"
    echo
    echo "示例:"
    echo "  $0 --auto           # 自动配置"
    echo "  $0 --office         # 切换到公司环境"
    echo "  $0 --home           # 切换到家庭环境"
    echo "  $0 --status         # 查看状态"
    echo
}

# 主函数
main() {
    case "${1:-}" in
        -h|--help)
            show_help
            ;;
        -s|--status)
            show_status
            ;;
        -a|--auto)
            auto_configure
            ;;
        -o|--office)
            setup_office
            apply_config "office"
            test_connectivity "office"
            ;;
        -H|--home)
            setup_home
            apply_config "home"
            test_connectivity "home"
            ;;
        -t|--test)
            local current_env=$(get_current_env)
            test_connectivity "$current_env"
            ;;
        -r|--restart)
            restart_dev_services
            ;;
        "")
            # 无参数时显示状态并提供交互选择
            show_status
            echo "请选择操作:"
            echo "1) 自动配置"
            echo "2) 配置为公司环境"  
            echo "3) 配置为家庭环境"
            echo "4) 测试连通性"
            echo "5) 重启服务"
            echo "0) 退出"
            echo
            read -p "请输入选择 (0-5): " choice
            
            case $choice in
                1) auto_configure ;;
                2) setup_office; apply_config "office"; test_connectivity "office" ;;
                3) setup_home; apply_config "home"; test_connectivity "home" ;;
                4) test_connectivity "$(get_current_env)" ;;
                5) restart_dev_services ;;
                0) exit 0 ;;
                *) print_error "无效选择" ;;
            esac
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"