# Eval 任务原型（Phase 2）

选题 5（SWE agent 失败模式分类学）的 3 个配套评测任务的可运行原型。
背景见 `../pilot/brief_2026-10-06.md`（轨迹 schema、标注结果、9 类 taxonomy）。

## 三个原型

| 目录 | 探针 | 针对失败类 | 输入 → 输出 |
|---|---|---|---|
| `localization-probe/` | 定位探针 | LOC（故障定位失败，pilot 主标签 25%） | issue 文本 + 候选文件 → 排序（禁编辑）；按 gold 文件算 P/R@k、MRR |
| `edit-recovery/` | 编辑恢复测试 | CASC / TOOL / RIGID（级联失败、工具误用、策略僵化） | 失败轨迹截断至首次失败编辑前 → 新 agent 限 N 步恢复；恢复率 + 恢复步数 |
| `hygiene-check/` | 变更卫生检查 | HYG（变更卫生差，pilot 最高频次标签） | git diff → 清洁度分数 + 分项 flag（动测试/debug 残留/junk 文件） |

## 运行

```bash
cd eval-proto
python3 -m venv venv && ./venv/bin/pip install -q datasets   # 仅取 gold patch 用过一次
cd localization-probe && python3 demo.py
cd ../edit-recovery   && python3 demo.py
cd ../hygiene-check   && python3 demo.py
```

各目录 README 含：测什么、针对哪类失败、指标精确定义、demo 结果、局限。
demo 用的都是 pilot 真实轨迹/补丁（`../pilot/failed_with_patch.json`），
gold patch 来自 SWE-Gym/SWE-Gym（`data/gold_patches.json`，HF streaming 抓取）。

## 关键设计取舍（诚实声明）

1. 三个 demo 里凡是"agent"字样的执行体都是**确定性桩**（mock probe / mock
   recovery agent），仅用于验证 harness 与指标计算。真正的探针/恢复 agent
   需按各 README 的接口实现（LLM + 只读/可执行沙箱）。
2. `localization-probe` 的候选文件集是"agent view 过的文件"的代理——正式版
   必须用 base_commit 的完整文件列表（本数据集根目录 view 为空，见 pilot §6.4）。
3. `hygiene-check` 的权重是 v0 启发式，引用前需校准。
4. `edit-recovery` 只处理显式 tool-error 的失败编辑；"静默破坏"型需二级检测器。

## 全量运行还需要什么

1. **数据**：200–300 条"失败且有补丁"轨迹的双人标注（rubric v2，见 pilot §5 修订建议）；
   empty_generation 子集的轻量分类（pilot §7.2）。
2. **执行环境**：定位探针需只读 repo 沙箱；恢复测试需可执行沙箱 + 真实 agent
   （N 步上限、失败通知注入已在 harness 中定义好接口）。
3. **校准**：hygiene 权重、截断信号的二级检测器（静默破坏）、多文件 gold 的
   partial-credit 计分。
4. **License 核实**：SWE-Gym 系列轨迹集的 license（pilot §6.5），writeup 引用前确认。
5. **投稿**：用户需自行在 Kaggle Join Paper Track（2026-11-12 截止）。

## Running from this repository (English note)

The demos read pilot trajectories from `../pilot/failed_with_patch.json`. That file contains
raw trajectory content from SWE-Gym/OpenHands-Sampled-Trajectories, whose dataset card declares
no license, so **it is not redistributed here**. To run the demos, download the trajectories from
the SWE-Gym release on Hugging Face, export the failed-with-patch rows used in the paper
(see `idx` / `instance_id` in `data/full_labels_v3.json` at the repository root) to
`pilot/failed_with_patch.json` at the repository root, then run each `demo.py`.

`data/gold_patches.json` holds three upstream gold patches and issue texts (getmoto/moto,
python/mypy) taken from the SWE-Gym task split; they remain under their original repositories'
licenses. All "agents" in the demos are deterministic stubs; no real agent has been evaluated.
