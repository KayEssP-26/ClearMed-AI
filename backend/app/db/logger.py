from supabase import create_client
from app.config import settings


def log_request(data: dict) -> None:
    """
    Insert data into the Supabase ''request_logs'' table.

    Any exception is caught and printed so that logging failures
    never interrupt the main API response.
    """
    try:
        client = create_client(settings.supabase_url, settings.supabase_key)
        # returning="minimal" so the insert doesn't try to read the row back.
        # The RLS INSERT policy permits writes but there is no SELECT policy,
        # so a default RETURNING * would be blocked. We never need the row back.
        client.table("request_logs").insert(data, returning="minimal").execute()
    except Exception as exc:  # noqa: BLE001
        print(f"[logger] Failed to log request: {exc}")
