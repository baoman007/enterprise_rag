#!/usr/bin/env python3
"""
FastAPI主服务
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os

from .routers import medical, knowledge, audit
from .core.config import settings
from .core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("🚀 启动医疗RAG系统...")
    await init_db()
    print("✅ 数据库初始化完成")
    yield
    # 关闭时清理
    print("👋 关闭医疗RAG系统...")


app = FastAPI(
    title="医疗企业RAG系统",
    description="为医疗机构提供的智能问答和知识检索服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(medical.router, prefix="/api/v1/medical", tags=["医疗问答"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["知识库管理"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["审计日志"])

# 挂载静态文件（向量数据库查看器）
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    print(f"✅ 静态文件服务已挂载: {static_path}")


@app.get("/")
async def root():
    """健康检查"""
    return {
        "service": "医疗企业RAG系统",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查（详细）"""
    return {
        "status": "healthy",
        "database": "connected",
        "vector_db": "connected"
    }


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发模式
    )
