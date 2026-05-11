# 🧬 问年 (WenNian) — 衰老干预决策系统

**AI探索 + 因果评估 + 实验验证**

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-GPLv3-green.svg)
![Status](https://img.shields.io/badge/status-MVP%20Active-brightgreen)

> 问年不是一个衰老检测工具。它是基于多维度衰老评估与因果推理的衰老干预决策引擎。  
> 本次开源的 **MVP 版本** 聚焦三大核心功能：**衰老全谱评估、健康访谈、白标报告生成**。

---

## 📊 已开放功能

### 🧬 衰老全谱评估
- 基于 9 项基础血检指标（白蛋白、肌酐、血糖、CRP 等），运行 **PhenoAge、KDM、DNN、LifeClock** 四大经典时钟。
- 结合 **器官时钟系统**（心、肝、肾、脑、肺、血管、免疫、骨骼肌）评估器官衰老异步性。
- 输出**主驱动维度**识别与干预优先级建议。
- 所有预测附带置信区间，并强制自动稽核（Auditor）确保合规。

### 💬 健康访谈
- 基于 Google 2026 年 AI 临床研究（主动追问可提升诊断准确率 27%），实现**结构化健康追问**。
- 用户以自然语言描述身体感受，智能体进行最多 3 轮追问，将模糊主诉转化为具体评估维度。
- 内置 **症状-衰老维度映射库**（100+ 常见主诉），确保追问科学有效。
- 访谈结果直接联动衰老全谱评估。

### 📋 白标报告生成
- 支持体检中心/长寿诊所**自定义品牌**（Logo、名称、主题色）。
- 一键生成带 **器官雷达图、生物年龄总结、干预建议、免责声明** 的 PDF 报告。
- 支持批量生成（上传 CSV）并打包 ZIP 下载。

---

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Windows/Linux/macOS

### 安装
```bash
git clone https://github.com/huangdi97/WenNian.git
cd WenNian
pip install -r requirements.txt

### 运行测试
bash
pytest tests/ -v

启动界面
bash
python src/ui/app.py

浏览器访问 http://127.0.0.1:7860 即可使用。

🧱 项目结构（已开源部分）
text
wennian/
├── src/
│   ├── core/           # 配置、日志、异常
│   ├── clocks/         # 衰老时钟（PhenoAge, KDM, DNN, LifeClock）
│   ├── dimensions/     # 器官时钟
│   ├── integrator/     # 评估融合与主驱动识别
│   ├── causality/      # 因果图（部分开放）
│   ├── agents/         # 智能体（Analyst, Auditor, HealthInterviewer 等）
│   ├── knowledge/      # 症状-衰老映射
│   ├── inputs/         # 数据模型与校验
│   ├── outputs/        # 报告构建与 PDF 生成
│   ├── validation/     # 输入校验、红线扫描、数值守护
│   ├── commercial/     # 白标报告模块
│   ├── api/            # FastAPI 接口
│   └── ui/             # Gradio 界面
├── tests/              # 单元测试与集成测试
├── config/             # YAML 配置文件
├── requirements.txt
└── README.md
🛡️ 安全与合规
内置 Auditor 稽核师 对所有输出进行红线扫描（禁止医疗建议、处方等）。

所有 PDF 报告每页附有免责声明：“本报告仅为健康趋势参考，不构成医疗诊断”。

支持本地隐私模式，数据不离开用户设备。

遵循 GPLv3 协议，鼓励学术研究与二次开发。

📄 许可证
本项目采用 GNU General Public License v3.0 (GPLv3)。
这意味着你可以自由使用、修改和分发代码，但任何衍生作品也必须以相同的许可证开源。

🤝 贡献与反馈
当前版本为 MVP，我们欢迎任何形式的反馈、Issue 和 Pull Request。



作者 GitHub: @huangdi97

电子邮箱: 304418554@qq.com

项目仓库: https://github.com/huangdi97/WenNian

“太一既立，灵境已启，虚明初照，静候万物生。”


