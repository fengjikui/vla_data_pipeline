"""Generate an actionable acquisition backlog without downloading more data."""
from pathlib import Path
import json
from vla_pipeline.io import write_json
ROOT=Path(__file__).resolve().parents[1]
START={'nvidia-g1-teleop','nvidia-x-sim','abc-v3-smoke'}
FIRST={'droid','unitree-g1-wbt','unitree-g1-dex1','robotwin-2','libero','bridge-v2'}
HOLD={'nvidia-gr1-current','open-h-excluded','genie-sim-3'}
SAMPLES={'droid':'官方小样包／100-episode 路线先验证，再选任务子集；暂不取全量视频', 'unitree-g1-wbt':'一个明确手型与全身控制配置，先取元数据和 10 条完整 episode','unitree-g1-dex1':'先选一个整理任务，取元数据与 10 条完整 episode','robotwin-2':'选择一个双臂操作任务，先取环境与少量成功示范','libero':'固定一个任务集与官方划分，先完成加载和一次评测回放','bridge-v2':'固定机器人配置与单个操作族，先取 10～20 条完整示范','rh20t':'仅选择包含所需力／触觉的配置；先取时间同步与标定样包','robomind-1':'单一本体、单任务样包；取得 gated 访问后核验动作契约','robomind-2':'若研究接触／移动，选择对应传感器子集；不要全量打包','abc-130k':'先取 MCAP 小样包并验证与 v3 派生集的原始轨迹关联','umi':'优先取采集与重定向说明，再取一个任务的完整示范','oxe':'先选组成数据集；优先避免与 DROID／Bridge 重复下载','agibot-world-2025':'按任务与本体选择；Alpha 是 Beta 子集，避免重复','agibot-world-2026':'先取与候选工位相关的单个 task archive','galaxea-open-world':'单个轮式双臂任务 archive；先核验许可与 gated 条件','robocasa365':'先取一个任务族、环境配置和少量示范','egodex':'按人体辅助学习用途取短片与姿态标签，不进入机器人 action BC','one-x-worldmodel':'先确认视频／状态／动作版本和世界模型用途，再取单个样包'}

def main():
    records=[]
    for d in json.loads((ROOT/'catalog/datasets.json').read_text())['datasets']:
        key=d['id']
        stage='已做小样本验证' if key in START else '第一批候选' if key in FIRST else '暂缓' if key in HOLD else '按场景选择'
        if key in START:sample='本机已固定 6 条 episode、一路相机；迁移清单即可，不再扩量'
        elif key=='nvidia-gr1-current':sample='数据卡与文件内容版本存在不一致，先核实版本'
        elif key=='open-h-excluded':sample='当前主方向是医疗，不作为工业数据优先项'
        elif key=='genie-sim-3':sample='先核实可用数据、权利与厂商规模口径，暂不批量下载'
        else:sample=SAMPLES.get(key,'先取元数据、许可与 10～20 条代表轨迹')
        records.append({'id':key,'name':d['name'],'stage':stage,'purpose':d['research_value'],'sample_plan':sample,'entry_url':d['entry_url'],'format':d['format'],'embodiments':d['embodiments'],'access_status':d['access_status'],'license':d['license_summary'],'reported_scale':d['scale_statement'],'capacity_bytes':None,'capacity_note':'全量压缩／解压／视频体积未在本次逐包实测；下载前查询目标文件清单，不把小时／轨迹数当作 GB。','expansion_gate':'样包能解释并接入目标训练器，且任务／控制配置与实验目标匹配，再决定扩量。','existing_parser_support':'本次所锁定子集已实测' if key in START else '待适配或待对目标子集验证，索引存在不等于 reader 已支持','source_ids':d['source_ids'],'limitations':d['limitations']})
    write_json(ROOT/'catalog/download_plan.json',{'as_of':'2026-09-12','policy':'Index broadly, download small representative samples; acquire larger data on approved company systems. Sample sizes are proposed budgets, not quality guarantees.','records':records})
    md='''# 公司环境数据获取清单

本机只保留已用于验证的约 **212 MB** 原始小样本，不再扩大外网电脑下载。下面是后续公司环境的获取顺序，不是全部下载指令。机器可读版本为 `catalog/download_plan.json`。

建议先用 3 个已锁定样本复现链路，然后按目标任务选择第一批候选。优先级针对本实验室起步，不代表厂商质量排名。研究目录的 P0/P1 与本清单的下载批次用途不同。

## 已验证的最小复现包

`configs/demo_sources.lock.json` 记录具体文件、固定 revision、字节数和 SHA256。3 个来源各选前 6 条完整 episode，只有 1 路相机。ABC v3 的共享 Parquet 和视频文件含额外未选中数据，因此原始下载字节大于所选轨迹净体积。

## 按批次获取

'''
    for stage in ['已做小样本验证','第一批候选','按场景选择','暂缓']:
        md+='### '+stage+'\n\n| 数据 | 建议先取什么 | 价值与接口范围 | 获取与许可 |\n|---|---|---|---|\n'
        for r in records:
            if r['stage']==stage:
                fields=[f'[{r["name"]}]({r["entry_url"]})',r['sample_plan'],r['purpose']+'；'+r['format'],r['access_status']+'；'+r['license']]
                md+='| '+' | '.join(x.replace('|','／').replace('\n',' ') for x in fields)+' |\n'
        md+='\n'
    md+='''## 每次扩大下载前的检查

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
'''
    (ROOT/'docs/11-download-priorities.md').write_text(md)

if __name__=='__main__':main()
