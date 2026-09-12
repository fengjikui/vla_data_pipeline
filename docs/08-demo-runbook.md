# 主管汇报与现场演示手册

## 1. 准备顺序

1. 先读 `docs/06-supervisor-brief.md`，掌握阶段结论和需要主管协调的事项。
2. 再读 `docs/07-presenter-learning-guide.md`，补齐 VLA 相对 LLM 的区别。
3. 使用 `deliverables/` 中的汇报 PPTX 或 PDF，按逐页讲稿练习一遍。
4. 双击 `deliverables/offline-report.html`，确认图片、数据表和实验结果可离线打开。
5. 在演示机器上提前运行本手册命令，不要在会议开始时首次安装依赖或下载样本。

建议主汇报 10～15 分钟，演示 3～5 分钟；技术问答另留时间。PPTX 中包含讲者备注，PDF 用于播放兼容性备用。文字讲稿见 `deliverables/speaker-notes.md`。

## 2. 讲解主线

**开场**：“我们还处在工业具身智能的探索阶段。这次先梳理数据与模型关系，并建立一条可检查的数据处理和训练接口链路，帮助后续确定投入方向。”

**中间**：先解释数据多维分类，再展示三类真实来源的文件和图像。用“未来语言标注”案例解释时序处理价值，展示异常隔离和小模型训练结果。

**收尾**：“下一步需要真实工位和目标控制接口。建议协调现场入口，确定第一项可测任务与资源范围，再完成真实 VLA 微调和闭环评测。”

讲数字时始终说明：18 条原始来源轨迹、23,109 个时刻、590 个窗口。三个量不能相加，窗口不是独立的新示范。三类来源中一个是公开仿真数据，不能称为 18 条真实世界采集轨迹。

## 3. 最可靠的离线演示

先展示 HTML 的真实图片与结果表，随后运行缓存重跑：

```bash
uv run --offline --frozen vla-pipeline run --offline
```

两个 `--offline` 分别限制 uv 的依赖网络和管线下载。应看到 `Reused immutable release: True`，来源轨迹数为 18，训练窗口为 590。新的代码版本会生成新 release，此时首次运行会重新处理已缓存样本。

再展示异常与检查结果：

```bash
uv run --offline --frozen python scripts/verify_delivery.py
```

应看到重复副本数 1、隔离数 3，原始 18 条样本通过当前工程检查。错误时间、NaN、缺少视频是人工构造的测试变体，不是对来源质量的统计。

如时间充裕，运行训练探针：

```bash
uv run --offline --frozen --extra train python -m vla_pipeline.training
```

三组分别输出初始训练误差、结束训练误差和验证误差。只需解释真实数据进入网络、loss 和梯度可计算、检查点可恢复。不要承诺某个具体耗时在不同电脑都相同，不用现场重新下载大模型。

## 4. 第一次在新电脑复现

在仓库根目录，先准备 Python 3.12 和 uv：

```bash
uv sync --frozen --extra dev --extra train
uv run --frozen vla-pipeline run
uv run --frozen python scripts/verify_delivery.py
uv run --frozen --extra train python -m vla_pipeline.training
uv run --frozen --extra dev pytest -q
```

第一轮约 212 MB 数据下载，依赖安装包另计。Linux 的 Torch 包来源可能导致较大 CUDA 依赖，CPU 环境与内网 wheelhouse 的准备见部署手册。

核心 CLI 支持 `--root` 自定义数据目录。当前报告生成脚本默认使用仓库 `data/`，用于制作这份交付的材料；公司生产目录使用 CLI 与训练模块的参数即可，后续可按需要扩展报告参数。

## 5. 公司自采数据接入方式

原型定义 `lab_json_v1`，每次采集是一份 JSON，视频是独立文件。它是本项目的演示接入契约，不是 LeRobot 官方格式。推荐先看 `configs/lab_source_example.json` 与 `configs/lab_episode_example.json`，占位样例不代表真实采集数据。

```text
incoming/
  episode-000.json
  camera.mp4
```

登记时会复制到 `{root}/raw/{source_id}/{revision}/`，生成带 SHA256 的锁文件：

```bash
uv run vla-pipeline register-local --source-dir incoming --descriptor configs/lab_source_example.json --root data --output data/lab.lock.json
uv run vla-pipeline run --lock data/lab.lock.json --root data --offline
```

样例 descriptor 中的 `episode_files`、机器人配置与来源信息必须改成实际内容。原始文件已存在且字节不同会拒绝覆盖，应为修改后的数据登记新 revision。

同契约新批次复用 reader；如果是 ROS/MCAP、RLDS、其他 v3 分片结构或新传感器，先增加针对性 reader 与测试。当前不是任意文件自动识别系统。

## 6. 演示失败时如何处理

| 现象 | 含义 | 处理 |
|---|---|---|
| Offline cache missing | 样本原件未迁移齐全 | 展示已保存的离线报告，会后补齐锁清单文件 |
| Hash mismatch | 缓存与锁定来源不一致 | 保留报错，查版本或文件损坏，不跳过校验 |
| No training episodes | 当前分组没有 train | 检查采集分组与样本规模，不拿验证集算统计 |
| Missing video / stale frame | 媒体缺失或时序不符合视图 | 查看 quality.json，定位来源、episode 和阶段 |
| Code changed during run | 运行时修改了管线代码 | 固定代码后重新运行，避免混合版本发布 |
| 安装失败 / 无网络 | 目标平台环境包未准备完整 | 按内网部署手册准备匹配 OS 的依赖 |

不将失败包装成通过。管线能给出可定位的失败原因也是工程验收的一部分。

## 7. 汇报前最后一次检查

- PPTX 与备用 PDF 能打开，中文正常，页面和讲稿顺序一致。
- HTML 在断网状态打开仍有图片和结果表。
- 仓库与证据文件在本机可访问，已提前完成一次缓存重跑。
- 知道训练探针与真实 VLA 的区别，知道机械臂与人形分别还缺什么。
- 明确本次是阶段交付，下一步需要主管协调哪些事项。

无需为会议携带完整大数据集。项目包默认不含视频原件，公司后续获取计划见 `docs/11-download-priorities.md`。
