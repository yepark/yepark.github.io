---
layout: single
title: "[Jekyll] GitHub Pages 블로그 설정과 문제 해결"
date: 2021-04-23
last_modified_at: 2026-11-01
comments: true
categories:
  - blog
tags: [Jekyll, GitHub-Pages, Minimal-Mistakes]
toc: true
toc_sticky: true
toc_label: "목차"
---

이 블로그는 Jekyll과 Minimal Mistakes 테마를 사용한다. 설정을 바꿀 때 자주 마주친 문제와 현재 프로젝트에서 확인한 해결 방법을 한곳에 정리한다.

## 로컬에서 실행하기

GitHub Pages와 비슷한 의존성으로 빌드하려면 프로젝트 루트의 `Gemfile`에 `github-pages` gem을 선언하고 Bundler를 사용한다.

```ruby
source "https://rubygems.org"

gem "github-pages", "~> 232", group: :jekyll_plugins
```

설치와 실행 명령은 다음과 같다.

```bash
bundle install
bundle exec jekyll serve
```

초안까지 미리 보려면 `--drafts`를 붙인다.

```bash
bundle exec jekyll serve --drafts
```

GitHub Pages에서 배포가 실패해도 원인이 항상 글에 있는 것은 아니다. Actions 화면에서 **Build with Jekyll**, **Upload artifact**, **Deploy to GitHub Pages** 중 어느 단계가 실패했는지 먼저 구분한다.

## `_config.yml` 변경이 바로 보이지 않을 때

Jekyll 실행 중 `_config.yml`을 수정하면 서버를 다시 시작해야 한다. 공개 사이트는 GitHub Actions의 배포가 끝난 뒤에도 CDN 캐시 때문에 짧은 지연이 생길 수 있다. 브라우저 강력 새로고침 전에 Actions의 배포 성공 여부와 공개 HTML의 `last-modified` 응답을 확인하면 원인을 좁히기 쉽다.

## 댓글 설정

Minimal Mistakes에서 utterances를 사용하려면 댓글 공급자와 저장소를 명시한다. 저장소에는 utterances 앱이 설치되어 있고 Discussions가 아닌 Issues를 사용할 권한이 있어야 한다.

```yaml
repository: "yepark/yepark.github.io"

comments:
  provider: "utterances"
  utterances:
    theme: "github-light"
    issue_term: "pathname"
```

`repository`를 빠뜨리면 댓글 스크립트가 어느 저장소에 이슈를 만들지 알 수 없다. 예전에 사용하던 Disqus 설정과 사용자 정의 embed 코드는 새 공급자로 전환할 때 함께 제거하는 편이 좋다.

## 테마 스타일 수정

글꼴 크기처럼 테마의 Sass 변수를 바꾸려면 먼저 Minimal Mistakes가 제공하는 변수와 오버라이드 위치를 확인한다. 생성된 CSS를 직접 수정하면 다음 빌드에서 덮어쓰이므로 `_sass`의 사용자 정의 파일이나 테마가 안내하는 변수 파일을 사용한다.

## 글을 발행하는 규칙

Jekyll 포스트는 `_posts` 아래에 `YYYY-MM-DD-title.md` 형식으로 저장하고 YAML front matter로 시작해야 한다. `_drafts`의 글은 기본 빌드에 포함되지 않으며, 완성 후 날짜가 포함된 파일명으로 `_posts`에 옮겨야 공개된다.

```yaml
---
layout: single
title: "[Swift] 글 제목"
date: 2026-11-01
categories:
  - Swift
tags: [Swift, iOS]
toc: true
---
```

`categories`는 현재 블로그의 URL에 포함되므로 기존 글에서 값을 바꾸면 주소도 달라질 수 있다. 이미 검색 엔진에 노출된 글이라면 permalink를 유지하거나 이전 주소에서 새 주소로 리디렉션해야 한다. `tags`는 글을 묶는 메타데이터지만 기본 설정에서는 URL을 결정하지 않는다.

## 안전한 발행 절차

수정한 글이 많을수록 로컬 확인과 공개 배포를 분리하는 편이 안전하다.

```bash
bundle exec jekyll build
git diff --check
git status --short
git add _posts assets _config.yml
git commit -m "Update blog content"
git push origin master
```

빌드 성공만으로 배포가 끝난 것은 아니다. GitHub Actions에서 artifact 업로드와 Pages deploy까지 성공했는지 확인하고, 공개 URL의 응답과 제목도 확인한다. `_config.yml`이나 레이아웃을 바꾼 경우에는 대표 글 하나뿐 아니라 홈, 카테고리, 모바일 화면까지 확인한다.

## 참고

- [GitHub Docs: Jekyll 사이트를 로컬에서 테스트하기](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/testing-your-github-pages-site-locally-with-jekyll)
- [Jekyll 문서: Posts와 Drafts](https://jekyllrb.com/docs/posts/)
- [Minimal Mistakes 문서](https://mmistakes.github.io/minimal-mistakes/docs/configuration/)
