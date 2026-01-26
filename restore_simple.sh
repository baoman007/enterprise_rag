#!/bin/bash
# 医疗 RAG 系统数据库恢复脚本（简化版）

set -e

BACKUP_DIR="./backups"
TIMESTAMP="${1:-$(ls -t $BACKUP_DIR/postgres_backup_*.sql 2>/dev/null | head -1 | xargs basename | sed 's/postgres_backup_//' | sed 's/.sql//')}"

echo "=========================================="
echo "  医疗 RAG 系统数据库恢复"
echo "  备份时间: $TIMESTAMP"
echo "=========================================="

# 检查备份文件是否存在
POSTGRES_BACKUP="$BACKUP_DIR/postgres_backup_$TIMESTAMP.sql"
REDIS_BACKUP="$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"
VECTOR_BACKUP="$BACKUP_DIR/vector_db_backup_$TIMESTAMP.tar.gz"

if [ ! -f "$POSTGRES_BACKUP" ]; then
    echo "错误: PostgreSQL 备份文件不存在: $POSTGRES_BACKUP"
    exit 1
fi

if [ ! -f "$REDIS_BACKUP" ]; then
    echo "错误: Redis 备份文件不存在: $REDIS_BACKUP"
    exit 1
fi

if [ ! -f "$VECTOR_BACKUP" ]; then
    echo "错误: ChromaDB 备份文件不存在: $VECTOR_BACKUP"
    exit 1
fi

echo ""
echo "备份文件："
echo "  - PostgreSQL: $POSTGRES_BACKUP"
echo "  - Redis: $REDIS_BACKUP"
echo "  - ChromaDB: $VECTOR_BACKUP"
echo ""

read -p "确认恢复？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "操作已取消"
    exit 0
fi

# 1. 恢复 PostgreSQL 数据库
echo ""
echo "[1/3] 恢复 PostgreSQL 数据库..."
cat "$POSTGRES_BACKUP" | docker-compose exec -T postgres psql -U postgres -d medical_rag
echo "✓ PostgreSQL 恢复完成"

# 2. 恢复 ChromaDB 向量数据库
echo ""
echo "[2/3] 恢复 ChromaDB 向量数据库..."
# 停止 API 服务
docker-compose stop api
sleep 2
# 删除现有向量数据库
rm -rf ./data/vector_db
# 解压备份
tar -xzf "$VECTOR_BACKUP"
# 重新启动 API 服务
docker-compose start api
sleep 3
echo "✓ ChromaDB 恢复完成"

# 3. 恢复 Redis 数据库
echo ""
echo "[3/3] 恢复 Redis 数据库..."
docker-compose exec redis redis-cli FLUSHALL
docker-compose exec -T redis bash -c "cat > /tmp/restore.rdb" < "$REDIS_BACKUP"
docker-compose exec redis redis-cli --rdb /tmp/restore.rdb
echo "✓ Redis 恢复完成"

echo ""
echo "=========================================="
echo "  恢复完成！"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
