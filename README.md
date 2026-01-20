# MySQL 考试练习系统 (MySQL Exam Practice System)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)](https://fastapi.tiangolo.com/)

一个基于 FastAPI 和 React 开发的 MySQL 题目练习工具，旨在帮助用户通过随机刷题、错题复习和统计分析来高效准备 MySQL 相关考试。

## 🚀 核心功能

- **🎯 随机练习**：支持按题目类型（单选、多选、填空、判断）和分类进行筛选练习。
- **📝 错题本**：自动记录做错的题目，支持针对性复习和重做。
- **📊 统计分析**：实时记录答题进度、正确率，并按类别统计掌握情况。
- **🛠️ 题目管理**：内置题目管理界面，支持手动添加、修改、删除题目。
- **📥 批量导入**：支持通过 JSON 格式批量导入题库数据。
- **🖥️ 桌面化体验**：支持通过 PyInstaller 打包为独立的可执行文件（.exe），即开即用。

## 🛠️ 技术栈

- **后端**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **前端**: [React](https://react.dev/) + [Vite](https://vitejs.dev/) + [Tailwind CSS](https://tailwindcss.com/)
- **打包**: [PyInstaller](https://pyinstaller.org/)
- **数据存储**: 本地 JSON 文件

## 📦 快速启动

### 生产环境 (使用编译好的 EXE)

1. 下载发布包并解压。
2. 确保 `question_bank` 文件夹与 `MySQL考试练习系统.exe` 处于同一目录下。
3. 双击运行 `MySQL考试练习系统.exe`。
4. 系统会自动在默认浏览器中打开 `http://127.0.0.1:8000`。

### 开发环境

#### 后端
1. 安装依赖：
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. 运行后端服务：
   ```bash
   python main.py
   ```

#### 前端
1. 安装依赖：
   ```bash
   cd frontend
   npm install
   ```
2. 启动开发服务器：
   ```bash
   npm run dev
   ```

## 📂 项目结构

```text
mysql_Learn_exam/
├── backend/            # Python 后端代码 (FastAPI)
├── frontend/           # React 前端代码 (Vite + TS)
├── question_bank/      # 题库数据文件夹
│   └── 题库_整合.json   # 核心题库文件
├── base/               # 原始题目文档 (.docx)
├── extract_docx.py     # 题目提取脚本
└── MySQL考试练习系统.spec # PyInstaller 打包配置文件
```

## ⚠️ 注意事项

- **数据保存**：练习进度和错题记录保存在根目录下的 `user_progress.json` 中，请勿随意删除。
- **端口占用**：程序默认使用 `8000` 端口，请确保该端口未被其他程序占用。

## 📄 开源协议

MIT License
