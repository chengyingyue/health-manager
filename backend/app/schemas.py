"""
Pydantic 数据模式模块
=====================

本模块定义了用于 API 请求和响应的数据验证模型 (Pydantic Schemas)。
确保前端与后端之间的数据交互符合预期的结构和类型。

Classes:
    MedicalReportBase: 医疗报告基础模型。
    MedicalReportCreate: 医疗报告创建模型。
    MedicalReport: 医疗报告响应模型。
    FamilyMemberBase: 家庭成员基础模型。
    FamilyMemberCreate: 家庭成员创建模型。
    FamilyMember: 家庭成员响应模型。
"""

from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel

class MedicalReportBase(BaseModel):
    """
    医疗报告基础属性模型。

    Attributes:
        hospital_name (str, optional): 医院名称。
        report_date (date, optional): 报告日期。
        report_type (str, optional): 报告类型。
        summary (str, optional): 报告摘要。
    """
    hospital_name: Optional[str] = None
    report_date: Optional[date] = None
    report_type: Optional[str] = None
    summary: Optional[str] = None

class MedicalReportCreate(MedicalReportBase):
    """
    创建医疗报告时使用的模型。

    Attributes:
        member_id (int, optional): 关联的成员 ID。
        file_path (str): 文件存储路径。
    """
    member_id: Optional[int] = None
    file_path: str

class MedicalReport(MedicalReportBase):
    """
    API 响应中返回的医疗报告模型。

    包含数据库生成的 ID 和创建时间。

    Attributes:
        id (int): 报告 ID。
        member_id (int, optional): 成员 ID。
        file_path (str): 文件路径。
        created_at (datetime): 创建时间。
    """
    id: int
    member_id: Optional[int] = None
    file_path: str
    created_at: datetime

    class Config:
        orm_mode = True

class FamilyMemberBase(BaseModel):
    """
    家庭成员基础属性模型。

    Attributes:
        name (str): 成员姓名。
        relation (str, optional): 关系。
        gender (str, optional): 性别。
        birth_date (date, optional): 出生日期。
    """
    name: str
    relation: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None

class FamilyMemberCreate(FamilyMemberBase):
    """
    创建家庭成员时使用的模型。
    """
    pass

class FamilyMember(FamilyMemberBase):
    """
    API 响应中返回的家庭成员模型。

    包含关联的报告列表。

    Attributes:
        id (int): 成员 ID。
        created_at (datetime): 创建时间。
        reports (List[MedicalReport]): 该成员的所有医疗报告。
    """
    id: int
    created_at: datetime
    reports: List[MedicalReport] = []

    class Config:
        orm_mode = True
