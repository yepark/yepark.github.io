import json, hashlib

def decl(dtype, ident, payload):
    body = {"Type": dtype, "Identifier": ident, "Payload": payload}
    # ServerToken: 내용이 바뀌면 함께 바뀌는 값. 여기서는 내용의 해시로 만든다
    body["ServerToken"] = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    return body

passcode = decl("com.apple.configuration.passcode.settings", "com.example.passcode",
                {"RequirePasscode": True, "MinimumLength": 6, "MaximumFailedAttempts": 10})
update = decl("com.apple.configuration.softwareupdate.enforcement.specific", "com.example.os-update",
              {"TargetOSVersion": "26.2", "TargetLocalDateTime": "2026-12-15T18:00:00",
               "DetailsURL": "https://it.example.com/os-update"})
subs = decl("com.apple.configuration.management.status-subscriptions", "com.example.status",
            {"StatusItems": [{"Name": "device.operating-system.version"},
                             {"Name": "softwareupdate.install-state"},
                             {"Name": "passcode.is-compliant"}]})
activation = decl("com.apple.activation.simple", "com.example.activation.ipad",
                  {"StandardConfigurations": ["com.example.passcode", "com.example.os-update", "com.example.status"],
                   "Predicate": "@status(device.model.family) == 'iPad'"})

decls = [passcode, update, subs, activation]
manifest = {"Declarations": {
    "Configurations": [{"Identifier": d["Identifier"], "ServerToken": d["ServerToken"]} for d in decls[:3]],
    "Activations": [{"Identifier": activation["Identifier"], "ServerToken": activation["ServerToken"]}],
    "Assets": [], "Management": []},
    "DeclarationsToken": hashlib.sha256("".join(d["ServerToken"] for d in decls).encode()).hexdigest()[:16]}
tokens = {"SyncTokens": {"DeclarationsToken": manifest["DeclarationsToken"], "Timestamp": "2026-11-27T09:00:00Z"}}

for name, obj in [("passcode", passcode), ("update", update), ("activation", activation), ("manifest", manifest), ("tokens", tokens)]:
    s = json.dumps(obj, ensure_ascii=False, indent=2)
    json.loads(s)
    print(f"--- {name}\n{s}")
