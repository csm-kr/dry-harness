# Astra 전환 기록

기준 원본은 사용자가 지정한 [csm-kr/harness-framework](https://github.com/csm-kr/harness-framework/tree/fc86b4db1bd66c5731a632e149279a3b45576824) 커밋 `fc86b4db1bd66c5731a632e149279a3b45576824`입니다. 2026-09-09에 `template/`, `hooks/`, `docs-catalog/`의 실제 파일을 확인했습니다. 기본 docs 6개·선택 문서 12종·훅 역할을 가져와 Astra용으로 재작성했습니다.

| 원본 구성 | dry-harness Astra 적용 |
| --- | --- |
| `template/CLAUDE.md` | `template/AGENTS.md`: 짧은 정본 라우터와 완료 조건, 관련 문서만 읽기 |
| `template/docs/PRD.md` | 사용자의 목표·범위·수용 조건을 기록; 가상의 제품 결정을 기본값으로 두지 않음 |
| `USER_FLOW.md` | 실제 목표의 성공·실패·취소·복귀 분기와 증거 연결 |
| `ARCHITECTURE.md` | 특정 웹 프레임워크·ORM 가정 없이 실제 경계·데이터 흐름·명령 기록 |
| `ADR.md` | 실제 결정과 근거·트레이드오프만 기록 |
| `RULES.md` | 영향을 설명할 수 있는 프로젝트 제약; 테스트 이름만 보는 TDD 강제 제거 |
| `ISSUES.md` | 재현·영향·차단 조건·해결 증거 기록; 3회 반복을 자동 불변 규칙으로 승격하지 않음 |
| `docs-catalog/` 12종 | 동일 문서 주제를 선택적으로 설치; 불필요한 상세를 매 step에 주입하지 않음 |
| `template/scripts/execute.py` | 새 Python 실행기: Codex Astra, 별도 검사, 상태 소유권, 내용 기반 재검증, 최종 독립 리뷰 |
| `danger-guard.js` | PreToolUse의 파괴 명령·흔한 비밀 출력 패턴 검사; 일반 상대경로 정리는 허용 |
| `tdd-guard.js` | 데이터·권한 변경에 필요한 검증 안내; 테스트 파일 유무로 편집을 차단하지 않음 |
| `ponytail-activate.js` | SessionStart에 짧은 단순성 지침; 긴 페르소나·상태줄 설치 권유 제거 |
| `ponytail-subagent.js` | SubagentStart에 동일한 짧은 지침 |
| `ponytail-mode-tracker.js` | UserPromptSubmit의 세션별 lean/off; 일반 요청에는 추가 주입 없음 |
| `weekly-check.js` | 프로젝트별 주기 안내만 유지; 감사/테스트 자동 실행 없음 |
| `.claude/settings.json`의 `.env` 포괄 차단 | `.codex` 훅의 흔한 비밀 출력 방지; 필요한 환경 설정 편집 자체는 허용 |

여섯 훅 역할은 `template/.codex/hooks/dry_harness.py` 한 파일에 모았습니다. Node/Ponytail 전역 상태가 필요하지 않습니다. 훅의 의미는 [공식 Codex Hooks 문서](https://learn.chatgpt.com/docs/hooks)의 이벤트·입력·출력·신뢰 형식과 대조했습니다. 훅 신뢰는 설치와 별도로 호스트에서 처리되며 우회하지 않습니다.

Astra 조정 근거는 [Rethinking skills and prompts for GPT-6 Astra](https://x.com/pvncher/article/2095991462416490862)의 짧은 설명, 점진적 문맥 로딩, 적절한 결정 경계, 완료까지의 지속성입니다. Dryforge에서는 의도와 완성된 계획을 작성자와 분리해 검토하는 방식을 결합했습니다. 원본의 스킬·훅 전체를 복제하거나 Astra의 성능 우위를 주장한 것이 아닙니다.

원본 Harness의 phase index와 이번 실행기의 JSON 계약은 서로 다릅니다. 기존 프로젝트에서는 이미 있는 실행기를 보존합니다. 새 실행기를 쓸 때는 사용자 요구·검증 조건을 보존해 명시적으로 변환합니다. 자동 원격 push·배포와 범용 cross-phase 스케줄러는 포함하지 않습니다.
