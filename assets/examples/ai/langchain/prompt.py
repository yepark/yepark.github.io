from langchain_core.prompts import (
    ChatPromptTemplate, MessagesPlaceholder)

prompt = ChatPromptTemplate.from_messages([
    ("system", "{level}에게 {n}문장으로 설명하세요."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])
print(prompt.input_variables)

easy = prompt.partial(level="초등학생")
print(easy.input_variables)

value = easy.invoke({
    "n": 2,
    "history": [("human", "안녕"), ("ai", "안녕하세요!")],
    "question": "리스트란?",
})
for m in value.to_messages():
    print(f"{m.type:6} {m.content}")

try:
    prompt.invoke({"level": "초보자", "question": "?"})
except KeyError as e:
    print("KeyError:", str(e)[:70], "...")
