# 公司环境数据获取清单

本机只保留已用于验证的约 **212 MB** 原始小样本，不再扩大外网电脑下载。下面是后续公司环境的获取顺序，不是全部下载指令。机器可读版本为 `catalog/download_plan.json`。

建议先用 3 个已锁定样本复现链路，然后按目标任务选择第一批候选。优先级针对本实验室起步，不代表厂商质量排名。研究目录的 P0/P1 与本清单的下载批次用途不同。

## 已验证的最小复现包

`configs/demo_sources.lock.json` 记录具体文件、固定 revision、字节数和 SHA256。3 个来源各选前 6 条完整 episode，只有 1 路相机。ABC v3 的共享 Parquet 和视频文件含额外未选中数据，因此原始下载字节大于所选轨迹净体积。

## 按批次获取

### 已做小样本验证

| 数据 | 建议先取什么 | 价值与接口范围 | 获取与许可 |
|---|---|---|---|
| [PhysicalAI-Robotics-GR00T-Teleop-G1](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1) | 本机已固定 6 条 episode、一路相机；迁移清单即可，不再扩量 | 小样本验证与人形上身；actual LeRobot v2.1; card says HDF5 | public_download；CC-BY-4.0 |
| [PhysicalAI-Robotics-GR00T-X-Embodiment-Sim](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-X-Embodiment-Sim) | 本机已固定 6 条 episode、一路相机；迁移清单即可，不再扩量 | 装配与多本体模拟闭环；LeRobot task folders | public_download；CC-BY-4.0 |
| [ABC LeRobot v3 smoke](https://huggingface.co/datasets/lerobot/abc_130k_v3_smoke/blob/b342a0ff262195d49bae3eece6e3f40c6e1dbe15/meta/info.json) | 本机已固定 6 条 episode、一路相机；迁移清单即可，不再扩量 | v3 reader smoke validation；LeRobot v3.0 | public_download；Apache-2.0 (card; retain upstream attribution) |

### 第一批候选

| 数据 | 建议先取什么 | 价值与接口范围 | 获取与许可 |
|---|---|---|---|
| [Unitree G1 Dex1 task series](https://huggingface.co/datasets/unitreerobotics/G1_Dex1_Clean_Table/tree/80a9d440fbd5366899b5875db5a9db11f1e7857c) | 先选一个整理任务，取元数据与 10 条完整 episode | 上身动作读取与复现；LeRobot v2.1 in checked task | public_download；Apache-2.0 (checked task) |
| [Unitree UnifoLM WBT](https://huggingface.co/datasets/unitreerobotics/G1_WBT_Brainco_Collect_Plates_Into_Dishwasher/blob/16c01dbfcb2159783ea575acd42d1cec9b69e311/README.md) | 一个明确手型与全身控制配置，先取元数据和 10 条完整 episode | 全身参考、手型与根部语义；LeRobot v3.0 | public_download；Apache-2.0 (checked task) |
| [DROID](https://droid-dataset.github.io/) | 官方小样包／100-episode 路线先验证，再选任务子集；暂不取全量视频 | Franka 多场景与 openpi 适配；RLDS; raw MP4 + HDF5 + JSON | public_download；CC-BY-4.0 |
| [BridgeData V2](https://rail-berkeley.github.io/bridgedata/) | 固定机器人配置与单个操作族，先取 10～20 条完整示范 | 基础操作和语言条件；raw JPEG/trajectory; RLDS/LeRobot derivatives | public_download；CC-BY-4.0 |
| [RoboTwin 2.0](https://github.com/RoboTwin-Platform/RoboTwin) | 选择一个双臂操作任务，先取环境与少量成功示范 | 双臂随机化与目标本体生成；HDF5 / current XPolicyLab / LeRobot conversion | public_download_and_generator；code/data/assets must be checked separately |
| [LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) | 固定一个任务集与官方划分，先完成加载和一次评测回放 | 训练与闭环评测起点；simulation demos; modified RLDS derivatives | public_download；verify data package; code license not substituted |

### 按场景选择

| 数据 | 建议先取什么 | 价值与接口范围 | 获取与许可 |
|---|---|---|---|
| [AgiBot World Alpha / Beta](https://github.com/OpenDriveLab/AgiBot-World) | 按任务与本体选择；Alpha 是 Beta 子集，避免重复 | 大规模真实多任务双臂；raw release + LeRobot conversion | public_download；CC-BY-NC-SA-4.0 |
| [AgiBot World 2026](https://huggingface.co/datasets/agibot-world/AgiBotWorld2026) | 先取与候选工位相关的单个 task archive | 长任务、多层标注、交互与接管；extended LeRobot v2.1 archives | public_download；CC-BY-NC-SA-4.0 |
| [Galaxea Open-World Dataset](https://huggingface.co/datasets/OpenGalaxea/Galaxea-Open-World-Dataset) | 单个轮式双臂任务 archive；先核验许可与 gated 条件 | 移动双臂、多层语言；LeRobot v2.1 | gated_auto；CC-BY-NC-SA-4.0 |
| [RoboMIND 1.x](https://huggingface.co/datasets/x-humanoid-robomind/RoboMIND) | 单一本体、单任务样包；取得 gated 访问后核验动作契约 | 多本体、单臂和双臂；HDF5 archives | gated_auto；Apache-2.0 (current card) |
| [RoboMIND 2.0](https://log2r.github.io/RoboMIND2.0/) | 若研究接触／移动，选择对应传感器子集；不要全量打包 | 接触、移动双臂、真仿配对；per-package format; full archives not inspected | official_download_login；Apache-2.0 (ModelScope card; package review pending) |
| [RH20T](https://rh20t.github.io/) | 仅选择包含所需力／触觉的配置；先取时间同步与标定样包 | 接触丰富、多模态；MP4 + NumPy + JSON + calibration | public_download；dataset terms require confirmation |
| [ABC-130k](https://huggingface.co/datasets/XDOF/ABC-130k/blob/75ca0b88bda489f2bd935d72454593ecb90efb52/README.md) | 先取 MCAP 小样包并验证与 v3 派生集的原始轨迹关联 | 双臂原始日志和细粒度标注；MCAP + annotation MCAP | gated_auto；Apache-2.0 |
| [1X World Model Challenge data](https://github.com/1x-technologies/1xgpt) | 先确认视频／状态／动作版本和世界模型用途，再取单个样包 | 世界模型与动作条件预测；video tokens + actions; later raw video/state release | public_download；Apache-2.0 early release; check raw variants |
| [EgoDex](https://github.com/apple/ml-egodex) | 按人体辅助学习用途取短片与姿态标签，不进入机器人 action BC | 人体手部先验、动作重定向；video + 3D pose annotations | public_download；CC-BY-NC-ND (dataset) |
| [UMI task data and collection system](https://umi-gripper.github.io/) | 优先取采集与重定向说明，再取一个任务的完整示范 | 机器人未确定时的夹爪操作采集；task-specific video/trajectory pipeline | project_download_links；check each data package |
| [Open X-Embodiment](https://github.com/google-deepmind/open_x_embodiment) | 先选组成数据集；优先避免与 DROID／Bridge 重复下载 | 多本体预训练与数据配方；RLDS / TFDS | public_component_links；component-specific licenses |
| [RoboCasa365](https://github.com/robocasa/robocasa) | 先取一个任务族、环境配置和少量示范 | 长任务、移动操作仿真；LeRobot current release | public_download_and_generator；CC-BY-4.0 datasets/assets per project; code MIT |

### 暂缓

| 数据 | 建议先取什么 | 价值与接口范围 | 获取与许可 |
|---|---|---|---|
| [Genie Sim 3.0 data](https://www.agibot.com/article/231/detail/29.html) | 先核实可用数据、权利与厂商规模口径，暂不批量下载 | 智元生态真仿路线；release archives; HF mixes data and checkpoints | public_mixed_artifacts；HF license metadata absent; verify package terms |
| [Teleop-GR1 current repository](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-GR1/blob/9f68429ad12535d30d1aae33b7945c79c830c8c4/README.md) | 数据卡与文件内容版本存在不一致，先核实版本 | 版本与内容漂移案例；mixed LeRobot directories | public_download；CC-BY-NC-4.0 current card |
| [Open-H-Embodiment](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-Open-H-Embodiment) | 当前主方向是医疗，不作为工业数据优先项 | 展示数据命名需核对；LeRobot v2.1 | public_download；CC-BY-4.0 card; component review still relevant |

## 每次扩大下载前的检查

1. 明确这一批回答什么实验问题，以及对应任务、本体、传感器和控制模式。
2. 记录来源的固定 revision 或发布版本；查询实际目标文件清单与压缩大小。
3. 取小样包，计算解压后体积和训练读取缓存开销，再估算存储预算。没有实测时标记未知。
4. 核实访问条件与数据许可。企业内部实验不自动免除 NC 等限制；需要按实际用途确认使用权利。
5. 核查与已有数据的来源重叠，例如 Alpha/Beta、OXE 组成集、ABC 原始／转换版本。
6. 确认动作、时钟、标定和任务字段可解释；用所选模型实际读取至少一个 batch。
7. 样包通过后再决定下载任务子集还是全量；下载、过滤和训练配方分别记录版本。

## 不同研究问题的优先组合

| 问题 | 优先查阅或获取 | 应补的目标数据 |
|---|---|---|
| 单臂选择与搬放 | DROID、Bridge、LIBERO | 实际工件、相机和夹爪配置 |
| 双臂操作 | ABC、RoboTwin、RoboMIND 对应本体 | 双手协作与目标工具动作接口 |
| 人形上身操作 | NVIDIA G1、宇树 Dex1、AgiBot 对应任务 | 所购人形的关节／手型与控制配置 |
| 人形移动与负载 | 宇树 WBT、全身控制接口资料 | root、接触、负载、行走控制器与稳定性日志 |
| 接触装配 | RH20T、RoboMIND 力／触觉相关子集 | 目标治具、公差、材料和失败恢复 |
| 场景变化 | RoboCasa、RoboTwin、匹配任务的仿真 | 独立真实工位测试，检验 sim-to-real 收益 |

这里的组合是实验起点，不承诺模型收益；也不意味着所有来源已被本 MVP reader 支持。

完整来源、规模口径和各数据集限制见 `docs/02-dataset-catalog.md` 与 `docs/sources.md`。内网部署、镜像和离线文件布局见 `docs/10-linux-windows-offline-deployment.md`。
