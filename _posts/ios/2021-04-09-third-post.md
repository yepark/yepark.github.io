---
layout: single
title: "[XCode] Bitcode 설정 방법"
date: 2021-04-09 14:26:00
comments: true
categories:
  - ios
# 목차
toc: true
toc_sticky: true
---
## Bitcode 요약
- 컴파일 된 프로그램의 중간 표현(Intermediate Representation)
- iOS앱의 경우 bitcode가 기본값이지만, 활성화 여부는 선택이 가능하다.(watchOS 및 tvOS 앱의 경우 bitcode가 필수)
- bitcode를 활성화하려면 앱과 프레임 워크에 모두 bitcode가 포함되어야 한다.
- 예전에는 유니버셜빌드 아키텍쳐를 앱스토어에 업로드하였지만, 현재는 bitcode로 빌드후 앱스토어에서 필요한 아키텍쳐를 사용자가 다운로드 할수 있게 되었다.

## Bitcode 설정
- XCode 프로젝트 Build Settings - Build Options의 Enable Bitcode를 활성화 한다.
![Embedded](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/bitcode.png) 

## Bitcode 지원 여부 확인
- 아래 명령어를 통하여 바이너리에 bitcode가 설정 되었는지 확인이 가능하다.
```
$ otool -arch armv7 -l framework/framework  | grep __LLVM
$ otool -arch armv64 -l framework/framework  | grep __LLVM
segname __LLVM  // bitcode 설정 확인
 segname __LLVM
```
- 위 명령어를 통하여 bitcode를 확인이 되어도 archive에 실패하는 경우가 있는데, 보통 static 라이브러리인 경우 해당 현상이 잦은듯 하다.  
빌드 실패시 XCode에 아래 프로젝트 설정을 추가해 본다.
  1. Skip Install옵션 YES 확인
  ![Embedded](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/bitcode3.png)  
  2. Other C Flags / Other C++ Flags에 -fembed-bitcode추가
  ![Embedded](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/bitcode1.png)  
  3. User-Defined에 BITCODE_GENERATION_MODE플래그 및 bitcode추가
  ![Embedded](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/bitcode2.png)  

## 참고 사이트
- [배포 옵션-Xcode 도움말](https://help.apple.com/xcode/mac/11.0/index.html?localePath=en.lproj#/devde46df08a)
- [IR(Intermediate Representation)](https://www.lazenca.net/pages/viewpage.action?pageId=6324673)
- [Stackoverflow](https://stackoverflow.com/questions/61824439/bitcode-bundle-could-not-be-generated-because)
- [정적라이브러리 bitcode](https://oraora.tistory.com/entry/iOS-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%EC%97%90%EC%84%9C-%EC%82%AC%EC%9A%A9%ED%95%98%EB%8A%94-%EC%A0%95%EC%A0%81-%EB%9D%BC%EC%9D%B4%EB%B8%8C%EB%9F%AC%EB%A6%AC%EB%8F%84-Bitcode-%EC%A0%81%EC%9A%A9)

  
