---
layout: single
title: "[TIL] MVVM패턴"
date: 2021-04-09
comments: true
categories:
  - TIL
tags: [iOS, XCode, Swift]
# 목차
toc: true
toc_sticky: true
---
***
## MVVM 정리
- Model-View-ViewModel 구조  
  Model : 데이터 혹은 서비스  
  View : 일반 UI화면 (데이터 바인딩된 화면)  
  ViewModel : View에 맞게끔 가공된 Model 데이터  
  Model -> View -> ViewModel (View는 Model에 대해 모르고, ViewModel은 View에 대해서 모른다)