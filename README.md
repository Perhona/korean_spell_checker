# 한글 맞춤법 검사기
<p align="center">
  <img src="https://github.com/user-attachments/assets/df334f53-907b-4569-954b-28605a07d024" alt="실행 화면" width="700"/>
</p>

이 프로그램은 윈도우에서 복사/붙여넣기를 통해 한글 맞춤법을 빠르게 검사할 수 있는 도구입니다. 다음 맞춤법 검사기와 부산대 맞춤법 검사기의 결과를 동시에 확인할 수 있습니다. 간단한 글 작성 시 별도의 웹사이트 방문 없이 프로그램을 통해 빠르게 맞춤법을 확인하기 위해 개발되었습니다.

## 기능

- 다음 맞춤법 검사기와 부산대 맞춤법 검사기 동시 사용
- 클립보드 자동 감지 기능 (기본값: 활성화, on/off 가능)
- 원본 텍스트의 줄바꿈 및 서식 유지
- 각 맞춤법 검사기 결과를 별도의 탭에 표시
- 결과 클립보드 복사 기능

## 서비스 정보 및 제한사항

- **부산대 맞춤법 검사기**
   - 주소: [https://nara-speller.co.kr/speller/](https://nara-speller.co.kr/speller/)
   - 비상업적 용도로만 사용 가능합니다.

- **다음 맞춤법 검사기**
   - 주소: [https://alldic.daum.net/grammar_checker.do](https://alldic.daum.net/grammar_checker.do)
   - 공백 포함 1000자 제한이 있습니다.

## 설치 방법

### 방법 1: 실행 파일 다운로드

1. Releases 페이지에서 최신 버전의 `한글맞춤법검사기.exe`를 다운로드합니다.
2. 다운로드한 파일을 원하는 위치에 저장합니다.
3. 파일을 더블클릭하여 실행합니다.

### 방법 2: 소스코드로부터 직접 실행

#### 필수 요구사항
- Python 3.11 이상
- 필요한 패키지: `aiohttp`, `pyperclip`

#### 설치 단계
1. 이 저장소를 클론하거나 다운로드합니다:
   ```bash
   git clone https://github.com/Perhona/korean_spell_checker.git
   cd korean-spell-checker
   ```

2. 필요한 패키지를 설치합니다:
   ```bash
   pip install aiohttp pyperclip
   ```
   또는 Poetry를 사용하는 경우:
   ```bash
   poetry install
   ```

3. 프로그램을 실행합니다:
   ```bash
   python korean_spell_checker.py
   ```
   또는 Poetry를 사용하는 경우:
   ```bash
   poetry run python korean_spell_checker.py
   ```

### 방법 3: 소스코드로부터 EXE 파일 생성

1. 필요한 패키지를 설치합니다:
   ```bash
   pip install aiohttp pyperclip pyinstaller
   ```
   또는 Poetry를 사용하는 경우:
   ```bash
   poetry add pyinstaller
   ```

2. PyInstaller를 사용하여 EXE 파일을 생성합니다:
   ```bash
   pyinstaller --onefile --windowed korean_spell_checker.py
   ```
   또는 Poetry를 사용하는 경우:
   ```bash
   poetry run pyinstaller --onefile --windowed korean_spell_checker.py
   ```

3. 생성된 EXE 파일은 `dist` 폴더에서 찾을 수 있습니다.

## 사용 방법

1. 프로그램을 실행합니다.
2. 텍스트 입력 방식:
   - 텍스트 박스에 직접 입력
   - 다른 프로그램에서 텍스트 복사(Ctrl+C) → 자동 감지됨 (기본값: ON)
3. "맞춤법 검사" 버튼 클릭
4. 검사 결과는 원본 텍스트의 줄바꿈, 띄어쓰기를 유지하며 괄호 `()` 안에 교정안을 표시합니다.
   - 예: "커밋을(커 맛을|커 믿을) 두 번 해야돼(해야 해)"
   - `|` 기호를 사용하여 여러 교정안이 제시되는 경우도 있습니다 (특히 부산대 검사기).
5. 다음 / 부산대 결과는 각 탭에서 확인 가능하며, 각각 클립보드 복사도 지원됩니다.

## 프로젝트 구조

```
korean-spell-checker/
├── korean_spell_checker.py  # 메인 코드 파일
├── README.md                # 이 파일
└── pyproject.toml           # Poetry 구성 파일
```

## 코드 설명

이 프로젝트는 다음과 같은 주요 클래스로 구성되어 있습니다:

1. `SpellChecker` - 다음 및 부산대 맞춤법 검사 API를 호출하고 결과를 처리하는 클래스
2. `SpellCheckerApp` - Tkinter 기반 GUI와 사용자 상호 작용을 관리하는 클래스

## 종속성

- Python >= 3.11, < 3.14
- aiohttp >= 3.11.18, < 4.0.0: 비동기 HTTP 요청을 위한 라이브러리
- pyperclip >= 1.9.0, < 2.0.0: 클립보드 액세스를 위한 라이브러리
- pyinstaller >= 6.13.0, < 7.0.0 (빌드 전용): EXE 파일 생성을 위한 라이브러리
- tkinter: GUI 구현을 위한 라이브러리 (Python 표준 라이브러리에 포함)
- asyncio: 비동기 작업을 위한 라이브러리 (Python 표준 라이브러리에 포함)

## 문제 해결

### 일반적인 문제

1. **맞춤법 검사 결과가 표시되지 않는 경우**
   - 인터넷 연결 상태를 확인하세요.
   - 검사할 텍스트가 너무 길면 여러 부분으로 나누어 검사를 시도하세요.
   - 다음 맞춤법 검사기는 1000자 제한이 있으니 참고하세요.
   - 짧은 시간 내에 너무 많은 요청을 보냈다면, 잠시 후 다시 시도하세요.

2. **특수 문자나 기호가 비정상적으로 표시되는 경우**
   - 일부 특수 문자는 표시에 문제가 있을 수 있지만, 결과를 복사하여 다른 텍스트 편집기에 붙여넣으면 정상적으로 보입니다.

3. **EXE 파일 실행 시 오류 발생**
   - 일부 안티바이러스 프로그램이 PyInstaller로 생성된 EXE 파일을 오탐할 수 있습니다.
   - 필요한 경우 안티바이러스 소프트웨어에 예외를 추가하거나 소스 코드에서 직접 실행하세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 그러나 다음과 같은 추가 고지사항이 적용됩니다.

```
이 소프트웨어는 다음과 부산대에서 제공하는 맞춤법 검사 서비스를 활용합니다.
이 서비스들의 이용 약관을 준수하는 것은 사용자의 책임입니다.

- 부산대 맞춤법 검사기는 비상업적 용도로만 사용해야 합니다.
- 다음 맞춤법 검사기는 1000자 제한이 있으며, 서비스 제공자의 이용 약관을 준수해야 합니다.

이 소프트웨어는 개인적, 비상업적 용도로만 사용하는 것을 권장합니다.
맞춤법 검사 서비스 자체에 대한 권리는 원 제공자(다음, 부산대)에게 있습니다.
```
