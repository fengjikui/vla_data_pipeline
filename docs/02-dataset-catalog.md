# VLA 重点公开数据集目录

## 1. 如何使用本目录

优先覆盖提供实际机器人数据、模型适配或采集工具的国内外产业团队，再补上不可绕过的研究数据。这里的“高价值”指对实验室工业机械臂和人形研究有明确用途，**不代表已经证明可直接用于生产**。

核查日期为 2026-09-11。表中“公开”包含直接下载和注册同意条款后下载；许可按照来源原文记录。`需确认` 表示尚不能建立清晰的使用权或字段映射，不代表数据不可研究。没有用代码仓库的许可证代替数据许可证。

优先级是建议的接入顺序：**P0** 适合小规模打通；**P1** 适合确定任务和本体后扩大；**P2** 适合专项研究或进一步核验。G1 指宇树平台时会注明“Unitree G1”；智元旧版数据中的 AgiBot G1 是另一款机器人。

## 2. 国内产业团队与机器人平台相关数据

| 数据集／发布主体 | 内容与规模口径 | 格式和入口 | 优先级与主要价值 | 权利与限制 |
|---|---|---|---|---|
| **AgiBot World Alpha / Beta**；智元、OpenDriveLab 合作 | Alpha 92,214 条；Beta 1,003,672 条，Alpha 是 Beta 子集；旧版 AgiBot G1 双臂操作 | 官方仓库链接 HF/OpenDataLab；原始版本需按工具转换为 LeRobot | P1；大规模真实双臂、多任务与接触操作；挑相关任务，不先下全量 | CC BY-NC-SA 4.0；不能默认用于商业训练；触觉／灵巧手覆盖需逐子集查验 [^5] |
| **AgiBot World 2026**；智元 | G2 平台；当前目录含 ImitationLearning、RichInteraction、ReinforcementLearning；不沿用 Beta 百万条口径 | LeRobot v2.1 扩展，任务包内含多层语言与关键帧标注 | P1；长任务、交互与部署经验；优先商业空间和工业相近任务 | CC BY-NC-SA 4.0；目录名为 RL 不保证某配方所需奖励与行为概率字段齐全 [^6] |
| **Galaxea Open-World Dataset**；星海图 OpenGalaxea | 官方卡称 500+ 小时，R1-Lite 统一移动双臂，细粒度中英子任务；当前列 227 个任务包 | LeRobot v2.1，四路视频，关节／末端／躯干／底盘等字段 | P1；移动双臂、长流程与语言层级；双足行走需另配数据 | CC BY-NC-SA 4.0，注册同意后下载 [^8] |
| **RoboMIND 1.x**；北京人形机器人创新中心等 | 初版论文口径 107k 条、479 任务，Franka、UR5e、AgileX、双灵巧手人形等；1.x 更新不能与初版数字混算 | 官方 HF 的 HDF5 打包与说明；版本工具配套 | P1；同一采集体系下比较多本体，单臂和双臂都相关 | 当前 HF 卡 Apache-2.0，gated；固定 1.x 子版本与实际条款 [^9][^49] |
| **RoboMIND 2.0**；北京人形机器人创新中心、北大 | 310k+ 双臂轨迹、739 任务、6 类本体；其中含 12k 触觉增强、20k 移动操作；另有 20k 配对仿真 | 项目页指向官方 ModelScope；仿真按本体分包；需逐包确认解析格式 | P1；机械臂接触与人形／移动双臂同等重要，适合研究真仿混合 | 官方 ModelScope 卡 Apache 2.0；本次未下载完整包验证内容，规模来自作者 [^10][^11] |
| **G1 Dex1 系列**；宇树 | 整理、擦拭、装包、叠毛巾等真实双臂示范；抽查 Clean_Table 为 200 episodes、30 Hz | 官方 HF；抽查 LeRobot v2.1、四路视频、双臂／夹爪／body 字段 | **P0 人形上身**；从一个任务测试读取、回放和动作映射 | 抽查卡 Apache-2.0；各任务单独固定版本；有 body 列不等于所有任务训练腿控 [^14] |
| **UnifoLM WBT 系列**；宇树 | 全身参考及双手操作；抽查 BrainCo 收盘到洗碗机任务为 300 episodes、30 Hz | LeRobot v3；root+关节为 36 维，双手命令为 12 维 | **P0 人形全身格式**；研究根部、手型、目标配置和控制器接口 | 抽查卡 Apache-2.0；BrainCo/Inspire/Dex1 的顺序与开合语义不同 [^15][^16] |
| **RH20T**；上海交大 | 110k+ 真实接触操作序列，视觉、力／力矩、音频、动作及对应人体示范 | 分配置 MP4/NumPy/JSON 与标定文件，官方 API 读取 | P1 机械臂接触；比只看 RGB 抓取更接近插入、按压和工具操作的数据需求 | 公开入口存在；本次未在主页确认统一明确的数据授权，列为需确认；不是全部配置都有指尖触觉 [^24] |

