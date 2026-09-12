"""Build a standalone, offline HTML evidence report from verified outputs."""
from pathlib import Path
import base64
import html
import json
import av
from vla_pipeline.io import write_json
from vla_pipeline.readers import read_source

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables';ASSETS=OUT/'assets'


def main():
    OUT.mkdir(exist_ok=True);ASSETS.mkdir(exist_ok=True)
    a=json.loads((ROOT/'reports/acceptance.json').read_text())
    t=json.loads((ROOT/'reports/training_probe.json').read_text())
    assert a['release_id']==t['release_id'],'Reports must describe the same release'
    lock=json.loads((ROOT/'configs/demo_sources.lock.json').read_text())
    figures=[];image_evidence=[]
    for spec in lock['sources']:
        ep=next(read_source(spec,ROOT/'data/raw'))
        target=float(ep.timestamps[len(ep.timestamps)//2])+ep.video_offset
        with av.open(str(ep.video)) as container:
            stream=container.streams.video[0];container.seek(int(target/float(stream.time_base)),stream=stream,backward=True)
            selected=None
            for frame in container.decode(stream):
                if frame.pts is not None:
                    ts=float(frame.pts*frame.time_base)
                    if ts>target:break
                    selected=frame
            if selected is None:raise ValueError('No source frame')
            path=ASSETS/(spec['id']+'.png');selected.to_image().save(path)
            pts=float(selected.pts*selected.time_base)
        data=base64.b64encode(path.read_bytes()).decode()
        figures.append(f'<figure><img src="data:image/png;base64,{data}" alt="{html.escape(spec["label"])}"><figcaption><strong>{html.escape(spec["label"])}</strong><br>原始来源第 0 条轨迹，视频 {pts:.2f} 秒<br>{spec["license"]}</figcaption></figure>')
        image_evidence.append({'asset':str(path.relative_to(ROOT)),'source_repo':spec['repo'],'revision':spec['revision'],'episode':0,'video_pts':pts,'license':spec['license'],'source_url':spec['source_url'],'transformation':'Extracted original-resolution video frame, no generative alteration'})
    write_json(ROOT/'reports/image_attribution.json',image_evidence)
    rows=''.join(f'<tr><td>{s["label"]}</td><td>{s["accepted"]}</td><td>{s["frames"]:,}</td><td>{s["state_dim"]} / {s["action_dim"]}</td><td>{s["splits"].get("train",0)} / {s["splits"].get("validation",0)}</td><td>{s["training_windows"]}</td></tr>' for s in a['sources'])
    training=''.join(f'<tr><td>{r["source_id"]}</td><td>{r["initial_train_masked_mse"]:.4f}</td><td>{r["final_train_masked_mse"]:.4f}</td><td>{r["validation_masked_mse"]:.4f}</td><td>{r["checkpoint_reload_max_abs_error"]:g}</td></tr>' for r in t['results'])
    checks=''.join(f'<tr><td>{x["episode_id"]}</td><td>{html.escape(", ".join(x["reasons"]))}</td><td>隔离，不进入训练视图</td></tr>' for x in a['adversarial_fixture_result']['quarantine_details'])
    source_links=''.join(f'<li><a href="{s["source_url"]}/tree/{s["revision"]}">{s["label"]}</a>，{s["license"]}，revision <code>{s["revision"][:12]}</code></li>' for s in lock['sources'])
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VLA 数据管线 · 实测交付</title><style>
:root{--ink:#202d29;--muted:#607069;--paper:#f5f3ec;--line:#d7ddd4;--accent:#9b502d}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif;font-size:17px;line-height:1.8}main{max-width:1120px;margin:auto;padding:66px 42px}header{padding-bottom:44px;border-bottom:2px solid var(--ink)}.eyebrow{color:var(--accent);font-size:14px;letter-spacing:.12em}h1{font-size:48px;line-height:1.2;letter-spacing:-.03em;margin:18px 0}h2{font-size:29px;margin:54px 0 18px}h3{font-size:21px}p{max-width:900px}strong{font-weight:650}.lead{font-size:22px;max-width:840px}.metrics{display:flex;gap:60px;margin:30px 0}.metrics b{font-size:44px;display:block;font-weight:600}.metrics span{color:var(--muted)}table{border-collapse:collapse;width:100%;font-size:15px;margin:22px 0}th{text-align:left;color:var(--muted);font-size:14px;font-weight:600}th,td{padding:14px 12px;border-bottom:1px solid var(--line);vertical-align:top}th:first-child,td:first-child{padding-left:0}.figures{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}figure{margin:0}img{width:100%;height:230px;object-fit:contain;background:#e5e7df}figcaption{font-size:13px;line-height:1.7;color:var(--muted);margin-top:12px}.note{padding:20px 24px;background:#e7ebe2;font-size:16px}.warning{color:#834424}pre{background:#202d29;color:#f8f6ef;padding:24px;overflow-x:auto;font-size:14px;line-height:1.7}code{font-family:ui-monospace,monospace;font-size:.85em}a{color:#3b6a56}footer{border-top:1px solid var(--line);margin-top:48px;padding-top:20px;color:var(--muted);font-size:13px}@media(max-width:700px){main{padding:28px 18px}h1{font-size:34px}.metrics{gap:22px;flex-wrap:wrap}.figures{grid-template-columns:1fr}table{display:block;overflow-x:auto}.metrics b{font-size:32px}}@media print{body{background:white}main{padding:0}h2{break-after:avoid}figure,table,.note{break-inside:avoid}pre{white-space:pre-wrap}header{break-after:page}}
</style><main><header><div class="eyebrow">工业具身智能预研 · 工程验证</div><h1>VLA 数据管线<br>已跑通的流程与下一步验证</h1><p class="lead">在应用尚未确定的阶段，先建立能解释数据、发现问题、生成训练样本的能力。</p><p>集团 AI 实验室 · 汇报日期 2026-09-14<br>研究与验证时间 2026-09-11 至 2026-09-12</p></header>
'''
    page+=f'<div class="metrics"><div><b>{a["accepted_real_source_episodes"]}</b><span>来源轨迹</span></div><div><b>{a["numeric_frames"]:,}</b><span>原始时刻</span></div><div><b>{a["training_windows"]}</b><span>训练窗口</span></div><div><b>3</b><span>代表性来源</span></div></div>'
    page+='<p class="note">本交付验证数据工程和训练接口。未进行预训练 VLA 微调、机器人闭环执行或工厂可靠性验证。切片窗口来自同一批轨迹，不是新增独立示范。</p><h2>01　真实数据看起来是什么样</h2><div class="figures">'+''.join(figures)+'</div>'
    page+='<table><tr><th>来源</th><th>轨迹</th><th>时刻</th><th>状态 / 动作维度</th><th>训练 / 验证轨迹</th><th>窗口</th></tr>'+rows+'</table><p>仅选取一路相机。G1 是上身桌面操作；ABC 是卷领带，仿真样本是双臂穿引。这些任务用于验证接入，不代表集团工位任务或完整数据集质量。</p>'
    page+='<h2>02　数据管线已经完成哪些步骤</h2><ol><li>读取固定版本与文件哈希，保存原始文件。</li><li>按 LeRobot v2 / v3 或实验室 JSON 契约解析完整轨迹。</li><li>检查维度、数值、时间、语言与媒体，隔离异常输入。</li><li>按原始轨迹组切分，识别数值完全重复的示范。</li><li>使用训练集统计归一化，选取源时间上的过去视频帧。</li><li>输出图像、语言、状态、动作块和 mask，发布不可变版本。</li></ol><p>原始动作保持来源含义，没有做未经验证的跨机器人转换；当前只开放 <code>interface_smoke</code> 训练视图。</p>'
    page+='<h2>03　一个容易漏掉的时序问题</h2><p>真实双臂数据的一行包含全段子任务标注。若直接拼接整个列表，模型会提前看到未来阶段。当前窗口只选择时间戳不晚于当前时刻的最近标注。</p><pre>0.0 秒    Pick up the tie from the bin.\n3.7 秒    Place the tie at the center of the board.\n17.33 秒  Roll the tie at the center of the board.\n\n在 1 秒时：仅使用当前任务和 0 秒已生效的子任务。</pre><p>视频同样按过去帧对齐。设备时钟与真实传输延迟仍需标定，当前验证的是源时间上的计算逻辑。</p>'
    page+='<h2>04　异常数据能否被阻止进入训练</h2><table><tr><th>明确标注的测试变体</th><th>检测结果</th><th>处理</th></tr>'+checks+'</table><p>另有一个数值完全重复副本被识别并跳过。以上人为注入的错误用于验收规则，不能推断原始数据集存在相同比例的问题。</p>'
    page+=f'<p>离线重跑复用同一发布版本；统计量只用训练轨迹；所有动作窗口均未跨轨迹。归一化往返最大绝对误差为 <code>{a["checks"]["action_normalization_roundtrip_max_abs_error"]:.2e}</code>。</p>'
    page+='<h2>05　数据已经进入实际训练程序</h2><p>使用随机初始化的小型 CNN、字节语言 embedding 和状态融合网络，预测 8 步连续动作。每个来源单独训练，避免混淆不同动作语义。CPU 执行 120 步，检查梯度、检查点与优化器恢复。</p><table><tr><th>来源</th><th>初始训练 MSE</th><th>结束训练 MSE</th><th>验证 MSE</th><th>恢复输出误差</th></tr>'+training+'</table><p class="warning">三组 MSE 的尺度受各自归一化影响，不能用于跨来源排名。验证集只有 1～2 条轨迹。训练误差下降不能说明机器人能力提升，也不能证明语言理解或泛化。</p>'
    page+='<h2>06　机械臂与人形的后续验证</h2><table><tr><th>路线</th><th>候选起点</th><th>进一步需要什么</th></tr><tr><td>机械臂</td><td>零件分拣、工位上下料</td><td>工件、治具、精度与节拍，控制器接口，必要的力／触觉</td></tr><tr><td>人形</td><td>静止双臂搬放，再做移动操作</td><td>底层行走与全身控制器、root / 接触 / 负载数据和稳定性指标</td></tr></table><p>建议主管协调 1～2 个工厂现场入口，明确首轮资源上限与两周复盘时间。先确定可测任务，再评价机器人与数据投入。</p>'
    page+='<h2>07　离线复现</h2><pre>uv run vla-pipeline run --offline\nuv run python scripts/verify_delivery.py\nuv run --extra train python -m vla_pipeline.training\nuv run --extra dev pytest -q</pre><p>首次换电脑需要安装依赖并运行在线下载；本机已缓存数据与依赖，可断网演示。原始下载共约 '+f'{a["raw_download_bytes"]/1e6:.1f}'+' MB，v3 共享文件包含未选用的额外轨迹。</p>'
    page+='<h2>来源与使用说明</h2><ul>'+source_links+'</ul><p>图片为上述数据集视频原分辨率帧提取，未做生成式修改。完整哈希与出处见 <code>configs/demo_sources.lock.json</code> 和 <code>reports/image_attribution.json</code>。</p>'
    page+=f'<footer>发布版本 {a["release_id"]} · 结果来源 reports/acceptance.json 与 reports/training_probe.json<br>此文件内嵌图片，无外部脚本或字体依赖，可离线阅读。</footer></main></html>'
    (OUT/'offline-report.html').write_text(page)
    print(OUT/'offline-report.html')

if __name__=='__main__':main()
