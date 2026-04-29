# 기업공시 판단 어드바이저

상장법인 공시 담당자를 위한 AI 기반 공시 판단 도구

## 배포 구조

```
GitHub → Render (자동 배포)
```

## 환경변수 설정 (Render 대시보드)

| 변수명 | 설명 | 필수 |
|--------|------|------|
| `DART_KEY` | 금융감독원 DART OpenAPI 키 | ✅ |
| `GROQ_KEY` | Groq AI API 키 | ✅ |
| `LAW_KEY` | 법령 조회 키 | render.yaml에 기본값 포함 |

## 로컬 실행

```bash
pip install -r requirements.txt
DART_KEY=your_key GROQ_KEY=your_key python app.py
```

## API 엔드포인트

- `GET /` → index.html 서빙 (키 자동 주입)
- `GET /api/dart?...` → DART OpenAPI 프록시
- `GET /api/dart-search?keyword=...` → DART 공시통합검색 프록시
