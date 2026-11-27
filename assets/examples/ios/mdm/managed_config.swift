// managed_config.swift
// Reads managed app configuration and writes feedback
// through UserDefaults, as an MDM-managed iOS app does.
// On macOS this simulates MDM by writing the dictionary
// ourselves into a throwaway suite.
//
// Run: swiftc managed_config.swift -o managed_config
//      ./managed_config

import Foundation

let configKey = "com.apple.configuration.managed"
let feedbackKey = "com.apple.feedback.managed"

struct AppConfig: Equatable {
    var serverURL: URL
    var tenantID: String
    var allowExport: Bool
}

// Defaults used until (or unless) MDM sends values.
let fallback = AppConfig(
    serverURL: URL(string: "https://api.example.com")!,
    tenantID: "default",
    allowExport: true)

// Read the managed dictionary. Every value is checked,
// and anything missing or of the wrong type falls back.
func readConfig(_ d: UserDefaults)
    -> (AppConfig, [String]) {
    var c = fallback
    var errors: [String] = []
    guard let raw = d.dictionary(forKey: configKey) else {
        return (c, [])
    }
    if let s = raw["serverURL"] as? String,
       let u = URL(string: s), u.scheme == "https" {
        c.serverURL = u
    } else if raw["serverURL"] != nil {
        errors.append("serverURL must be an https URL")
    }
    if let t = raw["tenantID"] as? String, !t.isEmpty {
        c.tenantID = t
    } else if raw["tenantID"] != nil {
        errors.append("tenantID must be a string")
    }
    if let b = raw["allowExport"] as? Bool {
        c.allowExport = b
    } else if raw["allowExport"] != nil {
        errors.append("allowExport must be a boolean")
    }
    return (c, errors)
}

// Write feedback that the MDM server can read with the
// ManagedApplicationFeedback command.
func writeFeedback(_ d: UserDefaults, _ errs: [String]) {
    let fb: [String: Any] = [
        "configValid": errs.isEmpty,
        "configErrors": errs,
    ]
    d.set(fb, forKey: feedbackKey)
}

// Writing feedback also fires didChangeNotification,
// so only act when the config itself changed.
nonisolated(unsafe) var current: AppConfig? = nil
nonisolated(unsafe) var notes = 0
nonisolated(unsafe) var applied = 0

func onDefaultsChanged(_ d: UserDefaults) {
    notes += 1
    let (c, errs) = readConfig(d)
    guard c != current else { return }
    current = c
    applied += 1
    writeFeedback(d, errs)
    print("  applied: \(c.serverURL.absoluteString)",
          "tenant=\(c.tenantID) export=\(c.allowExport)")
    let fb = d.dictionary(forKey: feedbackKey) ?? [:]
    let ok = fb["configValid"] as? Bool ?? false
    let list = fb["configErrors"] as? [String] ?? []
    print("  feedback: valid=\(ok)", list)
}

// --- simulation ---
let suite = "example.managed-config-demo"
let d = UserDefaults(suiteName: suite)!
d.removePersistentDomain(forName: suite)

let token = NotificationCenter.default.addObserver(
    forName: UserDefaults.didChangeNotification,
    object: d, queue: nil) { n in
    if let ud = n.object as? UserDefaults {
        onDefaultsChanged(ud)
    }
}

print("[1] app launch, nothing from MDM yet")
onDefaultsChanged(d)

print("[2] MDM sends a valid config")
d.set([
    "serverURL": "https://mdm-demo.example.com",
    "tenantID": "sales-kr",
    "allowExport": false,
], forKey: configKey)

print("[3] MDM sends bad values")
d.set([
    "serverURL": "http://insecure.example.com",
    "tenantID": "sales-kr",
    "allowExport": "no",
], forKey: configKey)

print("handler calls:", notes, "applied:", applied)
NotificationCenter.default.removeObserver(token)
d.removePersistentDomain(forName: suite)
