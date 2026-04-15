# Evidence Gap Coach Backend (V1)

这是一个**先跑通后端决策链路**的最小可用版本，目标不是把 NLP 做到最强，而是先把这条链路跑通：

1. 导入官方 property facts（`Description_PROC`）
2. 导入 review 文本（`Reviews_PROC`）
3. 抽取 `property × amenity × facet` evidence
4. 计算 snapshot
5. 在线返回最值得追问的 follow-up question

## 推荐你先做的顺序

1. 跑 `scripts/bootstrap_from_csv.py`
2. 看 `/v1/properties/{property_id}/snapshot`
3. 看 `/v1/properties/{property_id}/followup`
4. 调 `app/taxonomy.py` 里的阈值和 TTL
5. 只有这套规则版稳定后，再加更复杂的抽取模型

## 本项目的核心文件

- `app/taxonomy.py`：**你最该先改的地方**
  - amenity / facet 定义
  - 每个 facet 的 `expected_rate`
  - `ttl_days`
  - `business_importance`
  - 问题模板与选项
- `app/official_facts.py`：把 `Description_PROC` 归一化成官方事实
- `app/evidence_extractor.py`：把 review 文本抽成 amenity/facet evidence
- `app/snapshot_builder.py`：把 evidence 汇总成 snapshot
- `app/followup.py`：在线选题逻辑

## 本地启动

```bash
python3 -m venv .venv
source .venv/bin/activate 
pip install -r requirements.txt
cp .env.example .env
python3 -m scripts.bootstrap_from_csv --description-csv "./Description_PROC.csv" --reviews-csv "./Reviews_PROC.csv"


uvicorn app.main:app --reload
```

启动后打开：

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/v1/properties/{property_id}/snapshot`
- `http://127.0.0.1:8000/v1/properties/{property_id}/followup`

## 一个最常用的请求

```bash
curl -X POST "http://127.0.0.1:8000/v1/properties/<PROPERTY_ID>/followup"   -H "Content-Type: application/json"   -d '{
    "draft_text": "The room was clean and the staff was kind. Breakfast was good.",
    "stay_date": "2026-02-05",
    "asked_facets": []
  }'
```

## 什么时候该升级到 Postgres + Alembic

本仓库默认 SQLite，是为了让你先把业务跑通。  
当你开始做以下事情时，就该换 Postgres + Alembic：

- 多人协作
- 每天/每小时重算 snapshot
- 需要审计 `followup asked / answered / skipped`
- 需要线上回滚 schema

这时候：
- `DATABASE_URL` 改成 Postgres
- 加 `alembic init alembic`
- 用 migration 管 schema，不再用 `Base.metadata.create_all()`

## 当前 V1 的刻意取舍

- review 没有真正的 `stay_id`，所以先把 **一条 review 当作一个独立 stay proxy**
- evidence extractor 先走规则，不走 LLM
- 不做前端
- 不做 bandit / learning-to-ask
- 不做复杂 season month 推理，只保留 seasonal flag

## 你下一步最值得做的 3 件事

1. 先把 `taxonomy.py` 调到能稳定命中你在 Broomfield / Monterey / Ocala 的直觉
2. 在 `followup_answers` 表里记录用户是否回答 / skip
3. 等你有 enough outcome data，再做 learning-to-ask
