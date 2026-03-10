#!/bin/bash
# SQL 安全检查脚本
# 用途：验证 SQL 语句是否为安全的只读操作
# 返回值：0 = 安全，1 = 不安全
# 输出：不安全时输出拒绝原因

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "[错误] 未提供 SQL 语句"
    echo "用法: sql_guard.sh \"<SQL语句>\""
    exit 1
fi

SQL="$1"

# 转为大写用于关键字匹配（保留原始 SQL 用于错误提示）
SQL_UPPER=$(echo "$SQL" | tr '[:lower:]' '[:upper:]')

# 移除字符串常量，避免字符串内容中的关键字误报
# 将 '...' 和 "..." 替换为空占位符
SQL_CLEANED=$(echo "$SQL_UPPER" | sed -E "s/'[^']*'/__STR__/g; s/\"[^\"]*\"/__STR__/g")

# ========== 检查 1：是否以 SELECT 或 WITH 开头 ==========
# 去除前导空白
SQL_TRIMMED=$(echo "$SQL_CLEANED" | sed 's/^[[:space:]]*//')

if [[ ! "$SQL_TRIMMED" =~ ^(SELECT|WITH|SHOW|DESCRIBE|DESC|EXPLAIN) ]]; then
    echo "[拒绝] SQL 必须以 SELECT、WITH、SHOW、DESCRIBE 或 EXPLAIN 开头"
    echo "  检测到的开头: $(echo "$SQL_TRIMMED" | head -c 20)"
    exit 1
fi

# ========== 检查 2：禁止的 DML/DDL 关键字 ==========
FORBIDDEN_KEYWORDS=(
    "INSERT[[:space:]]"
    "UPDATE[[:space:]]"
    "DELETE[[:space:]]"
    "REPLACE[[:space:]]"
    "DROP[[:space:]]"
    "TRUNCATE[[:space:]]"
    "ALTER[[:space:]]"
    "CREATE[[:space:]]"
    "RENAME[[:space:]]"
    "GRANT[[:space:]]"
    "REVOKE[[:space:]]"
    "LOAD[[:space:]]"
    "INTO[[:space:]]+OUTFILE"
    "INTO[[:space:]]+DUMPFILE"
    "CALL[[:space:]]"
    "EXEC[[:space:]]"
    "EXECUTE[[:space:]]"
    "SET[[:space:]]"
    "LOCK[[:space:]]"
    "UNLOCK[[:space:]]"
    "FLUSH[[:space:]]"
    "PURGE[[:space:]]"
    "RESET[[:space:]]"
    "PREPARE[[:space:]]"
    "DEALLOCATE[[:space:]]"
    "HANDLER[[:space:]]"
)

for keyword in "${FORBIDDEN_KEYWORDS[@]}"; do
    if echo "$SQL_CLEANED" | grep -qE "(^|[[:space:];(,])${keyword}"; then
        # 提取匹配到的关键字名称用于提示
        KEYWORD_NAME=$(echo "$keyword" | sed 's/\[.*//g')
        echo "[拒绝] 检测到禁止的操作: ${KEYWORD_NAME}"
        echo "  此工具仅支持只读查询（SELECT），不允许修改数据或数据库结构"
        exit 1
    fi
done

# ========== 检查 3：禁止多语句执行 ==========
# 去掉字符串中的分号后，检查是否有多个分号分隔的语句
# 允许末尾的分号
SQL_NO_TRAILING=$(echo "$SQL_CLEANED" | sed 's/[[:space:]]*;[[:space:]]*$//')
if echo "$SQL_NO_TRAILING" | grep -q ";"; then
    echo "[拒绝] 检测到多语句执行（包含分号分隔的多条 SQL）"
    echo "  每次只能执行一条查询语句"
    exit 1
fi

# ========== 检查 4：禁止访问系统库 ==========
SYSTEM_DBS=(
    "MYSQL\."
    "PERFORMANCE_SCHEMA\."
    "SYS\."
)

for sysdb in "${SYSTEM_DBS[@]}"; do
    if echo "$SQL_CLEANED" | grep -qE "(FROM|JOIN)[[:space:]]+${sysdb}"; then
        DB_NAME=$(echo "$sysdb" | sed 's/\\\.//g')
        echo "[拒绝] 禁止查询系统数据库: ${DB_NAME}"
        echo "  出于安全考虑，不允许访问 MySQL 系统库"
        exit 1
    fi
done

# ========== 检查 5：禁止危险函数 ==========
DANGEROUS_FUNC_NAMES=("SLEEP" "BENCHMARK" "LOAD_FILE" "SYS_EXEC" "SYS_EVAL")

for func_name in "${DANGEROUS_FUNC_NAMES[@]}"; do
    if echo "$SQL_CLEANED" | grep -qE "${func_name}[[:space:]]*\("; then
        echo "[拒绝] 检测到危险函数: ${func_name}()"
        echo "  此函数可能被用于安全攻击，不允许使用"
        exit 1
    fi
done

# ========== 检查 6：禁止注释注入 ==========
if echo "$SQL" | grep -qE "(--|#|/\*)" ; then
    # 仅当注释出现在字符串外部时才拒绝
    SQL_NO_STRINGS=$(echo "$SQL" | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")
    if echo "$SQL_NO_STRINGS" | grep -qE "(--|#|/\*)" ; then
        echo "[拒绝] SQL 中包含注释符号（--、# 或 /*）"
        echo "  为防止注入攻击，不允许在查询中使用注释"
        exit 1
    fi
fi

# ========== 全部通过 ==========
echo "[通过] SQL 安全检查通过"
exit 0
