#!/bin/bash
# 数据库查询封装脚本
# 用途：隐藏数据库连接凭据，仅暴露 SQL 语句
# 用法：
#   db_query.sh <env文件路径> <数据库名> <SQL语句> [选项]
#
# 选项：
#   --raw       原始输出（-B 模式，TSV 格式，用于导出）
#   --table     表格输出（-t 模式，美化显示）
#   --silent    静默模式，不显示 warning
#
# 示例：
#   db_query.sh /path/.env mydb "SELECT 1"
#   db_query.sh /path/.env mydb "SELECT * FROM users" --raw > output.tsv
#   db_query.sh /path/.env "" "SHOW DATABASES"       # 数据库名为空则不指定库

set -uo pipefail

if [ $# -lt 3 ]; then
    echo "[错误] 参数不足"
    echo "用法: db_query.sh <env文件> <数据库名> <SQL语句> [--raw|--table|--silent]"
    exit 1
fi

ENV_FILE="$1"
DB_NAME="$2"
SQL="$3"
shift 3

# 解析选项
OUTPUT_MODE=""
SILENT=false
while [ $# -gt 0 ]; do
    case "$1" in
        --raw)   OUTPUT_MODE="-B" ;;
        --table) OUTPUT_MODE="-t" ;;
        --silent) SILENT=true ;;
        *) echo "[错误] 未知选项: $1"; exit 1 ;;
    esac
    shift
done

# 从 .env 读取配置
if [ ! -f "$ENV_FILE" ]; then
    echo "[错误] .env 文件不存在: $ENV_FILE"
    exit 1
fi

get_env() {
    local keys=("$@")
    for key in "${keys[@]}"; do
        local val
        val=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed "s/^['\"]//;s/['\"]$//")
        if [ -n "$val" ]; then
            echo "$val"
            return
        fi
    done
}

DB_HOST=$(get_env DB_HOST DATABASE_HOST MYSQL_HOST)
DB_PORT=$(get_env DB_PORT DATABASE_PORT MYSQL_PORT)
DB_USER=$(get_env DB_USER DB_USERNAME DATABASE_USER MYSQL_USER)
DB_PASSWORD=$(get_env DB_PASSWORD DATABASE_PASSWORD MYSQL_PASSWORD)

# 如果参数中的数据库名为空，尝试从 .env 读取
if [ -z "$DB_NAME" ]; then
    DB_NAME=$(get_env DB_DATABASE DB_NAME DATABASE_NAME MYSQL_DATABASE)
fi

# 默认值
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-3306}

# 必填校验
if [ -z "$DB_USER" ]; then
    echo "[错误] 未找到数据库用户名配置（DB_USER）"
    exit 1
fi
if [ -z "$DB_PASSWORD" ]; then
    echo "[错误] 未找到数据库密码配置（DB_PASSWORD）"
    exit 1
fi

# 检测 mysql 客户端
MYSQL=""
if command -v mysql &>/dev/null; then
    MYSQL="mysql"
elif command -v mysql.exe &>/dev/null; then
    MYSQL="mysql.exe"
elif [ -x "/mnt/c/Program Files/MySQL/MySQL Server 8.4/bin/mysql.exe" ]; then
    MYSQL="/mnt/c/Program Files/MySQL/MySQL Server 8.4/bin/mysql.exe"
else
    echo "[错误] 未找到 mysql 客户端"
    exit 1
fi

# 构建命令参数
CMD_ARGS=(-h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" --default-character-set=utf8mb4 --connect-timeout=5)

if [ -n "$DB_NAME" ]; then
    CMD_ARGS+=("$DB_NAME")
fi

if [ -n "$OUTPUT_MODE" ]; then
    CMD_ARGS+=("$OUTPUT_MODE")
fi

CMD_ARGS+=(-e "$SQL")

# 执行
if [ "$SILENT" = true ]; then
    "$MYSQL" "${CMD_ARGS[@]}" 2>/dev/null
else
    "$MYSQL" "${CMD_ARGS[@]}" 2>&1 | grep -v "Using a password on the command line interface can be insecure"
fi