### 2.1 智元：区分旧版大规模数据与 2026 分主题数据

旧版 Alpha/Beta 更适合研究大规模模仿数据的组织与任务覆盖；2026 版的多层标注有助于研究长任务与错误／接管边界。两者本体、发布方式和结构有变化，应建立两个 source adapter 或版本分支。

当前 2026 数据卡提供完整 episode 和按单指令切分的两种使用方式。切分方便训练短技能，但原始长序列和父 episode 必须保存，以便研究阶段切换并防止训练测试串漏。完整数据集名称中带年份，也不表示其每一包都有相同传感器与质量标注。[^6]

### 2.2 星海图：适合移动双臂，不等于足式全身控制

该数据同时包含腰部、底盘和双手信息，适合研究“移动到位后操作”以及多阶段语言监督。其四路相机和底盘 twist 让它很适合检验 Pipeline 是否能保留不同类型动作。与足式人形相比，地面支撑和步态问题不同；不能把轮式底盘速度直接映射成腿部关节角。[^8]

### 2.3 宇树：先区分同厂不同手型和数据格式

Dex1 与 WBT 的 schema 差别比名字暗示的更大：前者抽查是 v2.1，后者为 v3；一个有按左右臂拆开的字段，另一个包含 root+29 关节的当前／目标配置。第一次接入就同时处理这两类，比批量下载十个同格式任务更有助于验证基础设计。

WBT 官方说明的 BrainCo 与 Inspire 都可能是每手 6 个控制数，但手指排列不同；Dex1 开合范围又不同。模型维度相等不能作为可混训的证据。[^15]

## 3. 国外产业与生态团队数据

