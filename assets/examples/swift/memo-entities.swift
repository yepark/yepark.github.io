import AppIntents
import Foundation

struct MemoRecord: Sendable {
    let id: String
    let title: String
    let body: String
}

actor MemoStore {
    static let shared = MemoStore()
    private var records: [MemoRecord] = [
        .init(id: "memo-001", title: "여행 준비", body: "여권을 확인한다."),
        .init(id: "memo-002", title: "여행 준비", body: "충전기를 챙긴다.")
    ]

    func all() -> [MemoRecord] { records }
    func remove(id: String) { records.removeAll { $0.id == id } }
}

struct MemoEntity: AppEntity {
    static let typeDisplayRepresentation: TypeDisplayRepresentation = "메모"
    static let defaultQuery = MemoQuery()
    let id: String
    let title: String

    var displayRepresentation: DisplayRepresentation {
        DisplayRepresentation(title: "\(title)", subtitle: "\(id)")
    }
}

struct MemoQuery: EntityStringQuery {
    private func entities(_ records: [MemoRecord]) -> [MemoEntity] {
        records.map { MemoEntity(id: $0.id, title: $0.title) }
    }

    func entities(for identifiers: [String]) async throws -> [MemoEntity] {
        let records = await MemoStore.shared.all()
        return entities(records.filter { identifiers.contains($0.id) })
    }

    func entities(matching string: String) async throws -> [MemoEntity] {
        let records = await MemoStore.shared.all()
        return entities(records.filter { $0.title.localizedCaseInsensitiveContains(string) })
    }

    func suggestedEntities() async throws -> [MemoEntity] {
        entities(await MemoStore.shared.all())
    }
}

@main
struct Example {
    static func main() async throws {
        let query = MemoQuery()
        let matches = try await query.entities(matching: "여행")
        precondition(matches.count == 2)
        print("title search:", matches.map(\.id).sorted())

        let selected = try await query.entities(for: ["memo-002"])
        precondition(selected.map(\.id) == ["memo-002"])
        print("selected:", selected.map(\.id))

        await MemoStore.shared.remove(id: "memo-002")
        let deleted = try await query.entities(for: ["memo-002"])
        precondition(deleted.isEmpty)
        print("deleted ID:", deleted.count, "results")
    }
}
