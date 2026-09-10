# 来源与证据边界

## 核查范围

本文档、结构化来源索引及各章脚注共同构成证据索引。访问日期为 2026-09-11；网页的更新日期不一定等于论文或数据首次发布日期。引用优先使用官方项目、论文、代码、数据卡和版本固定元数据。

本次实际读取一个固定 G1 数值 episode、四类数据集的示例 metadata 与若干官方 README；未下载全部大型数据集、未解码该 episode 视频、未完成训练复现或机器人部署。商业服务只确认公开提供范围，未询价或验收。

## 已发现的口径差异

| 项目 | 差异 | 本报告处理 |
|---|---|---|
| G1 Teleop | 数据卡写 MP4/HDF5 和 1,000 条；实际为 v2.1 Parquet，四子集 metadata 声明共 1,095 条 | 以固定 revision 元数据和文件抽查确定 reader，不使用卡内存储体积做容量承诺 |
| GR1 Teleop | 当前 README 为 DreamDojo，API/卡许可 CC BY-NC，内容混合 | 待澄清，不延续历史名称推断许可与语料 |
| ABC-130k | 宣传／论文／当前卡规模存在差异 | 使用固定卡 130,703 episodes、3,590.7 小时、42,980 标注；不与转换版相加 |
| DROID | 早期摘要 84 任务，项目页 86；action 注释易误读 | 规模注明版本，动作接入需查 builder/transform；未断言可用 6 关节速度解释 |
| RoboMIND | 1.x、2.0 与仿真子集不同 | 分开记录；12k/20k 专项不与 310k 随意相加 |
| Genie Sim | 厂商合成规模与 HF 混合文件入口口径不同，license 字段缺失 | 不将宣传小时数视作实际下载验收，不推断统一数据许可 |
| OXE | 项目演进、多来源重叠及派生版本 | 不给未锁版本的唯一总量，不默认所有组成数据相同条款 |
| 开放能力 | 模型、SDK、资产与训练集开放范围不同 | 无可核验完整语料入口时不列为已开放训练集 |

## 证据文件

- [数据集版本记录](../evidence/dataset-revisions.json)：HF API 的 revision、访问条件与文件线索。
- [代码版本记录](../evidence/code-revisions.json)：核查时的公开仓库 HEAD；不是本项目训练依赖锁文件。
- [元数据抽查摘要](../evidence/metadata-inspections.json)：只保留事实摘要，不复制整套第三方文档。
- [G1 四子集清点](../evidence/g1-subset-inventory.json)：元数据声明的规模总数，未做完整数据验收。
- [G1 单 episode 抽查](../evidence/g1-sample-inspection.json)：来源、哈希、字段、真实数值；数字和原始内容归 NVIDIA GEAR 数据来源，遵循 CC BY 4.0。

## 一手来源清单

### S01

