from app.db import connect_args_for


def test_session_pooler_keeps_default_statement_cache() -> None:
    url = "postgresql+asyncpg://user@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    assert connect_args_for(url) == {}


def test_transaction_pooler_disables_statement_cache() -> None:
    url = "postgresql+asyncpg://user@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    args = connect_args_for(url)

    assert args["statement_cache_size"] == 0
    assert args["prepared_statement_name_func"]() != args["prepared_statement_name_func"]()
