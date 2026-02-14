# 家庭健康档案管理系统设计文档

本文档描述了家庭健康档案管理系统（Family Health Manager）的整体架构、核心业务流程及数据设计。

## 1. 系统概述

本系统旨在帮助用户数字化管理家庭成员的医疗报告。通过集成 OCR（光学字符识别）和 LLM（大语言模型）技术，系统能够自动从图片或 PDF 格式的医疗报告中提取关键信息（如患者姓名、医院、诊断摘要等），并自动归档到对应的家庭成员名下。

## 2. 系统架构

系统采用前后端分离架构：

*   **前端**: Vue 3 + Element Plus，负责用户交互、文件上传和数据展示。
*   **后端**: FastAPI (Python)，负责业务逻辑、API 接口、文件处理。
*   **AI/OCR 服务**:
    *   **RapidOCR**: 本地运行，用于从图像/PDF 中提取原始文本。
    *   **DeepSeek API**: 云端大模型，用于语义分析和结构化信息提取。
*   **数据库**: SQLite，存储家庭成员和报告的元数据。
*   **文件存储**: 本地文件系统，存储上传的原始报告文件。

## 3. 核心业务流程

### 3.1 医疗报告上传与智能化处理流程

这是系统的核心功能。当用户上传一份医疗报告时，后端会自动执行一系列处理步骤，实现“上传即归档”。

```mermaid
sequenceDiagram
    participant User as 用户
    participant Frontend as 前端 (Vue)
    participant Backend as 后端 (FastAPI)
    participant OCR as RapidOCR (本地)
    participant LLM as DeepSeek API
    participant DB as SQLite 数据库
    participant FS as 文件系统

    User->>Frontend: 拖拽/选择医疗报告文件
    Frontend->>Backend: POST /upload (文件流)
    
    Note over Backend: 1. 文件保存
    Backend->>FS: 保存文件到 /uploads 目录
    
    Note over Backend: 2. 文本识别 (OCR)
    Backend->>OCR: 调用 perform_ocr(文件路径)
    OCR-->>Backend: 返回识别到的原始文本
    
    Note over Backend: 3. 语义分析 (AI)
    alt 配置了 DeepSeek API Key 且 OCR 有结果
        Backend->>LLM: 发送原始文本 + 提取指令 (要求中文摘要)
        LLM-->>Backend: 返回 JSON (姓名, 医院, 日期, 摘要等)
    else 未配置 API Key 或 OCR 失败
        Backend->>Backend: 使用默认值/原始文本截断作为摘要
    end
    
    Note over Backend: 4. 关联家庭成员
    Backend->>DB: 查询是否存在该姓名 (name)
    alt 成员不存在
        Backend->>DB: 创建新成员 (FamilyMember)
    else 成员已存在
        Backend->>DB: 获取现有成员 ID
    end
    
    Note over Backend: 5. 创建报告记录
    Backend->>DB: 创建报告记录 (MedicalReport)
    Backend-->>Frontend: 返回处理结果 (报告详情)
    
    Frontend->>User: 显示上传成功及解析结果
    Frontend->>Backend: 自动刷新列表 (GET /reports, GET /members)
```

### 3.2 流程图视图

```mermaid
flowchart TD
    Start[用户上传文件] --> SaveFile[保存文件到本地]
    SaveFile --> OCR[调用 RapidOCR 识别文本]
    OCR --> CheckConfig{是否配置 DeepSeek API?}
    
    CheckConfig -- 是 --> LLM[调用 DeepSeek API 分析文本]
    LLM --> ExtractInfo["提取结构化数据\n(姓名/医院/日期/摘要)"]
    
    CheckConfig -- 否 --> Fallback[仅使用 OCR 文本摘要]
    Fallback --> ExtractInfo
    
    ExtractInfo --> FindMember{"查找家庭成员\n(按姓名)"}
    
    FindMember -- 不存在 --> CreateMember[自动创建新成员]
    FindMember -- 存在 --> GetMember[获取成员 ID]
    
    CreateMember --> SaveReport[保存报告记录到数据库]
    GetMember --> SaveReport
    
    SaveReport --> End[返回结果给前端]
```

## 4. 数据模型设计

系统主要包含两个核心实体：`FamilyMember`（家庭成员）和 `MedicalReport`（医疗报告），它们之间是一对多的关系。

```mermaid
erDiagram
    FamilyMember ||--o{ MedicalReport : "has"
    
    FamilyMember {
        int id PK
        string name "姓名 (索引)"
        string relation "关系 (如: 父亲, 配偶)"
        string gender "性别"
        date birth_date "出生日期"
        datetime created_at "创建时间"
    }

    MedicalReport {
        int id PK
        int member_id FK "关联 FamilyMember.id"
        string file_path "文件存储路径"
        string hospital_name "医院名称"
        date report_date "报告日期"
        string report_type "报告类型 (如: 验血, CT)"
        text summary "AI 生成的摘要"
        datetime created_at "上传时间"
    }
```

## 5. 接口设计摘要

| 方法 | 路径 | 描述 | 主要参数 |
| :--- | :--- | :--- | :--- |
| `POST` | `/upload` | 上传并分析报告 | `file`: Binary |
| `GET` | `/members` | 获取成员列表 | `skip`, `limit` |
| `GET` | `/reports` | 获取报告列表 | `skip`, `limit` |
| `GET` | `/` | 健康检查 | - |

## 6. 技术栈细节

*   **FastAPI**: 提供高性能的异步 Web 服务。
*   **SQLAlchemy**: ORM 框架，用于数据库操作。
*   **RapidOCR**: 基于 ONNXRuntime 的轻量级 OCR 引擎，无需联网即可运行。
*   **DeepSeek V3 (Chat)**: 通过 Prompt Engineering 指导模型输出严格的 JSON 格式，便于程序解析。
