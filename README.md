# Saturdaymap / 周六地图

> 把帖子里的喜欢，装进你的专属地图。

Saturdaymap（周六地图）是一款 **AI 目的地收藏工具**。

用户输入小红书等内容平台的帖子链接，Saturdaymap 自动识别帖子中提到的地点，并将它们保存到个人地图中，方便之后收藏、搜索和再次发现。

## Core Flow

```text
帖子链接
→ 内容解析
→ AI 地点提取
→ 地点匹配
→ 加入地图
```

## Current Stage

🚧 **Technical Feasibility Validation**

当前正在验证第一项关键技术问题：

> 能否仅通过小红书分享链接，稳定获取足够的帖子内容，用于后续 AI 地点提取。

实验见：

`experiments/xhs-link-parser/`

## Docs

* `PRODUCT.md` — 产品定位与核心设计
* `docs/PRD.md` — MVP 产品需求
* `docs/DECISIONS.md` — 产品与技术决策记录

## Status

Work in progress.
