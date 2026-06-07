from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Type, TypeVar
from sqlalchemy.orm import DeclarativeMeta
from pydantic import BaseModel

from shared.lib.basicError import errorWrapper, BasicError

T = TypeVar("T", bound=BaseModel)
M = TypeVar("M", bound=DeclarativeMeta)

class CRUD:
    OPERATORS = {
        "==": lambda col, val: col == val,
        "!=": lambda col, val: col != val,
        ">": lambda col, val: col > val,
        "<": lambda col, val: col < val,
        ">=": lambda col, val: col >= val,
        "<=": lambda col, val: col <= val,
        "like": lambda col, val: col.like(val),
        "ilike": lambda col, val: col.ilike(val),
        "in": lambda col, val: col.in_(val if isinstance(val, list) else [val]),
    }

    def __init__(self, db: Session, tableModel: Type[M]):
        """
        
        DB操作CRUDクラス

        parameters
        ----------
            db: Session
                SQLAlchemyのセッション
            
            tableModel: DeclarativeMeta
                SQLAlchemyのテーブル定義クラス
        
        """

        self.db = db
        self.table: Type[M] = tableModel

    # TODO: dataの型定義を設定
    @errorWrapper("QueryError")
    def create(self, data):
        """
        
        作成関数

        Parameters
        ----------
            data: BaseModel
                挿入データが入力された対象テーブルに対応するBaseModel

        Returns
        ---------
            DeclarativeMeta: 挿入結果

        Examples
        --------
            >>> @router.post("/", response_model=ArchiveTableSchema)
            >>> async def _(data: ArchiveTableSchema):
            >>>    success, result, error = archive_crud.create(data)

            >>>    if not success:
            >>>        return HTTPException(status_code=500, detail=error)
    
            >>>    return result
        
        """

        try:
            new_data = self.table(**data.model_dump())
            self.db.add(new_data)
            self.db.commit()
            self.db.refresh(new_data)
            return new_data
        except Exception as e:
            self.db.rollback()
            raise e

    @errorWrapper("QueryError")
    def read(self, filters: list[list] = []):
        """
        
        読み取り関数
        作成順にソート

        Parameters
        ----------
            filters: list[list] = []
                対象データの条件

        Returns
        ---------
            list[DeclarativeMeta]: 取得結果

        Examples
        --------
            >>> success, valid_tokens, error = auth_crud.read([
            >>>    ["token", "==", token],
            >>>    ["expires_at", ">=", get_utc_time()],
            >>>    ["used_at", "==", None]
            >>> ])
        
        """

        try:
            query = self.db.query(self.table)

            conditions = [self.OPERATORS[op](getattr(self.table, col), val) for col, op, val in filters]
            if conditions:
                query = query.filter(and_(*conditions))
                query = query.order_by(getattr(self.table, "created_at"))
            
            results = query.all()

            if results is None:
                raise BasicError("RecordNotFound")
            
            return results
        except Exception as e:
            self.db.rollback()
            raise e

    @errorWrapper("QueryError")
    def update(self, filters: list[list], update_data: dict):
        """
        
        更新関数
        作成順にソート

        Parameters
        ----------
            filters: list[list] = []
                対象データの条件
            
            updated_data: 
                更新データ

        Returns
        ---------
            list[DeclarativeMeta]: 更新結果

        Examples
        --------
            >>> success, new_archive, error = archive_crud.update(
            >>>    [
            >>>        ["id", "==", data.id]
            >>>    ],
            >>>    {
            >>>        "contents": new_contents,
            >>>        "archive_status": "RUNNING"
            >>>    }
            >>> )
        
        """

        try:
            records = self.db.query(self.table)
            
            conditions = [self.OPERATORS[op](getattr(self.table, col), val) for col, op, val in filters]
            if conditions:
                records = records.filter(and_(*conditions))    

            filterd_records = records.all()    
            if filterd_records is None: raise BaseError("RecordNotFound")

            updated_objects = []
            for obj in filterd_records:
                for k, v in update_data.items():
                    setattr(obj, k, v)
                self.db.commit()
                self.db.refresh(obj)
                updated_objects.append(obj)

            return updated_objects
        except Exception as e:
            self.db.rollback()
            raise e
    
    @errorWrapper("QueryError")
    def delete(self, filters: list[list]):
        """
        
        削除関数
        作成順にソート

        Parameters
        ----------
            filters: list[list] = []
                対象データの条件
            
        Returns
        ---------
            list[DeclarativeMeta]: 削除結果

        Examples
        ---------
            >>> success, deleted_memos, error = memo_crud.delete([
            >>>    ["id", "==", memo_id]
            >>> ])
        
        """
        
        try:
            query = self.db.query(self.table)
            conditions = [self.OPERATORS[op](getattr(self.table, col), val) for col, op, val in filters]
            if conditions:
                query = query.filter(and_(*conditions))
            records = query.all()

            if not records:
                return None

            for record in records:
                self.db.delete(record)
                self.db.commit()

            return records
        except Exception as e:
            self.db.rollback()
            raise e
