# link-data-viewer

Claude Code 数据库查询助手技能。连接 MySQL 数据库，通过自然语言对话查询数据并导出 Excel。

## 安装

在 Claude Code 中直接说：

> 请克隆 https://github.com/wangzfire/link-data-viewer.git 到 ~/.claude/skills/link-data-viewer 目录，并在 ~/.claude/settings.json 的 skills 中注册它

或手动执行：

```bash
git clone https://github.com/wangzfire/link-data-viewer.git ~/.claude/skills/link-data-viewer
```

然后在 `~/.claude/settings.json` 中添加：

```json
{
  "skills": {
    "link-data-viewer": {
      "path": "~/.claude/skills/link-data-viewer"
    }
  }
}
```

## 配置

在项目根目录创建 `.env` 文件：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_DATABASE=your_database
```

## 使用

在 Claude Code 中说"查数据"、"查询数据库"、"导出数据"等即可触发。

## 特性

- 自然语言 → SQL，只读安全查询
- 凭据隔离，密码不暴露在命令行
- 格式化 Excel 导出
- 环境依赖自动检测与安装
- WSL2 兼容

## 许可证

MIT
