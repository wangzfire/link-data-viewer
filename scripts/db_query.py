#!/usr/bin/env python3
"""
数据库查询封装脚本（pymysql 版）
用途：隐藏数据库连接凭据，仅暴露 SQL 语句
用法：
  python db_query.py <env文件路径> <数据库名> <SQL语句> [选项]

选项：
  --raw       原始输出（TSV 格式，用于导出）
  --table     表格输出（美化显示）
  --silent    静默模式，不显示 warning

示例：
  python db_query.py /path/.env mydb "SELECT 1"
  python db_query.py /path/.env mydb "SELECT * FROM users" --raw > output.tsv
  python db_query.py /path/.env "" "SHOW DATABASES"
"""

import sys
import os
import re


def read_env(env_file):
    """从 .env 文件读取配置"""
    config = {}
    if not os.path.exists(env_file):
        print(f"[错误] .env 文件不存在: {env_file}", file=sys.stderr)
        sys.exit(1)

    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            config[key] = value
    return config


def get_env_value(config, *keys):
    """从配置中按优先级获取值"""
    for key in keys:
        if key in config and config[key]:
            return config[key]
    return None


def format_table(headers, rows):
    """格式化为美化表格"""
    if not headers:
        return ""

    # 计算每列宽度（考虑中文字符占 2 个宽度）
    def display_width(s):
        s = str(s)
        width = 0
        for ch in s:
            if "\u4e00" <= ch <= "\u9fff" or "\uff00" <= ch <= "\uffef":
                width += 2
            else:
                width += 1
        return width

    col_widths = [display_width(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], display_width(val))

    def pad(s, width):
        s = str(s)
        return s + " " * (width - display_width(s))

    lines = []
    # 表头
    header_line = "| " + " | ".join(pad(h, col_widths[i]) for i, h in enumerate(headers)) + " |"
    sep_line = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    lines.append(sep_line)
    lines.append(header_line)
    lines.append(sep_line)
    # 数据行
    for row in rows:
        padded = []
        for i in range(len(headers)):
            val = row[i] if i < len(row) else ""
            padded.append(pad(val, col_widths[i]))
        lines.append("| " + " | ".join(padded) + " |")
    lines.append(sep_line)
    return "\n".join(lines)


def main():
    if len(sys.argv) < 4:
        print("[错误] 参数不足")
        print("用法: python db_query.py <env文件> <数据库名> <SQL语句> [--raw|--table|--silent]")
        sys.exit(1)

    env_file = sys.argv[1]
    db_name = sys.argv[2]
    sql = sys.argv[3]

    # 解析选项
    output_mode = "default"  # default / raw / table
    silent = False
    for arg in sys.argv[4:]:
        if arg == "--raw":
            output_mode = "raw"
        elif arg == "--table":
            output_mode = "table"
        elif arg == "--silent":
            silent = True
        else:
            print(f"[错误] 未知选项: {arg}", file=sys.stderr)
            sys.exit(1)

    # 读取 .env
    config = read_env(env_file)

    db_host = get_env_value(config, "DB_HOST", "DATABASE_HOST", "MYSQL_HOST") or "localhost"
    db_port = int(get_env_value(config, "DB_PORT", "DATABASE_PORT", "MYSQL_PORT") or "3306")
    db_user = get_env_value(config, "DB_USER", "DB_USERNAME", "DATABASE_USER", "MYSQL_USER")
    db_password = get_env_value(config, "DB_PASSWORD", "DATABASE_PASSWORD", "MYSQL_PASSWORD")

    if not db_name:
        db_name = get_env_value(config, "DB_DATABASE", "DB_NAME", "DATABASE_NAME", "MYSQL_DATABASE")

    if not db_user:
        print("[错误] 未找到数据库用户名配置（DB_USER）", file=sys.stderr)
        sys.exit(1)
    if not db_password:
        print("[错误] 未找到数据库密码配置（DB_PASSWORD）", file=sys.stderr)
        sys.exit(1)

    # 连接数据库
    try:
        import pymysql
    except ImportError:
        print("[错误] pymysql 模块未安装，请执行: pip install pymysql", file=sys.stderr)
        sys.exit(1)

    try:
        conn_params = {
            "host": db_host,
            "port": db_port,
            "user": db_user,
            "password": db_password,
            "charset": "utf8mb4",
            "connect_timeout": 5,
            "read_timeout": 600,
            "cursorclass": pymysql.cursors.Cursor,
        }
        if db_name:
            conn_params["database"] = db_name

        conn = pymysql.connect(**conn_params)
    except pymysql.Error as e:
        if not silent:
            print(f"[错误] 数据库连接失败: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)

            # 非查询语句（如 SHOW DATABASES 等也会返回结果）
            if cursor.description is None:
                print("Query OK")
                return

            headers = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            # 将所有值转为字符串
            str_rows = []
            for row in rows:
                str_row = []
                for val in row:
                    if val is None:
                        str_row.append("NULL")
                    else:
                        str_row.append(str(val))
                str_rows.append(str_row)

            if output_mode == "raw":
                # TSV 格式输出（用于导出）
                print("\t".join(headers))
                for row in str_rows:
                    print("\t".join(row))
            elif output_mode == "table":
                # 美化表格输出
                print(format_table(headers, str_rows))
            else:
                # 默认输出（同 TSV）
                print("\t".join(headers))
                for row in str_rows:
                    print("\t".join(row))

    except pymysql.Error as e:
        if not silent:
            print(f"[错误] 查询执行失败: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
