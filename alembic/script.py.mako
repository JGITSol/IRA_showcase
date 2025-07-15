"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

This is an auto-generated migration file. It will be used by Alembic to apply
schema changes to the database.

For more information on this file, see:
https://alembic.sqlalchemy.org/en/latest/api/runtime.html#alembic.runtime.environment.EnvironmentContext.config.attributes['transaction_per_migration']
"""

import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Connection
from sqlalchemy.sql import table, column, text

# Import any custom types or utilities if needed
# from app.core.types import JSONB

${imports if imports else ""}

# Revision identifiers, used by Alembic
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}

# Set up logging
logger = logging.getLogger('alembic')


def upgrade(engine_name: str = '') -> None:
    """Apply database schema upgrades.
    
    Args:
        engine_name: The name of the database engine to use. If empty, uses the default engine.
    """
    if engine_name:
        # If you need to run migrations on a different database
        from alembic import context
        from sqlalchemy import create_engine
        
        engine = create_engine(context.config.get_main_option('sqlalchemy.url').replace('%', engine_name))
        with engine.connect() as conn:
            context.configure(connection=conn, target_metadata=None)
            with context.begin_transaction():
                _upgrade()
    else:
        _upgrade()


def _upgrade() -> None:
    """Internal function to perform the actual upgrade operations."""
    logger.info(f"Running upgrade {down_revision} -> {revision}")
    
    # Example of a conditional upgrade based on database type
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        # PostgreSQL specific operations
        pass
    
    try:
        # Your upgrade operations go here
        ${upgrades if upgrades else "pass"}
        
        # Example of data migration
        # op.execute(
        #     table('users')
        #     .update()
        #     .where(column('status').is_(None))
        #     .values(status='active')
        # )
        
        logger.info(f"Successfully upgraded to {revision}")
    except Exception as e:
        logger.error(f"Error during upgrade to {revision}: {str(e)}")
        raise


def downgrade(engine_name: str = '') -> None:
    """Revert database schema to the previous version.
    
    Args:
        engine_name: The name of the database engine to use. If empty, uses the default engine.
    """
    if engine_name:
        # If you need to run migrations on a different database
        from alembic import context
        from sqlalchemy import create_engine
        
        engine = create_engine(context.config.get_main_option('sqlalchemy.url').replace('%', engine_name))
        with engine.connect() as conn:
            context.configure(connection=conn, target_metadata=None)
            with context.begin_transaction():
                _downgrade()
    else:
        _downgrade()


def _downgrade() -> None:
    """Internal function to perform the actual downgrade operations."""
    logger.info(f"Running downgrade {revision} -> {down_revision}")
    
    try:
        # Your downgrade operations go here
        ${downgrades if downgrades else "pass"}
        
        logger.info(f"Successfully downgraded from {revision}")
    except Exception as e:
        logger.error(f"Error during downgrade from {revision}: {str(e)}")
        raise
