from pydantic import BaseModel, EmailStr
from typing import List, Optional


class Education(BaseModel):
    institution: str
    degree: str
    year: str


class Experience(BaseModel):
    company: str
    position: str
    duration: str
    description: str


class CVModel(BaseModel):
    full_name: str
    job_title: str          # Masalan: Senior Backend Developer
    email: EmailStr
    phone: str
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: str            # O'zi haqida qisqacha
    skills: List[str]
    education: List[Education]
    work_experience: List[Experience]
    languages: List[str]


class CVRequest(BaseModel):
    """Veb-forma uchun oddiy model."""
    name: str
    email: str
    skills: str
    experience: str