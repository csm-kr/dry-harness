# dry-harness · Astra

**Harness의 명세·단계 실행에 Dryforge에서 착안한 독립 검토를 결합한 GPT-6 Astra용 Codex 스킬 패키지입니다.**

기획을 구현 가능한 계약으로 정리하고, 선택한 phase를 구현·검증·수정까지 이어갑니다. 새 기획에서는 의도와 계획을 각각 독립 검토하고, 구현이 끝나면 단계 전체의 동작과 증거를 검토합니다.

이 저장소는 재사용 가능한 스킬과 Python 도구만 제공합니다. 기존 Harness 실행기가 있으면 그대로 사용하며, 없으면 Codex가 단계별로 실행합니다. 자체 범용 step 실행기나 자동 배포기는 포함하지 않습니다.

## 설치

Python 3.10 이상이 필요합니다. CLI 독립 검토에는 인증된 Codex CLI와 `gpt-6-astra` 접근 권한도 필요합니다. Python 외부 패키지는 필요하지 않습니다.

```bash
git clone https://github.com/csm-kr/dry-harness.git
cd dry-harness

# /path/to/project를 실제 기존 프로젝트 경로로 바꾸세요.
python3 scripts/install.py /path/to/project
```

다음 두 스킬을 프로젝트에 설치합니다. 프로젝트 문서, `AGENTS.md`, 모델 설정, 전역 플러그인 캐시는 수정하지 않습니다.

```text
your-project/.agents/skills/
├── dry-harness/    # ready / run 안내와 필요한 참조 문서
└── dry-review/     # 독립 검토 안내와 선택적 CLI 도구
```

설치 후 대상 프로젝트에서 **새 Codex 세션**을 시작하세요. 같은 이름의 스킬이 이미 있으면 설치가 중단됩니다. 업데이트는 패키지에 속한 파일을 덮어쓰므로, 해당 파일에 직접 추가한 내용이 있다면 먼저 보관하세요. 별도로 추가한 파일은 유지됩니다.

```bash
git pull --ff-only
python3 scripts/install.py /path/to/project --update
```

저장소 루트의 `.codex-plugin/plugin.json`은 Codex 플러그인 패키징용입니다. 위 프로젝트 설치와 플러그인 설치를 함께 적용할 필요는 없습니다. 이 안내는 CLI 버전에 따라 달라지는 마켓플레이스 명령 대신 프로젝트 설치를 기본으로 사용합니다.

## Astra로 시작하기

```bash
cd /path/to/project
codex --model gpt-6-astra
```

Codex 앱에서는 모델 선택기에서 Astra를 선택한 뒤 실행하세요. **스킬 문구는 이미 열린 대화의 모델을 바꾸지 않습니다.** 이 저장소의 개발용 `.codex/config.toml`과 독립 검토 CLI의 기본값은 `gpt-6-astra`입니다. 대상 프로젝트의 모델 설정은 설치기가 변경하지 않습니다. Astra가 사용 불가하면 자동으로 다른 모델로 바꾸지 않습니다.

## 사용법

### 1. 기획 정리: ready

```text
$dry-harness ready로 plan.md를 읽고 구현 명세와 실행 계획을 만들어줘.
이미 결정한 정책은 유지하고, 구현에 꼭 필요한 미결정 사항만 질문해줘.
```

기존 문서가 있으면 그 문서를 정본으로 사용합니다. 새 프로젝트에서는 기본적으로 `docs/SPEC.md`에 행동 계약을, `phases/<name>.md`에 단계 계획을 작성합니다. `ready`는 스킬의 작업 모드이며 터미널 명령이 아닙니다.

중요한 새 기획·정책 변경은 작성하지 않은 별도 리뷰어가 두 번 확인합니다.

