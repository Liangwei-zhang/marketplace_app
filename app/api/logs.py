import os
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
from typing import Optional

logger = APIRouter(prefix="/logs", tags=["logs"])

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


@logger.get("/")
async def get_logs(
    lines: int = 100,
    level: Optional[str] = None
):
    """获取最近日志"""
    log_file = os.path.join(LOG_DIR, "app.log")
    
    if not os.path.exists(log_file):
        return {"logs": [], "message": "No logs yet"}
    
    with open(log_file, 'r') as f:
        all_lines = f.readlines()
    
    # Filter by level if specified
    if level:
        all_lines = [l for l in all_lines if level.upper() in l]
    
    # Get last N lines
    logs = all_lines[-lines:]
    
    return {
        "logs": logs,
        "count": len(logs),
        "level_filter": level
    }


@logger.get("/errors")
async def get_errors(
    hours: int = 24
):
    """获取最近错误日志"""
    error_file = os.path.join(LOG_DIR, "error.log")
    
    if not os.path.exists(error_file):
        return {"errors": [], "message": "No errors yet"}
    
    with open(error_file, 'r') as f:
        all_lines = f.readlines()
    
    # Get last N lines
    errors = all_lines[-500:]
    
    return {
        "errors": errors,
        "count": len(errors),
        "time_hours": hours
    }


@logger.get("/download/{filename}")
async def download_log(filename: str):
    """下载日志文件"""
    allowed_files = ["app.log", "error.log"]
    
    if filename not in allowed_files:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    log_file = os.path.join(LOG_DIR, filename)
    
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="Log file not found")
    
    return FileResponse(
        log_file,
        media_type="text/plain",
        filename=f"marketplace_{filename}"
    )


@logger.get("/stats")
async def get_log_stats():
    """获取日志统计"""
    stats = {}
    
    for log_type in ["app.log", "error.log"]:
        log_file = os.path.join(LOG_DIR, log_type)
        if os.path.exists(log_file):
            stat = os.stat(log_file)
            stats[log_type] = {
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        else:
            stats[log_type] = {"size_bytes": 0, "size_mb": 0, "modified": None}
    
    return stats
