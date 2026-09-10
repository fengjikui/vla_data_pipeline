# 真实数据文件到训练样本

## 1. 三种证据级别

本文明确区分：**实际读取**的固定版本 Parquet/JSON、小样本之外的**官方 schema 描述**、以及用于解释模型输入的**自拟教学样例**。没有在本次工作中训练模型、下载完整数据集或执行实机动作。

## 2. 实际读取：NVIDIA G1 水果拿放

来源是 NVIDIA GEAR 发布的 `nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1`，不是宇树自己的同名采集任务。固定 revision 为 `0d7bdd06e67f3ca0868892d0ec8f03bcd3e49e40`，许可证 CC BY 4.0。[^12][^13]

抽查的逻辑结构是：

```text
g1-pick-apple/
  meta/info.json
  meta/tasks.jsonl
  data/chunk-000/episode_000000.parquet
  videos/...                   # 本次未下载／解码视频
```

实际 Parquet 文件为 **65,601 bytes，111 行**，SHA-256 为：

```text
a0d5b462c5d27a7378b4bef68cbd6fdfcd85c5c033f5e9bd2abca47fe67fa22d
```

### 2.1 每一行有哪些字段

| 字段 | 实际观测 | 含义与需要确认的事项 |
|---|---|---|
| `observation.state` | 每行 43 个数，源元数据 float64 | 全身与手部状态；按 names 映射到部位 |
| `action` | 每行 43 个数，源元数据 float64 | 数据卡描述为目标关节配置；不是自然语言动作 |
| `observation.img_state_delta` | 第 0 行约 0.022999 | 与图像／状态时间差有关的字段；正负方向须查采集实现，不能猜 |
| `timestamp` | 前两行为 0 和约 0.05 秒 | episode 内时间 |
| `frame_index` | 前两行为 0、1 | 轨迹内行序号 |
| `episode_index` | 此文件为 0 | 来源数据内的 episode 编号 |
| `index` | 前两行为 0、1 | 数据全局行索引 |
| `task_index` | 此样本为 1 | 需通过 tasks 表查语言 |

`task_index=1` 对应原文 “Pick up the red apple and place it on the plate”。单独打开 Parquet 看不到这句话并不代表没有语言监督；训练 reader 会从关联元数据取出任务文本。[^56]

**视频像素不在这些数值列中。** reader 根据 episode、时间和视频路径加载图像。不能只对 Parquet 使用普通 DataLoader，就声称已拿到完整 VLA 输入。

### 2.2 真实数值节选

下表仅展示第一个 episode 的第 0 行前三个维度，四舍五入用于阅读；完整前两行在 [抽查 JSON](../evidence/g1-sample-inspection.json)。

| 部位（来自元数据 names） | 当前状态 | 目标动作 |
|---|---:|---:|
| left_hip_pitch_joint | -0.702895 | -0.532718 |
| left_hip_roll_joint | 0.080807 | -0.044161 |
| left_hip_yaw_joint | 0.056785 | 0.112653 |

这些数说明状态与动作不同，但**不能据此断言这份上身操作数据训练了行走**。身体保持或参考姿态也会占据动作维度。任务是否有走路、转身和搬运，需要看轨迹覆盖及控制配置。

### 2.3 这个样本能证明和不能证明什么

能证明固定文件能被 Parquet reader 读取、字段存在、状态动作维度、样本时间间隔，以及该 apple 子集的元数据为 LeRobot v2.1。不能证明视频同步正确、所有动作都是安全或成功的，也不能证明任意 VLA 无需转换便可使用。

补充读取四个水果子集 metadata 后，episode 声明数为 311、233、264、287，合计 1,095，与卡中 1,000 有差异。这是**元数据声明清点**，不是逐文件去重和逐轨迹验收后的真实总量；不能掩盖两种统计口径的区别。见 [四子集清点](../evidence/g1-subset-inventory.json)。

复现时从仓库根目录执行：

```bash
uv run --with pyarrow==25.0.1 python scripts/inspect_public_sample.py
```

脚本只下载固定 revision 的小型数值文件与少量元数据，校验已记录哈希，并打印结构；默认缓存到系统临时目录。它不会下载整个数据集、上传数据或启动训练。Python 3.14.3 + PyArrow 25.0.1 是本次实际验证环境，不是 VLA 训练环境要求。

## 3. 对照：宇树全身 WBT 数据

抽查 `G1_WBT_Brainco_Collect_Plates_Into_Dishwasher` 固定 revision `16c01dbfcb2159783ea575acd42d1cec9b69e311`，**只读取数据卡和 meta/info.json**。该子集元数据为 v3.0、30 Hz、300 episodes；未下载其大 Parquet 分片。[^15][^16]

