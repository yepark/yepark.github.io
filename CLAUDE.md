# 옙개발 작업 규칙

이 저장소는 Just the Docs 테마를 쓰는 개인 공부 노트 사이트(https://yepark.github.io)다. 주인은 Claude에게 글쓰기와 사이트 관리를 맡겼다.

## 글쓰기 원칙 (가장 중요)

1. **읽는 사람(주인)이 이해할 수 있어야 한다.** 강사가 학생에게 가르치듯 쓴다.
2. **쉬운 말**을 쓴다. 한자어나 논문 같은 말투는 풀어서 쓴다. 꼭 필요한 용어는 처음 나올 때 한 문장과 비유로 설명한다.
3. **사실만 쓴다.** 공식 문서로 확인했거나 직접 실행해서 본 것만 쓴다. "보통", "~인 경우가 많다" 같은 추측을 쓰지 않는다.
4. **코드는 전부 직접 실행**하고, 실제로 나온 결과를 붙인다.
5. 글 구성: 바로 본론(직관과 예제) → 자세한 설명 → 정리 → 다음 편 예고 → 참고(공식 문서 링크). "오늘 배울 것", "학습 목표" 같은 머리 섹션은 쓰지 않는다.
6. 문단은 짧게 쓰고, 강조 상자(`{: .tip }`, `{: .note }`, `{: .warning }`, `{: .question }`)를 활용한다.

## 사이트 밖으로 내보내지 않는 것

글쓰기 원칙, 사이트 구조, 운영 방법 같은 메타 내용은 사이트 페이지에 쓰지 않는다. 이 파일에만 둔다. (이 파일은 `_config.yml`의 `exclude`에 있어서 사이트에 올라가지 않는다.)

## 사이트 구조와 글 추가 방법

### 한눈에 보기

| 항목 | 지금 쓰는 것 |
| --- | --- |
| 사이트 만드는 도구 | Jekyll |
| 테마 | Just the Docs `v0.10.1` |
| 올리는 곳 | GitHub Pages (`master` 브랜치) |
| 주소 | https://yepark.github.io |

**Jekyll**은 마크다운(`.md`) 파일을 웹페이지(HTML)로 바꿔 주는 도구다. 나는 마크다운으로 글만 쓰고, 디자인과 메뉴는 테마가 만들어 준다.

**Just the Docs**는 원래 문서 사이트용 테마다. 왼쪽에 주제별 메뉴가 있고 검색이 된다. 블로그보다 "공부 노트"에 더 잘 맞아서 2026년 11월에 바꿨다.

### 폴더 구조

```text
yepark.github.io/
├── _config.yml          사이트 전체 설정
├── index.md             홈 화면
├── about.md             소개
├── ai/                  AI 주제 (메뉴의 "AI")
│   ├── index.md         주제 첫 페이지
│   └── mlx/             AI 안의 MLX 연재
│       ├── index.md     연재 첫 페이지 (메뉴의 "MLX")
│       └── 01-what-is-mlx.md
├── swift/  ios/  pki/    다른 주제들
├── _includes/head_custom.html  <head>에 넣을 것 (폰트, 사이트 인증)
├── _sass/custom/        글꼴, 줄 간격 같은 스타일
├── _sass/color_schemes/notes.scss  색상
└── assets/images/       글에 넣는 그림
```

**주제 하나 = 폴더 하나**다. 폴더 안의 `index.md`가 그 주제의 첫 페이지이고, 나머지 파일이 글이다.

### 새 글 추가하기

주제 폴더에 `.md` 파일을 만들고, 맨 위에 아래 머리말(front matter)을 붙인다. 머리말은 `---` 두 줄 사이에 쓰는 **글 정보**다.

```yaml
---
title: "2. 배열: MLX에서 숫자를 담는 그릇"
parent: MLX
grand_parent: AI
nav_order: 2
permalink: /ai/mlx/array/
first_written: 2026-11-16
last_modified_date: 2026-11-16
tags: [MLX, Python]
---
```

각 줄의 뜻은 이렇다.

- `title`: 글 제목. 왼쪽 메뉴에도 이 이름으로 나온다.
- `parent`: 어느 주제 아래에 넣을지. 주제 `index.md`의 `title`과 **글자가 똑같아야** 한다.
- `grand_parent`: 주제 안의 연재(예: AI 안의 MLX)에 넣을 때만 쓴다. 바깥 주제 이름을 적는다.
- `nav_order`: 메뉴에서 몇 번째에 놓을지. 작은 숫자가 위로 간다.
- `permalink`: 글 주소. 한 번 정하면 바꾸지 않는다. 바꾸면 예전 링크가 깨진다.
- `first_written`: 처음 쓴 날.
- `last_modified_date`: 마지막으로 고친 날. 글 아래에 표시되고, 홈의 "최근에 고친 글" 순서도 이 값으로 정해진다.

{: .warning }
`parent` 이름이 주제 `index.md`의 `title`과 한 글자라도 다르면, 글이 메뉴에 나타나지 않는다. 예를 들어 PKI 주제의 제목은 `PKI & 암호`다.

### 글 안에서 쓰는 강조 상자

`_config.yml`에 강조 상자 네 개를 만들어 두었다. 문단 바로 위에 한 줄을 붙이면 된다.

```markdown
{: .tip }
쉽게 풀어 쓴 설명.

{: .warning }
실수하기 쉬운 점.
```

| 쓰는 법 | 상자 제목 | 언제 |
| --- | --- | --- |
| `{: .note }` | 정리 | 중요한 내용을 한 번 더 짚을 때 |
| `{: .tip }` | 쉽게 말하면 | 어려운 개념을 비유로 풀 때 |
| `{: .warning }` | 주의 | 실수하기 쉬운 점 |
| `{: .question }` | 잠깐, 생각해 보기 | 스스로 생각해 볼 질문 |

### 내 컴퓨터에서 미리 보기

Mac 기본 Ruby(2.6)로는 빌드가 되지 않았다. Homebrew로 설치한 Ruby를 쓴다.

```bash
export PATH=/opt/homebrew/opt/ruby/bin:$PATH
bundle config set --local path vendor/bundle
bundle install
bundle exec jekyll serve
```

브라우저에서 http://localhost:4000 을 열면 된다. `_config.yml`을 고쳤다면 `jekyll serve`를 껐다가 다시 켜야 반영된다.

### 올리기

`master` 브랜치에 push하면 GitHub Pages가 알아서 사이트를 다시 만든다.

```bash
git add .
git commit -m "Add MLX 2: array"
git push origin master
```

push한 뒤에는 저장소의 **Actions** 탭에서 `pages build and deployment`가 초록색으로 끝났는지 확인한다. 빨간색이면 그 안의 로그를 열어 어떤 파일에서 실패했는지 본다.

### 참고 링크

- [Just the Docs 문서](https://just-the-docs.com/)
- [Jekyll 문서](https://jekyllrb.com/docs/)
- [GitHub Docs: Jekyll 사이트를 로컬에서 테스트하기](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/testing-your-github-pages-site-locally-with-jekyll)

## 주간 연재

| 주 | 주제 | 진행 |
| --- | --- | --- |
| 2026-11-15 ~ 11-22 | MLX (가장 기초부터) | `ai/mlx/index.md`의 순서표대로 하루 한 편 |

## 빌드 확인

```bash
export PATH=/opt/homebrew/opt/ruby/bin:$PATH
bundle exec jekyll build
```
