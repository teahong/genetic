# 유전 알고리즘 진화 시뮬레이션

초식동물과 포식자가 유전자를 물려주며 세대를 거듭하는 생태계 시뮬레이션입니다. Pygame으로 만들었고, [pygbag](https://github.com/pygame-web/pygbag)을 이용해 웹 브라우저에서도 실행할 수 있습니다.

▶ **웹에서 실행하기: https://teahong.github.io/genetic/**
(처음 열 때 화면을 한 번 클릭해야 시작될 수 있습니다.)

## 시뮬레이션 규칙

- **유전자(DNA)**: 각 개체는 `크기`, `속도`, `인식 범위` 세 가지 유전자를 가집니다. 자식은 부모의 유전자를 물려받고, 10% 확률로 돌연변이가 일어납니다.
- **초식동물 (초록)**: 시간이 지나면 체력이 줄어들고, 빠를수록 더 빨리 줄어듭니다. 일정 나이가 되면 번식합니다.
- **포식자 (빨강)**: 시간이 지나면 배고파지고, 크고 빠를수록 더 빨리 배고파집니다. 초식동물을 잡아먹으면 포만감이 회복되고, 배가 부르면 번식합니다.
- **안전지대 (파랑 원)**: 화면 가운데의 원 안에 있는 초식동물은 잡아먹히지 않습니다.
- **수용 한계**: 개체 수가 많아질수록 번식 확률이 낮아집니다. 개체 수가 너무 적어지면 새 개체가 추가되어 완전히 멸종하지 않습니다.

어떤 유전자가 살아남는지는 "빠르면 도망치기 쉽지만 에너지 소모가 크다" 같은 득실 관계에 따라 정해집니다.

## 화면 구성 (`evolution.py`)

- **좌측 상단**: 종별 개체 수와 평균 유전자 값
- **우측 상단**: 클릭한 개체의 상세 정보 (종류, 유전자, 나이, 체력/포만감)
- **하단 그래프**: 개체 수, 평균 크기, 평균 속도의 변화 추이 (초록: 초식동물, 빨강: 포식자)

## 파일 구성

| 파일 | 설명 |
|---|---|
| `evolution.py` | 메인 버전. 통계 그래프, 개체 선택, 한글 UI 포함 |
| `simulation.py` | 이전 버전. 유전자 평균 그래프(영문 UI) |
| `genetic2.py` | 초기 버전 |
| `web/main.py` | `evolution.py`를 웹(pygbag)용으로 바꾼 버전 |
| `web/NanumGothic-Regular.ttf` | 웹에서 한글을 표시하기 위한 나눔고딕 폰트 (SIL OFL 라이선스) |
| `.github/workflows/pages.yml` | `main`에 푸시하면 자동으로 빌드해서 GitHub Pages에 배포 |

## 실행 방법

### PC에서 실행

```
pip install pygame
python evolution.py
```

### 웹 버전을 로컬에서 테스트

```
pip install pygbag
```

`PYTHONUTF8=1`을 꼭 설정해야 합니다. 설정하지 않으면 한국어 Windows에서 `UnicodeDecodeError`가 납니다.

PowerShell:
```
$env:PYTHONUTF8=1; python -m pygbag web
```

macOS / Linux / Git Bash:
```
PYTHONUTF8=1 python -m pygbag web
```

실행한 뒤 브라우저에서 http://localhost:8000 을 열면 됩니다.

## 웹 버전 수정 시 주의사항

- `evolution.py`를 고친 내용은 `web/main.py`에 자동으로 반영되지 않습니다. 웹에도 반영하려면 `web/main.py`도 같이 고쳐야 합니다.
- `web/main.py`는 브라우저에서 돌아가도록 다음 부분이 다릅니다.
  - 메인 루프가 `async def main()`이고, 매 프레임마다 `await asyncio.sleep(0)`을 호출합니다.
  - 시스템 폰트 대신 같은 폴더의 `NanumGothic-Regular.ttf`를 불러옵니다.
- 빌드 결과물(`web/build/`)은 저장소에 올리지 않습니다. GitHub Actions가 푸시할 때마다 새로 빌드합니다.
