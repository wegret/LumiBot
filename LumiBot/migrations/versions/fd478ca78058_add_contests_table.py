"""Add contests table

迁移 ID: fd478ca78058
父迁移: 
创建时间: 2024-08-19 23:49:08.822213

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'fd478ca78058'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = ('contests',)
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade(name: str = "") -> None:
    if name:
        return
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