| 검토 | 입력 | 확인하는 것 |
| --- | --- | --- |
| 의도 | 관련 사용자 발언·결정 기록·요구사항 | 임의로 정한 제품 정책, 누락된 결정 |
| 계획 | 완성된 명세·단계 계획·관련 코드 | 요구사항 누락, 실행 불가능한 계약, 부족한 검증 |

검토 결과는 조정자가 판단합니다. 제안을 모두 강제하거나, 이미 승인된 내용을 다시 승인받는 절차를 만들지 않습니다. 기획만 요청하면 문서 작성까지 완료하고, 구현까지 허용했다면 필요한 검토 후 계속 진행합니다.

### 2. 구현과 재개: run

```text
$dry-harness run으로 phases/01-core.md를 구현해줘.
동작 확인과 영향받는 테스트, 실패 수정, phase 독립 검토까지 완료해줘.
```

```text
$dry-harness run으로 현재 phase를 재개해줘.
마지막 검증 이후 변경된 코드와 남은 차단 사유부터 확인해줘.
```

기존 실행기가 있으면 해당 저장소의 명령·상태 규칙을 따릅니다. 없다면 Codex가 단계별 결과와 검증 증거를 phase 문서에 기록합니다. 에이전트의 완료 메시지만으로 통과 처리하지 않으며, 실제 API·기기·사용 기간 관찰이 필요한 작업은 그 증거가 있어야 완료됩니다.

일상적인 작은 수정은 평소처럼 요청하세요. 매번 새 phase나 두 번의 기획 검토를 만들지 않습니다.

### 3. 검토만 하기: review

```text
$dry-review로 현재 phase의 누적 변경을 독립 검토해줘.
명세, 실제 코드와 테스트 결과를 대조하고 파일은 수정하지 마.
```

작성 에이전트가 이 요청을 받으면 새로운 읽기 전용 리뷰어를 사용합니다. 새 리뷰어를 실행할 수 없는 환경에서는 검토가 수행되지 않았다고 표시합니다. 같은 에이전트가 다시 읽은 것을 독립 검토로 간주하지 않습니다.

## 독립 검토 CLI

호스트의 하위 에이전트를 사용할 수 없거나, 별도 Codex 세션으로 검토를 재현하려면 설치된 도구를 사용할 수 있습니다. 입력 파일은 프로젝트 안의 UTF-8 파일이며, `--input`을 반복해 지정합니다.

```bash
cd /path/to/project

# 입력 경로 확인: 모델 호출과 파일 쓰기 없음
python3 .agents/skills/dry-review/scripts/review.py plan \
  --input docs/SPEC.md --input phases/01-core.md --dry-run

# 새 Astra 세션에서 계획 독립 검토
python3 .agents/skills/dry-review/scripts/review.py plan \
  --input docs/SPEC.md --input phases/01-core.md

# 의도 검토: 필요한 발언·결정만 별도 파일로 준비
python3 .agents/skills/dry-review/scripts/review.py intent \
  --input docs/review-input.md --input docs/SPEC.md

# phase 검토: 계약, 실제 diff 또는 비교할 기준, 관찰 결과를 함께 제공
python3 .agents/skills/dry-review/scripts/review.py phase \
  --input phases/01-core.md --input docs/validation/01-core.md
```

phase의 입력에는 검토할 변경 범위(예: 기준 커밋과 현재 변경), 관련 명세 경로와 검증 증거를 적으세요. 리뷰어는 필요한 실제 코드도 읽습니다. 의도 검토 입력은 관련 원문 발언을 유지하되 불필요한 사적 대화는 넣지 마세요. 입력과 필요한 코드가 Codex 모델에 전달됩니다. `read-only`는 쓰기 제한이며 비밀정보 읽기를 차단하는 별도 격리 장치는 아닙니다.

출력은 `verdict`, `summary`, `findings` JSON입니다. 각 finding에는 심각도, 위치, 근거, 영향, 개선 방향이 포함됩니다.

