"""MDM 등록 프로파일과 정책 프로파일을 만들고 검사한다.

만들기 (표준 라이브러리만):
  python3 make_policy_profiles.py
만들고 Apple 스키마로 검사 (PyYAML 필요):
  python3 make_policy_profiles.py <device-management 폴더>
"""
import hashlib
import json
import plistlib
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

OUT = Path("out")
ORG = "com.example"
NS = uuid.UUID("6f1b5a52-8d1e-4c51-9a4e-3f0d6c2b7a10")


def stable_uuid(ident, body):
    # 같은 내용이면 같은 UUID, 내용이 바뀌면 새 UUID
    blob = json.dumps(body, sort_keys=True, default=str)
    h = hashlib.sha256(blob.encode()).hexdigest()
    return str(uuid.uuid5(NS, f"{ident}:{h}")).upper()


def payload(ptype, ident, **keys):
    p = {"PayloadType": ptype, "PayloadVersion": 1,
         "PayloadIdentifier": ident}
    p.update(keys)
    p["PayloadUUID"] = stable_uuid(ident, p)
    return p


def profile(ident, name, contents, **extra):
    p = {"PayloadType": "Configuration",
         "PayloadVersion": 1,
         "PayloadIdentifier": ident,
         "PayloadDisplayName": name,
         "PayloadOrganization": "Example Corp",
         "PayloadContent": contents}
    p.update(extra)
    p["PayloadUUID"] = stable_uuid(ident, p)
    return p


# ---------- 1) MDM 등록 프로파일 ----------
ACCESS = {
    "프로파일 조회": 1, "프로파일 설치·제거": 2,
    "잠금·암호 제거": 4, "초기화": 8,
    "기기 정보 조회": 16, "네트워크 정보 조회": 32,
    "프로비저닝 프로파일 조회": 64,
    "프로비저닝 프로파일 설치·제거": 128,
    "앱 목록 조회": 256, "제한 조회": 512,
    "보안 정보 조회": 1024, "설정 변경": 2048,
    "앱 관리": 4096,
}

ca = payload(
    "com.apple.security.root", f"{ORG}.mdm.ca",
    PayloadCertificateFileName="mdm-ca.cer",
    PayloadContent=b"<DER of MDM server CA>")

scep = payload(
    "com.apple.security.scep", f"{ORG}.mdm.identity",
    PayloadContent={
        "URL": "https://mdm.example.com/scep",
        "Challenge": "<one-time challenge>",
        "Key Type": "RSA", "Keysize": 2048,
        "Subject": [[["CN", "device-identity"]]],
    })

mdm = payload(
    "com.apple.mdm", f"{ORG}.mdm.payload",
    ServerURL="https://mdm.example.com/mdm/connect",
    CheckInURL="https://mdm.example.com/mdm/checkin",
    Topic="com.apple.mgmt.External."
          "00000000-0000-0000-0000-000000000000",
    IdentityCertificateUUID=scep["PayloadUUID"],
    AccessRights=sum(ACCESS.values()),
    CheckOutWhenRemoved=True,
    SignMessage=True,
    ServerCapabilities=[
        "com.apple.mdm.per-user-connections",
        "com.apple.mdm.bootstraptoken"],
    ServerURLPinningCertificateUUIDs=[ca["PayloadUUID"]],
    CheckInURLPinningCertificateUUIDs=[ca["PayloadUUID"]])

enroll = profile(f"{ORG}.mdm", "Example MDM 등록",
                 [ca, scep, mdm])

# ---------- 2) 정책 프로파일: 목적별로 나눈다 ----------
PASSCODE = {
    "forcePIN": True, "allowSimple": False,
    "minLength": 6, "maxFailedAttempts": 10,
    "maxInactivity": 5, "maxGracePeriod": 1,
    "pinHistory": 3,
}
passcode = profile(
    f"{ORG}.policy.passcode", "보안 정책: 암호",
    [payload("com.apple.mobiledevice.passwordpolicy",
             f"{ORG}.policy.passcode.payload",
             **PASSCODE)])

