---
layout: posts
title: "XCode Bitcode 지원 "
date: 2021-04-09 14:26:00
comments: true
categories:
  - ios
# 목차
toc: true
toc_sticky: true
---

### Bitcode
  * 컴파일 된 프로그램의 중간 표현(Intermediate Representation)
  * iOS 앱의 경우 bitcode가 기본값이지만 활성화 여부 선택 가능(watchOS 및 tvOS 앱의 경우 bitcode가 필요)
  * bitcode를 사용할려면 앱과 프레임 워크에 모두 bitcode가 포함되어야함
  * 예전에는 유니버셜빌드로 모든 아키텍쳐를 전부 포함하여 앱스토어에 업로드하였지만, bitcode가 생김으로써 bitcode로 빌드시 앱스토어에 업로드후 필요한 아키텍쳐를 앱스토어에서 재컴파일하여 사용자가 다운로드 할 수 있게 된듯하다. 이전처럼 x64로 플랫폼이 변할때 재빌드해서 앱스토에 업로드할 필요성이 사라짐.

### Bitcode 설정 및 지원 여부 확인
  * XCode의 프로젝트 설정에서 Enable Bitcode를 enable한다.
  * 아래 명령어를 통하여 bitcode로 빌드가 되었는지 확인이 가능하다.
  ```
  $ otool -arch armv7 -l framework/framework  | grep __LLVM
  $ otool -arch armv64 -l framework/framework  | grep __LLVM
  ```
  * 위 명령어를 통하여 bitcode를 확인한 경우에도 archive에 실패하는 경우가 있는데, 보통 static 라이브러리인 경우 해당 현상이 잦은듯 하다. Xcode의 Skip Install옵션 YES 확인, XCode 프로젝트에서 other c flags, other c++ flags에 -fembed-bitcode값을 추가하고 user defined에 BITCODE_GENERATION_MODE키 추가와 함꼐 값으로 bitcode를 추가한다.

## 참고 사이트

  - [배포 옵션-Xcode 도움말](https://help.apple.com/xcode/mac/11.0/index.html?localePath=en.lproj#/devde46df08a)
  - [IR(Intermediate Representation)](https://www.lazenca.net/pages/viewpage.action?pageId=6324673)
  - [stackoverflow](https://stackoverflow.com/questions/61824439/bitcode-bundle-could-not-be-generated-because)
  - [정적라이브러리 bitcode](https://oraora.tistory.com/entry/iOS-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%EC%97%90%EC%84%9C-%EC%82%AC%EC%9A%A9%ED%95%98%EB%8A%94-%EC%A0%95%EC%A0%81-%EB%9D%BC%EC%9D%B4%EB%B8%8C%EB%9F%AC%EB%A6%AC%EB%8F%84-Bitcode-%EC%A0%81%EC%9A%A9)

  