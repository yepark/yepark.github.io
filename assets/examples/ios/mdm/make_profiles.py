import plistlib, uuid, json

def payload(ptype, ident, extra):
    d = {"PayloadType": ptype, "PayloadIdentifier": ident,
         "PayloadUUID": str(uuid.UUID(int=hash(ident) & (2**128-1))).upper(),
         "PayloadVersion": 1}
    d.update(extra); return d

# 1) 등록 프로파일 (com.apple.mdm)
enroll = {
  "PayloadType": "Configuration", "PayloadVersion": 1,
  "PayloadIdentifier": "com.example.mdm.enroll",
  "PayloadUUID": "8A7B2C3D-0000-4000-8000-000000000001",
  "PayloadDisplayName": "Example MDM 등록",
  "PayloadContent": [
    {"PayloadType": "com.apple.security.scep", "PayloadVersion": 1,
     "PayloadIdentifier": "com.example.mdm.enroll.scep",
     "PayloadUUID": "8A7B2C3D-0000-4000-8000-000000000002",
     "PayloadContent": {"URL": "https://mdm.example.com/scep", "Challenge": "<일회용 값>",
                        "Key Type": "RSA", "Keysize": 2048,
                        "Subject": [[["CN", "device-identity"]]]}},
    {"PayloadType": "com.apple.mdm", "PayloadVersion": 1,
     "PayloadIdentifier": "com.example.mdm.enroll.mdm",
     "PayloadUUID": "8A7B2C3D-0000-4000-8000-000000000003",
     "ServerURL": "https://mdm.example.com/mdm/connect",
     "CheckInURL": "https://mdm.example.com/mdm/checkin",
     "Topic": "com.apple.mgmt.External.00000000-0000-0000-0000-000000000000",
     "IdentityCertificateUUID": "8A7B2C3D-0000-4000-8000-000000000002",
     "AccessRights": 8191, "CheckOutWhenRemoved": True,
     "ServerCapabilities": ["com.apple.mdm.per-user-connections", "com.apple.mdm.bootstraptoken"],
     "SignMessage": True},
  ],
}
open("enroll.mobileconfig","wb").write(plistlib.dumps(enroll))

# 2) Wi-Fi + 제한 프로파일
cfg = {
  "PayloadType": "Configuration", "PayloadVersion": 1,
  "PayloadIdentifier": "com.example.office",
  "PayloadUUID": "8A7B2C3D-0000-4000-8000-000000000010",
  "PayloadDisplayName": "사무실 기본 설정",
  "PayloadRemovalDisallowed": True,
  "PayloadContent": [
    {"PayloadType": "com.apple.wifi.managed", "PayloadVersion": 1,
     "PayloadIdentifier": "com.example.office.wifi",
     "PayloadUUID": "8A7B2C3D-0000-4000-8000-000000000011",
     "SSID_STR": "Example-Office", "EncryptionType": "WPA2", "AutoJoin": True,
     "Password": "<Wi-Fi 암호>"},
    {"PayloadType": "com.apple.applicationaccess", "PayloadVersion": 1,
     "PayloadIdentifier": "com.example.office.restrictions",
     "PayloadUUID": "8A7B2C3D-0000-4000-8000-000000000012",
     "allowCamera": False, "allowScreenShot": False,
     "allowAppInstallation": False},
    {"PayloadType": "com.apple.mobiledevice.passwordpolicy", "PayloadVersion": 1,
     "PayloadIdentifier": "com.example.office.passcode",
     "PayloadUUID": "8A7B2C3D-0000-4000-8000-000000000013",
     "forcePIN": True, "minLength": 6, "maxFailedAttempts": 10},
  ],
}
open("office.mobileconfig","wb").write(plistlib.dumps(cfg))

# 3) 명령 plist
cmd = {"CommandUUID": "0001-DEVINFO",
       "Command": {"RequestType": "DeviceInformation",
                   "Queries": ["DeviceName", "OSVersion", "SerialNumber", "IsSupervised", "BatteryLevel"]}}
open("cmd_deviceinfo.plist","wb").write(plistlib.dumps(cmd))
resp = {"UDID": "00008110-000A1B2C3D4E801E", "CommandUUID": "0001-DEVINFO", "Status": "Acknowledged",
        "QueryResponses": {"DeviceName": "영업팀 iPad 07", "OSVersion": "26.1", "SerialNumber": "F9XXXXXXXX",
                            "IsSupervised": True, "BatteryLevel": 0.82}}
open("resp_deviceinfo.plist","wb").write(plistlib.dumps(resp))

for f in ["enroll.mobileconfig","office.mobileconfig","cmd_deviceinfo.plist","resp_deviceinfo.plist"]:
    d = plistlib.load(open(f,"rb")); print(f, "OK", d.get("PayloadType") or d.get("Command",{}).get("RequestType") or d.get("Status"))