| 종료 코드 | 의미 |
| --- | --- |
| `0` | 검토 범위에서 blocking 발견 없음. `--dry-run`에서는 경로 검사 성공만 의미 |
| `1` | 수정이 필요한 blocking 발견 |
| `2` | 증거 부족, 인증·모델·입력 오류 또는 시간 초과로 검토 불가 |

기본 시간 제한은 600초입니다. `--timeout 1200`으로 바꿀 수 있습니다. 모델을 의도적으로 바꿀 때만 `--model <model-id>`를 지정하세요. 호출 실패 시 재시도나 모델 대체는 자동으로 수행하지 않습니다. 도구는 `read-only` sandbox와 새 세션을 사용하고, 검사한 결과의 형식·판정 일관성도 확인합니다. JSON의 근거가 사실인지는 조정자가 실제 자료와 대조해야 합니다.

원시 CLI 로그와 임시 결과는 비공개 임시 디렉터리에 생성한 뒤 제거합니다. 이 도구는 프로젝트 완료 상태를 바꾸거나 커밋·push하지 않습니다. Codex 자체의 인증·호스트 정책은 그대로 적용됩니다.

## 기존 Harness / Dryforge 프로젝트에 적용

1. 현재 `AGENTS.md`가 가리키는 명세·계획 경로와 실행기를 유지합니다.
2. `ready`는 기존 결정을 다시 묻지 않고, 바뀌는 요구사항만 갱신합니다.
3. 기존 phase 실행과 검증 뒤에 `dry-review`를 연결합니다. 이미 독립 누적 검토가 있으면 중복 추가하지 않습니다.
4. `.dryforge`와 `docs`를 동시에 수정하는 두 개의 정본을 만들지 않습니다. 이전 문서를 보관할 경우 현재 정본으로 향하는 링크를 남깁니다.

프로젝트 전용 스킬이 같은 역할을 맡고 있다면 위 지침을 그 스킬에 통합해도 됩니다. 사용하지 않는 스킬을 함께 설치할 필요는 없습니다.

## 글에서 반영한 내용

Eric Provencher의 [Rethinking skills and prompts for GPT-6 Astra](https://x.com/pvncher/article/2095991462416490862)를 읽고 다음과 같이 적용했습니다.

- 짧은 스킬 설명과 적용 상황에 맞춘 선택.
- `SKILL.md`는 짧은 안내로, 기획·실행 세부는 필요할 때만 읽는 참조 문서로 분리.
- 매 수정마다 전체 문서 읽기·전체 테스트·새 승인을 요구하는 규칙 제거.
- 구현 레시피보다 완료 조건을 정의하고, 허용된 범위의 검증·수정까지 계속 진행.

이는 글의 조언을 적용한 설계입니다. Astra의 성능·비용 우위를 측정한 벤치마크는 아닙니다. 실제 검증 범위는 [검증 기록](docs/VALIDATION.md)에 적습니다.

## 개발·검증

```bash
python3 -m unittest discover -s tests -v
```

테스트는 임시 프로젝트와 가짜 CLI 응답을 사용하며 실제 모델을 호출하지 않습니다. 설치 충돌·경로 이탈·업데이트, 검토 판정·CLI 실패·모델 인자 전달을 검사합니다.

## 출처와 라이선스

[jha0313/harness_framework](https://github.com/jha0313/harness_framework)의 단계 실행 방식과 [Dryforge](https://github.com/prekuter/dryforge)의 작성자와 분리된 의도·산출물 검토에서 착안했습니다. 이 저장소의 스킬과 Python 도구는 새로 작성했으며, 두 프로젝트의 소스·스킬 본문을 복사해 배포하지 않습니다. 원 프로젝트의 공식 배포판이나 OpenAI 공식 플러그인은 아닙니다.

이 저장소에서 작성한 내용은 [MIT License](LICENSE)로 제공합니다. 링크된 프로젝트와 글에는 각각의 저작권·이용 조건이 적용됩니다.
