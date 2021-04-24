---
layout: single
title: "[Jenkins] MacOS Jenkins설치 및 Fortify 연동 "
date: 2020-08-04 20:36:00
comments: true
categories:
  - ios
# 목차
toc: true
toc_sticky: true
tags: [iOS, XCode, Jenkins, Fortify]
---
## Jenkins
> Jenkins는 소프트웨어 빌드, 테스트, 제공 또는 배포와 관련된 모든 종류의 작업을 자동화하는 데 사용할 수있는 독립형 오픈 소스 자동화 서버입니다.
Jenkins는 네이티브 시스템 패키지, Docker를 통해 설치하거나 JRE (Java Runtime Environment)가 설치된 모든 컴퓨터에서 독립형으로 실행할 수도 있습니다. - jenkis.io

## Jenkins 사용할려는 목적
- 배포 자동화를 통한 빌드의 안정화 ~~(편해지기 위한 목적..-_-;)~~
- 유닛테스트 자동화를 통한 오류 대응
- 본인은 회사에서 젠킨스를 사용함으로.. 공부 차원에서 사용(배포서버를 처음 구축 한다면 XCode Server가 더 좋아 보임)
- Jenkins-Fortify 플러그인을 사용할 수 있어 Fortify를 업무에 적용중인 회사는 한번에 처리 가능

## Jenkins 설치 및 실행
- Jenkins를 다운로드후 설치한다. <https://get.jenkins.io/osx-stable/> (현재 macOS용 네이티브 인스톨러는 deprecate되었다.) 
```
// Homebrew가 설치되어 있는 경우 Homebrew를 통한 설치
brew install jenkins-lts

// 삭제(~/.jenkins 파일도 삭제해야 한다)
brew uninstall jenkins-lts
```  
- Jenkins를 실행한다.  
```
brew services start jenkins-lts // 백그라운드 실행
brew services stop jenkins-lts // 백그라운드 실행 중단
jenkins-lts // Jenkins 콘솔 실행
```  
- 브라우저를 통해 http://localhost:8080에 접속한다. 아래 붉은색 텍스트 경로로 이동하여 초기 어드민 패스워드 파일 안의 내용를 복사하고, 텍스트 필드에 입력한다.
![Jenkins](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/jenkins1.png)
{: .full}

- 이후 진행은 일반적인 설치 작업이다. 플러그인은 구미에 맞게 선택한 후, 계정 설정을 마무리하면 아래와 같은 화면이 나타난다.
![Jenkins](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/jenkins6.png)
{: .full}

- Credentials 설정 부분에서 키젠 및 계정정보를 설정한다.(생략)

## XCode 빌드 설정
- Jenkins pluginManager에서 Xcode integration 검색후 설치한다.(재시작 필요)
![Jenkins](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/jenkins8.png)
- 대쉬 보드에서 새로운 Item 추가 및 이름을 설정한다.
- 프로젝트 성격을 선택한다.(FreeStyle project선택)
- 추가된 프로젝트 Item 선택후 구성으로 들어간다.
- github을 사용하는 경우, 레포지토리 정보를 입력한다. 
![Jenkins](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/jenkins9.png)
- 그외 나머지 설정은 필요한 부분에 대해 개별적으로 선택하고 Build로 넘어간다.
- Add Build Step 추가 XCode선택후(Xcode integration이 설치되어 있어야 나온다)
![Jenkins](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/jenkins11.png) 
- 애플 계정 및 프로젝트 타겟을 설정한다. 나머지 셋팅은 자신의 프로젝트 환경에 따라 설정한다.
![Jenkins](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/jenkins7.png)
- 환경 설정후 프로젝트 Item의 Build Now를 클릭하면 빌드후 성공시 대쉬보드에 프로젝트에 대한 상태가 변경된다.

## Jenkins-Fortify 연동
- Jenkins pluginManager에서 fortify를 검색후 설치한다.(재시작 필요)
![Jenkins](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/jenkins_fortify.png)
{: .full}

- Docker를 이용하는 경우 - <https://plugins.jenkins.io/fortify/>
- microfocus에 fortify-jenkins-plugin에 대한 문서가 있으니 참고 하도록 한다. (<https://www.microfocus.com/documentation/fortify-jenkins-plugin/>)
- Jenkins 프로젝트 구성에서 빌드후 조치탭으로 이동후 Fortify Assessment 선택한다.
![Jenkins](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/jenkins_fortify2.png)
{: .full}
![Jenkins](https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/jenkins10.png) 
- 어플리케이션 타입은 Other로 선택후 SCA와 룰팩 설정을 끝마친다. 


- Jenkins plugin 설치후 빌드 설정 및 Fortify Assessment 설정을 정상적으로 하였으나 **session id오류**가 나는 경우 ios build 폴더를 삭제후에 빌드 하도록 한다.

## 참고 사이트
- [jenkins.io](https://www.jenkins.io/)
- [fortify](https://www.microfocus.com/documentation/fortify-jenkins-plugin/)
- [fortify-docker](https://plugins.jenkins.io/fortify/)
