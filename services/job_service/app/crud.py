from core.db import session
from shared.lib.crud import CRUD

from models.HistoryTable import HistoryTable
from models.JobsTable import JobsTable

history_crud = CRUD(session, HistoryTable)
jobs_crud = CRUD(session, JobsTable)
