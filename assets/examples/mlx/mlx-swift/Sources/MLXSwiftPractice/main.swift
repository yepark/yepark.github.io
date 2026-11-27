// MLX Swift로 배열과 신경망 다루기 - 본문 예제 모음
// 이 파일은 작성 환경에서 빌드하지 못했다. 사용 중인 mlx-swift 버전에 맞게 고쳐 쓴다.
import MLX
import MLXNN
import MLXOptimizers

func arrays() {
    let a = MLXArray([1, 2, 3, 4] as [Float], [2, 2])
    let b = MLXArray([1, 1] as [Float], [2, 1])

    print(a.shape, a.dtype)      // [2, 2] float32
    print(matmul(a, b))          // [[3], [7]]
    print(a * 10)                // 원소별 곱
    print(a.sum(axis: 1))        // 행마다 합: [3, 7]
    print(a.mean(axis: 0))       // 열마다 평균: [2, 3]
}

func lazyEval() {
    let x = MLXArray(0 ..< 1_000_000).asType(.float32)
    let y = (x * 2 + 1).sum()   // 아직 계산하지 않음

    eval(y)                      // 여기서 계산
    print(y.item(Float.self))    // 값을 꺼낼 때도 계산이 일어난다
}

func gradDemo() {
    // f(x) = x² 의 합, 기울기는 2x
    let f: (MLXArray) -> MLXArray = { x in (x * x).sum() }
    let df = grad(f)

    let x = MLXArray([1, 2, 3] as [Float])
    print(df(x))   // [2, 4, 6]
}

func linearRegression() {
    let xs = MLXArray([0, 1, 2] as [Float])
    let ys = MLXArray([1, 3, 5] as [Float])   // y = 2x + 1

    func loss(_ p: MLXArray) -> MLXArray {
        let w = p[0], b = p[1]
        return square(w * xs + b - ys).mean()
    }

    let lossAndGrad = valueAndGrad(loss)
    var p = MLXArray([0, 0] as [Float])

    for step in 1 ... 500 {
        let (l, g) = lossAndGrad(p)
        p = p - 0.1 * g
        eval(p)
        if step == 1 || step == 500 {
            print("step \(step) loss \(l.item(Float.self)) w \(p[0].item(Float.self)) b \(p[1].item(Float.self))")
        }
    }
}

class MLP: Module, UnaryLayer {
    @ModuleInfo var l1: Linear
    @ModuleInfo var l2: Linear

    init(hidden: Int) {
        self.l1 = Linear(2, hidden)
        self.l2 = Linear(hidden, 1)
        super.init()
    }

    func callAsFunction(_ x: MLXArray) -> MLXArray {
        l2(relu(l1(x)))
    }
}

func xorDemo() {
    let x = MLXArray([0, 0, 0, 1, 1, 0, 1, 1] as [Float], [4, 2])
    let y = MLXArray([0, 1, 1, 0] as [Float], [4, 1])

    MLXRandom.seed(0)
    let model = MLP(hidden: 8)
    eval(model)   // 지연된 파라미터 초기화를 미리 실행

    func loss(model: MLP, x: MLXArray, y: MLXArray) -> MLXArray {
        mseLoss(predictions: model(x), targets: y, reduction: .mean)
    }

    let lossAndGrad = valueAndGrad(model: model, loss)
    let optimizer = SGD(learningRate: 0.5)

    for step in 1 ... 500 {
        let (l, grads) = lossAndGrad(model, x, y)
        optimizer.update(model: model, gradients: grads)
        eval(model, optimizer)
        if step % 100 == 0 {
            print("step \(step) loss \(l.item(Float.self))")
        }
    }

    print(round(model(x)))   // 기대값: [[0], [1], [1], [0]]
}

arrays()
lazyEval()
gradDemo()
linearRegression()
xorDemo()
