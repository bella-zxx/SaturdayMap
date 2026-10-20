# 地点提取提示词 v0.1

输入是一篇已成功解析的笔记 JSON，字段为 `title`、`body`、`source_url`、`note_id`、`image_urls`。本阶段只从标题和正文提取；图片 OCR 尚未接入。

请返回严格的 JSON 对象，格式如下：

```json
{
  "places": [
    {
      "place_name": "原文出现的地点名",
      "city": "上海",
      "place_kind": "poi",
      "features": ["原文中的特点短句"],
      "recommendation": "原文中的推荐理由短句",
      "evidence": "包含地点名的原文片段",
      "source_url": "与输入完全一致的分享链接"
    }
  ]
}
```

规则：

1. 只输出原文明确提到、可作为收藏目标的地点。可以是店铺、场馆、街道或区域；不要把整条 City Walk 路线当作一个地点。
2. 地铁站和路口如果仅用作起点或方向提示，不算推荐地点。
3. `place_name` 必须能在标题或正文中找到。每个地点只出现一次。
4. `features`、`recommendation` 和 `evidence` 必须直接截取自标题或正文，保留原字词，不要编造或改写。没有明确推荐理由时，`recommendation` 用空字符串。
5. `evidence` 必填，并应包含地点名；`features` 可以为空数组。
6. 城市不明确时，`city` 用空字符串，不要猜测。
7. 每个地点的 `source_url` 必须与输入完全一致。不要把帖子短链替换为别的地址。
8. 只返回 JSON，不要附加解释或 Markdown。

本提示词偏保守：宁可留下待人工确认的漏提，也不编造地点或推荐理由。POI 坐标匹配和用户确认属于后续步骤。
