# BeACodeContributor

### 📖 项目简介

本项目旨在解决开发者入门开源贡献时「找 Issue 难、析需求难、定方案难」的痛点，通过全自动化流程为开发者精准匹配可贡献任务：

✨  助力开发者快速成为 GitHub开源项目 Contributor，利用LLM自动化分析 Issue， 自动化打通「Issue 获取 - 智能分析 - 飞书推送」全流程，降低开源项目贡献门槛，助力快速成长为 GitHub Contributor ✨

1.自动抓取 GitHub 平台上开源项目（如大数据相关 Apache Doris、Flink、Hive 等）的新增及历史 Issue，
2.借助 MCP（Model Context Protocol）协议同步拉取 Issue 详情与项目 README 信息，补充上下文增强理解；
3.通过大模型深度解析 Issue 核心需求，明确所需技术栈、实现思路及步骤
4.最终将结构化分析结果推送至飞书，让开发者高效筛选适配自身能力的贡献任务。

### 🚀 核心特性

- 精准 Issue 采集：支持批量抓取指定开源仓库的新增/历史 Issue，可自定义仓库列表与抓取范围，适配 GitHub API 规范确保稳定性。

- 智能需求解析：依托LLM拆解 Issue 需求，明确标注所需技术栈（如 Java、Python、Flink SQL、Doris 调优、Redis 等）、核心难点及分步解决方案，降低技术判断成本。

- MCP 上下文增强：通过 MCP 协议自动关联 Issue 详情与项目 README，补全项目背景、代码规范等信息，让分析结果更贴合项目实际场景。

- 飞书实时推送：结构化推送分析结果（含 Issue 标题、难度等级、技术栈、解决方案），实时同步优质贡献机会。

- 轻量可扩展：纯 Python 开发，模块化架构，易适配新大模型（OpenAI/豆包/通义千问等）、新增数据源或推送渠道，灵活满足个性化需求。

### 推送样例展示
<img src="https://github.com/user-attachments/assets/f6aaadb7-b1ea-4d94-8b31-42a5642caa61" width="300" style="border-radius: 8px; border: 1px solid #ddd;" />

<img src="https://github.com/user-attachments/assets/f6aaadb7-b1ea-4d94-8b31-42a5642caa61" width="300" />


