from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


def get_chat_prompt(default_human_prompt,
                    default_system_prompt=None,
                    image_url=None) -> ChatPromptTemplate:
    system = default_system_prompt
    human = default_human_prompt

    messages = []

    if system:
        messages.append(SystemMessage(content=system))

    human_message = HumanMessagePromptTemplate.from_template(human)
    messages.append(human_message)

    if image_url:
        img_messag = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                },
            ]
        )
        messages.append(img_messag)

    return ChatPromptTemplate.from_messages(messages)
