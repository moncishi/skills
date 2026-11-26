---
name: task-distill
description: >-
  Distill a completed task into reusable strategic direction, methodology steps,
  high-signal semantic anchor terms, constraints, and a copy-paste starter
  prompt. Use after finishing a task when the user asks to summarize reusable
  experience, extract direction/keywords/anchors, or says "提炼方法论",
  "提炼方向", "提取词条", "复盘成提示词", or "task-distill".
---

# Task Methodology & Anchor Distiller

After completing a task, distill what actually worked into compact, high-signal
reusable assets so future prompts immediately activate the right latent
knowledge in an LLM and avoid trial-and-error.

## Workflow

1. **Review the completed task** (grounded strictly in what happened in the session):
   - **Problem class**: Strip surface details to name the underlying problem type.
   - **Effective path**: Identify the reasoning steps, architecture, or debugging funnel that actually resolved it.
   - **Semantic anchors**: Extract exact domain terms, frameworks, algorithms, protocols, or mental models that steered the model toward high-quality output.
   - **Boundaries & pitfalls**: Capture verified constraints and dead ends worth avoiding next time.
2. **Abstract without losing precision**:
   - Generalize one-off file names or temporary variables into reusable patterns, while keeping concrete technical terms and verifiable constraints.
   - Reject generic filler (e.g., "think carefully", "write clean code", "check logs carefully"). Every bullet must earn its tokens.
3. **Output the distilled card** using the format below.
4. **Optional persistence**:
   - Only write to disk if the user asks to save the result.
   - If saving inside a project repository, check whether `sort-out.config.txt` exists first and follow its declared paths and local/tracked boundaries instead of inventing an ad-hoc file structure.

## Output Format

Keep the entire card concise and scannable so it fits cleanly into future context windows:

```markdown
### 1. 问题定位与方向（Direction）
- **问题归类**：<一句话定义这类问题的本质，如“分布式状态一致性排查 / 提示词语义锚定”>
- **解决主轴**：<本次最终奏效的核心切入点>

### 2. 核心方法论（Methodology）
1. <步骤 / 判断维度 1>
2. <步骤 / 判断维度 2>
3. <步骤 / 判断维度 3>

### 3. 高信噪比锚点词条（Semantic Anchors）
> 下次提问时优先带入这些关键词，用于激活模型对应领域的深层知识：
- `词条1`：适用场景 / 作用说明
- `词条2`：适用场景 / 作用说明
- `词条3`：适用场景 / 作用说明

### 4. 关键约束与避坑（Constraints & Pitfalls）
- **必须满足**：<核心前置条件或验收标准>
- **避免踩坑**：<本次验证行不通的做法或常见误区>

### 5. 下次直接复用的开局 Prompt（Starter Prompt）
> <3~5 句话，融合上面的“方向 + 方法论 + 锚点词条 + 约束”，留出 `[具体任务]` 占位符，可直接复制使用>
```
