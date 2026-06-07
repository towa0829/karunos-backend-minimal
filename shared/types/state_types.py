from typing import Annotated
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

class Parts(TypedDict):
    category: str
    data: dict

class Section(TypedDict):
    section_title: str
    parts: list[Parts]

class Page(TypedDict):
    page_title: str
    sections: list[Section]
    resource: list[str]
    query: str

class State(TypedDict):
    messages: Annotated[list, add_messages]
    page: Page
    query_id: str