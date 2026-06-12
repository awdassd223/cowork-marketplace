# econ-news-brief

경제뉴스 RSS를 수집해 CSV로 정리하고, 기업별 **호재/악재** 여부와 근거를 산출한
보고서를 만들어 **Notion 페이지**로 올리는 Cowork 플러그인입니다. 단발 실행과
매일 아침 자동 실행(scheduled task) 모두 지원합니다.

## 포함 스킬

- **econ-news-brief** — RSS 수집 → 기사 CSV + 기업 집계 CSV → 호재/악재 정밀 판정 → Notion 보고서

## 동작 개요

1. 한국경제·머니투데이·연합인포맥스·아시아경제 경제 RSS를 샌드박스에서 직접 수집
   (`skills/econ-news-brief/scripts/econ_news_report.py`)
2. 워치리스트(`assets/watchlist.txt`) 우선 + 자동 추출로 기사–기업 매칭, 키워드 1차 감성 산출
3. `parsed_*.json`을 근거로 🟢호재 / 🔴악재 / ⚪중립 정밀 판정 (오탐 제거)
4. `notion-create-pages`로 호재/악재 표·헤드라인·거시 메모를 담은 일자별 페이지 생성

## 산출물

- `articles_YYYYMMDD.csv` — 기사 단위
- `companies_YYYYMMDD.csv` — 기업 단위 집계
- `parsed_YYYYMMDD.json` — 정밀 판정용 원자료
- Notion 보고서 페이지

## 사용법

대화에서 "경제뉴스 호재 악재 브리핑 해줘"처럼 요청하면 실행됩니다.
직접 스크립트만 돌리려면:

```bash
python3 skills/econ-news-brief/scripts/econ_news_report.py <출력_폴더>
```

## 커스터마이즈

- **추적 기업 변경**: `skills/econ-news-brief/assets/watchlist.txt` (한 줄에 `대표명 | 별칭1, 별칭2`)
- **피드 변경**: `scripts/econ_news_report.py` 상단 `FEEDS` 딕셔너리
- **Notion 부모 페이지**: SKILL.md의 기본 예시 id를 본인 워크스페이스 페이지로 교체

## 면책

호재/악재는 투자 판단 참고용이며 매매 권유가 아닙니다.
