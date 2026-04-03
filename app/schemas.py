from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, Any, Dict
from enum import Enum


# Enums
class TransactionSource(str, Enum):
    MANUAL = "manual"
    BANK_IMPORT = "bank_import"
    EXCEL_IMPORT = "excel_import"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    ACHIEVED = "achieved"
    CANCELLED = "cancelled"


class RecommendationStatus(str, Enum):
    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"


# User schemas
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    created_at: datetime


# Profile schemas
class FamilyMember(BaseModel):
    name: str
    relation: str  # spouse, son, daughter
    age: Optional[int] = None
    hobbies: List[str] = []


class UserProfileCreate(BaseModel):
    first_name: Optional[str] = None
    age: Optional[int] = None
    occupation: Optional[str] = None
    city: Optional[str] = None
    hobbies: List[str] = []
    family_type: Optional[str] = None  # single, couple, family_with_kids
    family_members: List[FamilyMember] = []
    financial_goals: List[str] = []
    risk_tolerance: Optional[str] = None
    education_budget: Optional[int] = None


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    first_name: Optional[str]
    age: Optional[int]
    occupation: Optional[str]
    city: Optional[str]
    hobbies: List[str]
    family_type: Optional[str]
    family_members: List[FamilyMember]
    financial_goals: List[str]
    risk_tolerance: Optional[str]
    education_budget: Optional[int]
    profile_completed_at: Optional[datetime]
    updated_at: datetime


# Transaction schemas
class TransactionCreate(BaseModel):
    amount: float
    category_name: str
    date: date
    description: Optional[str] = None
    source: TransactionSource = TransactionSource.MANUAL


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    category_name: str
    date: date
    description: Optional[str]
    source: TransactionSource
    created_at: datetime


# Budget schemas
class BudgetLimitCreate(BaseModel):
    category_name: str
    monthly_limit: float


class BudgetLimitResponse(BaseModel):
    id: int
    category_name: str
    monthly_limit: float
    effective_from: date
    spent: Optional[float] = None
    remaining: Optional[float] = None


# Goal schemas
class GoalCreate(BaseModel):
    name: str
    target_amount: float
    deadline: Optional[date] = None
    priority: int = Field(1, ge=1, le=3)
    monthly_contribution: Optional[float] = None


class GoalResponse(BaseModel):
    id: int
    name: str
    target_amount: float
    current_amount: float
    deadline: Optional[date]
    priority: int
    monthly_contribution: Optional[float]
    status: GoalStatus
    progress_percent: float
    months_remaining: Optional[int]


# Education schemas
class EducationInterestCreate(BaseModel):
    person_id: str  # 'self', 'spouse', или имя
    area: str
    skill_level: str
    interest_level: int = Field(3, ge=1, le=5)
    budget_per_month: Optional[int] = None
    time_available: Optional[int] = None
    notes: Optional[str] = None


# Career schemas
class CareerAspirationCreate(BaseModel):
    person_id: str = 'self'
    current_industry: str
    desired_industry: str
    reason: str
    urgency: str  # immediate, within_year, planning
    target_income: Optional[int] = None


# Recommendation schemas
class RecommendationResponse(BaseModel):
    id: int
    person_id: str
    type: str
    title: str
    description: str
    estimated_cost: Optional[int]
    estimated_duration: Optional[str]
    expected_benefit: Optional[str]
    roi_months: Optional[int]
    status: RecommendationStatus
    created_at: datetime


# Chat schemas
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    suggestions: List[str] = []


# Upload schemas
class UploadPreviewResponse(BaseModel):
    months: List[str]
    categories: List[str]
    total_amount: float
    anomalies: List[Dict[str, Any]]


class UploadConfirmRequest(BaseModel):
    category_mapping: Dict[str, str]  # исходная категория -> системная категория
    exclude_anomalies: List[int] = []  # индексы аномалий для исключения

# Goal schemas (дополнение)
class GoalCreate(BaseModel):
    name: str
    target_amount: float
    deadline: Optional[date] = None
    priority: int = Field(1, ge=1, le=3)
    monthly_contribution: Optional[float] = None


class GoalResponse(BaseModel):
    id: int
    name: str
    target_amount: float
    current_amount: float
    deadline: Optional[date]
    priority: int
    monthly_contribution: Optional[float]
    status: GoalStatus
    progress_percent: float
    months_remaining: Optional[int]


class GoalContribute(BaseModel):
    amount: float


class GoalSuggestionRequest(BaseModel):
    target_amount: float
    months: int


class GoalSuggestionResponse(BaseModel):
    target_amount: float
    months: int
    monthly_contribution: float
    free_budget: float
    is_affordable: bool
    recommendation: str