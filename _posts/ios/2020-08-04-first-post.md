---
layout: posts
title: "[XCode]iOS 프로젝트 프레임워크 추가시 file not found 오류"
date: 2020-08-04
comments: true
categories:
  - ios
tags: [iOS, XCode, Framework]
# 목차
toc: true
toc_sticky: true
---

###### 프레임워크를 정상적으로 추가 하였으나 'file not found'가 발생하는 경우

* 추가할 프레임워크가 static또는 dynamic인지 확인한다.(file명령어를 통하여 확인 가능)
```
$ file 파일명
```
![Framework1][logo1]

[logo1]: https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/screen_shot_20200805_3.png "check framework"


1. 프레임워크가 dynamic인 경우 General탭의 Frameworks, Libraries, and Embedded Content에 포함되어야 한다.(Build Phases에는 Embed Frameworks에만 포함)
![Framework2][logo2]

[logo2]: https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/screen_shot_20200805_2.png "check embed1"
![Framework3][logo3]

[logo3]: https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/screen_shot_20200805_4.png "check embed2"


2. 정상적으로 추가가 되었으나 오류가 나는 경우 Build Setting에 Search Framework를 확인한다.(<mark style='background-color: #fff5b1'> 프로젝트 하위 경로가 아닌 다른 곳에 프레임워크가 있는 경우 Search Framework에 포함안되는 경우가 있다. </mark>)
![Framework4][logo4]

[logo4]: https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/screen_shot_20200805_1.png "check path"
