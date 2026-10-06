# 定位探针 (localization-probe)

## 测什么
Agent 是否真懂仓库结构：给定 issue 文本，在**不做任何编辑**的前提下，
输出最可能需要改动的文件排序。针对失败类 **LOC（故障定位失败）**——
pilot 发现 25% 的失败补丁主因是改错文件/函数。

## 协议
- 实现 `probe.py` 中的 `LocalizationProbe.rank_files(issue_text, candidate_files) -> list[str]`。
- 输入：issue/PR 文本 + 候选文件列表（repo 相对路径）。
- 输出：同一候选集的排序，越可能改动越靠前。
- 硬约束：探针不得做任何编辑（正式评测时用只读沙箱强制）。

## 指标（`scorer.py`）
Gold = gold patch 实际改动的文件集合（SWE-bench 类任务通常为单文件）。
- `hit@k`：top-k 命中任一 gold 文件则为 1，否则 0
- `precision@k = |top-k ∩ gold| / k`
- `recall@k = |top-k ∩ gold| / |gold|`
- `reciprocal_rank`：首个命中的排名倒数，未命中为 0
- 汇总取实例均值；单文件 gold 时 recall@1 == hit@1。

## 运行 demo
```bash
cd localization-probe
python3 demo.py        # 3 个 pilot 实例，K=3
python3 data_loader.py # 只看数据抽取
```
`data_loader.py` 从 `../../pilot/failed_with_patch.json` 抽 issue 文本
（首条 user 消息的 `<pr_description>`）和 agent 实际 view 过的文件作候选集；
gold 文件来自 `../data/gold_patches.json`（SWE-Gym/SWE-Gym train，streaming 抓取）。
`probe.py` 里的 `MockKeywordProbe` 是弱基线（issue token 与路径 token 重叠），
仅用于跑通 scorer；正式探针应为带只读仓库访问的 LLM agent。

## Demo 结果（3 实例，K=3）
mean hit@3 = 1.0，mean recall@3 = 1.0，MRR = 0.778。
注意候选集很小（2–4 个文件），基线数字仅证明 harness 可用，不代表探针能力。

## 局限
1. 候选文件集是"agent view 过的文件"的代理——正式版必须用 base_commit 的完整文件列表
   （本数据集根目录 view observation 为空，见 pilot brief §6.4）。
2. Gold 取自 SWE-Gym 的 `patch` 字段；test patch 文件需排除（本 demo 的 3 个 gold 均为单源码文件）。
3. 多文件 gold 的 partial-credit 计分（本 demo 未覆盖）待加权方案。
