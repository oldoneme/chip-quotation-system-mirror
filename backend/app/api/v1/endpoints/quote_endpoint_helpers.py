import json
import logging
from typing import Optional

from fastapi import BackgroundTasks

from ....database import SessionLocal
from ....models import User, Quote as QuoteModel
from ....schemas import Quote as QuoteSchema, QuoteList
from ....services.quote_service import QuoteService


def quote_to_schema(service: QuoteService, quote: QuoteModel) -> QuoteSchema:
    pdf_url = service.get_pdf_url(quote)
    model = QuoteSchema.model_validate(quote, from_attributes=True)
    if pdf_url:
        model = model.model_copy(update={"pdf_url": pdf_url})
    return model


def list_item_to_dict(service: QuoteService, quote: QuoteModel) -> dict:
    model = QuoteList.model_validate(quote, from_attributes=True)
    pdf_url = service.get_pdf_url(quote)
    if pdf_url:
        model = model.model_copy(update={"pdf_url": pdf_url})
    return model.model_dump(mode="json")


def generate_pdf_cache_background(
    quote_id: int,
    user_id: int,
    force: bool,
    event: str,
    column_configs: Optional[dict] = None,
) -> None:
    session = SessionLocal()
    try:
        service = QuoteService(session)
        quote = service.load_quote_with_details(quote_id)
        user = session.query(User).filter(User.id == user_id).first()
        if not quote or not user:
            return
        try:
            service.ensure_pdf_cache(
                quote, user, force=force, column_configs=column_configs
            )
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("app.snapshot").error(
                json.dumps(
                    {
                        "event": event,
                        "quote_id": quote.id,
                        "quote_number": quote.quote_number,
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                )
            )
    finally:
        session.close()


def schedule_pdf_refresh(
    background_tasks: BackgroundTasks,
    quote_id: int,
    user_id: int,
    force: bool,
    event: str,
    column_configs: Optional[dict] = None,
) -> None:
    if background_tasks is None:
        return
    background_tasks.add_task(
        generate_pdf_cache_background,
        quote_id,
        user_id,
        force,
        event,
        column_configs,
    )
