---
layout: posts
permalink: /posts/
title: "[Jenkins]Fortify 연동 "
date: 2020-08-04 20:36:00
comments: true
# categories: bugfix
# 목차
toc: true
toc_sticky: true
---
# Jenkins-Fortify 연동
  * https://plugins.jenkins.io/fortify/ 에서 플러그인을 다운받아 설치한다.
  * https://www.microfocus.com/documentation/fortify-jenkins-plugin/ 설치 문서 참고
  * 설치후 Fortify Assessment 설정을 정상적으로 하였으나 session id오류가 나는 경우
  * ios build 폴더를 삭제후에 빌드하도록 한다.