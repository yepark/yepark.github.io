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

공부한 것을 **내가 다시 읽어도 바로 이해되게** 쉬운 말로 적어 둡니다.
{: .home-intro__lead }
</div>

## 주제

<ul class="topic-list">
  <li><a href="{{ '/mlx/' | relative_url }}">MLX</a><span>Apple 실리콘 Mac에서 머신러닝을 돌리는 방법, 가장 기초부터</span></li>
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
