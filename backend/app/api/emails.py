import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user
from app.core.exceptions import NotFoundError, BadRequestError
from app.database import get_db
from app.models.outreach_email import OutreachEmail
from app.models.user import User
from app.schemas.email import (
    EmailDraftRequest,
    EmailUpdateRequest,
    EmailResponse,
    EmailDraftStatusResponse,
    EmailBulkPushRequest,
    EmailPushResponse,
    EmailBulkPushResponse,
)
from app.services.gmail import get_gmail_service
from app.workers.queue import enqueue

logger = logging.getLogger(__name__)

router = APIRouter(tags=["emails"])


def _email_to_response(email: OutreachEmail) -> EmailResponse:
    """Convert an ORM email to a response with denormalized contact/brand fields."""
    data = EmailResponse.model_validate(email)
    if email.contact:
        data.contact_name = email.contact.full_name
        data.contact_email = email.contact.email
        data.contact_title = email.contact.title
    if email.brand_target:
        data.brand_name = email.brand_target.company_name
    return data


@router.post("/emails/draft", response_model=EmailDraftStatusResponse, status_code=202)
async def trigger_draft_emails(
    body: EmailDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Draft outreach emails for selected contacts (async)."""
    if not body.contact_ids:
        raise BadRequestError("At least one contact_id is required")

    await enqueue(
        "run_draft_emails",
        [str(cid) for cid in body.contact_ids],
        str(body.creator_id),
        str(body.brand_target_id),
        str(current_user.agency_id),
        str(current_user.id),
    )
    logger.info(
        f"Enqueued email drafting for {len(body.contact_ids)} contacts"
    )

    return EmailDraftStatusResponse(status="processing")


@router.get("/creators/{creator_id}/emails", response_model=list[EmailResponse])
async def list_creator_emails(
    creator_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all outreach emails for a creator."""
    result = await db.execute(
        select(OutreachEmail)
        .where(
            OutreachEmail.creator_id == creator_id,
            OutreachEmail.agency_id == current_user.agency_id,
        )
        .options(
            selectinload(OutreachEmail.contact),
            selectinload(OutreachEmail.brand_target),
        )
        .order_by(OutreachEmail.created_at.desc())
    )
    emails = result.scalars().all()
    return [_email_to_response(e) for e in emails]


@router.get("/emails/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single outreach email."""
    result = await db.execute(
        select(OutreachEmail)
        .where(
            OutreachEmail.id == email_id,
            OutreachEmail.agency_id == current_user.agency_id,
        )
        .options(
            selectinload(OutreachEmail.contact),
            selectinload(OutreachEmail.brand_target),
        )
    )
    email = result.scalar_one_or_none()
    if not email:
        raise NotFoundError("Email not found")
    return _email_to_response(email)


@router.patch("/emails/{email_id}", response_model=EmailResponse)
async def update_email(
    email_id: UUID,
    body: EmailUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Edit an outreach email's subject, body, or media kit flag."""
    result = await db.execute(
        select(OutreachEmail)
        .where(
            OutreachEmail.id == email_id,
            OutreachEmail.agency_id == current_user.agency_id,
        )
        .options(
            selectinload(OutreachEmail.contact),
            selectinload(OutreachEmail.brand_target),
        )
    )
    email = result.scalar_one_or_none()
    if not email:
        raise NotFoundError("Email not found")

    if email.status not in ("draft", "reviewed"):
        raise BadRequestError(
            f"Cannot edit an email with status '{email.status}'. "
            "Only draft or reviewed emails can be edited."
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(email, field, value)

    if email.status == "draft" and update_data:
        email.status = "reviewed"

    await db.flush()
    await db.refresh(email)
    return _email_to_response(email)


# --- Gmail push endpoints ---

async def _push_single_email(
    email: OutreachEmail, db: AsyncSession
) -> EmailPushResponse:
    """Push one email to Gmail as a draft. Returns result."""
    try:
        gmail = get_gmail_service()

        attachment_path = None
        if email.attach_media_kit and email.creator:
            attachment_path = email.creator.media_kit_file_path

        draft_id = gmail.create_draft(
            to=email.contact.email,
            subject=email.subject,
            body=email.body,
            attachment_path=attachment_path,
        )

        email.gmail_draft_id = draft_id
        email.status = "pushed_to_gmail"
        await db.flush()

        return EmailPushResponse(
            id=email.id, status="pushed_to_gmail", gmail_draft_id=draft_id
        )
    except Exception as e:
        logger.error(f"Failed to push email {email.id} to Gmail: {e}")
        return EmailPushResponse(
            id=email.id, status="failed", gmail_draft_id=None
        )


@router.post("/emails/{email_id}/push-to-gmail", response_model=EmailPushResponse)
async def push_to_gmail(
    email_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Push a single email draft to Gmail."""
    result = await db.execute(
        select(OutreachEmail)
        .where(
            OutreachEmail.id == email_id,
            OutreachEmail.agency_id == current_user.agency_id,
        )
        .options(
            selectinload(OutreachEmail.contact),
            selectinload(OutreachEmail.creator),
        )
    )
    email = result.scalar_one_or_none()
    if not email:
        raise NotFoundError("Email not found")

    if email.status not in ("draft", "reviewed"):
        raise BadRequestError(
            f"Cannot push an email with status '{email.status}'. "
            "Only draft or reviewed emails can be pushed to Gmail."
        )

    push_result = await _push_single_email(email, db)
    return push_result


@router.post("/emails/bulk-push", response_model=EmailBulkPushResponse)
async def bulk_push_to_gmail(
    body: EmailBulkPushRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Push multiple email drafts to Gmail at once."""
    if not body.email_ids:
        raise BadRequestError("At least one email_id is required")

    result = await db.execute(
        select(OutreachEmail)
        .where(
            OutreachEmail.id.in_(body.email_ids),
            OutreachEmail.agency_id == current_user.agency_id,
            OutreachEmail.status.in_(["draft", "reviewed"]),
        )
        .options(
            selectinload(OutreachEmail.contact),
            selectinload(OutreachEmail.creator),
        )
    )
    emails = result.scalars().all()

    pushed = 0
    failed = 0
    results = []

    for email in emails:
        push_result = await _push_single_email(email, db)
        results.append(push_result)
        if push_result.gmail_draft_id:
            pushed += 1
        else:
            failed += 1

    return EmailBulkPushResponse(pushed=pushed, failed=failed, results=results)
