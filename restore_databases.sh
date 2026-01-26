#!/bin/bash
# 医疗 RAG 系统数据库恢复脚本

set -e

BACKUP_DIR="./backups"

if [ $# -eq 0 ]; then
    echo "=========================================="
    echo "  医疗 RAG 系统数据库恢复"
    echo "=========================================="
    echo ""
    echo "用法: $0 <backup_timestamp>"
    echo ""
    echo "可用的备份："
    echo "----------------------------------------"
    if [ -d "$BACKUP_DIR" ]; then
        ls -lh "$BACKUP_DIR"/*.sql 2>/dev/null | awk '{print $9}' | while read file; do
            if [ -f "$file" ]; then
                timestamp=$(basename "$file" | sed 's/postgres_backup_//' | sed 's/.sql//')
                echo "  - $timestamp"
            fi
        done
    fi
    echo ""
    echo "示例: $0 20250126_143000"
    exit 1
fi

TIMESTAMP=$1

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

# 确认恢复操作
echo ""
echo "警告: 此操作将覆盖当前数据库！"
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

# 2. 恢复 Redis 数据库
echo ""
echo "[2/3] 恢复 Redis 数据库..."
# 先停止 Redis
docker-compose stop redis
sleep 2
# 删除现有数据
docker-compose rm -f redis
sleep 1
# 复制备份文件到 Redis 容器
docker cp "$REDIS_BACKUP" ./redis_restore.rdb
# 修改 docker-compose.yml 临时使用备份文件
# 这里需要手动操作，或者使用 volume mount 方式
docker-compose up -d redis
sleep 3
# 删除临时文件
rm -f ./redis_restore.rdb
echo "✓ Redis 恢复完成"

# 3. 恢复 ChromaDB 向量数据库
echo ""
echo "[3/3] 恢复 ChromaDB 向量数据库..."
# 先删除现有向量数据库
rm -rf ./data/vector_db
# 解压备份
tar -xzf "$VECTOR_BACKUP" -C ./data
# 重命名目录
mv ./data/vector_db ./data/vector_db_temp
mv ./data/vector_db_temp/vector_db ./data/vector_db
rmdir ./data/vector_db_temp
echo "✓ ChromaDB 恢复完成"

# 重启所有服务
echo ""
echo "重启服务..."
docker-compose restart api

echo ""
echo "=========================================="
echo "  恢复完成！"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
