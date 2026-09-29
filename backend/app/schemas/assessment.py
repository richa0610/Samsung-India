from typing import Annotated, List, Optional

from pydantic import BaseModel, Field

from app.schemas._common import IdStr


class QuestionOption(BaseModel):
    id: str
    text: str


class QuestionOut(BaseModel):
    id: int
    question: str
    question_type: str
    sort_order: int
    options: List[QuestionOption]


class AssessmentQuestionsOut(BaseModel):
    title: Optional[str] = None
    testTime: Optional[str] = None
    questions: List[QuestionOut]


class AnswerIn(BaseModel):
    questionId: Annotated[int, Field(ge=1)]
    selectedOption: Optional[Annotated[str, Field(max_length=200)]] = None


class SubmitRequest(BaseModel):
    conferenceUid: IdStr
    answers: Annotated[List[AnswerIn], Field(max_length=500)]


class SubmitResult(BaseModel):
    totalScore: float
    maxScore: float
    percentage: float
    correctCount: int
    totalQuestions: int


class LeaderboardUserOut(BaseModel):
    rank: int
    traineeUid: str
    name: str
    score: str
    accuracy: str
    percentage: float
    timeTaken: str
    isYou: bool


class LeaderboardResponse(BaseModel):
    title: Optional[str] = None
    totalQuestions: int = 0
    userRank: Optional[int] = None
    userScore: Optional[float] = None
    userAccuracy: Optional[float] = None
    timeTakenFormatted: Optional[str] = None
    correctCount: Optional[int] = None
    incorrectCount: Optional[int] = None
    leaderboard: List[LeaderboardUserOut]

