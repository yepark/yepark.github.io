---
title: 홈
nav_order: 1
permalink: /
redirect_from:
  - /categories/
  - /tags/
  - /page2/
  - /page3/
  - /page4/
---

<div class="home-intro" markdown="1">
# 나중의 나를 위한 노트
{: .fs-9 }

iOS 개발자 yep의 공부 노트
{: .home-intro__lead }
</div>

## 주제

<ul class="topic-list">
  <li><a href="{{ '/ai/' | relative_url }}">AI</a><span>MLX로 Mac에서 머신러닝 돌리기, 기초부터</span></li>
  <li><a href="{{ '/swift/' | relative_url }}">Swift</a><span>옵셔널, 프로퍼티, 클로저처럼 매일 만나는 것들</span></li>
  <li><a href="{{ '/ios/' | relative_url }}">iOS</a><span>화면 배치, 데이터 저장, 테스트, 빌드</span></li>
  <li><a href="{{ '/pki/' | relative_url }}">PKI & 암호</a><span>인증서, RSA, 블록 암호</span></li>
</ul>

## 최근에 고친 글

{% assign notes = site.html_pages | where_exp: "p", "p.parent" | sort: "last_modified_date" | reverse %}
<ul class="recent-list">
{% for p in notes limit: 8 %}
  <li><span class="date">{{ p.last_modified_date | date: "%Y-%m-%d" }}</span><a href="{{ p.url | relative_url }}">{{ p.title }}</a></li>
{% endfor %}
</ul>
