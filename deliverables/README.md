# 汇报材料使用说明

建议先读 [主管摘要](../docs/06-supervisor-brief.md)，再按 [逐页讲稿](speaker-notes.md) 练习 10～15 分钟。PPTX 可编辑，PDF 保持已检查的版式，HTML 下载后可离线阅读。完整数据研究在 [技术报告](../docs/01-vla-data-research.md)。

| 文件 | 用途 |
|---|---|
| [VLA数据预研与管线验证-主管汇报.pptx](VLA数据预研与管线验证-主管汇报.pptx) | 16 页、可编辑文本与表格，附讲者备注 |
| [VLA数据预研与管线验证-主管汇报.pdf](VLA数据预研与管线验证-主管汇报.pdf) | 固定版式备用；中文可搜索与复制 |
| [offline-report.html](offline-report.html) | 三类来源图片、数据量、质量与小模型训练结果 |
| [speaker-notes.md](speaker-notes.md) | 逐页讲稿、3 分钟短版和会前检查 |
| [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) | 样本图片出处、许可和派生说明 |

## 重新生成

数据与训练报告更新后，先确保 `reports/acceptance.json` 与 `reports/training_probe.json` 的 release ID 一致，再运行 `scripts/build_offline_report.py`。它会读取本机已缓存原始视频，不需要重新下载全部数据。

`scripts/build_presentation.mjs` 是本次汇报制作脚本，使用 Codex 随附的 `@oai/artifact-tool` 和演示文稿校验工具。它们**不是数据 Pipeline 的运行依赖**；公司服务器只需安装 `pyproject.toml` 指定的数据处理依赖。PPTX 可以直接用办公室软件编辑，无须安装报告制作工具。

若在具有同样制稿工具的环境重新生成，需要设置 `PROJECT_ROOT、PRESENTATIONS_SKILL、RUNTIME_PYTHON、RUNTIME_NODE_MODULES`，使 Node 能解析 `@oai/artifact-tool`。最终输出不能覆盖既有文件，重新生成前请另存旧稿，或通过 `DECK_FILENAME` 指定新名称。

本次 PDF 使用 LibreOffice 导出，字体为 Arial Unicode MS。制稿环境需要能找到中文字体；缺字时修复字体配置后重新导出，不能仅凭 PDF 文件存在就认为成功。导出后逐页渲染、确认字形与换行，再交付。不要将本机字体文件直接复制到公司环境而忽略其使用条件。

主管看到的结论和数字来自 JSON 验收记录，不是手工编造的跑分。修改正文时，保持“数据工程／小模型接口验证”与“完整 VLA／机器人能力验证”的边界。
