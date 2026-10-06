# 变更卫生检查 (hygiene-check)

## 测什么
补丁的"清洁度"——与正确性正交的维度。针对失败类 **HYG（变更卫生差）**，
pilot 中它作主标签 0 次、作次标签 15 次（最高频共现）：复现脚本、mock 文件、
debug 打印常混入最终补丁。动机：能过的补丁 ≠ 好补丁。

## 检查项（`checker.py`，均为静态规则，只看 diff）
1. `touches_test_files`：补丁动了测试文件（`tests/`、`test_*.py`、`*_test.py`、
   `conftest.py`）。SWE-bench 类任务中测试由 test patch 单独施加，模型补丁
   不应碰测试。
2. `debug_leftovers`：**新增行**中含 `print(`、`breakpoint()`、`pdb.set_trace`、
   `ipdb`、`console.log`、`debugger`（只扫 `+` 行，不扫 `+++` 头）。
3. `junk_files`：新增的脚手架文件——basename 形如 `reproduce*`、`mock_*`、
   `debug_*`、`scratch*`，或扩展名 `.log/.tmp/.bak/.pyc/.orig/.rej`。
4. `only_junk`：补丁没有改动任何真实源码文件（极端：整个补丁只有
   `reproduce_error.py`，如 mypy-10658）。

## 清洁度分数（v0 启发式权重，引用前需在标注数据上校准）
100 起扣：only_junk −40；动测试文件 −20；每个含 debug 残留的文件 −15（上限 30）；
每个 junk 文件 −10（上限 20）；钳制到 [0, 100]。

## 运行 demo
```bash
cd hygiene-check
python3 demo.py
```
4 个 diff：dvc-9391（mock_test.py + reproduce_error.py + print 残留）、
moto-5835（reproduce_error.py + print 残留）、mypy-10658（只有 reproduce_error.py）、
moto-5835 的 **gold patch** 作对照。

## Demo 结果
| diff | score | 命中项 |
|---|---|---|
| dvc-9391 agent patch | 30 | 动测试文件、2 junk 文件、3 处 print 残留 |
| moto-5835 agent patch | 75 | 1 junk 文件、1 处 print 残留 |
| mypy-10658 agent patch | 50 | ONLY_JUNK（无源码改动） |
| moto-5835 GOLD patch | 100 | 干净（对照通过） |

## 局限
1. 权重是拍脑袋的 v0，需用双人标注数据校准后再引用。
2. `print(` 在 added 行即判为残留——正式版应排除字符串字面量内的误报
   （如 `msg = "print(x)"`）与确有必要的 logging。
3. "无关文件"（改了与 issue 无关的源码文件）需要 repo 结构知识，未实现；
   当前 junk 检测只覆盖脚手架类文件。
4. 测试文件判定是启发式；monorepo 中测试与源码混放时需按 repo 调整。
