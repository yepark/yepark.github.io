---
layout: single
title: "[Jenkins] Jenkins설치 및 Fortify 연동 "
date: 2020-08-04 20:36:00
comments: true
categories:
  - ios
# 목차
toc: true
toc_sticky: true
tags: [iOS, XCode, Jenkins]
---
## Jenkins
> Jenkins는 소프트웨어 빌드, 테스트, 제공 또는 배포와 관련된 모든 종류의 작업을 자동화하는 데 사용할 수있는 독립형 오픈 소스 자동화 서버입니다.
Jenkins는 네이티브 시스템 패키지, Docker를 통해 설치하거나 JRE (Java Runtime Environment)가 설치된 모든 컴퓨터에서 독립형으로 실행할 수도 있습니다. - jenkis.io

## Jenkins 사용 목적
- 배포 자동화를 통한..편해지기 위한 목적..-_-;
- 유닛테스트 자동화를 통한 소스 안정화
- XCode Server가 더 편해 보이지만.. 회사에서 젠킨스를 사용함으로 공부 차원에서 사용
- Jenkins-Fortify 플러그인 사용을 통한 회사 업무 적용(더 편해지고자..)

## Jenkins 설치 및 실행
- Jenkins를 다운로드후 설치한다. [젠킨스 다운](https://get.jenkins.io/osx-stable/)  
or  
Homebrew가 설치되어 있는 경우
```
//Homebrew를 통한 설치
brew install jenkins-lts
```  
- Jenkins를 실행한다.
```
brew services start jenkins-lts // Jenkins실핼
백그라운드로 실행 jenkins-lts // 백그라운드로 실행
```  

- http://localhost:8080에 접속한다. 붉은색 텍스트 경로로 이동하여 패스워드를 복사하고, 텍스트 필드에 입력한다.
![Jenkins](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/jenkins1.png)  

- 이후 진행은 일반적인 설치 작업으로 계정 설정후, 설치가 완료되면 아래와 같은 화면이 나타난다.
![Jenkins](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/jenkins6.png)  

## Jenkins 기본 설정
- 기본 설정

## Jenkins-Fortify 연동
- https://plugins.jenkins.io/fortify/ 에서 플러그인을 다운받아 설치한다.
- https://www.microfocus.com/documentation/fortify-jenkins-plugin/ 설치 문서 참고
- 설치후 Fortify Assessment 설정을 정상적으로 하였으나 session id오류가 나는 경우 ios build 폴더를 삭제후에 빌드하도록 한다.

## 참고 사이트
- [jenkins.io](https://www.jenkins.io/)
- [fortify](https://www.microfocus.com/documentation/fortify-jenkins-plugin/)
