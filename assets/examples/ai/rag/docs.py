from langchain_core.documents import Document

raw = [
    Document(
        page_content=(
            "환불 규정\n\n"
            "결제 후 7일 이내에는 전액 환불한다. "
            "7일이 지나면 사용한 일수만큼 빼고 환불한다.\n\n"
            "연간 플랜은 30일이 지나면 환불하지 않는다."
        ),
        metadata={"source": "refund.md"},
    ),
    Document(
        page_content=(
            "요금제 안내\n\n"
            "무료 플랜은 프로젝트를 3개까지 만든다. "
            "프로 플랜은 월 9,900원이고 프로젝트 제한이 없다."
        ),
        metadata={"source": "pricing.md"},
    ),
    Document(
        page_content=(
            "고객센터\n\n"
            "운영 시간은 평일 오전 9시부터 오후 6시까지다. "
            "주말과 공휴일에는 이메일로만 문의를 받는다."
        ),
        metadata={"source": "support.md"},
    ),
    Document(
        page_content=(
            "오류 E-4012\n\n"
            "카드 유효기간이 지났다는 뜻이다. "
            "새 카드를 등록하면 해결된다."
        ),
        metadata={"source": "error-4012.md"},
    ),
    Document(
        page_content=(
            "오류 E-4013\n\n"
            "카드 한도를 넘었다는 뜻이다. "
            "카드사에 한도를 확인한다."
        ),
        metadata={"source": "error-4013.md"},
    ),
]
