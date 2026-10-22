from typing import Literal
from pydantic import BaseModel, Field

Issue = Literal["order", "missing", "damaged", "return", "refund", "partner", "human"]


class Item(BaseModel):
    name: str
    quantity_ordered: int = Field(ge=0)
    quantity_delivered: int = Field(ge=0)
    condition: str


class Order(BaseModel):
    order_id: str
    status: str
    delivery_status: str
    delivery_date: str | None = None
    issue_type: str | None = None
    missing_item_status: str | None = None
    damaged_item_case: str | None = None
    partner_order: bool = False
    partner_name: str | None = None
    return_eligible: bool | str | None = None
    refund_status: str = "onbekend"
    items: list[Item]
    recommended_next_step: str = ""
    handoff_reason: str = ""


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    message: str = Field(min_length=1, max_length=1000)
    category: Issue | None = None


class TraceStep(BaseModel):
    step: str
    detail: str


class ChatResponse(BaseModel):
    messages: list[str]
    mode: Literal["demo", "rasa"]
    order: Order | None = None
    case_id: int | None = None
    quick_replies: list[str] = []
    trace: list[TraceStep] = []


class CaseCreate(BaseModel):
    session_id: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    issue: Issue
    reason: str = Field(min_length=3, max_length=500)
    order_id: str | None = None
    summary: str = Field(min_length=3, max_length=1000)


class CaseUpdate(BaseModel):
    status: Literal["open", "investigating", "resolved"] | None = None
    assignee: str | None = Field(default=None, max_length=80)
