# 编辑恢复测试 (edit-recovery)

## 测什么
一次失败编辑之后，agent 能否诊断并恢复——而不是"越修越坏"或原地打转。
针对失败类 **CASC（级联编辑失败）**、**TOOL（工具误用）**、**RIGID（策略僵化）**。
pilot 数据：一次失败后最终恢复率从 90.5% 跌到 57.2%（SWE-agent 论文），
且失败编辑常以完全相同的报错连续重复（pydantic-6104）。

## 协议
1. 取一条 resolved=False 的轨迹。
2. `truncate.py` 找到**首次失败编辑**——str_replace/insert/create 调用，
   其 observation 含显式 ERROR 信号（`No replacement was performed` /
   `did not appear verbatim`，均从真实轨迹挖掘得到）。
3. 在该次编辑**之前**截断轨迹；recovery agent 收到
   `build_recovery_input(prefix, failure)`（完整前缀 + 失败通知），
   在 N 步（默认 10）内继续。
4. 若轨迹中不存在失败编辑（如 agent 从未做源码编辑），记为
   **NOT TRUNCATABLE**，不计入恢复指标（单独报告比例）。

真实 agent 需实现 `harness.py` 的 `RecoveryAgent.run(messages, max_steps)`。

## 指标（`harness.score_recovery`）
- `truncation_yield = 可截断数 / 失败轨迹数`（本探针能覆盖的失败面占比）
- `recovery_rate = 恢复数 / 可截断数`
- `steps_to_recovery`：恢复所用步数（报告均值与中位数）
- demo 中的 `MockRecoveryAgent` 是确定性桩（`retry_same` 永不恢复，
  `replan` 在 3 步恢复），仅用于验证 harness 与指标计算。

## 运行 demo
```bash
cd edit-recovery
python3 demo.py
```
3 个案例：pydantic-6104（TOOL，3 次相同失败）、hydra-2189（CASC，轨迹中段失败）、
mypy-11567（LOC，无失败编辑 → NOT TRUNCATABLE）。

## Demo 结果
- pydantic-6104：46/59 turn 处截断；hydra-2189：30/59 处截断
- mypy-11567：NOT TRUNCATABLE（从未做源码编辑）
- mock 汇总：recovery_rate=0.5（桩行为），truncation_yield=0.8（demo 样本，非总体）

## 局限
1. 只检测显式 tool-error 的失败编辑；"静默破坏"（编辑成功应用但引入
   IndentationError，如 hydra-2189 后段）需要"编辑→K 步内 traceback 指向该文件"
   的二级检测器，未实现。
2. 完整重跑需要真实 agent + 执行环境（out of scope）；本交付物是 harness 与指标。
3. pilot 显示细粒度失败中 tool-error 型是少数——truncation_yield 在全量数据上
   预计显著低于 demo 的 0.8，需实测。