# 감독 없이도 적용되는 데이터 유출 방지
dlp = profile(
    f"{ORG}.policy.dlp", "보안 정책: 데이터 유출 방지",
    [payload("com.apple.applicationaccess",
             f"{ORG}.policy.dlp.payload",
             allowOpenFromManagedToUnmanaged=False,
             requireManagedPasteboard=True,
             forceAirDropUnmanaged=True,
             allowManagedAppsCloudSync=False,
             allowUntrustedTLSPrompt=False)])

# 감독 기기 전용 기기 기능 제한
device = profile(
    f"{ORG}.policy.supervised",
    "보안 정책: 회사 기기 제한",
    [payload("com.apple.applicationaccess",
             f"{ORG}.policy.supervised.payload",
             allowAirDrop=False,
             allowEraseContentAndSettings=False,
             allowAccountModification=False,
             allowEnterpriseAppTrust=False,
             allowCloudBackup=False)])

# ---------- 3) 같은 암호 정책의 DDM 선언 ----------
TO_DDM = {
    "forcePIN": "RequirePasscode",
    "minLength": "MinimumLength",
    "maxFailedAttempts": "MaximumFailedAttempts",
    "maxInactivity": "MaximumInactivityInMinutes",
    "maxGracePeriod": "MaximumGracePeriodInMinutes",
    "pinHistory": "PasscodeReuseLimit",
}
ddm_body = {TO_DDM[k]: v for k, v in PASSCODE.items()
            if k in TO_DDM}
# allowSimple=false 는 RequireComplexPasscode=true
ddm_body["RequireComplexPasscode"] = True
ddm = {"Type": "com.apple.configuration.passcode.settings",
       "Identifier": f"{ORG}.passcode",
       "Payload": ddm_body}
ddm["ServerToken"] = stable_uuid(ddm["Identifier"], ddm)

FILES = {"enroll.mobileconfig": enroll,
         "passcode.mobileconfig": passcode,
         "dlp.mobileconfig": dlp,
         "supervised.mobileconfig": device}


def write_all():
    OUT.mkdir(exist_ok=True)
    for name, p in FILES.items():
        (OUT / name).write_bytes(plistlib.dumps(p))
    (OUT / "passcode.settings.json").write_text(
        json.dumps(ddm, ensure_ascii=False, indent=2))
    print("AccessRights =", mdm["AccessRights"])
    for f in sorted(OUT.iterdir()):
        print(f"wrote {f.name:26} {f.stat().st_size} B")
    if shutil.which("plutil"):
        for name in FILES:
            cmd = ["plutil", "-lint", str(OUT / name)]
            r = subprocess.run(cmd, capture_output=True,
                               text=True)
            print(r.stdout.strip())


# ---------- 스키마 검사 (PyYAML 필요) ----------
PY = {"<boolean>": bool, "<integer>": int,
      "<string>": str, "<array>": list,
      "<dictionary>": dict, "<data>": bytes,
      "<real>": float, "<date>": datetime}
STD = {"PayloadType", "PayloadVersion", "PayloadUUID",
       "PayloadIdentifier", "PayloadDisplayName",
       "PayloadDescription", "PayloadOrganization"}


def load(repo, ptype):
    import yaml
    if ptype.startswith("com.apple.configuration."):
        name = ptype.split(".", 3)[3]
        f = repo / "declarative/declarations/configurations"
    else:
        name = "TopLevel" if ptype == "Configuration" \
            else ptype
        f = repo / "mdm/profiles"
    return yaml.safe_load((f / f"{name}.yaml").read_text())


def ios_of(base, spec):
    o = dict(base)
    o.update((spec.get("supportedOS") or {}).get("iOS", {}))
    return o


