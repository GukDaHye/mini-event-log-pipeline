# Kubernetes Manifest

이 디렉터리는 선택 과제용 Kubernetes 배포 manifest를 두는 위치입니다.

현재 프로젝트는 `docker compose up --build` 실행을 기본 제출 경로로 삼습니다. Kubernetes로 확장한다면 이벤트 생성기는 상시 실행되는 서버가 아니라 한 번 실행되고 종료되는 배치 작업이므로 `Deployment`보다 `Job`이 적합합니다.

- `configmap.yaml`: 생성 건수와 DB 접속 기본값
- `job.yaml`: 파이프라인 앱을 한 번 실행하는 배치 Job

`job.yaml`은 `commerce-postgres`라는 PostgreSQL Service와 `mini-commerce-pipeline-secret` Secret이 이미 있다고 가정합니다.