| 字段 | 维度 | 物理含义 |
|---|---:|---|
| `observation.state.robot_q_current` | 36 | root 的 xyz、wxyz 四元数、29 个关节 |
| `action.robot_q_desired` | 36 | 对应的目标配置 |
| `observation.state.ee_state` | 12 | 左右末端状态，官方说明由 root 到末端的 FK 得到，包含腰部影响 |
| `action.ee_action` | 12 | 对应目标末端状态；旋转细节还需实现确认 |
| `observation.state.hand_state` | 12 | 双手状态；此处 BrainCo 每手 6 个控制量 |
| `action.hand_cmd` | 12 | 双手目标命令 |
| 四路 camera | 各 480×640×3 | 左右头部和左右腕部视图 |

不要简单把 36+12+12 拼成一个“60 自由度人形”。某些表示描述同一运动的不同视图，36 维中还含四元数；到底训练 `q_desired` 还是末端目标，要由模型与控制器决定。脚部接触、IMU 或力矩不在上述示例字段中，不能自动假定已有。

该文件按 v3 组织，多个 episode 可以共享 Parquet 和 MP4，需要元数据定位偏移。与前面的 v2 文件边界不同，却可以在规范层统一成 episode/stream 的抽象。[^34]

## 4. 官方结构：DROID / RLDS

根据 DROID 官方说明，RLDS 观测含腕部和两路外部相机、7 维关节位置、夹爪状态以及笛卡尔状态；`action_dict` 提供多种命令表示。下面是**按说明缩写的逻辑示意**，不是本次已下载的真实 DROID 记录。[^3]

```python
episode = {
    "episode_metadata": {"file_path": "source_path"},
    "steps": [
        {
            "observation": {
                "joint_position": "float64[7]",
                "gripper_position": "float64[1]",
                "wrist_image_left": "uint8[180,320,3]",
                "exterior_image_1_left": "uint8[180,320,3]",
                "exterior_image_2_left": "uint8[180,320,3]"
            },
            "action_dict": {
                "joint_position": "float64[7]",
                "cartesian_position": "float64[6]",
                "cartesian_velocity": "float64[6]",
                "gripper_position": "float64[1]"
            },
            "language_instruction": "task text",
            "is_first": True,
            "is_last": False,
            "is_terminal": False
        }
    ]
}
```

官方说明某处把 7 维 `action` 注释成“6 个 joint velocities＋夹爪”，与其 7 关节机器人及同时提供的 Cartesian 命令容易混淆。工程接入不应照着注释猜：优先定位原 builder、`action_dict` 与目标模型 transform，验证它究竟是笛卡尔命令、控制尺度还是物理速度。本文没有将这处疑点当作已确认的关节动作定义。

RLDS 末步与 reward/discount 约定也需要单独处理；这类结构虽然常用于 RL，也完全可以用于没有复杂奖励的行为克隆训练。[^35]

## 5. 教学示例：如何形成一个 batch

以下维度**是自拟的单臂训练配置，不是前面 G1 的数据参数**：两路相机，224×224，当前状态 8 维（7 关节＋夹爪），动作块 16 步，batch 32。

| 张量 | 教学 shape | 处理方式 |
|---|---|---|
| `images` | `[32, 2, 3, 224, 224]` | 从视频取帧，resize，HWC→CHW，按视觉编码器要求处理像素范围 |
| `input_ids` | `[32, L]` | 任务语言 tokenization 与 padding；L 由 tokenizer/batch 决定 |
| `attention_mask` | `[32, L]` | 区分有效文本和 padding |
| `state` | `[32, 8]` | 显式字段映射、单位转换和训练配方归一化 |
| `actions` | `[32, 16, 8]` | 从同一 episode 取未来命令块，再变换和归一化 |
| `action_valid_mask` | `[32, 16, 8]` | 区分有效时间、存在维度与可监督动作 |

有历史输入时还会有时间轴；有的模型将每路相机放在独立字典；有的模型会 padding 到固定 action_dim。动作离散化路线把 `actions` 编码成 token；连续路线保留实数。归一化和 padding 都要保留可逆信息与 mask。

一个数值说明：若某个连续维度训练均值为 0.2、标准差为 0.1，原始值 0.3 归一化为 $(0.3-0.2)/0.1=1$。模型输出 1 后，执行前还原为 0.3，再按动作接口转换；不能把 1 当作 1 米或 1 弧度发出去。

下面是算法示意，不是对某个库版本作 API 承诺：

