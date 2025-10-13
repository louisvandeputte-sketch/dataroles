"""Pydantic models for data validation and serialization."""

from models.linkedin import (
    LinkedInJobPosting,
    LinkedInCompany,
    LinkedInLocation,
    LinkedInBaseSalary,
    LinkedInJobPoster
)

__all__ = [
    "LinkedInJobPosting",
    "LinkedInCompany",
    "LinkedInLocation",
    "LinkedInBaseSalary",
    "LinkedInJobPoster"
]
