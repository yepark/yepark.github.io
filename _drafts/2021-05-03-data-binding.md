## 스위프트 데이타 바인딩(Use Boxing)
데이타 바인딩은 아래 방법으로 할수 있음
1. kvo
2. delegate
3. FRP
4. Boxing 옵저버 프로퍼티 이용

4번에 대해.. 공부
```swift
final class Box<T> {
  //1
  typealias Listener = (T) -> Void
  var listener: Listener?
  //2
  var value: T {
    didSet {
      listener?(value)
    }
  }
  //3
  init(_ value: T) {
    self.value = value
  }
  //4
  func bind(listener: Listener?) {
    self.listener = listener
    listener?(value)
  }
}
```  

https://www.raywenderlich.com/6733535-ios-mvvm-tutorial-refactoring-from-mvc
