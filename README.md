# VLA 数据预研与训练数据 Pipeline 设计

面向计划开展工业具身智能研究的实验室，解释 VLA 数据是什么、如何训练模型、哪些公开数据值得使用，以及如何逐步建立可持续接入新数据的处理流水线。机械臂与人形机器人按同等深度讨论。

当前已交付**系统调研、可运行的数据 Pipeline 原型、真实样本工程验收、CPU 训练接口验证及主管汇报包**。机械臂与人形同等展开。训练探针是随机初始化的小型多模态行为克隆网络；完整预训练 VLA 微调、机器人执行和工厂能力仍待后续验证。

## 周一汇报入口

- [主管汇报摘要](docs/06-supervisor-brief.md)：先读这份，掌握结论、成果与需要协调的事项。
- [汇报 PPTX](deliverables/VLA数据预研与管线验证-主管汇报.pptx) / [备用 PDF](deliverables/VLA数据预研与管线验证-主管汇报.pdf)。
- [离线实测报告](deliverables/offline-report.html)：下载后用浏览器打开，内嵌真实样本图片。
- [逐页讲稿](deliverables/speaker-notes.md) / [学习指南与问答](docs/07-presenter-learning-guide.md)。
- [现场演示手册](docs/08-demo-runbook.md) / [工程实现状态](docs/09-implementation-status.md) / [最终验收记录](reports/final-acceptance.md)。
- [Ubuntu、Windows 与内网部署](docs/10-linux-windows-offline-deployment.md) / [公司环境下载计划](docs/11-download-priorities.md)。
- [工厂交流与任务卡](docs/12-factory-intake.md)：带着具体问题与现场共同缩小研究范围。

## 运行原型

Python 3.12，推荐 uv。在仓库根目录执行：

```bash
uv sync --frozen --extra dev
uv run --frozen vla-pipeline run
uv run --frozen python scripts/verify_delivery.py
uv run --frozen --extra dev pytest -q
```

首次约 212 MB 原始样本下载，3 个来源各选 6 条 episode，一路相机。不会下载完整数据集。已缓存后：

```bash
uv run --offline --frozen vla-pipeline run --offline
```

可选 CPU 训练探针（需安装额外 Torch 依赖，Linux 环境安装包可能较大）：

```bash
uv sync --frozen --extra train --extra dev
uv run --frozen --extra train python -m vla_pipeline.training
```

核心 CLI 支持 `--root` 指定数据盘；`register-local` 接入实验室 JSON 和本地视频。数据使用 `raw/{source}/{revision}`、`releases/{id}` 分层，来源锁和输出哈希可追溯。当前实现范围见 [状态清单](docs/09-implementation-status.md)。

## 实测结果

18 条来源轨迹，23,109 个时刻，590 个窗口。按来源独立切分与统计；来源动作维度保持不变。验证了动作窗口不跨轨迹、训练集统计、源时间上的过去帧及语言选择、异常隔离、数值完全重复检测、离线重跑和检查点恢复。

工程检查通过不等于动作语义已完整确认，当前输出视图仅为 `interface_smoke`。[验收原始结果](reports/acceptance.json)、[训练结果](reports/training_probe.json)、[完整实施计划](plans/2026-09-14-delivery.md)。

Ubuntu 24.04 与 Windows 已分别通过 21 项契约／集成测试、CLI 检查与 wheel 构建。[CI 实际运行记录](https://github.com/fengjikui/vla_data_pipeline/actions/runs/34678405092)。这不涵盖 GPU、机器人 SDK 或公司内网。

## 阅读顺序

| 文档 | 解决的问题 |
|---|---|
| [01 · VLA 数据与模型研究报告](docs/01-vla-data-research.md) | 数据分类、模型结构和损失、数据与能力的关系、仿真、遥操作、训练设备、跨硬件适配 |
| [02 · 重点数据集目录](docs/02-dataset-catalog.md) | 国内外厂商与研究机构的开放数据、许可、格式、价值、下载入口和优先级 |
| [03 · Pipeline 设计](docs/03-pipeline-design.md) | 多来源接入、统一语义、质检、分割、防泄漏、训练导出和增量更新 |
| [04 · 真实数据与训练样本拆解](docs/04-data-examples.md) | 实际 Parquet 字段与数值、LeRobot v2/v3、RLDS、如何形成训练 batch |
| [05 · 实验室实施与验证计划](docs/05-lab-roadmap.md) | 机械臂与人形两条试验路线、数据消融、设备决策和商业采购 |
| [来源与证据边界](docs/sources.md) | 一手来源、版本口径、已抽查范围和未解决问题 |

## 先记住这五点

1. **“开源、仿真、遥操作、商业购买”不是四个互斥类别。** 它们分别涉及获取权利、采集环境和控制方式，同一数据集可以同时拥有这些标签。
2. VLA 的关键监督信号是“在某种观测和指令下，机器人应执行什么动作”。视频有帮助，但没有动作的普通视频不能直接当作机器人行为克隆标签。
3. 换 GPU 通常调整训练配置；换机器人需要处理动作定义、坐标系、控制接口、传感器和动力学差异，往往还要目标机器人数据。
4. 开放模型、开放数据、开放采集工具是三件不同的事。公开可下载也不等于可直接用于工厂商业项目。
5. Pipeline 应保留原始数据与物理含义，再按模型生成不同训练视图；不存在一个无需配置、适配所有 VLA 的最终文件格式。

## 配套文件

- [结构化数据集索引](catalog/datasets.json)：可继续扩展，包含来源和适用方向。
- [公开数据版本记录](evidence/dataset-revisions.json)：核查时的 Hugging Face revision、访问条件和字段线索。
- [真实样本抽查结果](evidence/g1-sample-inspection.json)：一个公开 episode 的统计和前两行数值，附来源与文件哈希。
- [抽查复现脚本](scripts/inspect_public_sample.py)：只读取一个固定版本的小型 Parquet 文件，不启动机器人或训练任务。

基础调研核查日期为 **2026-09-11**，工程验证与部署材料更新于 **2026-09-12**。统计规模采用明确标注的版本；厂商自报能力与实验室建议在正文中区分。未下载完整 TB 级数据集，未对所有公开条目做训练复现。
