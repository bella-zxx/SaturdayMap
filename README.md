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

🚧 **AI Place Extraction Experiment**

小红书链接内容获取已完成三篇真实样本的初步验证：

> TikHub App V2 接口在单地点、多地点和多路线三篇样本上，均返回匹配的正文和图片地址。生产稳定性尚未验证。

当前开始地点提取实验，定义有原文依据的结构化输出和校验规则。实验见：

- `experiments/xhs-link-parser/`
- `experiments/place-extraction/`

## Docs

* `docs/PRODUCT.md` — 产品定位与核心设计
* `docs/PRD.md` — MVP 产品需求
* `docs/DECISIONS.md` — 产品与技术决策记录

## Status

Work in progress.
