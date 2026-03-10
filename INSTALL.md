# link-data-viewer 安装与使用指南

## 一、安装

### 1.1 克隆仓库

将技能克隆到 Claude Code 的技能目录：

```bash
git clone https://github.com/wangzfire/link-data-viewer.git ~/.claude/skills/link-data-viewer
```

### 1.2 注册技能

打开 Claude Code 的设置文件 `~/.claude/settings.json`，在 `skills` 中添加：

```json
{
  "skills": {
    "link-data-viewer": {
      "path": "~/.claude/skills/link-data-viewer"
    }
  }
}
```

如果 `settings.json` 不存在，直接创建即可。

### 1.3 环境依赖

技能首次运行时会**自动检测**以下依赖，缺失时会引导安装：

| 依赖 | 用途 | 自动安装方式 |
|------|------|-------------|
| MySQL 客户端 | 连接数据库执行查询 | 通过 winget 安装 |
| Python 3 | Excel 导出 | 通过 winget 安装 |
| openpyxl | Python Excel 库 | 通过 pip 安装 |

> 如果你在 WSL2 环境下使用，技能会自动检测 Windows 侧的 `mysql.exe`、`python.exe`，无需在 Linux 侧额外安装。

---

## 二、配置数据库

在你的**项目根目录**（即 Claude Code 的工作目录）创建 `.env` 文件：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_DATABASE=your_database
```

**配置说明：**

| 配置项 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| DB_HOST | 否 | localhost | 数据库主机地址 |
| DB_PORT | 否 | 3306 | 数据库端口 |
| DB_USER | 是 | — | 数据库用户名 |
| DB_PASSWORD | 是 | — | 数据库密码 |
| DB_DATABASE | 否 | — | 默认数据库名（留空则手动选择） |

支持的变体名称：`DATABASE_HOST`、`MYSQL_HOST`、`DB_USERNAME`、`DATABASE_PASSWORD` 等。

> **安全提示**：`.env` 文件已被 `.gitignore` 排除，不会被提交到 Git 仓库。技能运行时**绝不会修改** `.env` 文件，仅作为只读配置源。

---

## 三、使用方式

### 3.1 触发技能

在 Claude Code 对话中使用以下任意关键词即可自动触发：

- "查询数据库"
- "查看数据表"
- "导出数据"
- "查数据"
- "看表"
- "帮我查一下 xxx 数据"

**示例对话：**

```
你：帮我查一下用户表的数据
你：查询最近7天的订单
你：导出所有状态为启用的记录
```

### 3.2 交互流程

技能会按以下步骤引导你完成查询：

```
① 环境预检
   ↓ 自动检测 mysql、Python3、openpyxl
② 连接数据库
   ↓ 读取 .env，测试连接
③ 浏览数据表
   ↓ 展示所有表名、备注、行数
④ 选择目标表
   ↓ 支持模糊匹配，展示表结构
⑤ 描述查询需求
   ↓ 用自然语言描述，自动生成 SQL
⑥ 预览 & 输出
   ↓ 先看样本，确认后输出完整结果
```

### 3.3 查询示例

你可以用自然语言描述查询需求，技能会自动转换为 SQL：

| 你说的话 | 生成的 SQL |
|---------|-----------|
| "查所有启用的用户" | `SELECT ... FROM users WHERE status = 1` |
| "最近7天的订单" | `SELECT ... FROM orders WHERE create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)` |
| "按部门统计人数" | `SELECT dept, COUNT(*) FROM users GROUP BY dept` |
| "金额最高的前10条" | `SELECT ... FROM orders ORDER BY amount DESC LIMIT 10` |
| "名字包含'张'的" | `SELECT ... FROM users WHERE name LIKE '%张%'` |

### 3.4 输出方式

查询结果支持两种输出方式：

**直接显示**（≤1000 条时可选）：
- 以 Markdown 表格形式展示在对话中
- 超过 50 行时分批显示

**导出 Excel**（>1000 条时强制）：
- 自动生成格式化的 `.xlsx` 文件
- 包含表头样式、交替行色、自动列宽、筛选器
- 文件保存在当前工作目录，文件名格式：`表名_yyyyMMdd_HHmmss.xlsx`

---

## 四、安全机制

### 4.1 只读保护

技能**仅允许**以下 SQL 操作：
- `SELECT` — 数据查询
- `SHOW` — 查看数据库/表信息
- `DESCRIBE` — 查看表结构
- `EXPLAIN` — 查看执行计划

**禁止**所有写操作（INSERT、UPDATE、DELETE、DROP 等），即使用户主动要求也不会执行。

### 4.2 凭据保护

- 数据库密码**不会**在命令行中暴露
- 所有查询通过封装脚本 `db_query.sh` 执行，凭据在脚本内部读取
- 对话中展示连接信息时密码显示为 `****`

### 4.3 性能保护

- 单次查询最大 **10000 行**
- 大表无 WHERE 条件时自动添加 LIMIT
- 查询超时限制 **30 秒**
- JOIN 最多关联 **3 张表**

---

## 五、常见问题

### Q: 提示"未找到 mysql 客户端"怎么办？

技能会自动引导通过 winget 安装。如果 winget 也不可用，可以手动安装：
- **Windows**：下载 [MySQL Installer](https://dev.mysql.com/downloads/installer/)
- **Ubuntu/WSL2**：`sudo apt install mysql-client`

### Q: Excel 导出失败怎么办？

检查 Python3 和 openpyxl 是否可用：
```bash
python3 -c "import openpyxl; print('OK')"
```
如果报错，执行：`pip3 install openpyxl`

### Q: .env 文件中 DB_DATABASE 留空会怎样？

技能会先列出所有可用的数据库，让你选择要查询的库。

### Q: 能否同时查询多张表？

支持 JOIN 关联查询，最多关联 3 张表。用自然语言描述即可，例如："查询订单表和用户表，显示订单号和对应的用户名"。

### Q: 查询结果中文乱码？

技能默认使用 `utf8mb4` 字符集连接数据库。如果仍有乱码，检查数据库和表的字符集设置。