Google DeepMind / OXE Collaboration. [Open X-Embodiment repository](https://github.com/google-deepmind/open_x_embodiment). 2023 起，持续更新。

用途：RLDS、访问入口、多来源集合。访问：2026-09-11。

### S02

DROID Dataset Team. [DROID project](https://droid-dataset.github.io/). 2024；页面列 2025 更新。

用途：规模、场景、标定与语言更新。访问：2026-09-11。

### S03

DROID Dataset Team. [The DROID Dataset](https://droid-dataset.github.io/droid/the-droid-dataset). 持续更新，未标明完整发布日期。

用途：下载体积、100 episode 调试集、schema 与已知注释疑点。访问：2026-09-11。

### S04

Berkeley RAIL 等. [BridgeData V2](https://rail-berkeley.github.io/bridgedata/). 2023。

用途：示范与脚本轨迹区分、WidowX、CC BY。访问：2026-09-11。

### S05

OpenDriveLab / AgiBot World. [AgiBot World / GO-1 repository](https://github.com/OpenDriveLab/AgiBot-World). 2024–2025 发布，持续更新。

用途：Alpha/Beta 规模、转换流程、NC-SA。访问：2026-09-11。

### S06

AgiBot World Team. [AgiBot World 2026 dataset card](https://huggingface.co/datasets/agibot-world/AgiBotWorld2026). 2026；核查 revision 见 evidence。

用途：G2、扩展标注、访问结构与许可。访问：2026-09-11。

### S07

AGIBOT. [AGIBOT WORLD 2026 Theme 3 announcement](https://www.agibot.com/article/231/detail/95.html). 2026-09-01。

用途：检索摘要可见；正文重取不稳定，主题目录以 HF 文件清单核验。访问：2026-09-11。

### S08

OpenGalaxea. [Galaxea Open-World Dataset card](https://huggingface.co/datasets/OpenGalaxea/Galaxea-Open-World-Dataset). 2025 研究发布；当前卡持续更新。

用途：500+ 小时、R1-Lite、字段、LeRobot v2.1、许可。访问：2026-09-11。

### S09

x-humanoid-robomind. [RoboMIND dataset card](https://huggingface.co/datasets/x-humanoid-robomind/RoboMIND). 2024 起，持续更新。

用途：1.x 数据入口、gated、Apache-2.0。访问：2026-09-11。

### S10

Beijing Innovation Center of Humanoid Robotics / Peking University. [RoboMIND 2.0 project](https://log2r.github.io/RoboMIND2.0/). 2025-12 论文，持续更新。

用途：310k、触觉／移动／仿真子集及本体。访问：2026-09-11。

### S11

X-Humanoid / ModelScope. [RoboMIND2.0 official release](https://www.modelscope.cn/datasets/X-Humanoid/RoboMIND2.0). 2026 发布入口，持续更新。

用途：官方下载与 Apache 2.0 标示；未下载完整包。访问：2026-09-11。

### S12

NVIDIA GEAR. [PhysicalAI-Robotics-GR00T-Teleop-G1 card](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1). 2025-06-01 创建日期（数据卡）。

用途：上身水果拿放、数据卡规模与格式、CC BY。访问：2026-09-11。

### S13

NVIDIA GEAR. [G1 apple subset info.json](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1/blob/0d7bdd06e67f3ca0868892d0ec8f03bcd3e49e40/g1-pick-apple/meta/info.json). 固定 revision 0d7bdd0，2025-06-11。

用途：实际读取：20 Hz、43 维、311 episodes、v2.1。访问：2026-09-11。

### S14

Unitree Robotics. [G1_Dex1_Clean_Table card and metadata](https://huggingface.co/datasets/unitreerobotics/G1_Dex1_Clean_Table/tree/80a9d440fbd5366899b5875db5a9db11f1e7857c). 固定 revision 80a9d44，2026-01-29。

用途：200 episodes、v2.1、四相机和动作分组。访问：2026-09-11。

### S15

Unitree Robotics. [G1 WBT BrainCo dishwasher card](https://huggingface.co/datasets/unitreerobotics/G1_WBT_Brainco_Collect_Plates_Into_Dishwasher/blob/16c01dbfcb2159783ea575acd42d1cec9b69e311/README.md). 固定 revision 16c01db，2026-03-27。

用途：root 和关节、手型顺序与开合语义。访问：2026-09-11。

### S16

Unitree Robotics. [G1 WBT BrainCo info.json](https://huggingface.co/datasets/unitreerobotics/G1_WBT_Brainco_Collect_Plates_Into_Dishwasher/blob/16c01dbfcb2159783ea575acd42d1cec9b69e311/meta/info.json). 固定 revision 16c01db，2026-03-27。

用途：实际读取：300 episodes、30 Hz、v3、各字段维度。访问：2026-09-11。

### S17

NVIDIA. [PhysicalAI-Robotics-GR00T-X-Embodiment-Sim](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-X-Embodiment-Sim). 2025 起；核查 revision 2026-03-05。

用途：分组轨迹规模、G1 loco-manipulation、许可。访问：2026-09-11。

### S18

RoboTwin Team. [RoboTwin 2.0 repository](https://github.com/RoboTwin-Platform/RoboTwin). 2025 论文；持续更新。

用途：预采轨迹、任务生成、文档入口。访问：2026-09-11。

### S19

RoboCasa Team. [RoboCasa / RoboCasa365 repository](https://github.com/robocasa/robocasa). 365 版发布 2026-02-18。

用途：场景规模、示范、代码与数据许可。访问：2026-09-11。

### S20

AGIBOT. [Genie Sim 3.0 introduction](https://www.agibot.com/article/231/detail/29.html). CES 2026。

用途：厂商自报合成规模；不是独立验收结果。访问：2026-09-11。

### S21

AgiBot World. [GenieSim3.0-Dataset current files](https://huggingface.co/datasets/agibot-world/GenieSim3.0-Dataset/tree/0369966c70a7fd98dbc3ad767224365e1469691d). 固定 revision 0369966，2026-09-07。

用途：实际清单含 checkpoints；API license 缺失。访问：2026-09-11。

### S22

Apple. [EgoDex repository](https://github.com/apple/ml-egodex). 2025。

用途：人类视频与姿态、829 小时、CC BY-NC-ND。访问：2026-09-11。

### S23

Stanford / Columbia / Toyota Research Institute. [Universal Manipulation Interface](https://umi-gripper.github.io/). 2024。

用途：手持采集、相对轨迹、时延与迁移。访问：2026-09-11。

### S24

Shanghai Jiao Tong University. [RH20T project and data specification](https://rh20t.github.io/). 2023 起，持续更新。

用途：接触多模态、格式、触觉覆盖与下载。访问：2026-09-11。

### S25

XDOF / ABC collaborators. [ABC-130k pinned dataset card](https://huggingface.co/datasets/XDOF/ABC-130k/blob/75ca0b88bda489f2bd935d72454593ecb90efb52/README.md). 2026；固定 revision 75ca0b8。

用途：当前精确规模、MCAP、标注与 Apache 2.0。访问：2026-09-11。

### S26

1X Technologies. [1X World Model Challenge repository](https://github.com/1x-technologies/1xgpt). 2024 起，持续更新。

用途：EVE、视频 token 与 action、官方 HF 链接。访问：2026-09-11。

### S27

Figure. [Introducing Helix 02: Full-Body Autonomy](https://www.figure.ai/news/helix-02). 2026-01-27。

用途：厂商全身技术描述；不是公开训练集证据。访问：2026-09-11。

### S28

Physical Intelligence. [openpi repository](https://github.com/Physical-Intelligence/openpi). 2024 起；核查 HEAD 2026-08-24。

用途：模型种类、数据适配、推理／微调资源与发布边界。访问：2026-09-11。

### S29

OpenVLA Team. [OpenVLA repository and project](https://github.com/openvla/openvla). 2024 起，持续更新。

用途：原版动作 token、LoRA 显存；项目入口可追溯。访问：2026-09-11。

### S30

OpenVLA-OFT Team. [OpenVLA-OFT repository](https://github.com/moojink/openvla-oft). 2025 起，持续更新。

用途：连续动作和动作块配方差异。访问：2026-09-11。

### S31

NVIDIA. [GR00T N1.7 Hardware Recommendations](https://github.com/NVIDIA/Isaac-GR00T/blob/main/getting_started/hardware_recommendation.md). 核查 HEAD 2026-08-20。

用途：显存、解冻范围、推理率与执行率。访问：2026-09-11。

### S32

NVIDIA. [GR00T Fine-tune on Custom Embodiments](https://github.com/NVIDIA/Isaac-GR00T/blob/main/getting_started/finetune_new_embodiment.md). 核查 HEAD 2026-08-20。

用途：LeRobot v2、模态与动作配置。访问：2026-09-11。

### S33

NVIDIA GR00T-WholeBodyControl. [Data Collection for VLA](https://nvlabs.github.io/GR00T-WholeBodyControl/tutorials/data_collection.html). 持续更新。

用途：全身采集、robot/SMPL/camera 输入。访问：2026-09-11。

### S34

Hugging Face LeRobot. [LeRobotDataset v3.0](https://huggingface.co/docs/lerobot/lerobot-dataset-v3). v3 文档，持续更新。

用途：文件布局、episode 元数据、v2/v3 差异。访问：2026-09-11。

### S35

Google Research. [RLDS specification](https://github.com/google-research/rlds). 2021 起；仓库 2025-11-29 archived。

用途：episode、step、末步与终止约定。访问：2026-09-11。

### S36

robomimic Team. [robomimic Dataset Overview](https://robomimic.github.io/docs/datasets/overview.html). 0.5 文档。

用途：HDF5 容器内的逻辑结构。访问：2026-09-11。

### S37

Isaac Lab Team. [Synthetic Data Generation and Imitation Learning with Isaac Lab Mimic](https://isaac-sim.github.io/IsaacLab/develop/source/overview/imitation-learning/teleop_imitation.html). develop 文档，核查 2026-09-11。

用途：种子示范、子任务与轨迹扩展。访问：2026-09-11。

### S38

Unitree Robotics. [xr_teleoperate repository](https://github.com/unitreerobotics/xr_teleoperate). v1.6 2026-07-29，持续更新。

用途：XR 遥操作和记录工具。访问：2026-09-11。

### S39

Zhao et al., ALOHA / ACT. [Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware](https://tonyzhaozh.github.io/aloha/aloha.pdf). RSS 2023。

用途：主从命令、状态、动作块与模仿。访问：2026-09-11。

### S40

Chi et al.. [Diffusion Policy](https://diffusion-policy.cs.columbia.edu/). 2023。

用途：条件动作生成与滚动执行。访问：2026-09-11。

### S41

Physical Intelligence. [Our First Generalist Policy (pi0)](https://www.pi.website/blog/pi0). 2024。

用途：VLA 与 flow-based 动作模型。访问：2026-09-11。

### S42

Physical Intelligence. [pi-star-0.6: a VLA That Learns From Experience](https://www.physicalintelligence.company/download/pistar06.pdf). 2025。

用途：RECAP、自主数据、干预与价值条件。访问：2026-09-11。

### S43

Lifelong Robot Learning Team. [LIBERO repository](https://github.com/Lifelong-Robot-Learning/LIBERO). 2023 起，持续更新。

用途：基准、数据与评测环境。访问：2026-09-11。

### S44

DROID Dataset Team. [DROID Robot Platform](https://github.com/droid-dataset/droid). 2024 起，持续更新。

用途：真实遥操作与采集硬件工具。访问：2026-09-11。

### S45

RoboTwin Team. [Collect Data – RoboTwin 2.0](https://robotwin-platform.github.io/doc/usage/collect-data.html). 当前在线文档。

用途：数据格式路径、生成流程、GPU 兼容提醒。访问：2026-09-11。

### S46

Scale AI. [Physical AI Data Engine](https://scale.com/physical-ai). 服务页未标发布日期。

用途：采集与标注服务范围，供应商自报。访问：2026-09-11。

### S47

数据堂. [具身智能数据解决方案](https://www.datatang.com/embodied-ai-solutions). 服务页未标发布日期。

用途：定制采集／多模态服务，供应商自报。访问：2026-09-11。

### S48

XDOF. [About XDOF](https://www.xdof.ai/about). 页面未标发布日期。

用途：规模化数据与基础设施服务。访问：2026-09-11。

### S49

RoboMIND authors. [RoboMIND: Benchmark on Multi-embodiment Intelligence Normative Data](https://arxiv.org/abs/2412.13877). 2024-12。

用途：初版 107k/479 与四本体，不混入 2.0。访问：2026-09-11。

### S50

Hugging Face LeRobot. [ABC v3 smoke metadata](https://huggingface.co/datasets/lerobot/abc_130k_v3_smoke/blob/b342a0ff262195d49bae3eece6e3f40c6e1dbe15/meta/info.json). 固定 revision b342a0f，2026-06-24。

用途：实际读取：85 episodes、14 维、v3。访问：2026-09-11。

### S51

1X Technologies. [1X World Model: Sampling Challenge Update](https://www.1x.tech/discover/1x-world-model-sampling-challenge). 2024-11-05。

用途：原始视频和状态更新，区别早期 token 发布。访问：2026-09-11。

### S52

NVIDIA. [Teleop-GR1 current README](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-GR1/blob/9f68429ad12535d30d1aae33b7945c79c830c8c4/README.md). 固定 revision 9f68429，2026-02-14。

用途：当前内容 DreamDojo 与 CC BY-NC；作为版本异常证据。访问：2026-09-11。

### S53

Khazatsky et al.. [DROID RSS paper](https://www.jiajunwu.com/papers/droid_rss.pdf). RSS 2024。

用途：数据集与 CC BY 4.0 声明。访问：2026-09-11。

### S54

RoboCasa Team. [Using RoboCasa Datasets](https://github.com/robocasa/robocasa/blob/main/docs/datasets/using_datasets.md). 2026 当前文档。

用途：LeRobot 下载和 human/MimicGen 划分。访问：2026-09-11。

### S55

NVIDIA / Open-H-Embodiment contributors. [Open-H-Embodiment README](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-Open-H-Embodiment). 2026-02 创建，持续更新。

用途：H 为 healthcare，与工业人形不同。访问：2026-09-11。

### S56

NVIDIA GEAR. [G1 apple task lookup](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1/blob/0d7bdd06e67f3ca0868892d0ec8f03bcd3e49e40/g1-pick-apple/meta/tasks.jsonl). 固定 revision 0d7bdd0，2025-06-11。

用途：实际读取 task_index=1 的语言。访问：2026-09-11。

### S57

OpenVLA Team. [OpenVLA project page](https://openvla.github.io/). 2024。

用途：架构与 64 A100 / 15 天的历史预训练规模。访问：2026-09-11。
