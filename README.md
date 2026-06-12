# htlee-cowork-marketplace

Cowork(Claude Code) 자동화 플러그인을 모아 배포하는 **플러그인 마켓플레이스**입니다.

## 들어있는 플러그인

| 플러그인 | 설명 |
|----------|------|
| `lesson-writer-plugin` | 주제 하나로 구조화된 강의안(학습목표·핵심개념·실습·요약·과제)을 한국어 마크다운으로 작성 |

## 설치해서 쓰기

Claude Code / Cowork에서:

```
/plugin marketplace add <본인깃허브아이디>/cowork-marketplace
/plugin install lesson-writer-plugin@htlee-cowork-marketplace
```

마켓플레이스 내용이 바뀌면 사용자는 아래로 새로고침합니다:

```
/plugin marketplace update htlee-cowork-marketplace
```

## 폴더 구조

```
cowork-marketplace/
├── .claude-plugin/
│   └── marketplace.json        # 마켓플레이스 카탈로그 (플러그인 목록)
├── lesson-writer-plugin/       # 플러그인 1개
│   ├── .claude-plugin/
│   │   └── plugin.json         # 플러그인 메타정보
│   └── skills/
│       └── lesson-writer/
│           └── SKILL.md        # 실제 스킬 내용
└── README.md
```

## 플러그인 새로 추가하는 법

1. 새 플러그인 폴더를 만들고 그 안에 `.claude-plugin/plugin.json` 작성
2. 스킬은 `skills/<스킬이름>/SKILL.md` 로 넣기
3. `.claude-plugin/marketplace.json` 의 `plugins` 배열에 항목 추가
4. 커밋 후 깃허브에 push
