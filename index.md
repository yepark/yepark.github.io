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
# 나를 위한 개발 기록
{: .fs-9 }
</div>

## 주제

<ul class="topic-list">
  <li><a class="topic-card" href="{{ '/ai/' | relative_url }}"><span class="topic-card__title">AI</span><span class="topic-card__description">MLX로 Mac에서 머신러닝 돌리기, 기초부터</span></a></li>
  <li><a class="topic-card" href="{{ '/swift/' | relative_url }}"><span class="topic-card__title">Swift</span><span class="topic-card__description">옵셔널, 프로퍼티, 클로저처럼 매일 만나는 것들</span></a></li>
  <li><a class="topic-card" href="{{ '/ios/' | relative_url }}"><span class="topic-card__title">iOS</span><span class="topic-card__description">화면 배치, 데이터 저장, 테스트, 빌드</span></a></li>
  <li><a class="topic-card" href="{{ '/pki/' | relative_url }}"><span class="topic-card__title">PKI & 암호</span><span class="topic-card__description">인증서, RSA, 블록 암호</span></a></li>
</ul>

## 최근에 고친 글

{% assign notes = site.html_pages | where_exp: "p", "p.parent" | where_exp: "p", "p.has_children != true" | sort: "last_modified_date" | reverse %}
<ul class="recent-list">
{% for p in notes limit: 8 %}
  <li><span class="date">{{ p.last_modified_date | date: "%Y-%m-%d" }}</span><a href="{{ p.url | relative_url }}">{{ p.title }}</a></li>
{% endfor %}
</ul>
