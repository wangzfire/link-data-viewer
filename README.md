# link-data-viewer

Claude Code 数据库查询助手技能。连接 MySQL 数据库，以对话式交互帮助用户查询数据、预览结果并导出 Excel。

## 功能特性

- **对话式查询**：用自然语言描述查询需求，自动生成 SQL
- **安全只读**：仅允许 SELECT 查询，内置 SQL 安全检查
- **凭据保护**：数据库密码不会在命令行中暴露
- **Excel 导出**：支持格式化 Excel 导出（自动列宽、表头样式、交替行色、筛选器）
- **环境自检**：自动检测并安装 MySQL 客户端、Python3、openpyxl 等依赖
- **WSL2 兼容**：完整支持 WSL2 环境下调用 Windows 侧工具

## 文件结构

```
link-data-viewer/
├── SKILL.md                      # 技能主指令文件
├── README.md                     # 本文件
├── scripts/
│   ├── db_query.sh               # 数据库查询封装脚本（隐藏凭据）
│   ├── sql_guard.sh              # SQL 安全检查脚本
│   └── export_excel.py           # TSV → Excel 导出脚本
└── references/
    └── query-patterns.md         # 常用查询模式参考
```

## 使用方式

### 1. 安装技能

将本仓库克隆到 Claude Code 技能目录：

```bash
git clone https://github.com/wangzfire/link-data-viewer.git ~/.claude/skills/link-data-viewer
```

### 2. 配置数据库

在你的项目根目录创建 `.env` 文件：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_DATABASE=your_database
```

### 3. 触发技能

在 Claude Code 中使用以下关键词即可触发：

- "查询数据库"
- "查看数据表"
- "导出数据"
- "帮我查一下 xxx 数据"

## 工作流程

1. **环境预检** — 检测 mysql 客户端、Python3、openpyxl
2. **数据库连接** — 读取 .env 配置，测试连接
3. **数据表浏览** — 列出所有数据表（表名、备注、行数）
4. **表选择** — 模糊匹配表名/备注，展示表结构
5. **查询构建** — 自然语言 → SQL，安全检查，先 COUNT
6. **结果输出** — 样本预览 → 直接显示 / Excel 导出

## 安全机制

- 仅允许 `SELECT` / `SHOW` / `DESCRIBE` / `EXPLAIN` 语句
- 禁止所有 DML/DDL 操作（INSERT、UPDATE、DELETE、DROP 等）
- 禁止访问系统库（mysql、performance_schema、sys）
- 禁止危险函数（SLEEP、BENCHMARK、LOAD_FILE 等）
- 禁止注释注入和多语句执行
- 数据库凭据通过封装脚本隔离，不在命令行中暴露
- 单次查询最大 10000 行，超时限制 30 秒

## 依赖

- MySQL 客户端（mysql CLI）
- Python 3 + openpyxl（用于 Excel 导出）
- 缺失依赖会在首次运行时自动检测并引导安装

## 许可证

MIT
