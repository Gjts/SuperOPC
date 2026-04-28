---
name: opc-business
description: One-person-company business advisory — dispatches business-advisory skill which owns the workflow
---
# /opc-business — 商业决策入口
用户显式触发一人公司商业活动。等价于自然语言 "这个想法怎么样" / "怎么定价" / "怎么获取第一批用户"。
## 动作
调用 `business-advisory` skill，传入 `$ARGUMENTS`。
business-advisory skill 会派发 `opc-business-advisor` agent，先做 Phase 0 子活动识别。当前支持 20 个商业场景：19 个 `references/business/<sub-activity>.md` playbook（validate-idea / mvp / find-community / first-customers / pricing / marketing-plan / seo / content-engine / grow-sustainably / company-values / minimalist-review / legal-basics / finance-ops / investor-materials / product-lens / user-interview / daily-standup / brand-voice / processize）+ 内置 `anti-build-trap` 硬门。需要专业执行时再委派 domain agent（seo / content / growth / pricing）。
## 入口要求
- `validate-idea` / `find-community` 等早期子活动**必须**先于编码推进（Anti-Build-Trap HARD-GATE）
- 跨活动的组合问题先让 advisor 识别首要子活动
## 参数
- `$ARGUMENTS` — 商业问题、产品描述、或子活动关键字
