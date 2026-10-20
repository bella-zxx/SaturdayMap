# AI 地点提取实验

## 目标

承接已验证的小红书链接解析结果，建立可复现的“笔记内容 → 地点候选”流程。遵守冻结的 [PRD](/docs/PRD.md)：一篇笔记可有多个地点，每个地点保留原始 `source_url`，推荐理由不能编造。

## 当前实现

- `pipeline.py prepare` 从 TikHub 成功响应中提取笔记 ID、标题、正文、图片地址和原始分享链接；不再调用任何付费接口。
- [PROMPT.md](PROMPT.md) 定义第一版模型输入和结构化输出规则。
- `pipeline.py validate` 对模型候选结果做基本校验：地点名、证据、特点和推荐理由须能在原文找到；来源链接须保持一致；重复地点会报错。
- 尚未绑定具体模型，也**没有**地点提取准确率。校验只检查字面依据，不能替代人工判断是否为真实 POI、推荐理由是否对应正确地点。

三篇笔记的首轮对话内试跑记录见 [INITIAL_REVIEW.md](INITIAL_REVIEW.md)。它是候选结果检查，不是模型准确率。

## 本机操作

API 原始响应保存在 `/private/tmp/saturdaymap-tikhub/`，不提交到 Git。准备规范化笔记示例：

```bash
python3 experiments/place-extraction/pipeline.py prepare /private/tmp/saturdaymap-tikhub/case-01-sdk-raw-5008xjwo.json --source-url https://xhslink.cn/o/2HAggjcl6B9 --out /private/tmp/saturdaymap-place-extraction/case-01-note.json
```

把规范化笔记和 [PROMPT.md](PROMPT.md) 交给待选模型，保存模型返回的纯 JSON 后运行：

```bash
python3 experiments/place-extraction/pipeline.py validate /private/tmp/saturdaymap-place-extraction/case-01-note.json /private/tmp/saturdaymap-place-extraction/case-01-result.json
```

下一步：选定模型与调用方式；为三篇样本制作人工核对清单，再记录地点准确率、漏提、误提和错误推荐理由。图片 OCR、POI 匹配和地图展示不属于本实验。
