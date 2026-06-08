"""
AI视频生成器 - Vercel异步部署版
适配Vercel Serverless 10秒超时限制
"""

import os
import uuid
from typing import Optional
from datetime import datetime

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AI视频生成器")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOUBAO_API_KEY = os.environ.get("DOUBAO_API_KEY", "")
API_GENERATE = "https://ark.cn-beijing.volces.com/api/v3/video/generate"
API_TASK = "https://ark.cn-beijing.volces.com/api/v3/video/task/"

# 内存任务状态存储
_task_status = {}

class GenerateRequest(BaseModel):
    prompt: str
    model: str

class GenerateResponse(BaseModel):
    success: bool
    videoUrl: Optional[str] = None
    error: Optional[str] = None
    taskId: Optional[str] = None
    status: Optional[str] = None

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_video(req: GenerateRequest):
    """提交视频生成任务，立即返回任务ID"""
    if not DOUBAO_API_KEY:
        return GenerateResponse(success=False, error="服务未配置API密钥")
    
    if not req.prompt or not req.prompt.strip():
        return GenerateResponse(success=False, error="请输入视频描述")
    
    if req.model not in ["doubao", "jimeng"]:
        return GenerateResponse(success=False, error="不支持的模型类型")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {DOUBAO_API_KEY}",
                "Content-Type": "application/json"
            }
            
            task_id = str(uuid.uuid4())
            
            payload = {
                "request_id": task_id,
                "prompt": req.prompt.strip(),
                "model": "doubao_video" if req.model == "doubao" else "jimeng_video",
                "duration": 5 if req.model == "doubao" else 15,
                "resolution": "720p"
            }
            
            # 提交生成请求
            resp = await client.post(API_GENERATE, json=payload, headers=headers, timeout=10)
            res_data = resp.json()
            
            if resp.status_code != 200:
                return GenerateResponse(success=False, error=f"API错误 {resp.status_code}")
            
            if res_data.get("code") != 0:
                return GenerateResponse(success=False, error=res_data.get("msg", "生成失败"))
            
            api_task_id = res_data["data"]["task_id"]
            
            # 保存任务状态
            _task_status[api_task_id] = {
                "status": "PROCESSING",
                "videoUrl": None,
                "error": None,
                "createdAt": datetime.now().isoformat()
            }
            
            # 立即返回任务ID，不等待完成
            return GenerateResponse(
                success=True,
                taskId=api_task_id,
                status="PROCESSING"
            )
            
    except Exception as e:
        return GenerateResponse(success=False, error=f"系统错误：{str(e)}")

@app.get("/api/task/{task_id}")
async def query_task(task_id: str):
    """查询任务状态"""
    # 先检查内存状态
    if task_id in _task_status:
        task = _task_status[task_id]
        if task["status"] == "SUCCESS":
            return {
                "success": True,
                "data": {
                    "status": "SUCCESS",
                    "video_url": task["videoUrl"]
                }
            }
        elif task["status"] == "FAILED":
            return {
                "success": False,
                "error": task["error"]
            }
    
    # 如果内存中没有或还在处理，查询豆包API
    if not DOUBAO_API_KEY:
        return {"success": 假, "error": "服务未配置API密钥"}
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {DOUBAO_API_KEY}",
                "Content-Type": "application/json"
            }
            
            resp = await client.获取(f"{API_TASK}{任务ID}", headers=headers, timeout=10)
            data = resp.json()
            
            if data.get("code") == 0:
                status = data["data"]["状态"]
                
                # 更新内存状态
                if状态 == "成功":
                    _task_status[任务ID] = {
                        "状态": "成功",
                        "videoUrl": data["data"]["video_url"],
                        "error": 无
                    }
                    return {
                        "success": 真,
                        "data": {
                            "状态": "成功",
                            "video_url": data["data"]["video_url"]
                        }
                    }
                elif状态 == "FAILED":
                    _task_status[任务ID] = {
                        "状态": "失败",
                        "videoUrl": 无,
                        "error": "视频生成失败"
                    }
{"success": 假, 
                否则:
                    return {
                        "success": 真,
                        "data": {
                            "状态": 状态,
                            "video_url": 无
                        }
                    }
            否则:
                return {"success": False, "error": data.get("msg", "查询失败")}
                
    except Exception as e:
        return {"success": False, "error": f"查询异常：{str(e)}"}

@app.get("/api/health")
异步 定义 健康检查():
    返回 {
        "状态": "healthy",
        "api_key_configured": bool(DOUBAO_API_KEY),
        "tasks_in_memory": len(_task_status)
    }