def check(specs, data, base, where, errs, rows):
    by = {s["key"]: s for s in specs}
    for s in specs:
        if s.get("presence") == "required" \
                and s["key"] not in data:
            errs.append(f"{where}: 필수 키 {s['key']} 없음")
    for k, v in data.items():
        s = by.get(k)
        if s is None:
            if k not in STD:
                errs.append(f"{where}: 스키마에 없는 키 {k}")
            continue
        t = PY[s["type"]]
        bad = not isinstance(v, t) or \
            (t is int and isinstance(v, bool))
        if bad:
            errs.append(f"{where}.{k}: {s['type']} 아님")
            continue
        r = s.get("range") or {}
        if "min" in r and v < r["min"] or \
                "max" in r and v > r["max"]:
            errs.append(f"{where}.{k}={v}: 범위 {r}")
        allowed = s.get("rangelist")
        items = v if isinstance(v, list) else [v]
        sub = (s.get("subkeys") or [{}])[0]
        allowed = allowed or sub.get("rangelist")
        if allowed and any(i not in allowed for i in items):
            errs.append(f"{where}.{k}: 허용 값 아님")
        o = ios_of(base, s)
        if o.get("introduced") == "n/a" or o.get("removed"):
            errs.append(f"{where}.{k}: iOS 미지원")
        rows.append((k, s["type"], o))
        if t is dict and s.get("subkeys"):
            check(s["subkeys"], v, o, f"{where}.{k}",
                  errs, [])


def validate(repo):
    errs = []
    for name, prof in FILES.items():
        top = load(repo, "TopLevel")
        check(top["payloadkeys"], prof, {}, name, errs, [])
        print(f"\n## {name}")
        for p in prof["PayloadContent"]:
            sch = load(repo, p["PayloadType"])
            base = sch["payload"]["supportedOS"]["iOS"]
            rows = []
            check(sch["payloadkeys"], p, base,
                  p["PayloadType"], errs, rows)
            print(f"- {p['PayloadType']}"
                  f" (iOS {base['introduced']},"
                  f" multiple={base.get('multiple')})")
            for k, t, o in rows:
                ue = (o.get("userenrollment") or {}) \
                    .get("mode", "-")
                dep = o.get("deprecated", "-")
                print(f"  {k:34} {t:11}"
                      f" iOS {o.get('introduced'):6}"
                      f" sup={str(o.get('supervised')):5}"
                      f" UE={ue:9} dep={dep}")
    sch = load(repo, ddm["Type"])
    base = sch["payload"]["supportedOS"]["iOS"]
    print(f"\n## {ddm['Type']} (iOS {base['introduced']},"
          f" apply={sch['payload'].get('apply')})")
    by = {s["key"]: s for s in sch["payloadkeys"]}
    check(sch["payloadkeys"], ddm["Payload"], base,
          "DDM", errs, [])
    for k in ddm["Payload"]:
        print(f"  {k:28} combine="
              f"{by[k].get('combinetype')}")
    errs += extra_rules()
    print("\n오류:", errs or "없음")
    return errs


def extra_rules():
    errs = []
    a = mdm["AccessRights"]
    if a == 0:
        errs.append("AccessRights는 0이면 안 됨")
    if a & 2 and not a & 1:
        errs.append("AccessRights: 2에는 1 필요")
    if a & 128 and not a & 64:
        errs.append("AccessRights: 128에는 64 필요")
    # 같은 제한 키를 여러 페이로드에서 관리하지 않는다
    seen = {}
    for name, prof in FILES.items():
        for p in prof["PayloadContent"]:
            if p["PayloadType"] != \
                    "com.apple.applicationaccess":
                continue
            for k in set(p) - STD:
                if k in seen:
                    errs.append(f"{k}: {seen[k]}, {name}")
                seen[k] = name
    return errs


def broken_demo(repo):
    # 일부러 틀린 값: 기기는 이런 실수를 알려 주지 않는다
    bad = {
        "com.apple.applicationaccess":
            {"allowScreenshot": False},  # 대소문자 오타
        "com.apple.mobiledevice.passwordpolicy":
            {"minLength": 20,            # 범위 0~16
             "maxInactivity": "5"},      # 정수여야 함
    }
    errs = []
    for ptype, data in bad.items():
        sch = load(repo, ptype)
        base = sch["payload"]["supportedOS"]["iOS"]
        check(sch["payloadkeys"], data, base, ptype,
              errs, [])
    print("\n## 틀린 예제 검사")
    for e in errs:
        print(" ", e)


if __name__ == "__main__":
    write_all()
    if len(sys.argv) > 1:
        repo = Path(sys.argv[1])
        bad = validate(repo)
        broken_demo(repo)
        sys.exit(1 if bad else 0)
