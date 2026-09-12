# 第三方样本与图像出处

汇报 PPTX、PDF 和离线 HTML 使用三张公开数据集视频帧。图片仅作数据结构与场景说明，不表示厂商认可本项目。原始分辨率帧提取后按比例展示，没有生成式修改。具体 revision、episode、视频时间与派生图片路径见 [图像出处记录](../reports/image_attribution.json)，文件哈希见 [样本锁文件](../configs/demo_sources.lock.json)。

| 图片 | 提供者与原数据集 | 数据卡许可 |
|---|---|---|
| `g1_real.png` | NVIDIA：[PhysicalAI-Robotics-GR00T-Teleop-G1](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `panda_sim.png` | NVIDIA：[PhysicalAI-Robotics-GR00T-X-Embodiment-Sim](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-X-Embodiment-Sim) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `abc_real.png` | Hugging Face LeRobot 组织发布：[abc_130k_v3_smoke](https://huggingface.co/datasets/lerobot/abc_130k_v3_smoke)，ABC/YAM 数据派生转换样本 | [Apache License 2.0](licenses/Apache-2.0.txt) |

这些许可标注依据固定版本来源记录。扩大使用时保留原始许可、NOTICE 和派生关系，并核查上游数据条款；本项目没有为第三方数据重新授予权利。程序运行时下载的原始视频与 Parquet 不提交到 Git 仓库。
