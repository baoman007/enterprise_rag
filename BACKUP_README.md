# 医疗 RAG 系统数据库备份与恢复指南

## 数据库组成

本系统包含以下 3 个数据库：

1. **PostgreSQL** - 存储文档元数据、知识库信息
2. **Redis** - 缓存层
3. **ChromaDB** - 向量数据库（存储文档向量和相似度检索）

---

## 快速备份

### 一键备份所有数据库

```bash
./backup_databases.sh
```

该脚本会自动：
- 备份 PostgreSQL 数据库（SQL 格式）
- 备份 Redis 数据库（RDB 格式）
- 备份 ChromaDB 向量数据库（压缩归档）
- 自动清理超过 7 天的旧备份

备份文件保存在 `./backups/` 目录，命名格式：
- `postgres_backup_YYYYMMDD_HHMMSS.sql`
- `redis_backup_YYYYMMDD_HHMMSS.rdb`
- `vector_db_backup_YYYYMMDD_HHMMSS.tar.gz`

---

## 快速恢复

### 查看可用备份

```bash
./restore_databases.sh
```

### 恢复指定时间的备份

```bash
./restore_databases.sh 20260126_143000
```

或使用简化版恢复脚本：

```bash
./restore_simple.sh
```

---

## 详细文档

更多详细信息请查看备份恢复脚本中的注释，或联系技术支持。
