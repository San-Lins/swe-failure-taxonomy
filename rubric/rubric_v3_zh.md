# 标注 Rubric（v3，adjudication + writeup 方法论用）

> **注（v3 定稿）**：论文最终版本把 NOVER-INSUF 从主标签降为次级标签 VERIF-ABSENT（理由见论文 §3.2），定稿英文版见 `rubric_v3_final_en.md`。下文保留 v3 修订时的原始记录。

基于 v2 + 双人标注一致性检验（n=50，Cohen's kappa=0.68）修订。修订点见文末"v2 → v3 变更日志"，每条附一句话理由。
每条"失败且有补丁"轨迹打 **1 个主标签**（最能解释"为什么补丁没解决问题"）+ 可选次级维度。
只看轨迹内可观测证据，不脑补。主标签互斥；次级维度可多选、可与主标签共现。

## 数据质量门（step 0）：EVAL-BROKEN 评估中断

**主标签前先判**：若 `test_output` 无有效通过/失败信号（`passed=None` 且 `failed=None`），直接打 **EVAL-BROKEN**，不参与"失败模式"主分类。
这类样本的"失败"本身未被观测到——任何"补丁为何失败"的标签都是猜测。
信号：`TEST_OUT: passed=None failed=None`（常伴随 `EVAL_INTERRUPTED` 标记或仅有 `ERR_FILES` 收集错误）。
注：EVAL-BROKEN 是数据质量标记，不是失败模式；prevalence 统计中单独列出（或分母剔除后分别报告）。

## 主标签（primary）

**NARROW-INCOMPLETE 实现不完整**：补丁方向正确、改对了地方，但没完全解决问题；目标测试仍挂、回归测试基本通过。
信号：test_output 显示目标测试 fail、其余大多 pass；patch 改动小且位置合理。
**v3 收紧**：要求目标测试可识别，且 failed 数量少（经验门槛 ≤4）并集中在目标文件/模块；不满足则回退人工复核，不得作为"默认桶"。
（理由：一致性检验中它被当成默认桶，precision 仅 0.58。）

**NARROW-REGRESSIVE 实现引入回归**：补丁试图修问题，但破坏了原本通过的测试（"修好了 A，弄坏了 B/C/D"）。
信号：failed 数量多（经验阈值 ≥5，或回归数 > 目标测试数）；patch 改动面大或改了共享逻辑。
**v3 补充**：digest 升级为 FAIL_TO_PASS / PASS_TO_PASS 划分前（见"未来工作"），"回归 vs 目标"的区分以失败测试名是否落在目标模块为准，不确定时标注"边界"。

**LOC-EXPLORE 定位失败（没找到）**：agent 从未有效查看/定位到与 issue 根因相关的文件；补丁落在无关位置或只有复现脚本。
信号：issue 明确指向某模块，正确文件零**成功** view（`[ok]` 且返回内容）；final patch 文件集合与根因无交集。
**v3 澄清**："查看"以成功返回内容的 view 为准；`[ERR]` 的 view 计数是 observation artifact，不得作为"找到文件"的证据。

**LOC-REPAIR 定位后修不出来**：agent 找到了正确文件（多次**成功**查看），但始终没做出有效源码编辑；补丁只有复现脚本或空改动。
信号：正确文件成功 view ≥3 次；源码编辑次数为 0 或全是复现脚本。

**CASC 级联编辑失败**：一次失败编辑（报错/测试挂）之后行为走偏、越改越乱；补丁在错误基础上叠加；多次 revert/覆盖后文件损坏。
信号：首次失败编辑点之后 action 序列发散；出现 IndentationError/无法 import 等"越修越坏"痕迹。

**CTX 上下文管理失败**：超长轨迹中反复重新探索已看过的文件；同一 grep/view 跑多次无新信息；后半段 action 与前半段重复，呈"迷失"状。
信号：同一文件 view ≥3 次且无新信息；轨迹 turn 数大（>40）且后期 action 重复前期。

**RIGID-PERSEV 策略僵化（perseveration）**：同一编辑意图在同一文件上、以同类报错重复 ≥3 次；收到明确负信号后不换策略。
信号：同一文件、同一编辑意图、同一类报错的 action 重复 ≥3 次。
**v3 放宽**：不再要求"相同命令+路径+参数"逐字相同；"同一文件 + 同一编辑意图 + 同类报错"即算。
（理由：v2 的逐字相同定义太窄，一致性检验中两例漏判。）

**RIGID-OSCIL 策略僵化（oscillation）**：在两个（或少数几个）候选编辑/策略间来回震荡（A-B-A-B），如 str_replace 与 undo_edit 交替，不收敛。
信号：action 序列呈 A,B,A,B 交替模式；无新信息输入却反复切换。

**NOVER-INSUF 验证不充分**：agent 在 finish 前从未运行真实测试集，仅靠自制复现脚本/肉眼确认。
信号：轨迹中真实测试运行为零（`TESTS_RUN(real): -`），只有自制脚本；或自制 mock 测试代替真实测试。
**v3 优先级**："零真实测试运行"是硬信号，**优先于 NARROW**（tie-break step 2 之前检查）。但注意：若同时满足 EVAL-BROKEN 条件，EVAL-BROKEN 优先（step 0）。
**v3 已知问题（诚实记录）**：v2 的 30 例 NOVER-INSUF 经核查全部落在 EVAL-BROKEN（无测试信号）样本上——v2 的 NOVER 类与"评估中断"完全混杂。v3 定义下 NOVER-INSUF 的真实规模需在"有有效测试信号 + 零真实测试运行"子集上重新估计（全量 250 中约 131 条满足该条件，见 adjudication_report §5）。

