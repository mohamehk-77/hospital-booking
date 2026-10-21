from datetime import time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScheduleCreate(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0 = Monday ... 6 = Sunday")
    start_time: time
    end_time: time
    slot_minutes: int = Field(default=30, ge=5, le=240)

    @model_validator(mode="after")
    def check_times(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class ScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    weekday: int
    start_time: time
    end_time: time
    slot_minutes: int
    is_active: bool