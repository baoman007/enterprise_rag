#!/usr/bin/env python3
"""
Embedding 模型下载脚本（使用 Python API）
"""

import os
import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
    # 不导入 sentence_transformers，避免版本冲突
except ImportError as e:
    print(f"错误: 缺少依赖包 - {e}")
    print("请运行: pip3 install huggingface_hub")
    sys.exit(1)

# 配置
MODEL_NAME = "BAAI/bge-small-zh-v1.5"
MODELS_DIR = Path("./models")
LOCAL_MODEL_DIR = MODELS_DIR / MODEL_NAME

print("=" * 50)
print("  Embedding 模型私有化部署")
print("=" * 50)
print(f"\n模型名称: {MODEL_NAME}")
print(f"本地路径: {LOCAL_MODEL_DIR}\n")

# 检查是否已下载
if LOCAL_MODEL_DIR.exists():
    print(f"✅ 模型已存在: {LOCAL_MODEL_DIR}")

    response = input("\n重新下载? (y/n): ").strip().lower()
    if response != 'y':
        print("使用现有模型")
        sys.exit(0)

    print("\n删除旧模型...")
    import shutil
    shutil.rmtree(LOCAL_MODEL_DIR)

# 创建目录
MODELS_DIR.mkdir(exist_ok=True)

# 使用国内镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

print("=" * 50)
print("开始下载模型...")
print("=" * 50)

try:
    # 下载模型
    model_path = snapshot_download(
        repo_id=MODEL_NAME,
        local_dir=str(LOCAL_MODEL_DIR),
        local_dir_use_symlinks=False,
        resume_download=True
    )

    print("\n" + "=" * 50)
    print("✅ 模型下载完成!")
    print("=" * 50)

    # 显示下载的文件
    print("\n下载的文件:")
    for f in sorted(LOCAL_MODEL_DIR.rglob("*")):
        if f.is_file():
            size = f.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"  {f.name:30} {size_mb:8.2f} MB")

    # 验证模型文件
    print("\n验证模型文件...")
    required_files = ['config.json', 'model.safetensors', 'tokenizer.json', 'tokenizer_config.json']
    missing_files = []
    for f in required_files:
        if not (LOCAL_MODEL_DIR / f).exists():
            missing_files.append(f)

    if missing_files:
        print(f"⚠️  缺少文件: {', '.join(missing_files)}")
    else:
        print("✅ 所有必需文件都已下载")

    # 更新配置文件
    print("\n" + "=" * 50)
    print("更新配置文件...")
    print("=" * 50)

    env_file = Path(".env")
    if env_file.exists():
        # 备份
        backup_file = Path(".env.backup")
        import shutil
        shutil.copy(env_file, backup_file)
        print("✅ 已备份 .env 到 .env.backup")

        # 更新配置
        lines = env_file.read_text(encoding='utf-8').split('\n')
        new_lines = []
        updated = False

        for line in lines:
            if line.startswith('EMBEDDING_MODEL='):
                new_lines.append(f'EMBEDDING_MODEL=/app/models/{MODEL_NAME}')
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            new_lines.append(f'EMBEDDING_MODEL=/app/models/{MODEL_NAME}')

        env_file.write_text('\n'.join(new_lines), encoding='utf-8')
        print(f"✅ 已更新 EMBEDDING_MODEL = /app/models/{MODEL_NAME}")
    else:
        print("⚠️  未找到 .env 文件")

    # 检查 docker-compose.yml
    compose_file = Path("docker-compose.yml")
    if compose_file.exists():
        content = compose_file.read_text(encoding='utf-8')
        if './models:/app/models' not in content:
            print("\n" + "=" * 50)
            print("⚠️  需要手动更新 docker-compose.yml")
            print("=" * 50)
            print("\n请在 api 服务的 volumes 部分添加:")
            print("  - ./models:/app/models")
        else:
            print("✅ docker-compose.yml 已正确配置")

    print("\n" + "=" * 50)
    print("部署完成!")
    print("=" * 50)
    print("\n下一步:")
    print("1. 如果需要，手动编辑 docker-compose.yml")
    print("2. 重启服务:")
    print("   docker-compose down && docker-compose up -d")
    print("3. 查看日志:")
    print("   docker logs enterprise_rag-api-1 | grep embedding")

except Exception as e:
    print(f"\n❌ 下载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
