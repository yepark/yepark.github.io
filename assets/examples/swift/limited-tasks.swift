// Swift 6.0.3, macOS command line; no network or UI framework.
func process(_ value: Int) async -> Int {
    value * 2
}

func processLimited(_ values: [Int], limit: Int) async -> [Int] {
    precondition(limit > 0, "limit must be positive")
    return await withTaskGroup(of: Int.self, returning: [Int].self) { group in
        var iterator = values.makeIterator()
        var results: [Int] = []
        for _ in 0..<min(limit, values.count) {
            if let value = iterator.next() {
                group.addTask { await process(value) }
            }
        }
        while let result = await group.next() {
            results.append(result)
            if let value = iterator.next() {
                group.addTask { await process(value) }
            }
        }
        return results
    }
}

@main
struct Demo {
    static func main() async {
        let result = await processLimited([1, 2, 3, 4, 5], limit: 2)
        precondition(result.sorted() == [2, 4, 6, 8, 10])
        let empty = await processLimited([], limit: 2)
        precondition(empty == [])
        print("doubled (sorted):", result.sorted())
        print("empty input: []")
    }
}
