import math
from fastapi import HTTPException, Depends, APIRouter, Request, Query
from sqlalchemy.orm import Session, joinedload
from app.models import DiscussionMessage, User
from app.schemas import (
    DiscussionMessageCreate,
    DiscussionMessageUpdate,
    DiscussionMessageResponse,
    DiscussionReplyResponse,
    DiscussionPaginatedResponse,
    DiscussionAuthor,
)
from app.dependencies import get_db
from app.helpers import find_meetup, is_participant
from app.supabase_auth import get_current_user_supabase
from app.rate_limit import limiter

router = APIRouter()


def message_to_response(message: DiscussionMessage):
    """Convert a DiscussionMessage ORM object to the appropriate response schema."""
    author = DiscussionAuthor(
        id=message.user.id,
        username=message.user.username,
        profile_picture_url=message.user.profile_picture_url,
    )

    if message.parent_message_id is not None:
        return DiscussionReplyResponse(
            id=message.id,
            meetup_id=message.meetup_id,
            content=message.content,
            created_at=message.created_at,
            updated_at=message.updated_at,
            author=author,
        )

    return DiscussionMessageResponse(
        id=message.id,
        meetup_id=message.meetup_id,
        content=message.content,
        created_at=message.created_at,
        updated_at=message.updated_at,
        author=author,
        reply_count=len(message.replies) if message.replies else 0,
        replies=[
            DiscussionReplyResponse(
                id=reply.id,
                meetup_id=reply.meetup_id,
                content=reply.content,
                created_at=reply.created_at,
                updated_at=reply.updated_at,
                author=DiscussionAuthor(
                    id=reply.user.id,
                    username=reply.user.username,
                    profile_picture_url=reply.user.profile_picture_url,
                ),
            )
            for reply in message.replies
        ],
    )


@router.get("/meetups/{meetup_id}/discussion", response_model=DiscussionPaginatedResponse)
@limiter.limit("60/minute")
def get_discussion(
    request: Request,
    meetup_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")

    # Count total top-level messages
    total = (
        db.query(DiscussionMessage)
        .filter(
            DiscussionMessage.meetup_id == meetup_id,
            DiscussionMessage.parent_message_id == None,  # noqa: E711
        )
        .count()
    )

    pages = math.ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit

    # Get paginated message IDs (subquery pattern to avoid joinedload row count issues)
    message_ids = (
        db.query(DiscussionMessage.id)
        .filter(
            DiscussionMessage.meetup_id == meetup_id,
            DiscussionMessage.parent_message_id == None,  # noqa: E711
        )
        .order_by(DiscussionMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    message_ids = [mid[0] for mid in message_ids]

    # Fetch full messages with eager loading filtered by those IDs
    messages = (
        db.query(DiscussionMessage)
        .options(
            joinedload(DiscussionMessage.user),
            joinedload(DiscussionMessage.replies).joinedload(DiscussionMessage.user),
        )
        .filter(DiscussionMessage.id.in_(message_ids))
        .order_by(DiscussionMessage.created_at.asc())
        .all()
    )

    return DiscussionPaginatedResponse(
        messages=[message_to_response(msg) for msg in messages],
        page=page,
        pages=pages,
        limit=limit,
        total=total,
    )


@router.post("/meetups/{meetup_id}/discussion", status_code=201, response_model=DiscussionMessageResponse)
@limiter.limit("20/minute")
def create_discussion_message(
    request: Request,
    meetup_id: int,
    message: DiscussionMessageCreate,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db),
):
    meetup = find_meetup(db, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")

    is_host = meetup.host_id == current_user.id
    is_member = is_participant(db, user_id=current_user.id, meetup_id=meetup_id)
    if not is_host and not is_member:
        raise HTTPException(status_code=403, detail="Not allowed")

    content = message.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    db_message = DiscussionMessage(
        meetup_id=meetup_id,
        user_id=current_user.id,
        content=content,
    )

    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    return message_to_response(db_message)


@router.post("/discussion/{message_id}/reply", status_code=201, response_model=DiscussionReplyResponse)
@limiter.limit("20/minute")
def create_reply(
    request: Request,
    message_id: int,
    message: DiscussionMessageCreate,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db),
):
    parent = db.query(DiscussionMessage).filter(DiscussionMessage.id == message_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Message not found")

    if parent.parent_message_id is not None:
        raise HTTPException(status_code=400, detail="Cannot reply to a reply")

    meetup = find_meetup(db, parent.meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")

    is_host = meetup.host_id == current_user.id
    is_member = is_participant(db, user_id=current_user.id, meetup_id=parent.meetup_id)
    if not is_host and not is_member:
        raise HTTPException(status_code=403, detail="Not allowed")

    content = message.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    reply = DiscussionMessage(
        meetup_id=parent.meetup_id,
        user_id=current_user.id,
        parent_message_id=message_id,
        content=content,
    )

    db.add(reply)
    db.commit()
    db.refresh(reply)

    return message_to_response(reply)


@router.put("/discussion/{message_id}", response_model=DiscussionMessageResponse | DiscussionReplyResponse)
@limiter.limit("20/minute")
def update_discussion_message(
    request: Request,
    message_id: int,
    message: DiscussionMessageUpdate,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db),
):
    db_message = (
        db.query(DiscussionMessage)
        .options(
            joinedload(DiscussionMessage.user),
            joinedload(DiscussionMessage.replies).joinedload(DiscussionMessage.user),
        )
        .filter(DiscussionMessage.id == message_id)
        .first()
    )
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")

    if db_message.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    content = message.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    db_message.content = content
    db.commit()
    db.refresh(db_message)

    return message_to_response(db_message)


@router.delete("/discussion/{message_id}")
@limiter.limit("20/minute")
def delete_discussion_message(
    request: Request,
    message_id: int,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db),
):
    db_message = db.query(DiscussionMessage).filter(DiscussionMessage.id == message_id).first()
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")

    meetup = find_meetup(db, db_message.meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")

    is_host = meetup.host_id == current_user.id
    is_author = db_message.user_id == current_user.id
    if not is_host and not is_author:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(db_message)
    db.commit()

    return {"detail": "Message deleted"}
