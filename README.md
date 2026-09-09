# dry-harness · Astra

**Harness의 docs·단계 실행기·훅에 Dryforge 방식의 독립 검토를 결합한 GPT-6 Astra용 Codex 프레임워크입니다.**

[`csm-kr/harness-framework`](https://github.com/csm-kr/harness-framework)의 프로젝트 골격과 훅 역할을 Astra에 맞게 재구성했습니다. 짧은 스킬, 필요한 문서만 읽는 문맥 구성, 승인된 범위의 구현·검증·수정 지속이 기본입니다. 새 기획에서는 의도와 계획을 각각 독립 검토하고, 구현 후에는 누적 동작과 증거를 확인합니다.

## 포함된 구성

| 구성 | 역할 |
| --- | --- |
| `scripts/install.py` | 프로젝트에 스킬·실행기·기본 docs·Codex 훅 설치 및 병합 |
| `scripts/execute.py` | 새 Astra 세션으로 step 실행, 검증, 재시도·재개, 최종 독립 리뷰 |
| `skills/dry-harness/` | `ready` / `run` 기획·실행 안내 |
| `skills/dry-review/` | 의도·계획·phase 독립 검토와 별도 검토 CLI |
| `template/docs/` | PRD·USER_FLOW·ARCHITECTURE·ADR·RULES·ISSUES 기본 6개 |
| `template/AGENTS.md` | 문서를 선택적으로 읽도록 하는 짧은 프로젝트 라우터 |
| `template/.codex/` | Astra 기본 설정, 훅 등록과 Python 이벤트 처리기 |
| `docs-catalog/` | DB·API·SECURITY·STATE·UI 등 선택 문서 12종 |
| `examples/` | 실제 실행 가능한 Python phase 예제 |

0.1.0에서 빠졌던 실행기·훅·docs 설치 구성을 **0.2.0에 추가**했습니다. 기존 Harness의 Claude 전용 명령이나 상태 형식을 무조건 호환한다고 가정하지 않습니다. 변경 대응표는 [Astra 전환 기록](docs/ASTRA_ADAPTATION.md)에 있습니다.

## 설치

Python 3.10 이상, Git, 인증된 Codex CLI와 `gpt-6-astra` 접근 권한이 필요합니다. Python 외부 패키지와 Node는 필요하지 않습니다. 훅 설치·테스트는 macOS/Linux를 대상으로 합니다.

```bash
git clone https://github.com/csm-kr/dry-harness.git
cd dry-harness

# 실제 기존 프로젝트 경로로 바꾸세요.
python3 scripts/install.py /path/to/project
```

새 프로젝트에 설치하면 다음 구조가 생깁니다.

```text
your-project/
├── AGENTS.md
├── docs/
│   ├── PRD.md
│   ├── USER_FLOW.md
│   ├── ARCHITECTURE.md
│   ├── ADR.md
│   ├── RULES.md
│   └── ISSUES.md
├── scripts/execute.py
├── .agents/skills/
│   ├── dry-harness/       # 실행기 본체와 안내 포함
│   └── dry-review/        # 독립 검토 도구 포함
└── .codex/
    ├── config.toml
    ├── hooks.json
    ├── hooks/dry_harness.py
    └── dry-harness-install.json
```

기존 `AGENTS.md`, docs, 모델 설정, 다른 실행기는 유지합니다. 기존 `hooks.json`에는 누락된 이벤트 명령만 병합합니다. 수정된 자체 훅과 충돌하면 쓰기 전에 중단합니다. 전역 설정과 훅 신뢰 기록은 변경하지 않습니다. 디스크·권한 오류에 대한 파일시스템 트랜잭션은 아니므로 복사 도중 장애가 나면 원인을 해결한 뒤 `--update`로 재실행하세요.

```bash
# 업데이트: 스킬 파일과 수정되지 않은 패키지 관리 코드를 갱신
# 스킬 파일에 직접 추가한 내용은 먼저 보관하세요.
git pull --ff-only
python3 scripts/install.py /path/to/project --update

# 필요할 때만 선택 문서 추가; 이미 있는 docs는 유지
python3 scripts/install.py /path/to/project --update --doc DB --doc API

# 기존 골격을 전혀 건드리지 않고 스킬과 내부 도구만 설치
python3 scripts/install.py /path/to/project --skills-only
```

`.codex-plugin/plugin.json`은 플러그인 패키징 메타데이터입니다. 스킬 발견만으로 프로젝트 docs와 훅 파일이 생기는 것은 아니므로, 전체 골격은 위 설치기로 주입합니다.

## Astra와 훅 시작

**대상 프로젝트 루트에서** 새 세션을 시작하세요.

```bash
cd /path/to/project
codex --model gpt-6-astra --enable hooks
```

Codex 앱에서는 Astra를 선택합니다. 스킬은 이미 열린 대화의 모델을 바꾸지 않습니다. 새로 생성하는 `.codex/config.toml`은 Astra와 hooks를 설정하지만, 기존 config는 보존하므로 그 설정과 충돌하면 명시적인 CLI 옵션이나 사용자의 프로젝트 설정을 따릅니다. 실행기·리뷰 CLI는 기본 모델을 Astra로 지정하며 자동 fallback을 하지 않습니다.

**`/hooks`에서 새로 추가되거나 변경된 훅을 확인하고 신뢰하세요.** Codex는 프로젝트 신뢰와 훅 정의의 신뢰 상태를 따릅니다. 설치 완료와 호스트에서 훅이 활성화된 상태는 다릅니다. 설치기나 실행기는 신뢰 기록을 대신 승인하거나 우회하지 않습니다. [공식 Codex 훅 안내](https://learn.chatgpt.com/docs/hooks)

| 이벤트 | Astra용 동작 |
| --- | --- |
| `SessionStart` | 필요한 문서·완료 조건만 짧게 안내하고, 주기가 된 경우에만 점검 알림 |
| `SubagentStart` | 맡은 작업 안에서 간결한 구현을 유지하도록 짧게 안내 |
| `UserPromptSubmit` | `$dry-harness mode lean` / `$dry-harness mode off`로 세션 안내 모드 전환 |
| `PreToolUse` | 위험 명령·흔한 `.env` 출력 방지, 데이터/권한 변경 시 검증 안내 |

원본의 TDD 훅은 테스트 파일 이름만 보고 코드 편집을 막던 방식에서 **실제 검증을 돕는 안내**로 바꿨습니다. 완료 판정은 실행기의 검사와 독립 리뷰가 담당합니다. 매 종료 전체 테스트를 실행하는 Stop 훅은 넣지 않았습니다. 주간 알림은 `DRY_HARNESS_WEEKLY_DAYS=0`으로 끌 수 있습니다.

훅은 모든 셸 표현이나 비밀 유출 경로를 막는 보안 경계가 아닙니다. 구체적인 차단 패턴과 동작은 [훅 안내](skills/dry-harness/references/hooks.md)에 있습니다.

## 1. 기획 정리: ready

```text
$dry-harness ready로 plan.md를 읽고 구현 명세와 실행 계획을 만들어줘.
이미 결정한 정책은 유지하고, 구현에 꼭 필요한 미결정 사항만 질문해줘.
기본 docs를 채우고 scripts/execute.py가 실행할 phase JSON까지 만들어줘.
```

`ready`는 대화에서 사용하는 작업 모드입니다. 템플릿에는 확정되지 않은 정책을 미리 넣지 않습니다. 관련 docs를 실제 결정으로 채우고, 필요한 경우 `docs/SPEC.md`를 추가합니다. 번들 실행기용 계획은 `phases/<name>.json`으로 작성합니다.

중요한 새 기획·정책 변경은 작성하지 않은 리뷰어가 두 관점으로 확인합니다.

| 검토 | 입력 | 확인하는 것 |
| --- | --- | --- |
| 의도 | 관련 사용자 원문·결정 기록·요구사항 | 임의로 정한 정책, 누락된 결정 |
| 계획 | 완성된 명세·phase·관련 코드 | 요구사항 연결, 의존성, 검증의 실효성 |

기획만 요청하면 사용 가능한 문서까지 마무리합니다. 구현도 이미 허용했다면 필요한 검토 후 계속 진행하며, 이미 결정한 내용에 새 승인을 요구하지 않습니다. 작은 수정마다 새 phase나 두 기획 검토를 강제하지 않습니다.

## 2. 구현·검증·재개: execute

실제 실행에는 **대상 프로젝트 루트의 Git 저장소와 초기 커밋**이 필요합니다. 먼저 실제 프로젝트 문서·명령을 준비하세요. 초기 커밋에는 시크릿과 개인 자료를 포함하지 않습니다.

```bash
cd /path/to/project

# 형식·경로 확인: 모델 호출, Git·상태 쓰기 없음
python3 scripts/execute.py phases/01-core.json --dry-run

# 한 단계씩 실행; 한 단계 성공은 phase 완료와 다릅니다.
python3 scripts/execute.py phases/01-core.json --max-steps 1

# 남은 단계 → 최종 통합 검사 → 읽기 전용 독립 리뷰
python3 scripts/execute.py phases/01-core.json

# 실패 원인 확인 후 재시도 (기본 최대 3회)
python3 scripts/execute.py phases/01-core.json --retry

# 모든 step이 검증된 상태에서 독립 리뷰
python3 scripts/execute.py phases/01-core.json --review

# 외부에서 코드/증거를 고친 뒤 재검증·리뷰
python3 scripts/execute.py phases/01-core.json --reverify --review
```

대화에서 실행과 실패 수정을 함께 맡겨도 됩니다.

```text
$dry-harness run으로 phases/01-core.json을 실행해줘.
구현·검증·실패 수정·독립 리뷰까지 완료하고 실제 외부 증거가 부족하면 구체적으로 알려줘.
```

각 step은 새 `codex exec --model gpt-6-astra` 세션입니다. 모델이 완료를 보고해도 실행기가 선언된 `checks`를 별도 프로세스로 실행하고 `evidence`를 확인해야 완료로 기록합니다. 마지막에는 모든 phase 검사를 통합된 코드에 다시 적용한 뒤 별도 읽기 전용 리뷰를 실행합니다.

리뷰에서 수정 요청이 나오면 조정자가 해당 문제를 고친 뒤 `--reverify --review`로 이어갑니다. 실행기는 완료 상태를 조작하거나 요구사항을 약화하는 변경을 거부합니다. 정당하게 명세를 바꿨다면 내용을 검토한 후 `--reset`으로 새 계약의 실행을 시작합니다. 실패한 코드 변경은 자동 삭제하지 않습니다.

상태·로그는 `$(git rev-parse --absolute-git-dir)/dry-harness/<phase-id>/`에 보관합니다. 일반적으로 `.git/dry-harness/`이며 Git worktree에서도 해당 Git 메타데이터 경로를 사용합니다. 원시 로그에 프로젝트 내용이 들어갈 수 있으므로 공개하지 마세요. 코드와 선언된 증거가 바뀌면 기존 완료 판정을 재사용하지 않습니다.

| 종료 코드 | 의미 |
| --- | --- |
| `0` | 명령 성공. `--dry-run`·`--max-steps`에서는 전체 완료를 뜻하지 않음 |
| `1` | 구현/검사 실패 또는 리뷰 수정 요청 |
| `2` | 필수 입력·환경·증거 부족, 잘못된 설정 등 |
| `130` | 사용자 중단 |

기본 제한은 호출/검사당 1800초, step당 3회입니다. `--timeout`, `--attempts`, `--model`로 명시 변경할 수 있습니다. blocked 결과는 무조건 반복하지 않습니다. 자동 commit·push·배포는 하지 않습니다.

**phase 형식과 전제는 [실행기 계약](skills/dry-harness/references/executor.md)을 확인하세요.** 각 검사는 argv 배열이고 현재 사용자 권한·환경으로 실행되므로, 프로젝트에서 검토한 로컬 검증 명령을 넣으세요. 원본 Harness의 `phases/<name>/index.json` 형식은 자동 변환하지 않습니다. 기존 실행기가 있으면 유지하거나 명시적으로 새 형식으로 옮깁니다. 실행 범위는 한 phase이며 phase 간 선행 조건은 조정자가 확인합니다.

## 3. 독립 리뷰만 실행

```text
$dry-review로 현재 phase의 누적 변경을 독립 검토해줘.
명세, 실제 코드와 테스트 결과를 대조하고 파일은 수정하지 마.
```

별도 CLI로 실행할 수도 있습니다. `--input`은 프로젝트 안의 UTF-8 파일이며 반복할 수 있습니다.

```bash
python3 .agents/skills/dry-review/scripts/review.py plan \
  --input docs/PRD.md --input phases/01-core.json

python3 .agents/skills/dry-review/scripts/review.py intent \
  --input docs/review-input.md --input docs/PRD.md

python3 .agents/skills/dry-review/scripts/review.py phase \
  --input phases/01-core.json --input docs/validation/01-core.md
```

의도 검토에는 필요한 원문 발언만, phase 검토에는 기준 커밋/변경 범위와 실제 증거를 제공하세요. 출력은 `verdict`, `summary`, `findings` JSON입니다. `clear`는 검사한 범위에서 blocking이 없다는 뜻이며 전체 제품 완성 보장은 아닙니다. 종료 코드는 `clear=0`, `changes_required=1`, `blocked/실행불가=2`입니다.

독립 검토는 작성에 참여하지 않은 새 세션에서 수행합니다. 새 리뷰어를 실행할 수 없으면 미수행이라고 표시합니다. 실제 API·기기 관찰을 모델의 추측이나 단위 테스트로 대체하지 않습니다. 읽기 전용 sandbox도 비밀정보 읽기를 차단하는 별도 격리 장치는 아닙니다.

## 예제 실행

`examples/hello.json`은 stdlib 함수 하나와 테스트를 만드는 작은 실행 예제입니다. 다른 제품과 섞지 않도록 **별도 임시 프로젝트**를 준비하고 전체 설치 후 `examples/hello.json`, `examples/hello-spec.md`를 복사하세요. 초기 Git 커밋 뒤 다음을 실행합니다.

```bash
python3 scripts/execute.py examples/hello.json --dry-run
python3 scripts/execute.py examples/hello.json
```

## Astra에 맞게 바꾼 점

[Eric Provencher의 Astra 글](https://x.com/pvncher/article/2095991462416490862)에 따라 스킬 설명을 짧게 하고, 관련 문서만 읽으며, 승인된 구현·검증·수정까지 이어가도록 했습니다. 기존 명세를 한 곳에서 관리하고, 작은 변경에 전체 문서 읽기·재승인·무조건적인 테스트 순서를 요구하지 않습니다.

원본의 기본 docs 6개와 선택 카탈로그 역할은 유지하면서 특정 웹 스택 기본값, 모든 docs 강제 주입, 반복 이슈의 자동 규칙 승격, 전역 모드 변경을 제거했습니다. 실제 변화의 범위와 근거는 [전환 기록](docs/ASTRA_ADAPTATION.md)을 확인하세요.

## 검증과 출처

```bash
python3 -m unittest discover -s tests -v
```

오프라인 테스트는 임시 프로젝트와 가짜 모델 응답을 사용합니다. 실제 Astra 호출은 별도 스모크 검증입니다. [검증 기록](docs/VALIDATION.md)에 실행한 범위와 한계를 적습니다. Astra의 성능·비용 우위를 측정한 벤치마크는 아닙니다.

설계 출처: [csm-kr/harness-framework](https://github.com/csm-kr/harness-framework), [jha0313/harness_framework](https://github.com/jha0313/harness_framework), [Dryforge](https://github.com/prekuter/dryforge). 이 저장소의 Python 도구와 Astra 지침·문서 템플릿은 새로 작성했으며 원본의 전체 소스나 Ponytail 번들을 재배포하지 않습니다. 원 프로젝트 또는 OpenAI의 공식 배포판은 아닙니다. 이 저장소에서 작성한 내용은 [MIT](LICENSE), 링크된 자료에는 각각의 이용 조건이 적용됩니다.
