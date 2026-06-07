from core.db import session
from shared.lib.crud import CRUD

from models.DreamerGroupMembersTable import DreamerGroupMembersTable
from models.DreamerGroupTable import DreamerGroupTable
from models.DreamerTable import DreamerTable


dreamer_group_members_crud = CRUD(session, DreamerGroupMembersTable)
dreamer_group_crud = CRUD(session, DreamerGroupTable)
dreamer_crud = CRUD(session, DreamerTable)
