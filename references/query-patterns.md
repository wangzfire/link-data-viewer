# 常用查询模式参考

本文档帮助将用户的自然语言描述转换为准确的 MySQL SELECT 语句。

---

## 目录

1. [条件筛选](#条件筛选)
2. [时间范围](#时间范围)
3. [统计聚合](#统计聚合)
4. [排序与分页](#排序与分页)
5. [模糊搜索](#模糊搜索)
6. [多表关联](#多表关联)
7. [分组查询](#分组查询)
8. [空值处理](#空值处理)

---

## 条件筛选

| 用户说法 | SQL 模式 |
|---------|---------|
| "状态为已完成的" | `WHERE status = '已完成'` 或 `WHERE status = 1`（根据字段类型判断） |
| "价格大于100的" | `WHERE price > 100` |
| "价格在100到500之间" | `WHERE price BETWEEN 100 AND 500` |
| "类型是A或B的" | `WHERE type IN ('A', 'B')` |
| "不是管理员的" | `WHERE role != 'admin'` 或 `WHERE role <> 'admin'` |

**提示**：如果用户描述的条件对应的字段有备注（COLUMN_COMMENT），优先使用备注来推断字段含义。例如字段 `status` 备注为"状态：0-禁用，1-启用"，则用户说"启用的"应转为 `WHERE status = 1`。

---

## 时间范围

| 用户说法 | SQL 模式 |
|---------|---------|
| "今天的" | `WHERE DATE(create_time) = CURDATE()` |
| "昨天的" | `WHERE DATE(create_time) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)` |
| "最近7天" | `WHERE create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)` |
| "最近一个月" | `WHERE create_time >= DATE_SUB(NOW(), INTERVAL 1 MONTH)` |
| "本月的" | `WHERE YEAR(create_time) = YEAR(NOW()) AND MONTH(create_time) = MONTH(NOW())` |
| "上个月的" | `WHERE create_time >= DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 1 MONTH), '%Y-%m-01') AND create_time < DATE_FORMAT(NOW(), '%Y-%m-01')` |
| "2024年的" | `WHERE YEAR(create_time) = 2024` |
| "从3月1日到3月15日" | `WHERE create_time >= '2024-03-01' AND create_time < '2024-03-16'` |

**提示**：
- 自动识别表中可能的时间字段：`create_time`、`created_at`、`add_time`、`gmt_create`、`create_date` 等
- 时间范围查询优先使用 `>=` 和 `<` 而非 `BETWEEN`，避免边界问题
- 展示时间字段使用 `DATE_FORMAT(create_time, '%Y-%m-%d %H:%i:%s')` 格式化

---

## 统计聚合

| 用户说法 | SQL 模式 |
|---------|---------|
| "有多少条" / "总数" | `SELECT COUNT(*) AS 总数 FROM ...` |
| "总金额" / "合计" | `SELECT SUM(amount) AS 总金额 FROM ...` |
| "平均价格" | `SELECT AVG(price) AS 平均价格 FROM ...` |
| "最高/最大的" | `SELECT MAX(price) AS 最高价格 FROM ...` |
| "最低/最小的" | `SELECT MIN(price) AS 最低价格 FROM ...` |
| "去重后有多少" | `SELECT COUNT(DISTINCT user_id) AS 去重数量 FROM ...` |

---

## 排序与分页

| 用户说法 | SQL 模式 |
|---------|---------|
| "按时间倒序" / "最新的" | `ORDER BY create_time DESC` |
| "按时间正序" / "最早的" | `ORDER BY create_time ASC` |
| "金额最高的前10条" | `ORDER BY amount DESC LIMIT 10` |
| "按名称排序" | `ORDER BY name ASC`（默认升序） |

---

## 模糊搜索

| 用户说法 | SQL 模式 |
|---------|---------|
| "名字包含'张'" | `WHERE name LIKE '%张%'` |
| "以'A'开头的" | `WHERE code LIKE 'A%'` |
| "手机号以138开头" | `WHERE phone LIKE '138%'` |

**提示**：前缀匹配（`LIKE 'xxx%'`）可以利用索引，全模糊匹配（`LIKE '%xxx%'`）无法利用索引，大表上需提醒用户。

---

## 多表关联

当用户的查询涉及多张表时（最多3张），使用 JOIN：

```sql
-- 用户想查"订单和对应的用户名"
SELECT o.order_no, u.name, o.amount, o.create_time
FROM orders o
LEFT JOIN users u ON o.user_id = u.id
WHERE o.status = 1;
```

**规则**：
- 优先使用 LEFT JOIN 保留主表所有数据
- 关联字段通常是主表的外键字段和从表的主键
- 最多关联 3 张表
- 需要关联时，先查看目标表的结构确认关联字段

---

## 分组查询

| 用户说法 | SQL 模式 |
|---------|---------|
| "按部门统计人数" | `SELECT dept, COUNT(*) AS 人数 FROM users GROUP BY dept` |
| "每天的订单数" | `SELECT DATE(create_time) AS 日期, COUNT(*) AS 订单数 FROM orders GROUP BY DATE(create_time)` |
| "每月的销售额" | `SELECT DATE_FORMAT(create_time, '%Y-%m') AS 月份, SUM(amount) AS 销售额 FROM orders GROUP BY DATE_FORMAT(create_time, '%Y-%m')` |
| "统计人数大于5的部门" | `SELECT dept, COUNT(*) AS 人数 FROM users GROUP BY dept HAVING COUNT(*) > 5` |

---

## 空值处理

- 查询输出时使用 `IFNULL(字段, '<NULL>')` 标识空值
- 用户说"为空的" → `WHERE column IS NULL`
- 用户说"不为空的" → `WHERE column IS NOT NULL`
- 用户说"为空或空字符串" → `WHERE (column IS NULL OR column = '')`

---

## SQL 别名规范

为让输出对用户更友好，字段别名使用中文（来自 COLUMN_COMMENT）：

```sql
SELECT
  id AS 'ID',
  user_name AS '用户名',
  DATE_FORMAT(create_time, '%Y-%m-%d %H:%i:%s') AS '创建时间',
  IFNULL(remark, '<NULL>') AS '备注'
FROM users
LIMIT 10;
```