**LIT 字面化理解**（v3 重定义）：agent 对 issue/约束做字面化解读，做了"字面正确、实质错误"的事。拆两个子型：
- **LIT-TASK 字面理解任务**：把 issue 标题/字面描述当成任务本身（如 issue 说"import: no changes are made to .gitignore"，agent 就往 .gitignore 加一行了事，不实现 import 逻辑）。
- **LIT-CONSTRAINT 自我设限**：明确引用某条约束（如"不能改测试文件"）而拒绝必要动作；本该动测试/配置时主动回避。
（理由：v2 的 LIT 只覆盖自我设限一半；一致性检验中 dvc-2266 的案例证明"字面理解任务"是更有洞察力的用法。）

**DEGEN 退化/无实质尝试**：中途放弃工具调用、重复输出相同文本段落自我合理化；补丁只有配置/复现脚本、无实质源码改动。**它是 no-attempt（empty_generation）子集的主分支**；在有补丁子集中仅用于"有补丁但零实质尝试"的极端情况。
信号：后半轨迹无 tool_calls；重复文本；patch 无源码文件改动。

## 次级维度（secondary，可多选，与主标签正交）

**HYG 变更卫生差**：final diff 含 debug print、临时文件、复现脚本、无关文件（.dvc、数据文件、mock）混入。
信号：git_patch 出现 print(/console.log、*.tmp、repro*.py、与 issue 无关的文件。

**TOOL 工具误用**：工具参数格式错误、str_replace old_str 多次不匹配、bash 命令拼错导致反复报错。**只作次级维度**，因为它解释"过程磕绊"不解释"补丁为何失败"。
信号：observation 反复出现参数错误/命令未找到/编辑未匹配。

**CONFAB 自我合理化**：observation 明确报错的情况下，agent 用文本宣称"已成功修复"。只作次级信号。
信号：文本声称成功 vs test_output/observation 报错，直接矛盾。

## 标注优先级（tie-break，v3）
0. 先判 EVAL-BROKEN（无测试信号 → 直接定，不再往下）。
1. 再判 DEGEN（无实质尝试则直接定）。
2. **零真实测试运行 → NOVER-INSUF**（硬信号，优先于 NARROW；EVAL-BROKEN 除外）。
3. 补丁与测试的关系：回归多 → NARROW-REGRESSIVE；目标测试挂但回归少（且 failed ≤4 集中）→ NARROW-INCOMPLETE。
4. 补丁位置与根因无关 → LOC-EXPLORE；找对地方但零有效编辑 → LOC-REPAIR。
5. 有"越修越坏"痕迹 → CASC；同一失败重复（放宽定义）→ RIGID-PERSEV；A-B 震荡 → RIGID-OSCIL。
6. 字面化理解（任务或约束）→ LIT-TASK / LIT-CONSTRAINT；长轨迹迷失 → CTX。
7. 主标签定后，扫一遍次级维度（HYG/TOOL/CONFAB）打勾。

## 标注流程
1. 读 issue（一句话概括需求）
2. 检查 test_output 有效性（无信号 → EVAL-BROKEN，停止）
3. 扫 action 序列（定位→复现→编辑→验证四阶段是否完整；真实测试是否跑过）
4. 看 final patch（diff stat：文件、增删行；有无卫生问题）
5. 看 test_output（passed/failed 数、失败测试名）确认失败原因
6. 按 tie-break 打主标签 + 次级维度（可多个）+ 一句话理由（中文，≤40 字）

## 未来工作（v3 未解决）
- **digest 升级**：加入 FAIL_TO_PASS / PASS_TO_PASS 划分（可从 SWE-bench 元数据获得），否则"回归 vs 目标"的区分在边界 case 永远靠猜（影响 NARROW-REGRESSIVE / INCOMPLETE 的判定）。
- **NOVER-INSUF 全量重估**：v3 定义下需在"有有效测试信号 + 零真实测试运行"的 131 条上重标，不能直接沿用 v2 的 30 条（它们全是 EVAL-BROKEN）。
- **LIT 定向检索**：LIT 在随机样本中极稀有（2/250），考虑 targeted retrieval 补充案例，或在论文中作为"罕见但有趣"类别报告。

## v2 → v3 变更日志（每条一句话理由）
1. 新增 step 0 **EVAL-BROKEN**：一致性检验发现 12 条分歧中 8 条实为评估中断——"失败"未被观测时任何失败模式标签都是猜测，必须先排除。
2. **NOVER-INSUF 提为硬信号**（优先于 NARROW）：6 条 NOVER 分歧的根因是 tie-break 优先级模糊；"未经验证的补丁"是独立且重要的失败模式。
3. **收紧 NARROW-INCOMPLETE**（目标测试可识别 + failed ≤4 + 集中）：它正在变成 v1 时代 NARROW 那样的废纸篓（第二标注者用了 26/50，precision 0.58）。
4. **放宽 RIGID-PERSEV 的"相同"定义**（同一文件+同一编辑意图+同类报错 ≥3 次）：v2 的逐字相同定义太窄导致漏判。
5. **LIT 重定义为"字面化理解"**并拆 LIT-TASK / LIT-CONSTRAINT：dvc-2266 案例证明"字面理解任务"是比"自我设限"更有解释力的用法。
6. **LOC 类的"查看"以成功 view 为准**：`[ERR]` 的 view 计数是 observation artifact（pilot §6.4 已预警），不得作为"找到文件"的证据。
7. 诚实记录：**v2 的 NOVER-INSUF（30 条）与 EVAL-BROKEN 完全混杂**——30 条全部无测试信号；v3 下该类的真实规模待重估。
