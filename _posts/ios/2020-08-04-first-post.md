---
layout: single
title: "[XCode] 프로젝트에 프레임워크 추가 하기 "
date: 2020-08-04 12:00:00
comments: true
categories:
  - ios
tags: [iOS, XCode, Framework]
# 목차
toc: false
toc_sticky: false
---
## 프로젝트에 프레임워크를 추가할때 확인 사항

1. 추가할 프레임워크가 static으로 빌드되어 있는지 또는 dynamic으로 빌드되어 있는지 확인한다. 터미널에서 **file** 명령어를 통하여 확인 가능하다.  
```
$ file TestDummy.framework/TestDummy
TestDummy: Mach-O 64-bit dynamically linked shared library arm64 // 동적으로 빌드된 파일
```  
<br/>
2. 프레임워크가 dynamic으로 빌드 된 경우 XCode프로젝트의 General탭 **Frameworks, Libraries, and Embedded Content** 에 포함되어야 한다.  
![Embedded](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/screen_shot_20200805_2.png)  
<br/>
3. Build Phases 탭에서는 **Embed Frameworks**만 포함 시킨다.  
![Embedded](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/screen_shot_20200805_4.png)  
<br/>
4. 프레임워크를 정상적으로 추가 하였으나 **'file not found'** 오류가 발생하는 경우, 프로젝트 Build Settings탭에 **Search Framework**를 확인해 본다.(<mark  style='background-color: #fff5b1'> 프로젝트 하위 경로가 아닌 곳에 있는 프레임워크를 추가 하는 경우 Search Framework에 포함 안 되는 경우가 있다. </mark>)  
![Embedded](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/screen_shot_20200805_1.png)
