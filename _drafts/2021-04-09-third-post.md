---
layout: posts
title: "XCode Bitcode 지원 "
date: 2021-04-09 14:26:00
comments: true
# categories: bugfix
# 목차
toc: true
toc_sticky: true
---

### Bitcode란?
  * 모듈 최적화를 해준다. - TODO 수정 예정
  * 예전에는 유니버셜바이너리로써 모든 아키텍쳐를 전부 품고 있었는데 bitcode가 생김으로써 bitcode로 업로드후 앱스토어에서 재컴파일하여 해당 아키텍쳐에 맞게 다운로드 할 수 있게 내려줌. 이전처럼 x64로 플랫폼이 바뀌거나 할때 재컴파일해서 앱스토어에 업로드 할 필요가 없음. bitcode가지고 자기들이 알아서 아키텍쳐에 맞게 컴파일하니깐..TODO 수정예정

### XCode Bitcode 지원
  * XCode의 프로젝트 설정에서 Enable Bitcode를 enable한다.
  * 아래 명령어를 통하여 bitcode가 들어가 있는지 확인한다.
  ```
  $ otool -arch armv7 -l framework/framework  | grep __LLVM
  $ otool -arch armv64 -l framework/framework  | grep __LLVM
  ```
  * bitcode가 들어가 있음에도 어카이브가 실패하는 경우가있음
  * 보통 static라이브러리인 경우 해당 현상이 발생(*.a) 
  * Xcode의 Skip Install옵션 YES 확인, XCode 프로젝트에서 other c flags, other c++ flags에 -fembed-bitcode값을 추가하고 user defined에 BITCODE_GENERATION_MODE키 추가와 함꼐 값으로 bitcode를 추가한다.
