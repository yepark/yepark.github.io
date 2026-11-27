#!/bin/sh
# 학습용 루트 CA와 서버 인증서를 만들고 검증한다. 실제 서비스에 쓰지 않는다.
set -e
cat > leaf.ext <<'EXT'
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature
extendedKeyUsage = serverAuth
subjectAltName = DNS:api.example.test, DNS:www.example.test
EXT
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes \
  -keyout ca.key -out ca.pem -days 365 -subj "/C=KR/O=Example Lab/CN=Example Lab Root CA" \
  -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign"
openssl req -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes \
  -keyout leaf.key -out leaf.csr -subj "/C=KR/O=Example Lab/CN=api.example.test"
openssl x509 -req -in leaf.csr -CA ca.pem -CAkey ca.key -CAcreateserial \
  -out leaf.pem -days 90 -extfile leaf.ext
openssl x509 -in leaf.pem -noout -text
openssl verify -CAfile ca.pem -verify_hostname api.example.test leaf.pem
