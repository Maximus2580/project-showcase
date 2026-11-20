# 설치 전 사전 준비

[English](installation.md) · [한국어](installation.ko.md) · [README로 돌아가기](../i18n/README.ko.md)

Project Showcase는 내 컴퓨터에서 실행됩니다. 아래 도구를 한 번 준비하면 여러 프로젝트에서 사용할 수 있습니다.

| 도구 | 필요한 이유 |
| --- | --- |
| Claude Code 또는 Codex | 프로젝트를 읽고 발표 내용과 디자인을 작성합니다 |
| Python 3.12 | 발표자료 제작 과정을 실행합니다 |
| Node.js 22 이상·npm | 브라우저와 영상 도구를 실행합니다 |
| FFmpeg·ffprobe | 영상을 만들고 음성·영상 길이를 확인합니다 |
| Google Chrome | HTML을 슬라이드와 영상 프레임으로 그립니다 |
| Git | 저장소를 내려받고 업데이트합니다 |

이미 설치한 도구는 그대로 두고 아래 버전 확인만 하세요.

## 에이전트 준비

둘 중 하나를 설치하고 로그인하세요. 이미 프로젝트를 작업하고 있다면 건너뛰어도 됩니다.

- [Claude Code 공식 시작 가이드](https://code.claude.com/docs/en/quickstart)
- [Codex 공식 시작 가이드](https://developers.openai.com/codex/quickstart)

## macOS

1. **⌘ Space**를 누르고 **터미널**을 검색해 엽니다.
2. `brew --version`을 입력했을 때 명령을 찾지 못하면 [Homebrew를 설치](https://brew.sh/)하세요. 설치 마지막에 나오는 **Next steps**도 실행해야 터미널에서 `brew`를 사용할 수 있습니다.
3. 다음 명령으로 필요한 도구를 설치합니다.

   ```sh
   brew install python@3.12 node@24 ffmpeg git
   ```

4. 현재 터미널에서 설치한 Node를 찾을 수 있도록 실행 경로를 추가합니다.

   ```sh
   export PATH="$(brew --prefix node@24)/bin:$PATH"
   ```

   새 터미널에서도 이 설정을 유지하려면 다음 명령을 한 번 실행하세요.

   ```sh
   printf '%s\n' 'export PATH="$(brew --prefix node@24)/bin:$PATH"' >> "$HOME/.zprofile"
   ```

   터미널을 다시 여세요. 에이전트도 `node`와 `npm`을 찾을 수 있어야 하므로 그 터미널에서 시작하거나 에디터에 같은 Node 경로를 설정하세요. 이미 지원 버전의 Node를 사용한다면 기존 설정을 유지하면 됩니다.

5. Chrome이 없다면 [Google Chrome을 다운로드](https://www.google.com/chrome/)하세요. 다운로드한 파일을 열고 Chrome을 **응용 프로그램** 폴더로 옮깁니다.
6. 설치를 확인합니다.

   ```sh
   python3.12 --version
   node --version
   npm --version
   git --version
   ffmpeg -version
   ffprobe -version
   ```

각 명령에서 버전이 나오면 됩니다. Node는 22 이상이어야 합니다.

같은 터미널에서 [스킬 설치](../i18n/README.ko.md#설치)를 이어가세요.

## Windows

1. **시작**에서 **PowerShell**을 검색해 엽니다.
2. 다음 명령을 한 줄씩 실행합니다. 이미 설치한 도구는 건너뛰세요.

   ```powershell
   winget install --exact --id Python.Python.3.12
   winget install --exact --id OpenJS.NodeJS.LTS
   winget install --exact --id Git.Git
   winget install --exact --id Gyan.FFmpeg
   winget install --exact --id Google.Chrome
   ```

   `winget`을 찾지 못하면 Microsoft의 [앱 설치 관리자](https://learn.microsoft.com/windows/package-manager/winget/)를 먼저 설치하세요.

3. **PowerShell을 닫았다가 다시 엽니다.** 설치한 도구의 실행 경로를 새 창에서 인식합니다.
4. 설치를 확인합니다.

   ```powershell
   py -3.12 --version
   node --version
   npm.cmd --version
   git --version
   ffmpeg -version
   ffprobe -version
   ```

이제 [스킬 설치](../i18n/README.ko.md#설치)를 이어가세요. Python 명령은 `py -3.12`를 사용합니다. Windows 전체 제작 과정의 실기기 검증은 아직 남아 있습니다.

## 설치한 스킬 점검하기

설치 프로그램이 실행 파일의 전체 경로를 출력합니다. 파일을 저장할 수 있는 작업 폴더에서 환경 검사를 실행하세요.

**macOS**

```sh
"$HOME/.local/bin/project-showcase" --out showcase-output/preflight preflight
```

**Windows**

```powershell
& "$env:USERPROFILE\.local\bin\project-showcase.cmd" --out showcase-output/preflight preflight
```

`preflight PASS`가 나오면 음성 생성, 진단 화면 렌더, 짧은 시험 영상 제작이 끝난 것입니다. 발표 내용이나 최종 청취까지 합격한 것은 아닙니다.

## 자주 막히는 부분

| 상황 | 해결 방법 |
| --- | --- |
| macOS의 `python3`가 오래된 버전입니다 | 위 안내처럼 `python3.12`를 사용하세요 |
| `node`, `npm`, `ffmpeg`를 찾지 못합니다 | 터미널을 다시 열고, macOS는 위 PATH 설정도 확인하세요 |
| `project-showcase`를 찾지 못합니다 | 위의 전체 경로나 설치 프로그램이 출력한 경로를 사용하세요 |
| 에이전트가 스킬을 찾지 못합니다 | 새 세션을 여세요. Claude Code에서는 `/project-showcase`를 사용합니다 |
| 이미 설치되어 있다고 나옵니다 | `scripts/install_global.py --replace`로 실행하세요. 기존 설치는 백업합니다 |
| `E_DESIGN_SELECTION_REQUIRED`가 나옵니다 | 비교 화면에서 방향과 리비전을 먼저 선택하세요 |
| 음성 생성·렌더 중 오류가 납니다 | 오류와 출력 폴더를 에이전트에게 주고 이어서 작업하도록 요청하세요 |

Chrome을 다른 위치에 설치했다면 `CHROME_PATH`에 Chrome 실행 파일 경로를 지정하세요. 온라인 음성 생성에 보내는 대본에서 비밀키와 고객 개인정보를 제거하세요.
