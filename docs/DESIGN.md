# Design - Mini Commerce Event Log Pipeline

> 플랫폼/데이터 엔지니어링 인턴 채용 과제 구현용 설계 문서  
> 기준일: 2026-05-25

## 1. 프로젝트 목적

미니 커머스 서비스에서 발생하는 사용자 행동 이벤트를 **생성 → 저장 → 분석 → 시각화**하는 작은 배치 파이프라인을 구현한다. 실시간 스트리밍이 아니라, 이벤트 로그가 어떻게 구조화되어 쌓이고 분석되는지 보여주는 것이 목표다.

핵심 요구사항은 JSON을 통째로 저장하지 않고, 분석 가능한 컬럼 단위로 정규화해 저장하는 것이다.

## 2. 요구사항 충족 방식

| 요구사항 | 구현 |
|---|---|
| 랜덤 이벤트 생성기 | Python `app/generator.py` |
| 이벤트 타입 2종 이상 | 5종: page_view / product_view / add_to_cart / purchase / error |
| 파일 또는 DB 저장 | PostgreSQL |
| JSON 통째 저장 금지 | `events` 테이블 컬럼 단위 저장 |
| 분석 쿼리 2개 이상 | 5종 SQL 집계 |
| `docker compose up` 단일 실행 | `docker-compose.yml` |
| 실행 후 자동 생성·저장 | `python -m app.main` |
| 시각화 | matplotlib PNG 5종 |

## 3. 이벤트 설계

| 타입 | 의미 | 비율 |
|---|---|---|
| `page_view` | 페이지 진입 | 45% |
| `product_view` | 상품 상세 조회 | 25% |
| `add_to_cart` | 장바구니 담기 | 12% |
| `purchase` | 구매 완료 | 8% |
| `error` | 에러 발생 | 10% |

실제 커머스 트래픽은 진입이 가장 많고 구매로 갈수록 줄어드는 퍼널 형태다. 균등 분포 대신 위 비율을 사용해 분석과 시각화에서 자연스러운 감소 흐름이 보이도록 했다. `error`는 운영 안정성 지표를 보여주기 위해 현실보다 높게 둔 10%로 설정했다.

이벤트 시각은 실행 시각 기준 최근 24시간에 랜덤 분산한다. 모든 시각은 UTC 기준 `TIMESTAMPTZ`로 저장하고, 시간대별 집계는 `date_trunc('hour', event_time)`를 사용한다.

## 4. 스키마

```sql
CREATE TABLE IF NOT EXISTS events (
    event_id      BIGSERIAL PRIMARY KEY,
    event_type    VARCHAR(20)  NOT NULL,
    user_id       VARCHAR(36)  NOT NULL,
    session_id    VARCHAR(36)  NOT NULL,
    event_time    TIMESTAMPTZ  NOT NULL,
    page_url      TEXT,
    product_id    VARCHAR(20),
    quantity      INTEGER,
    amount        NUMERIC(12,2),
    error_code    VARCHAR(20),
    error_message TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_time ON events (event_time);
CREATE INDEX IF NOT EXISTS idx_events_user ON events (user_id);
```

단일 `events` 테이블을 선택한 이유는 이벤트 로그가 하나의 타임라인에 모든 행동이 쌓이는 데이터이기 때문이다. 이벤트 타입별로 테이블을 나누면 전체 추이, 타입별 비율, 퍼널 전환 같은 통합 분석에서 반복적인 `UNION`이 필요하다. 이 규모에서는 단일 와이드 테이블과 타입별 nullable 컬럼이 더 단순하고 분석 친화적이다.

금액은 부동소수점 오차를 피하기 위해 `NUMERIC(12,2)`로 저장한다.

## 5. 파이프라인 흐름

```text
app/generator.py
  -> app/db.py
  -> app/analysis.py
  -> output/*.png
```

1. `db` 컨테이너가 `sql/init.sql`로 테이블과 인덱스를 만든다.
2. `pg_isready` healthcheck가 통과하면 `app` 컨테이너가 실행된다.
3. `app.main`이 이벤트 1,000건을 생성한다.
4. 기존 이벤트를 비우고 새 이벤트를 bulk insert 한다.
5. SQL 집계 5종을 실행한다.
6. matplotlib `Agg` 백엔드로 PNG 차트 5종을 `output/`에 저장한다.

## 6. 분석 쿼리

### 이벤트 타입별 발생 수

```sql
SELECT event_type, COUNT(*) AS cnt
FROM events
GROUP BY event_type
ORDER BY cnt DESC;
```

### 시간대별 이벤트 추이

```sql
SELECT date_trunc('hour', event_time) AS hour, COUNT(*) AS cnt
FROM events
GROUP BY 1
ORDER BY 1;
```

### 에러 이벤트 비율

```sql
SELECT
    ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'error') / COUNT(*), 2) AS error_pct
FROM events;
```

### 상품별 매출 Top 10

```sql
SELECT product_id, SUM(amount) AS revenue, COUNT(*) AS orders
FROM events
WHERE event_type = 'purchase'
GROUP BY product_id
ORDER BY revenue DESC
LIMIT 10;
```

### 퍼널 전환율

```sql
SELECT
    COUNT(*) FILTER (WHERE event_type = 'product_view') AS views,
    COUNT(*) FILTER (WHERE event_type = 'add_to_cart')  AS carts,
    COUNT(*) FILTER (WHERE event_type = 'purchase')     AS purchases,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE event_type = 'purchase')
        / NULLIF(COUNT(*) FILTER (WHERE event_type = 'product_view'), 0),
        2
    ) AS view_to_purchase_pct
FROM events;
```

## 7. 테스트 전략

`pytest`로 다음을 검증한다.

- 이벤트 가중치 합계가 1.0인지
- 정의된 이벤트 타입만 생성되는지
- 고정 seed와 대량 샘플에서 분포가 기대 비율 근처인지
- 타입별 필수 필드가 채워지는지
- 이벤트 시각이 timezone-aware인지

랜덤 테스트는 고정 seed, 충분한 샘플 수, 허용 오차를 함께 사용해 flaky하지 않게 작성했다.

## 8. 의도적으로 제외한 것

| 제외 항목 | 이유 |
|---|---|
| Kafka 등 실시간 스트리밍 | 과제 범위는 배치 파이프라인으로 충분 |
| Airflow 등 오케스트레이션 | 단일 배치 흐름에는 과함 |
| 실제 웹 서버 API | 이벤트는 시뮬레이션 생성이므로 수신 서버가 필요 없음 |
| 세션 상태머신 | 확률 기반 생성으로도 분석 목적 달성 가능 |
| 대규모 파티셔닝 | 1,000건 규모에서는 불필요 |

## 9. 확장한다면

- Kafka 기반 실시간 이벤트 수집
- 시간 기준 파티셔닝
- dbt 또는 배치 스케줄러 연동
- Grafana/Metabase 대시보드
- Kubernetes Job 기반 정기 실행
