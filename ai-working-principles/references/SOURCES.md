# 准则参考来源

本技能是结合用户偏好编写的原创协作准则。以下资料提供部分条款的风险背景和实践依据，不代表这些机构逐条制定或认可本技能。查阅日期：2026-10-15。

| 来源 | 发布日期或版本 | 支持的内容与适用范围 |
| --- | --- | --- |
| [NIST AI 600-1：Generative Artificial Intelligence Profile](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) | 2024-07，NIST AI 600-1 | 将自信地产生错误内容、错误逻辑或伪造引文列为风险。作为区分事实与推断、核实来源和承认未知的依据；不意味着标注置信度即可保证准确。 |
| [OWASP：LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) | LLM01:2025 | 网页、文件等外部内容可能包含间接提示注入。支持限制外部内容改写任务与权限的能力；不将用户明确授权遵循的正常项目说明一概视为恶意。 |
| [OpenAI Developers：Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex) | 2026-05-09 | 以目标、约束和相应验证证据判断完成，验证受阻时如实报告。仅借鉴其代理实践，不要求使用 Codex Goals，也不将其产品机制推广为所有 AI 的机制。 |
| [OWASP：Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) | 持续维护的文档；页面未标固定发布日期或版本 | 支持复用现有日志机制、可配置级别、记录有用事件、脱敏和检查日志副作用。具体诊断位置、日志量及硬件时序要求，仍须依据项目实际情况判断。 |
| [OpenAI：Expanding on what we missed with sycophancy](https://openai.com/index/expanding-on-sycophancy/) | 2025-05-02 | 针对一次 GPT-4o 更新的迎合问题复盘。作为如实纠正错误前提、避免以取悦用户代替真实性的案例依据，不推断所有模型具有相同行为。 |

资料时效核对、默认简洁、框架选择、减少重复确认、来源数量、范围控制和调试流程，是结合用户已确认要求整理的协作条款。更新这些条款时，应核对原文是否仍可访问、内容是否改变，以及其适用版本与当前任务是否一致。规则用于降低错误概率，不能保证消除幻觉、过时信息或验证遗漏。
