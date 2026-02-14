# 家庭健康档案管理系统 (Family Health Manager)

这是一个基于 FastAPI 和 Vue 3 构建的家庭健康档案管理系统，旨在帮助用户数字化管理家庭成员的医疗报告、体检数据和健康趋势。

系统集成了 **DeepSeek API** 和本地 OCR 技术，实现了医疗报告的自动化识别、关键信息提取（如姓名、医院、日期、诊断结果）以及家庭成员的自动关联与创建。

## ✨ 主要功能

*   **智能档案录入**:
    *   支持拖拽上传图片或 PDF 格式的医疗报告。
    *   **DeepSeek 深度集成**: 利用大模型能力自动提取患者姓名、医院、日期、报告类型和摘要。
    *   **自动成员关联**: 自动识别报告中的姓名，如果家庭成员不存在，系统会提示并自动创建新成员档案。
    *   **本地 OCR 兜底**: 在网络不可用或 API 未配置时，自动降级使用本地 RapidOCR 进行基础文本识别。
*   **家庭成员管理**:
    *   管理多位家庭成员（父母、配偶、子女等）的档案。
    *   支持为不同成员建立独立的健康数据视图。
*   **健康趋势可视化**:
    *   自动从报告中提取关键健康指标（需结构化数据支持）。
    *   提供 ECharts 图表展示血压、血糖等指标的历史趋势（开发中）。
*   **报告归档与检索**:
    *   按成员、时间、医院等多维度筛选和查找历史报告。

## 🛠 技术栈

*   **后端**: Python, FastAPI, SQLAlchemy, SQLite
*   **前端**: Vue 3, Element Plus, ECharts (CDN 引入，无需构建)
*   **AI & OCR**:
    *   DeepSeek API (LLM/Vision) - 用于高精度语义提取
    *   RapidOCR / PyMuPDF - 本地 OCR 和 PDF 处理
*   **存储**: 本地文件系统 (uploads/) + SQLite 数据库

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.8+。

### 2. 后端设置

进入 `backend` 目录并安装依赖：

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置 API Key (推荐)

在 `backend` 目录下创建或修改 `config.json` 文件，填入你的 DeepSeek API Key：

```json
{
    "deepseek_api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxx",
    "deepseek_base_url": "https://api.deepseek.com"
}
```

> **注意**: 如果未配置 API Key，系统将仅使用本地 OCR 功能，识别准确率和结构化能力会受限。

### 4. 启动服务

在 `backend` 目录下运行：

```bash
python -m uvicorn app.main:app --reload
```

服务默认运行在 `http://127.0.0.1:8000`。

### 5. 访问前端

打开浏览器访问 `http://127.0.0.1:8000/` 即可使用系统。

## 📂 目录结构

```
health-manager/
├── backend/
│   ├── app/
│   │   ├── main.py        # API 入口与业务逻辑
│   │   ├── models.py      # 数据库模型
│   │   ├── schemas.py     # Pydantic 数据验证
│   │   └── database.py    # 数据库连接
│   ├── uploads/           # 存储上传的医疗报告文件
│   ├── config.json        # 配置文件 (需手动创建)
│   └── requirements.txt   # 项目依赖
├── frontend/
│   └── index.html         # 单页应用入口 (Vue 3 + Element Plus)
└── README.md              # 项目说明文档
```

## 📝 待办事项

- [ ] 完善健康指标的自动提取逻辑 (从文本中解析血压、血糖数值)。
- [ ] 增加更多图表类型。
- [ ] 支持多用户登录与权限隔离 (目前为单机单用户模式演示)。
