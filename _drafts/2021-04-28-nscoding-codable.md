objective-c 와 swift를 같이 써야하는 경우가 있는데
swift에 cordable을 보고 objective-c에는 비슷한게 없나 찾아보다가 nscoding을 찾게되어 써보았는데..
오브젝트씨의 NSCoding을 json으로 바꿔주는건..불가능했다.(일반 NSObject의 경우 오픈소스 프레임워크를 쓰면 json으로 가능하긴함)
NSCoding은 그냥 객체 어카이빙에 사용할 뿐이지.. json과는 1도 연관이 없다.
그래도 써봤으니깐 정리하는 차원에서 적어 놓는다.
NSCoding을 상속받고 해당 coder에 대한 프로퍼티를 지정해주면 이제 NSArchive를 통해서 파일에 객체를 읽고 쓰는게 가능해진다.

스위프트에 Cordable은 객체를 json으로 시리얼라이징 할수 있다..! 엄청난 기능
진짜 편한것이었다...
