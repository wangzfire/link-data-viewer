#!/usr/bin/env python3
"""
SQL 安全检查脚本
用途：验证 SQL 语句是否为安全的只读操作
返回值：0 = 安全，1 = 不安全
输出：不安全时输出拒绝原因
用法：python sql_guard.py "<SQL语句>"
"""

import sys
import re


def check_sql(sql):
    """检查 SQL 是否安全，返回 (安全, 原因)"""

    # 移除字符串常量，避免字符串内容中的关键字误报
    sql_cleaned = re.sub(r"'[^']*'", "__STR__", sql)
    sql_cleaned = re.sub(r'"[^"]*"', "__STR__", sql_cleaned)
    sql_upper = sql_cleaned.upper()
    sql_trimmed = sql_upper.strip()

    # 检查 1：是否以允许的关键字开头
    allowed_starts = ("SELECT", "WITH", "SHOW", "DESCRIBE", "DESC", "EXPLAIN")
    if not any(sql_trimmed.startswith(kw) for kw in allowed_starts):
        return False, (
            f"[拒绝] SQL 必须以 SELECT、WITH、SHOW、DESCRIBE 或 EXPLAIN 开头\n"
            f"  检测到的开头: {sql_trimmed[:20]}"
        )

    # 检查 2：禁止的 DML/DDL 关键字
    forbidden_keywords = [
        r"INSERT\s", r"UPDATE\s", r"DELETE\s", r"REPLACE\s",
        r"DROP\s", r"TRUNCATE\s", r"ALTER\s", r"CREATE\s", r"RENAME\s",
        r"GRANT\s", r"REVOKE\s", r"LOAD\s",
        r"INTO\s+OUTFILE", r"INTO\s+DUMPFILE",
        r"CALL\s", r"EXEC\s", r"EXECUTE\s",
        r"SET\s", r"LOCK\s", r"UNLOCK\s",
        r"FLUSH\s", r"PURGE\s", r"RESET\s",
        r"PREPARE\s", r"DEALLOCATE\s", r"HANDLER\s",
    ]
    for pattern in forbidden_keywords:
        if re.search(r"(?:^|[\s;(,])" + pattern, sql_upper):
            keyword_name = re.split(r"\\", pattern)[0]
            return False, (
                f"[拒绝] 检测到禁止的操作: {keyword_name}\n"
                f"  此工具仅支持只读查询（SELECT），不允许修改数据或数据库结构"
            )

    # 检查 3：禁止多语句执行
    sql_no_trailing = sql_upper.rstrip().rstrip(";").rstrip()
    if ";" in sql_no_trailing:
        return False, (
            "[拒绝] 检测到多语句执行（包含分号分隔的多条 SQL）\n"
            "  每次只能执行一条查询语句"
        )

    # 检查 4：禁止访问系统库
    system_dbs = {"MYSQL": r"MYSQL\.", "PERFORMANCE_SCHEMA": r"PERFORMANCE_SCHEMA\.", "SYS": r"SYS\."}
    for db_name, db_pattern in system_dbs.items():
        if re.search(r"(?:FROM|JOIN)\s+" + db_pattern, sql_upper):
            return False, (
                f"[拒绝] 禁止查询系统数据库: {db_name}\n"
                f"  出于安全考虑，不允许访问 MySQL 系统库"
            )

    # 检查 5：禁止危险函数
    dangerous_funcs = ["SLEEP", "BENCHMARK", "LOAD_FILE", "SYS_EXEC", "SYS_EVAL"]
    for func in dangerous_funcs:
        if re.search(func + r"\s*\(", sql_upper):
            return False, (
                f"[拒绝] 检测到危险函数: {func}()\n"
                f"  此函数可能被用于安全攻击，不允许使用"
            )

    # 检查 6：禁止注释注入
    sql_no_strings = re.sub(r"'[^']*'", "", sql)
    sql_no_strings = re.sub(r'"[^"]*"', "", sql_no_strings)
    if re.search(r"(--|#|/\*)", sql_no_strings):
        return False, (
            "[拒绝] SQL 中包含注释符号（--、# 或 /*）\n"
            "  为防止注入攻击，不允许在查询中使用注释"
        )

    return True, "[通过] SQL 安全检查通过"


def main():
    if len(sys.argv) < 2:
        print("[错误] 未提供 SQL 语句")
        print("用法: python sql_guard.py \"<SQL语句>\"")
        sys.exit(1)

    sql = sys.argv[1]
    safe, message = check_sql(sql)
    print(message)
    sys.exit(0 if safe else 1)


if __name__ == "__main__":
    main()
