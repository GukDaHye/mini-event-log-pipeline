# Mini Commerce Event Log Pipeline

미니 커머스 사용자 행동 이벤트를 **생성 → 저장 → 분석 → 시각화**하는 배치 데이터 파이프라인.
`docker compose up --build` 한 번으로 전체 스택(앱 + PostgreSQL)이 실행됩니다.

**Stack** · Python · PostgreSQL · matplotlib · Docker Compose · pytest

---

## 1. 실행 방법

**필요한 도구**: Docker / Docker Compose

```bash
git clone https://github.com/GukDaHye/mini-event-log-pipeline.git
cd mini-event-log-pipeline
docker compose up --build
# DB 기동 → 스키마 생성 → 이벤트 1,000건 생성·저장 → 차트 생성까지 자동 수행
```

완료 후 `output/`에 차트 PNG가 생성됩니다.
스키마를 바꾼 뒤 재실행할 땐 `docker compose down -v`로 DB 볼륨을 초기화하세요.

**테스트 실행**

```bash
docker compose run --rm app pytest
```

---

## 2. 이벤트 설계

| 타입 | 의미 | 비율 |
|---|---|---|
| `page_view` | 페이지 진입 | 45% |
| `product_view` | 상품 상세 조회 | 25% |
| `add_to_cart` | 장바구니 담기 | 12% |
| `purchase` | 구매 완료 | 8% |
| `error` | 에러 발생 | 10% |

실제 커머스 트래픽은 진입이 가장 많고 구매로 갈수록 줄어드는 퍼널 형태입니다. 균등 분포(각 20%) 대신 위 비율을 사용해 시각화했을 때 전환 흐름이 한눈에 보이도록 설계했습니다. `error`는 운영 안정성 분석을 보여주기 위해 현실보다 높은 10%로 설정했습니다.

---

## 3. 스키마 설명

```sql
CREATE TABLE events (
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
```

이벤트 로그는 모든 행동이 하나의 타임라인에 쌓이는 데이터이므로, 이벤트 타입별로 테이블을 나누지 않고 **단일 테이블 + 타입별 nullable 컬럼**으로 설계했습니다. 이렇게 하면 퍼널 전환율처럼 여러 타입을 한 쿼리에서 비교할 때 `UNION` 없이 바로 집계할 수 있습니다.

**PostgreSQL을 선택한 이유**: `GROUP BY`, `date_trunc`, `FILTER` 같은 표준 SQL 집계가 강력하고, 금액을 `NUMERIC(12,2)`로 저장해 부동소수점 오차를 피할 수 있으며, `docker-entrypoint-initdb.d`로 초기 스키마 주입이 쉬웠기 때문입니다.

---

## 4. SQL 집계 분석

| 분석 | 내용 |
|---|---|
| 이벤트 타입별 발생 수 | 전체 트래픽 분포, 퍼널 폭 확인 |
| 시간대별 이벤트 추이 | `date_trunc('hour', event_time)` 기준 |
| 에러 이벤트 비율 | 전체 대비 에러 비중 |
| 상품별 매출 Top 10 | 구매 이벤트 기반 매출 집계 |
| 퍼널 전환율 | 조회→장바구니→구매 단계별 전환율 |

---

## 5. 결과 미리보기

| 차트 | 보여주는 것 |
|---|---|
| `event_type_counts.png` | 트래픽 분포·퍼널 폭 |
| `hourly_trend.png` | 시간대별 이벤트 추이 |
| `error_ratio.png` | 운영 안정성(에러 비율) |
| `top_products_revenue.png` | 매출 기여 상품 Top10 |
| `funnel.png` | 조회→장바구니→구매 전환 |

![funnel](output/funnel.png)

---

## 6. 구현하면서 고민한 점

**단일 테이블 vs 이벤트별 테이블 분리**
처음에 이벤트 타입마다 테이블을 나누는 방식을 검토했지만, 통합 분석(전체 추이, 퍼널 전환율)을 할 때마다 `UNION`이 필요해진다는 점에서 단일 와이드 테이블을 선택했습니다.

**DB 기동 타이밍 문제**
`depends_on`만으로는 컨테이너 시작만 보장하고 DB 접속 준비 완료는 보장하지 않습니다. `pg_isready` healthcheck + `service_healthy` 조건으로 앱 실행 자체를 막고, `db.py`에도 0.5초 간격 최대 20회 재시도 루프를 넣어 이중으로 방어했습니다.

**랜덤 테스트 안정화**
확률 기반 생성 로직을 테스트할 때 seed를 고정하지 않으면 가끔 실패하는 flaky 테스트가 됩니다. 고정 seed(`42`) + 50,000건 대량 샘플 + ±2%p 허용 오차를 조합해 통계적으로 안정적인 테스트를 작성했습니다.

**금액 타입**
`float`은 `0.1 + 0.2 = 0.30000000000000004` 같은 오차가 누적됩니다. Python에서는 `Decimal`, DB에서는 `NUMERIC(12,2)`로 맞춰 표현 불일치 없이 처리했습니다.

**의도적으로 제외한 것**
Kafka 스트리밍, Airflow 오케스트레이션, 세션 상태머신은 이 규모의 배치 파이프라인에서 복잡도만 높이고 핵심을 보여주는 데 기여하지 않아 제외했습니다.

---

## 7. 선택 과제 — Kubernetes

`k8s/` 디렉터리에 manifest 2개를 작성했습니다.

- `k8s/configmap.yaml` — 생성 건수·DB 접속 기본값
- `k8s/job.yaml` — 파이프라인 앱 실행

이벤트 생성기는 한 번 실행하고 종료되는 배치 작업이므로 상시 구동하는 `Deployment`가 아니라 `Job`을 선택했습니다. DB 비밀번호는 `Secret`으로 분리해 ConfigMap에 평문으로 노출되지 않도록 했습니다.

자세한 설계 의도 → **[docs/DESIGN.md](docs/DESIGN.md)**
