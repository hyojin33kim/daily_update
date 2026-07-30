# Codex 작업 지시서
## KOSPI 대시보드 GitHub 배포 자동화

---

## 작업 개요
이 레포에 있는 파일들을 GitHub에 올리고,
매일 KST 07:00에 자동으로 KOSPI 데이터를 수집해서
대시보드를 업데이트한 뒤 웹으로 배포하는 파이프라인을 완성해줘.

---

## 레포 파일 구성 (이미 있음)
- `index.html`       : KOSPI 대시보드 (수정 금지 — update.py가 자동 수정)
- `update.py`        : 매일 실행할 데이터 수집 + HTML 업데이트 스크립트
- `CLAUDE.md`        : 프로젝트 컨텍스트
- `.github/workflows/update.yml` : GitHub Actions 스케줄러

---

## Step 1: 레포 초기화 및 GitHub Push

아래 명령을 순서대로 실행해줘:

```bash
git init
git add .
git commit -m "최초 업로드: KOSPI 대시보드"
git branch -M main
git remote add origin https://github.com/$GITHUB_USER/kospi-dashboard.git
git push -u origin main
```

레포가 없으면 GitHub API로 먼저 생성:
- 이름: kospi-dashboard
- Private: false (GitHub Pages 무료 사용)
- auto_init: false

---

## Step 2: GitHub Secrets 등록

GitHub API로 아래 Secret을 레포에 등록해줘:

| Secret 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | 환경변수 $ANTHROPIC_API_KEY 값 사용 |

GitHub Secrets API 엔드포인트:
`PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}`

Secrets는 레포의 public key로 암호화해서 등록해야 함.
필요 라이브러리: `pip install PyNaCl requests`

암호화 방법:
```python
from base64 import b64encode
from nacl import encoding, public

def encrypt(public_key_str, secret_value):
    public_key = public.PublicKey(public_key_str.encode(), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted  = sealed_box.encrypt(secret_value.encode())
    return b64encode(encrypted).decode()
```

---

## Step 3: GitHub Pages 활성화

GitHub API로 Pages를 활성화해줘:

```
POST /repos/{owner}/{repo}/pages
{
  "source": {"branch": "main", "path": "/"},
  "build_type": "workflow"
}
```

---

## Step 4: 즉시 테스트 실행

GitHub API로 workflow를 수동 트리거해줘:

```
POST /repos/{owner}/{repo}/actions/workflows/update.yml/dispatches
{"ref": "main"}
```

---

## Step 5: 결과 확인 및 보고

완료 후 아래 정보를 알려줘:
1. GitHub 레포 URL
2. GitHub Pages URL (대시보드 접속 주소)
3. Actions 탭 URL (실행 상태 확인)
4. 다음 자동 실행 예정 시각 (KST)

---

## 환경변수 (자동 주입됨)
- `GITHUB_TOKEN`       : GitHub PAT (repo + pages 권한)
- `GITHUB_USER`        : GitHub 유저명
- `ANTHROPIC_API_KEY`  : Anthropic API 키

## 주의사항
- git push 시 HTTPS 인증은 GITHUB_TOKEN 사용
  `https://$GITHUB_TOKEN@github.com/$GITHUB_USER/kospi-dashboard.git`
- 오류 발생 시 각 Step을 독립적으로 재시도
- index.html 내용은 절대 수정하지 말 것 (update.py가 관리)