```python
for episode in manifest.train_episodes:
    trajectory = reader.decode(episode)
    aligned = synchronizer.align(trajectory, observation_contract)
    canonical = semantic_adapter.convert(aligned, embodiment_spec)
    for t in sampler.select_valid_starts(canonical):
        inputs = model_adapter.observation(canonical, t)
        targets, mask = model_adapter.action_chunk(canonical, t, horizon)
        yield inputs, targets, mask
```

## 6. 一个新数据集接入后，怎样知道可以训练

先用同一时间轴回放图像、状态和命令，核对语言；然后检查 train/test 分组，拟合训练统计；生成一个实际模型 batch，确认形状、有限值、mask 和动作解码；最后做短训练和闭环评测。每一步解决不同的问题。

数据集自带 `stats.json` 不代表它适用于新的训练 split 或不同动作表达。能 import、能迭代、loss 能下降三个条件，也都不能单独证明策略能在工厂完成任务。

## 7. 机器人术语速查

| 术语 | 在这份报告中的意思 |
|---|---|
| Embodiment／本体 | 机器人的身体和可操作接口，包括关节拓扑、手型、传感器及控制约定 |
| DoF／自由度 | 独立运动变量；末端 6-DoF 位姿不代表机器人只有 6 个关节 |
| Proprioception／本体感知 | 机器人对自身关节、运动、惯性等状态的测量或估计 |
| TCP／工具中心点 | 实际用于操作的工具参考点；换夹爪后通常要重新定义或校准 |
| FK／正运动学 | 从关节配置计算末端或身体各部分位姿 |
| IK／逆运动学 | 从期望末端位姿求可实现的关节配置；可能多解或无解 |
| Pose／位姿 | 位置和朝向；四元数、旋转矩阵等是朝向的不同表达 |
| Twist | 刚体线速度和角速度的组合，必须注明坐标系与单位 |
| Retargeting／重定向 | 把另一身体或采集器的动作映射成目标机器人的可执行参考 |
| BC／行为克隆 | 用示范中的观测与动作配对，监督学习一个动作策略 |
| Rollout | 让策略在真实或模拟环境执行一段时间并记录交互 |
| Action chunk | 一次预测的一段未来动作；不代表必须全部开环执行 |
| World model／世界模型 | 预测环境如何变化的模型；与直接预测控制动作的策略职责不同 |
| Sim-to-real | 将仿真中学习的策略或知识迁移到真实环境 |

<!-- source-footnotes -->

## 本文引用

[^3]: DROID Dataset Team. [The DROID Dataset](https://droid-dataset.github.io/droid/the-droid-dataset). 持续更新，未标明完整发布日期；访问 2026-09-11。

[^12]: NVIDIA GEAR. [PhysicalAI-Robotics-GR00T-Teleop-G1 card](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1). 2025-06-01 创建日期（数据卡）；访问 2026-09-11。

[^13]: NVIDIA GEAR. [G1 apple subset info.json](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1/blob/0d7bdd06e67f3ca0868892d0ec8f03bcd3e49e40/g1-pick-apple/meta/info.json). 固定 revision 0d7bdd0，2025-06-11；访问 2026-09-11。

[^15]: Unitree Robotics. [G1 WBT BrainCo dishwasher card](https://huggingface.co/datasets/unitreerobotics/G1_WBT_Brainco_Collect_Plates_Into_Dishwasher/blob/16c01dbfcb2159783ea575acd42d1cec9b69e311/README.md). 固定 revision 16c01db，2026-03-27；访问 2026-09-11。

[^16]: Unitree Robotics. [G1 WBT BrainCo info.json](https://huggingface.co/datasets/unitreerobotics/G1_WBT_Brainco_Collect_Plates_Into_Dishwasher/blob/16c01dbfcb2159783ea575acd42d1cec9b69e311/meta/info.json). 固定 revision 16c01db，2026-03-27；访问 2026-09-11。

[^34]: Hugging Face LeRobot. [LeRobotDataset v3.0](https://huggingface.co/docs/lerobot/lerobot-dataset-v3). v3 文档，持续更新；访问 2026-09-11。

[^35]: Google Research. [RLDS specification](https://github.com/google-research/rlds). 2021 起；仓库 2025-11-29 archived；访问 2026-09-11。

[^56]: NVIDIA GEAR. [G1 apple task lookup](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1/blob/0d7bdd06e67f3ca0868892d0ec8f03bcd3e49e40/g1-pick-apple/meta/tasks.jsonl). 固定 revision 0d7bdd0，2025-06-11；访问 2026-09-11。
