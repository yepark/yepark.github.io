"""Download Apple's root CA and the sample attestation object from
Apple's "Attestation Object Validation Guide" into this folder."""

import json
import pathlib
import urllib.request

HERE = pathlib.Path(__file__).parent
ROOT_URL = ("https://www.apple.com/certificateauthority/"
            "Apple_App_Attestation_Root_CA.pem")
GUIDE_URL = ("https://developer.apple.com/tutorials/data/documentation/"
             "devicecheck/attestation-object-validation-guide.json")


def code_listings(node, out):
    if isinstance(node, dict):
        if node.get("type") == "codeListing":
            out.append("\n".join(node["code"]))
        for v in node.values():
            code_listings(v, out)
    elif isinstance(node, list):
        for v in node:
            code_listings(v, out)
    return out


def main():
    with urllib.request.urlopen(ROOT_URL) as r:
        (HERE / "Apple_App_Attestation_Root_CA.pem").write_bytes(r.read())
    with urllib.request.urlopen(GUIDE_URL) as r:
        doc = json.load(r)
    blocks = code_listings(doc["primaryContentSections"], [])
    # The attestation object is the long Base64 block starting with "o2Nm".
    sample = next(b.strip().strip('"') for b in blocks
                  if b.strip().strip('"').startswith("o2Nm"))
    (HERE / "apple_sample_attestation.b64").write_text(sample + "\n")
    print("saved Apple_App_Attestation_Root_CA.pem and",
          f"apple_sample_attestation.b64 ({len(sample)} chars)")


if __name__ == "__main__":
    main()
