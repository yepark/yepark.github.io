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

<header class="home-intro">
  <p class="home-intro__eyebrow">yep · 옙개발</p>
  <h1>이해한 만큼,<br>단단해지는 개발.</h1>
  <p class="home-intro__lead">Swift와 iOS, AI와 보안의 원리를 코드로 확인하고<br class="desktop-break"> 다시 꺼내 읽을 수 있는 글로 정리합니다.</p>
  <a class="home-intro__author" href="{{ '/about/' | relative_url }}">yep의 개발 기록 <span aria-hidden="true">↗</span></a>
</header>

<section class="home-section" aria-labelledby="topics-heading">
  <div class="section-heading"><h2 id="topics-heading">주제 탐색</h2><span>궁금한 원리부터 시작하세요</span></div>
  <ul class="topic-list">
    <li><a href="{{ '/ai/' | relative_url }}"><span class="topic-title">AI</span><span class="topic-description">머신러닝의 기초부터 AI 에이전트의 설계와 평가까지</span><span class="topic-arrow" aria-hidden="true">→</span></a></li>
    <li><a href="{{ '/swift/' | relative_url }}"><span class="topic-title">Swift</span><span class="topic-description">언어의 기본 개념과 동시성, 더 안전한 코드의 구조</span><span class="topic-arrow" aria-hidden="true">→</span></a></li>
    <li><a href="{{ '/ios/' | relative_url }}"><span class="topic-title">iOS</span><span class="topic-description">앱의 설계와 테스트, MLX와 Apple 플랫폼 AI</span><span class="topic-arrow" aria-hidden="true">→</span></a></li>
    <li><a href="{{ '/pki/' | relative_url }}"><span class="topic-title">PKI &amp; 암호</span><span class="topic-description">암호 알고리즘부터 인증서와 전자서명의 동작 원리</span><span class="topic-arrow" aria-hidden="true">→</span></a></li>
  </ul>
</section>

<section class="home-section" aria-labelledby="recent-heading">
  <div class="section-heading"><h2 id="recent-heading">최근 다듬은 글</h2><span>새로 쓰고, 다시 살펴본 기록</span></div>
  {% assign notes = site.html_pages | where_exp: "p", "p.parent" | where_exp: "p", "p.has_children != true" | where_exp: "p", "p.last_modified_date" | sort: "last_modified_date" | reverse %}
  <ul class="recent-list">
  {% for p in notes limit: 8 %}
    <li><a href="{{ p.url | relative_url }}"><span class="recent-list__text"><span class="recent-list__topic">{{ p.grand_parent | default: p.parent | escape }}{% if p.grand_parent %} · {{ p.parent | escape }}{% endif %}</span><span class="recent-list__title">{{ p.title | escape }}</span></span><time datetime="{{ p.last_modified_date | date: '%Y-%m-%d' }}">{{ p.last_modified_date | date: "%Y.%m.%d" }}</time></a></li>
  {% endfor %}
  </ul>
</section>
