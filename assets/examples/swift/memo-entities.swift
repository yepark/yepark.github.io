import AppIntents
import Foundation

struct MemoRecord: Sendable {
    let id: String
    let title: String
    let body: String
}

enum MemoError: Error {
    case missing
    case accessDenied
}

actor MemoStore {
    static let shared = MemoStore()
    private var records: [MemoRecord] = [
        .init(id: "memo-001", title: "여행 준비", body: "여권을 확인한다."),
        .init(id: "memo-002", title: "여행 준비", body: "충전기를 챙긴다.")
    ]

    // A small stand-in for the current account's record-level access rules.
    private var deniedIDs: Set<String> = []

    func allReadable() -> [MemoRecord] {
        records.filter { !deniedIDs.contains($0.id) }
    }
    func read(id: String) throws -> MemoRecord {
        guard let record = records.first(where: { $0.id == id }) else {
            throw MemoError.missing
        }
        guard !deniedIDs.contains(id) else { throw MemoError.accessDenied }
        return record
    }
    func deny(id: String) { deniedIDs.insert(id) }
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
        let records = await MemoStore.shared.allReadable()
        return entities(records.filter { identifiers.contains($0.id) })
    }

    func entities(matching string: String) async throws -> [MemoEntity] {
        let records = await MemoStore.shared.allReadable()
        return entities(records.filter { $0.title.localizedCaseInsensitiveContains(string) })
    }

    func suggestedEntities() async throws -> [MemoEntity] {
        entities(await MemoStore.shared.allReadable())
    }
}

struct ReadMemoIntent: AppIntent {
    static let title: LocalizedStringResource = "메모 읽기"
    static var authenticationPolicy: IntentAuthenticationPolicy { .requiresAuthentication }

    @Parameter(title: "메모")
    var memo: MemoEntity

    init() {}
    init(memo: MemoEntity) { self.memo = memo }

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        let current = try await MemoStore.shared.read(id: memo.id)
        return .result(value: current.body)
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

        let intent = ReadMemoIntent(memo: selected[0])
        let result = try await intent.perform()
        precondition(result.value == "충전기를 챙긴다.")
        print("read body:", result.value ?? "")

        await MemoStore.shared.deny(id: "memo-002")
        let hidden = try await query.entities(for: ["memo-002"])
        precondition(hidden.isEmpty)
        do {
            _ = try await intent.perform()  // The already-selected Entity is stale.
            preconditionFailure("A revoked record must not be readable")
        } catch MemoError.accessDenied {
            print("revoked access: denied")
        }

        await MemoStore.shared.remove(id: "memo-002")
        let deleted = try await query.entities(for: ["memo-002"])
        precondition(deleted.isEmpty)
        print("deleted ID:", deleted.count, "results")
        do {
            _ = try await intent.perform()
            preconditionFailure("A deleted record must not be readable")
        } catch MemoError.missing {
            print("deleted read: missing")
        }
    }
}
