---
title: MLX
parent: iOS
nav_order: 22
has_children: true
has_toc: false
permalink: /ai/mlx/
redirect_from:
  - /mlx/
last_modified_date: 2026-11-20
---

# MLX

같은 숫자 배열도 축을 다르게 해석하면 다른 손실을 만들고, 같은 연산식도 평가 경계를 잘못 잡으면 실행 시간을 잘못 측정한다. 이 연재는 작은 배열의 값과 shape에서 출발해 지연 평가, CPU·GPU 실행 엔진, 자동 미분과 학습 업데이트를 하나의 흐름으로 연결한다.

Python 기본 문법을 아는 독자는 앞의 개요와 배열 글부터 읽을 수 있다. 구현 분석이 목적이라면 실행 모델과 소스 분석을 함께 읽는다. 패키지 실행 결과와 개발 브랜치 소스 분석은 기준 버전을 구분해 기록한다.

[자동 미분과 학습 루프]({{ '/ai/mlx/training-loop/' | relative_url }})에서는 작은 선형 모델을 실제로 학습한다. 첫 손실과 기울기를 손으로 계산한 뒤 실행 결과와 대조하고, 파라미터 저장·복원까지 연결한다.

{% include series-list.html %}

## 재현 자료

[검증 스크립트]({{ '/assets/examples/mlx/reproduce.py' | relative_url }})는 배열 연산, 자동 미분, CPU/GPU 결과 비교와 측정 구간을 포함한다. 본문에 기록한 숫자는 특정 장치와 실행 조건의 관찰값이며 일반적인 성능 보증이 아니다.
