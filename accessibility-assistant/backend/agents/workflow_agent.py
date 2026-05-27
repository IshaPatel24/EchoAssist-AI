"""
VoiceForge — Workflow Agent
============================
Manages guided multi-step workflows for form completion.
Each workflow breaks a document into a sequence of voice prompts,
collecting one piece of information at a time.
"""

from typing import Dict, Optional
from models.schemas import WorkflowState, WorkflowStep
from services.qdrant_service import QdrantService
from services.lyzr_service import LyzrService
from services.document_service import DocumentService


# Friendly prompts per common field names
FIELD_PROMPTS = {
    "full_name": "What is the full name?",
    "date_of_birth": "What is the date of birth?",
    "address": "What is the address?",
    "phone": "What is the phone number?",
    "email": "What is the email address?",
    "emergency_contact": "Who is the emergency contact and their number?",
    "insurance_provider": "What is the insurance provider name?",
    "primary_complaint": "What is the primary reason for the visit or complaint?",
    "current_medications": "What are the current medications, if any?",
    "allergies": "Are there any known allergies?",
    "medical_history": "Any relevant medical history to mention?",
    "position_applied": "What position are you applying for?",
    "work_experience": "Please describe your work experience.",
    "education": "What is your highest level of education?",
    "skills": "What are your key skills?",
    "references": "Can you provide any references?",
    "availability": "When are you available to start?",
    "date_of_incident": "What was the date of the incident?",
    "location": "Where did this occur?",
    "description": "Please describe what happened.",
    "witnesses": "Were there any witnesses?",
    "injuries": "Were there any injuries?",
    "actions_taken": "What actions were taken afterward?",
    "meeting_title": "What is the title of this meeting?",
    "date": "What is the date?",
    "attendees": "Who attended?",
    "agenda": "What was the agenda?",
    "discussion_points": "What were the main discussion points?",
    "decisions_made": "What decisions were made?",
    "action_items": "What are the action items?",
    "next_meeting": "When is the next meeting?",
    "organization": "What is the organization or employer name?",
    "supervisor_name": "What is the supervisor's name?",
    "nature_of_disability": "Please briefly describe the nature of the disability or condition.",
    "requested_accommodations": "What accommodations are being requested?",
    "supporting_documentation": "Is there any supporting documentation available?",
    "preferred_start_date": "What is the preferred start date for accommodations?",
    "reporter_name": "What is your name?",
}


class WorkflowAgent:
    """Manages guided step-by-step data collection workflows."""

    def __init__(self, qdrant: QdrantService, lyzr: LyzrService, docs: DocumentService):
        self.qdrant = qdrant
        self.lyzr = lyzr
        self.docs = docs

    def create_workflow(self, template: Dict) -> WorkflowState:
        """Create a new workflow state from a template."""
        import uuid
        fields = template.get("fields", [])

        steps = []
        for i, field in enumerate(fields):
            prompt = FIELD_PROMPTS.get(field, f"Please provide the {field.replace('_', ' ')}.")
            steps.append(WorkflowStep(
                step_number=i + 1,
                title=field.replace("_", " ").title(),
                prompt=prompt,
                field_key=field,
                required=False,  # Allow skipping
                input_type="voice",
            ))

        return WorkflowState(
            workflow_id=str(uuid.uuid4()),
            template_name=template.get("name", "form"),
            current_step=0,
            total_steps=len(steps),
            steps=steps,
            collected_data={},
        )

    def get_current_step(self, state: WorkflowState) -> Optional[WorkflowStep]:
        """Get the current step object."""
        if state.current_step < len(state.steps):
            return state.steps[state.current_step]
        return None

    async def process_step(self, state: WorkflowState, user_response: str) -> Dict:
        """
        Process user's voice response for the current workflow step.
        Advances state and returns next step or completion.
        """
        current_step = self.get_current_step(state)
        if not current_step:
            return {"completed": True, "template": {"name": state.template_name}, "collected_data": state.collected_data}

        # Extract the answer from the user's speech
        extracted = await self.lyzr.extract_fields(
            user_response,
            [current_step.field_key],
            state.collected_data,
        )

        value = extracted.get(current_step.field_key)
        if value and value != "null":
            state.collected_data[current_step.field_key] = value

        # Advance step
        state.current_step += 1

        # Check if workflow is complete
        if state.current_step >= state.total_steps:
            # Find template from Qdrant would go here; use name for now
            return {
                "completed": True,
                "template": {"name": state.template_name, "title": state.template_name.replace("_", " ").title()},
                "collected_data": state.collected_data,
            }

        # Return next step
        next_step = self.steps_at(state, state.current_step)
        return {
            "completed": False,
            "current_step": state.current_step,
            "next_step": next_step,
            "collected_data": state.collected_data,
        }

    def steps_at(self, state: WorkflowState, index: int) -> Optional[WorkflowStep]:
        if 0 <= index < len(state.steps):
            return state.steps[index]
        return None