| 数据集／发布主体 | 内容与规模口径 | 格式和入口 | 优先级与主要价值 | 权利与限制 |
|---|---|---|---|---|
| **PhysicalAI-Robotics-GR00T-Teleop-G1**；NVIDIA GEAR | 官方卡称 1,000 条 Unitree G1 水果拿放；四子集元数据声明合计 **1,095** 条，口径存在差异 | 当前实查为 LeRobot v2.1 Parquet+MP4，43 维状态／动作；一条 Parquet 仅约 66 KB | **P0**；小样本读取和人形上身动作教学入口 | CC BY 4.0；已读取四子集 metadata 和一条数值轨迹，未逐条验收全库；见 [清点记录](../evidence/g1-subset-inventory.json) [^12][^13] |
| **PhysicalAI-Robotics-GR00T-X-Embodiment-Sim**；NVIDIA | 跨本体双臂 9k、上身桌面 240k、其降采样版 24k、单臂 72k、G1 移动操作 102 条，按卡中分组 | LeRobot 风格分任务数据；可选择单一子目录 | **P0**；同时覆盖机械臂与人形；装配、穿线等子集有针对性 | CC BY 4.0；24k downsampled 不可与原版直接算独立新增数据；大部分不是走路数据 [^17] |
| **ABC-130k**；XDOF 与 ABC 合作团队 | 本次固定数据卡口径 130,703 episodes、3,590.7 小时，42,980 条有子任务标注；YAM 双 6-DoF 臂 | 原始 MCAP，视频／状态／标定；独立 annotation.mcap；官方卡连接训练代码 | P1；大规模双臂、原始日志接入与子任务质量；也是商业数据团队的开放样本 | Apache 2.0，原库 gated；作者宣传“最大”不作跨口径排名依据 [^25] |
| **ABC LeRobot v3 smoke**；LeRobot 转换维护 | 抽查 85 episodes、313,094 帧；14 维双臂动作／状态、三路 224×224 视频 | `lerobot/abc_130k_v3_smoke` | **P0 机械臂双臂**；验证 v3 reader；明确是转换子集，不是新的独立语料 | 卡 Apache-2.0；应回溯 XDOF 原库和转换版本 [^50] |
| **1X World Model Challenge 数据**；1X | EVE 的视频 token 与动作；官方 2024 更新还发布 100 小时原始视频与状态序列 | 官方 challenge 仓库和 HF 入口；不同发布阶段格式不同 | P2；研究动作条件世界模型和评估，不是自动可用的工厂 VLA SFT 数据 | 早期 challenge 标 Apache 2.0；不同 raw/token 版本需分别查卡；不等于最新 NEO 全量训练集 [^26][^51] |
| **EgoDex**；Apple | 829 小时第一视角人体桌面操作，配对头／上身／手部 3D 姿态与语言 | 官方下载 ZIP；视频与姿态标注，代码提供可视化 | P2；人类手部先验、工具使用、语义与重定向研究 | 数据 CC BY-NC-ND；代码另有许可；不能当成已含机器人电机命令的轨迹 [^22] |
| **UMI 数据与采集体系**；Stanford/Columbia/TRI 等 | 手持夹爪的真实操作示范，含相机与轨迹重建；按具体任务数据包选择 | 项目页链接代码和数据处理流程 | P1；在现场机器人尚未确定时采集可迁移夹爪操作；单手和双手都有参考 | 具体下载包许可需核对；硬件无关接口不保证任意机械臂可零调整执行 [^23] |

### 3.1 NVIDIA 的 GR1 同名入口有需要隔离的变化

本次核查 `nvidia/PhysicalAI-Robotics-GR00T-Teleop-GR1` 的当前 revision 时，README 内容为 DreamDojo，许可为 CC BY-NC 4.0，文件目录含人类评测和 GR1 数据。它不能继续按历史 Teleop-GR1 的介绍直接归档为一份许可清晰、内容不变的传统遥操作集。

建议状态设为“**待澄清版本与来源**”，分别核对所需子集的原始发布、许可、字段和数据卡历史。本目录优先推荐已验证结构的 Teleop-G1 与 X-Embodiment-Sim。这个异常记录在 [证据边界](sources.md) 和 [版本索引](../evidence/dataset-revisions.json) 中。[^52]

### 3.2 为什么没有把 Figure、PI 的所有训练集列出来

Figure 的 Helix 02 展示全身控制技术，PI 的 openpi 提供模型、训练与适配代码。这些是重要的产业路线来源，但本次检查的页面不足以证明它们将相应内部训练语料完整开放。PI 公开了部分示例数据／微调入口，也不能据此推断其全部预训练数据开放。[^27][^28]

因此目录分开标记“模型可用”“采集工具可用”“训练轨迹可下载”。不把宣传视频、SDK、URDF 或权重文件填进数据集清单，也不以未找到公开下载推断厂商绝对没有开放数据。

## 4. 研究基础数据与仿真数据

