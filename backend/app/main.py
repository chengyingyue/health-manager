"""
家庭健康档案管理系统后端 API
==========================

本模块实现了基于 FastAPI 的后端服务，提供文件上传、OCR 识别、
DeepSeek API 集成以及家庭成员和医疗报告的管理功能。

Routes:
    /upload (POST): 上传医疗报告并自动处理。
    /members (GET): 获取家庭成员列表。
    /reports (GET): 获取医疗报告列表。
    / (GET): API 根路径。
"""

import os
import json
import shutil
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import desc
import requests

from . import models, schemas, database
from .database import engine, get_db

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Family Health Manager")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploads
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Config
CONFIG_PATH = "config.json"
DEEPSEEK_API_KEY = None
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            DEEPSEEK_API_KEY = config.get("deepseek_api_key")
            DEEPSEEK_BASE_URL = config.get("deepseek_base_url", DEEPSEEK_BASE_URL)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")

# OCR
ocr_engine = None
try:
    from rapidocr_onnxruntime import RapidOCR
    ocr_engine = RapidOCR()
except ImportError:
    logger.warning("RapidOCR not installed or failed to import.")
except Exception as e:
    logger.warning(f"RapidOCR initialization failed: {e}")

# --- Logic ---

def perform_ocr(file_path: str) -> str:
    """
    使用 RapidOCR 对上传的文件进行本地文本识别。

    Args:
        file_path (str): 待识别文件的本地路径。

    Returns:
        str: 识别出的所有文本内容，以换行符分隔。
             如果 OCR 引擎未初始化或识别失败，返回空字符串。
    """
    if not ocr_engine:
        return ""
    try:
        result, _ = ocr_engine(file_path)
        if result:
            text = "\n".join([line[1] for line in result])
            return text
        return ""
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""

def analyze_with_deepseek(text: str) -> dict:
    """
    调用 DeepSeek API 分析医疗报告文本并提取关键信息。

    Args:
        text (str): OCR 提取的原始文本。

    Returns:
        dict: 包含提取信息的字典（姓名、医院、日期、类型、摘要）。
              如果 API Key 未配置或调用失败，返回空字典。
    """
    if not DEEPSEEK_API_KEY:
        return {}
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""
    Please extract the following information from the medical report text below:
    - Patient Name (name)
    - Hospital Name (hospital_name)
    - Report Date (report_date, YYYY-MM-DD format)
    - Report Type (report_type, e.g., Blood Test, CT Scan)
    - Summary (summary, brief description of findings in Chinese)

    Return the result as a valid JSON object only, without any markdown formatting.

    Text:
    {text}
    """
    
    data = {
        "model": "deepseek-chat", 
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(f"{DEEPSEEK_BASE_URL}/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        else:
            logger.error(f"DeepSeek API error: {response.text}")
            return {}
    except Exception as e:
        logger.error(f"DeepSeek request failed: {e}")
        return {}

# --- Routes ---

@app.post("/upload", response_model=schemas.MedicalReport)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传医疗报告文件。

    该接口执行以下步骤：
    1. 保存上传的文件到本地。
    2. 使用 OCR 识别文件中的文本。
    3. 调用 DeepSeek API 提取结构化信息（姓名、医院等）。
    4. 自动创建或查找对应的家庭成员。
    5. 保存医疗报告记录到数据库。

    Args:
        file (UploadFile): 上传的文件对象。
        db (Session): 数据库会话。

    Returns:
        MedicalReport: 创建的医疗报告对象。
    """
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 1. OCR
    extracted_text = perform_ocr(file_location)
    
    # 2. Extract Info
    info = {}
    if DEEPSEEK_API_KEY and extracted_text:
        info = analyze_with_deepseek(extracted_text)
    
    # 3. Process extracted info
    patient_name = info.get("name") or "Unknown Member"
    hospital_name = info.get("hospital_name")
    report_date_str = info.get("report_date")
    report_type = info.get("report_type")
    summary = info.get("summary") 
    
    if not summary:
        summary = extracted_text[:200] + "..." if extracted_text else "No text extracted."

    report_date = None
    if report_date_str:
        try:
            report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
        except:
            pass
    
    # 4. Find or Create Family Member
    member = db.query(models.FamilyMember).filter(models.FamilyMember.name == patient_name).first()
    if not member:
        member = models.FamilyMember(name=patient_name)
        db.add(member)
        db.commit()
        db.refresh(member)
    
    # 5. Create Report
    report = models.MedicalReport(
        member_id=member.id,
        file_path=file_location,
        hospital_name=hospital_name,
        report_date=report_date,
        report_type=report_type,
        summary=summary
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return report

@app.get("/members", response_model=List[schemas.FamilyMember])
def read_members(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取家庭成员列表。

    Args:
        skip (int, optional): 跳过的记录数，默认为 0。
        limit (int, optional): 返回的最大记录数，默认为 100。
        db (Session): 数据库会话。

    Returns:
        List[FamilyMember]: 家庭成员列表。
    """
    members = db.query(models.FamilyMember).offset(skip).limit(limit).all()
    return members

@app.get("/reports", response_model=List[schemas.MedicalReport])
def read_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取医疗报告列表。

    报告按创建时间倒序排列。

    Args:
        skip (int, optional): 跳过的记录数，默认为 0。
        limit (int, optional): 返回的最大记录数，默认为 100。
        db (Session): 数据库会话。

    Returns:
        List[MedicalReport]: 医疗报告列表。
    """
    reports = db.query(models.MedicalReport).order_by(desc(models.MedicalReport.created_at)).offset(skip).limit(limit).all()
    return reports

@app.delete("/members/{member_id}", status_code=204)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    """
    删除家庭成员及其关联的所有医疗报告。

    Args:
        member_id (int): 家庭成员 ID。
        db (Session): 数据库会话。
    """
    member = db.query(models.FamilyMember).filter(models.FamilyMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # 由于我们在 models.py 中配置了 cascade="all, delete-orphan"
    # 删除 member 时，关联的 reports 会自动从数据库中删除。
    # 但是，我们也需要删除对应的物理文件。
    for report in member.reports:
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
            except Exception as e:
                logger.error(f"Failed to delete file {report.file_path}: {e}")

    db.delete(member)
    db.commit()
    return None

@app.delete("/reports/{report_id}", status_code=204)
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """
    删除单个医疗报告。

    Args:
        report_id (int): 医疗报告 ID。
        db (Session): 数据库会话。
    """
    report = db.query(models.MedicalReport).filter(models.MedicalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # 删除物理文件
    if report.file_path and os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except Exception as e:
            logger.error(f"Failed to delete file {report.file_path}: {e}")

    db.delete(report)
    db.commit()
    return None

@app.get("/", response_class=HTMLResponse)
def read_root():
    """
    返回前端主页。
    """
    try:
        # 假设前端文件在 backend 目录的同级 frontend 目录下
        with open("../frontend/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Frontend file not found</h1>"
