# Meteora Scan

一个用于扫描和分析 Meteora 交易对数据的工具。

## 功能特点

- 实时获取 Meteora 交易对数据
- 支持自定义筛选条件（APR、交易量、流动性等）
- 数据可视化展示
- 支持一键刷新数据

## 环境要求

- Python 3.8 或更高版本
- pip（Python 包管理器）

## 安装步骤

1. **克隆项目**   ```bash
   git clone https://github.com/kagamimoe/meteora_scan.git
   cd meteora_scan   ```

2. **创建虚拟环境**   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate   ```

3. **安装依赖**   ```bash
   pip install -r requirements.txt   ```

## 运行项目

1. **启动服务器**   ```bash
   python app.py   ```

2. **访问应用**
   - 打开浏览器
   - 访问 http://localhost:8000

## 使用说明

1. **设置筛选条件**
   - 最小 APR (%)
   - 最大 APR (%)
   - 最小交易量
   - 最小流动性

2. **刷新数据**
   - 点击"刷新数据"按钮获取最新数据
   - 等待数据加载完成（可能需要几秒钟）

3. **查看结果**
   - 数据将以表格形式展示
   - 可以点击表头进行排序
   - 点击交易对名称可跳转到 Meteora 详情页
   - 点击 Dexscreener 链接可查看更多市场数据

## 常见问题

1. **安装依赖失败**
   - 确保使用的是最新版本的 pip
   - 尝试使用以下命令更新 pip：     ```bash
     python -m pip install --upgrade pip     ```

2. **运行时报错**
   - 确保已激活虚拟环境
   - 确保所有依赖都已正确安装
   - 检查 Python 版本是否满足要求

3. **数据加载缓慢**
   - 这是正常现象，因为需要从多个源获取数据
   - 请耐心等待数据加载完成

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

[MIT License](LICENSE)