| 数据集／框架 | 内容和格式 | 优先级与用途 | 边界与获取方式 |
|---|---|---|---|
| **Open X-Embodiment (OXE)**；DeepMind 与多机构 | 多本体真实数据集合，按 RLDS episode 组织 | P1；跨本体预训练与理解数据混合 | 使用官方数据表逐项选源；集合规模随版本变化，不能对所有来源套一个许可，也不与子数据集重复计数 [^1] |
| **DROID**；DROID 合作团队 | 76k 条、约 350 小时、564 场景；RLDS 与原始视频/HDF5/JSON 两套 | **P0 机械臂**；Franka 多场景操作，适合 openpi/DROID 路线和相机适配 | 官方有约 2 GB 的 100-episode 调试集；CC BY 4.0；任务数项目页 86、早期摘要 84，有版本差别 [^2][^3][^53] |
| **BridgeData V2**；Berkeley 等 | 60,096 条，其中 50,365 遥操作与 9,731 脚本 rollout，24 环境，WidowX | P1；基础操作、目标语言和小型机械臂生态 | CC BY 4.0；原始图片版本与 RLDS/LeRobot 派生版本的相机、裁剪和动作转换要分开 [^4] |
| **RoboTwin 2.0**；RoboTwin 团队 | 双臂模拟任务、强随机化、公开 100k+ 预采轨迹和可自采工具 | **P0 双臂仿真**；调整任务、本体后生成匹配数据 | 当前采集文档支持 HDF5 与 LeRobot 转换等路径；代码、数据、外部物体资产许可分别确认 [^18][^45] |
| **RoboCasa365**；RoboCasa 团队 | 365 任务、2,500+ 厨房场景、2,200+ 小时仿真示范；人遥操作和 MimicGen 生成分开 | P1；长任务、空间泛化、移动操作仿真 | 2026 版提供 LeRobot，代码 MIT、项目声明资产和数据 CC BY 4.0；不是工业工位集 [^19][^54] |
| **LIBERO**；LIBERO 团队 | 语言条件多任务操作与终身学习基准；官方模拟示范和常见派生 RLDS | **P0 软件闭环**；容易比较训练与评测实现 | 不把离线动作 loss 当仿真成功率；使用原始与 modified 数据时固定版本；数据包权利另核对 [^43] |
| **Genie Sim 3.0 数据**；智元 | 官方宣称 10,000+ 小时合成数据，模拟器／资产／数据／基准分模块 | P1/P2；智元 G2 场景与真仿配对路线 | 官网统计为厂商自报；HF 当前入口还含 checkpoints 且 license 元字段缺失，需按数据包和官方协议确认，不能给整库默认授权 [^20][^21] |

### 4.1 第一批实际接入建议

以**控制工作量和覆盖格式**为目标，而不是覆盖最多厂商：

1. 机械臂：DROID 100-episode 调试集；另选 ABC v3 smoke 验证双臂和 v3。
2. 人形：NVIDIA Teleop-G1 单条或单任务；宇树 WBT 一小组完整 episodes 验证全身语义。
3. 仿真：RoboTwin 或 NVIDIA 单一装配／搬运子任务，加一个 LIBERO 训练评测基准。
4. 完成字段、时序、动作和导出验证后，再挑 RoboMIND、智元、星海图中与预定工位最接近的任务。

上面的两类硬件并列推进。DROID 和 G1 的任务本身不必相同，第一阶段要验证各自的数据闭环；之后若研究跨本体能力，再构建相同任务族、不同本体的对照。

### 4.2 数据许可对选择的实际影响

若目标很快进入企业工厂试验，应优先沿“明确允许所需用途的公开数据＋实验室自采”的路线构建可复现基线，限制较多的数据保留在独立研究视图。若要用 NC/ND 数据或传播派生数据、训练权重，则必须落实实际使用权，而不是只在 README 标个来源。

不能从“可商用数据”推导“模型一定可商用”；模型骨干、权重、训练代码和机器人 SDK 可能采用各自条款。也不能把有数据卡但访问门槛未完成的库标记为“已经获取”。本次没有接受需共享联系人信息的门槛，也没有发起商业询价。

## 5. 暂不优先的类别

普通人类活动视频适合视觉语义和阶段理解，但第一版 Pipeline 应先把带机器人动作的数据做好；后续再增加人体动作、伪动作和世界模型分支。医疗机器人数据可能格式成熟，但与工业操作差距大。本次检查的 NVIDIA Open-H-Embodiment 中 H 指 healthcare，不能因名称误归为 humanoid 大规模工厂数据。[^55]

