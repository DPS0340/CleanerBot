# CleanerBot

빠르고 안전한 디시인사이드, 아카라이브 클리너 디스코드봇

현재 안정성 및 보안의 문제로 공식 봇의 형태로 배포하지 않고 있습니다.

참고 문서를 보시면서 직접 코드를 클론받아 로컬에서 돌리시면 캡챠에 거의 걸리지 않고 사용할 수 있습니다.

## 설치법

### 도커 설치

CleanerBot은 도커라이즈된 채로 배포됩니다. 도커를 설치해 주세요.

윈도우 환경에서는 [도커 데스크탑](https://www.docker.com/products/docker-desktop)을 추천드립니다.

### 봇 생성

[디스코드 봇 만들기](https://lektion-von-erfolglosigkeit.tistory.com/65) 티스토리 문서를 참조하셔서 봇을 만드시고 토큰을 저장해주세요.

사용을 위해서는 개인 서버에 봇을 추가하셔야 합니다.

### 환경 변수 저장

방금 전에 생성한 토큰을 프로그램이 가져올 수 있는 위치에 저장해야 합니다.
powershell이나 bash등의 터미널을 엽니다.

Windows
```sh
set CLEANERBOT_TOKEN=토큰값
```

Linux/MacOS
```sh
export CLEANERBOT_TOKEN=토큰값
```

### 레포 클론

git을 설치하여 주세요. 터미널 환경에서 적절한 폴더에서 레포를 클론받습니다.

```sh
git clone https://github.com/DPS0340/Cleanerbot
```

### 컨테이너 실행

방금 받은 폴더로 들어가서 컨테이너를 실행합니다.

```sh
cd Cleanerbot
docker-compose up -d --build
```

### hosts 파일 수정

두 가지 방법중에 선호하는 방법 하나를 선택하시면 됩니다.

이 작업은 존재하지 않는 서브도메인인 cleanerbot.dcinside.com을 캡챠 우회를 위해 127.0.0.1, 즉 자신의 IP에 연동하는 과정입니다.

봇이 자신의 IP에서 돌아가는 상황이 아니라면 봇 서버의 IP로 수정해주시면 됩니다.

#### 유틸리티 프로그램을 사용하는 간단한 방법

https://github.com/DPS0340/CleanerBot/releases 에서 파일을 받으시고, 관리자 권한으로 실행하시면 hosts에 상기한 라우팅이 됩니다.

MacOS는 두 가지 아키텍처로 파편화되어 있어, x86 (인텔)의 경우 darwin-x86_64를 선택하시고, ARM (Apple Silicon)의 경우 darwin-aarch64를 선택하시면 됩니다.

Linux 혹은 MacOS 환경에서는 컴파일된 바이너리를 브라우저를 통해 다운받을 경우에는, 실행 권한이 부여되지 않기 때문에 터미널을 사용해서 실행하시면 관련된 문제를 해결할 수 있습니다.

```sh
cd Downloads # 다운로드 폴더 접근, 폴더 이름과 경로에 따라 적절히 수정
chmod +x ./host-manager-linux-x86_64 # 바이너리에 실행 권한 부여, 아키텍처에 맞게 파일명 적절히 수정 필요
sudo ./host-manager-linux-x86_64 # 바이너리를 관리자 권한으로 실행
```

#### 직접 hosts 파일 수정 (Windows 전용)

관리자 권한으로 C:\Windows\System32\drivers\etc\hosts 파일을 직접 수정하셔서 마지막 부분에 한 줄을 추가합니다.

```
127.0.0.1 cleanerbot.dcinside.com
```

비주얼 스튜디오 코드를 사용하시면 관리자 권한으로 쉽게 저장할 수 있습니다. 그렇지 않다면 사본을 저장한 뒤 다시 경로로 옮겨줘야 합니다.

이제 설치가 끝났습니다. 수고 많으셨습니다.

## 클리너 코어 부분

[74l35rUnn3r](https://gist.github.com/74l35rUnn3r/f689bce5b6abb15d0185a4754e4e6da5)님의 코드를 가져왔습니다.

이 자리를 빌어서 감사를 표합니다.

## CLEANERBOT 사용 설명서

봇에게 멘션을 하시면 사용법이 나옵니다. 가급적이면 로그인같이 보안에 민감한 명령어는 다이렉트 메시지를 사용하시는 것을 추천드립니다.

### clb login id pw
id와 pw를 통해 로그인합니다.
### 제한 사항
이후 커맨드는 로그인된 사용자만 사용 가능합니다.
### clb stat
글과 댓글 갯수를 보여줍니다.
### clb clean
글과 댓글을 지웁니다.
### clb post
글을 지웁니다.
### clb comment
댓글을 지웁니다.
### clb arca id pw nickname
id와 pw, 닉네임을 통해 아카라이브에 있는 글과 댓글을 지웁니다.
### clb arca post id pw nickname
id와 pw, 닉네임을 통해 아카라이브에 있는 글을 지웁니다.
### clb arca comment id pw nickname
id와 pw, 닉네임을 통해 아카라이브에 있는 댓글을 지웁니다.
