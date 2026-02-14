"""
数据库模型定义模块
================

本模块定义了应用程序的 SQLAlchemy 数据库模型，映射到数据库表结构。
包括家庭成员 (FamilyMember) 和医疗报告 (MedicalReport) 两个主要实体。

Classes:
    FamilyMember: 家庭成员模型。
    MedicalReport: 医疗报告模型。
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class FamilyMember(Base):
    """
    家庭成员数据库模型。

    表示系统中的一个用户或家庭成员实体。

    Attributes:
        id (int): 主键 ID。
        name (str): 成员姓名，用于关联报告。
        relation (str, optional): 与主用户的关系（如父亲、母亲、本人）。
        gender (str, optional): 性别。
        birth_date (date, optional): 出生日期。
        created_at (datetime): 记录创建时间。
        reports (relationship): 关联的医疗报告列表。
    """
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    relation = Column(String, nullable=True) # e.g., Father, Mother, Self
    gender = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reports = relationship("MedicalReport", back_populates="member")

class MedicalReport(Base):
    """
    医疗报告数据库模型。

    存储上传的医疗报告文件的元数据及分析结果。

    Attributes:
        id (int): 主键 ID。
        member_id (int, optional): 关联的家庭成员 ID。
        file_path (str): 报告文件的存储路径。
        hospital_name (str, optional): 就诊医院名称。
        report_date (date, optional): 报告生成日期。
        report_type (str, optional): 报告类型（如验血报告、CT 扫描）。
        summary (str, optional): 报告内容的文本摘要或关键发现。
        created_at (datetime): 记录创建时间。
        member (relationship): 关联的家庭成员对象。
    """
    __tablename__ = "medical_reports"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("family_members.id"), nullable=True)
    file_path = Column(String, nullable=False)
    hospital_name = Column(String, nullable=True)
    report_date = Column(Date, nullable=True)
    report_type = Column(String, nullable=True) # e.g., Blood Test, CT Scan
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    member = relationship("FamilyMember", back_populates="reports")