本目录不是所有公开机器人数据的穷举。尚未列入的数据应先按“发布主体可核验、访问入口明确、动作语义完整、任务相关、许可可追溯、提供样本”六项检查，再决定是否扩展。

<!-- source-footnotes -->

## 本文引用

[^1]: Google DeepMind / OXE Collaboration. [Open X-Embodiment repository](https://github.com/google-deepmind/open_x_embodiment). 2023 起，持续更新；访问 2026-09-11。

[^2]: DROID Dataset Team. [DROID project](https://droid-dataset.github.io/). 2024；页面列 2025 更新；访问 2026-09-11。

[^3]: DROID Dataset Team. [The DROID Dataset](https://droid-dataset.github.io/droid/the-droid-dataset). 持续更新，未标明完整发布日期；访问 2026-09-11。

[^4]: Berkeley RAIL 等. [BridgeData V2](https://rail-berkeley.github.io/bridgedata/). 2023；访问 2026-09-11。

[^5]: OpenDriveLab / AgiBot World. [AgiBot World / GO-1 repository](https://github.com/OpenDriveLab/AgiBot-World). 2024–2025 发布，持续更新；访问 2026-09-11。

[^6]: AgiBot World Team. [AgiBot World 2026 dataset card](https://huggingface.co/datasets/agibot-world/AgiBotWorld2026). 2026；核查 revision 见 evidence；访问 2026-09-11。

[^8]: OpenGalaxea. [Galaxea Open-World Dataset card](https://huggingface.co/datasets/OpenGalaxea/Galaxea-Open-World-Dataset). 2025 研究发布；当前卡持续更新；访问 2026-09-11。

[^9]: x-humanoid-robomind. [RoboMIND dataset card](https://huggingface.co/datasets/x-humanoid-robomind/RoboMIND). 2024 起，持续更新；访问 2026-09-11。

[^10]: Beijing Innovation Center of Humanoid Robotics / Peking University. [RoboMIND 2.0 project](https://log2r.github.io/RoboMIND2.0/). 2025-12 论文，持续更新；访问 2026-09-11。

[^11]: X-Humanoid / ModelScope. [RoboMIND2.0 official release](https://www.modelscope.cn/datasets/X-Humanoid/RoboMIND2.0). 2026 发布入口，持续更新；访问 2026-09-11。

[^12]: NVIDIA GEAR. [PhysicalAI-Robotics-GR00T-Teleop-G1 card](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1). 2025-06-01 创建日期（数据卡）；访问 2026-09-11。

[^13]: NVIDIA GEAR. [G1 apple subset info.json](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1/blob/0d7bdd06e67f3ca0868892d0ec8f03bcd3e49e40/g1-pick-apple/meta/info.json). 固定 revision 0d7bdd0，2025-06-11；访问 2026-09-11。

[^14]: Unitree Robotics. [G1_Dex1_Clean_Table card and metadata](https://huggingface.co/datasets/unitreerobotics/G1_Dex1_Clean_Table/tree/80a9d440fbd5366899b5875db5a9db11f1e7857c). 固定 revision 80a9d44，2026-01-29；访问 2026-09-11。

[^15]: Unitree Robotics. [G1 WBT BrainCo dishwasher card](https://huggingface.co/datasets/unitreerobotics/G1_WBT_Brainco_Collect_Plates_Into_Dishwasher/blob/16c01dbfcb2159783ea575acd42d1cec9b69e311/README.md). 固定 revision 16c01db，2026-03-27；访问 2026-09-11。

[^16]: Unitree Robotics. [G1 WBT BrainCo info.json](https://huggingface.co/datasets/unitreerobotics/G1_WBT_Brainco_Collect_Plates_Into_Dishwasher/blob/16c01dbfcb2159783ea575acd42d1cec9b69e311/meta/info.json). 固定 revision 16c01db，2026-03-27；访问 2026-09-11。

[^17]: NVIDIA. [PhysicalAI-Robotics-GR00T-X-Embodiment-Sim](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-X-Embodiment-Sim). 2025 起；核查 revision 2026-03-05；访问 2026-09-11。

[^18]: RoboTwin Team. [RoboTwin 2.0 repository](https://github.com/RoboTwin-Platform/RoboTwin). 2025 论文；持续更新；访问 2026-09-11。

[^19]: RoboCasa Team. [RoboCasa / RoboCasa365 repository](https://github.com/robocasa/robocasa). 365 版发布 2026-02-18；访问 2026-09-11。

[^20]: AGIBOT. [Genie Sim 3.0 introduction](https://www.agibot.com/article/231/detail/29.html). CES 2026；访问 2026-09-11。

[^21]: AgiBot World. [GenieSim3.0-Dataset current files](https://huggingface.co/datasets/agibot-world/GenieSim3.0-Dataset/tree/0369966c70a7fd98dbc3ad767224365e1469691d). 固定 revision 0369966，2026-09-07；访问 2026-09-11。

[^22]: Apple. [EgoDex repository](https://github.com/apple/ml-egodex). 2025；访问 2026-09-11。

[^23]: Stanford / Columbia / Toyota Research Institute. [Universal Manipulation Interface](https://umi-gripper.github.io/). 2024；访问 2026-09-11。

[^24]: Shanghai Jiao Tong University. [RH20T project and data specification](https://rh20t.github.io/). 2023 起，持续更新；访问 2026-09-11。

[^25]: XDOF / ABC collaborators. [ABC-130k pinned dataset card](https://huggingface.co/datasets/XDOF/ABC-130k/blob/75ca0b88bda489f2bd935d72454593ecb90efb52/README.md). 2026；固定 revision 75ca0b8；访问 2026-09-11。

[^26]: 1X Technologies. [1X World Model Challenge repository](https://github.com/1x-technologies/1xgpt). 2024 起，持续更新；访问 2026-09-11。

[^27]: Figure. [Introducing Helix 02: Full-Body Autonomy](https://www.figure.ai/news/helix-02). 2026-01-27；访问 2026-09-11。

[^28]: Physical Intelligence. [openpi repository](https://github.com/Physical-Intelligence/openpi). 2024 起；核查 HEAD 2026-08-24；访问 2026-09-11。

[^43]: Lifelong Robot Learning Team. [LIBERO repository](https://github.com/Lifelong-Robot-Learning/LIBERO). 2023 起，持续更新；访问 2026-09-11。

[^45]: RoboTwin Team. [Collect Data – RoboTwin 2.0](https://robotwin-platform.github.io/doc/usage/collect-data.html). 当前在线文档；访问 2026-09-11。

[^49]: RoboMIND authors. [RoboMIND: Benchmark on Multi-embodiment Intelligence Normative Data](https://arxiv.org/abs/2412.13877). 2024-12；访问 2026-09-11。

[^50]: Hugging Face LeRobot. [ABC v3 smoke metadata](https://huggingface.co/datasets/lerobot/abc_130k_v3_smoke/blob/b342a0ff262195d49bae3eece6e3f40c6e1dbe15/meta/info.json). 固定 revision b342a0f，2026-06-24；访问 2026-09-11。

[^51]: 1X Technologies. [1X World Model: Sampling Challenge Update](https://www.1x.tech/discover/1x-world-model-sampling-challenge). 2024-11-05；访问 2026-09-11。

[^52]: NVIDIA. [Teleop-GR1 current README](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-GR1/blob/9f68429ad12535d30d1aae33b7945c79c830c8c4/README.md). 固定 revision 9f68429，2026-02-14；访问 2026-09-11。

[^53]: Khazatsky et al.. [DROID RSS paper](https://www.jiajunwu.com/papers/droid_rss.pdf). RSS 2024；访问 2026-09-11。

[^54]: RoboCasa Team. [Using RoboCasa Datasets](https://github.com/robocasa/robocasa/blob/main/docs/datasets/using_datasets.md). 2026 当前文档；访问 2026-09-11。

[^55]: NVIDIA / Open-H-Embodiment contributors. [Open-H-Embodiment README](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-Open-H-Embodiment). 2026-02 创建，持续更新；访问 2026-09-11。
