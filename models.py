from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ShiftRequest:
    id: Optional[str] = None
    date_request: Optional[str] = None
    flight_number: Optional[str] = None
    requester_name: Optional[str] = None
    requester_employee_number: Optional[str] = None
    requester_email: Optional[str] = None
    cover_name: Optional[str] = None
    cover_employee_number: Optional[str] = None
    cover_email: Optional[str] = None
    supervisor_status: Optional[str] = None
    date_accepted_by_cover: Optional[str] = None
    supervisor_decision_date: Optional[str] = None
    supervisor_comments: Optional[str] = None
    supervisor_name: Optional[str] = None


@dataclass
class Employee:
    id: Optional[int] = None
    full_name: str = ""
    raic_color: str = ""
    email: str = ""
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Token:
    token: str
    shift_request_id: str
    expires_at: datetime
    used: bool = False
