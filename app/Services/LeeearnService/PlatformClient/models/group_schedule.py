from datetime import datetime, timedelta
from http.client import HTTPResponse
from typing import TYPE_CHECKING

from app.Services.LeeearnService.PlatformClient.models._default import (
    BaseMethods,
    BaseClass
)
from app.Services.LeeearnService.PlatformClient.query_builder import QueryBuilder
from app.Services.LeeearnService.PlatformClient.types import SafeUUID

if TYPE_CHECKING:
    from ..client import PlatformClient


class GroupScheduleMethods(BaseMethods):
    path = "/CompanyBranchGroupSchedule"

    async def Get(
            self,
            branch_id: SafeUUID | str,
            group_id: SafeUUID | str,
            filter_query: None | dict | QueryBuilder = None
    ) -> HTTPResponse:
        """
        Endpoint: /CompanyBranchGroupSchedule/Get

        Body:
        ``{
            "companyBranchId": branch_id,
            "groupId": group_id,
            "data": filter_query
        }``
        """
        new_filter_query = filter_query or {}
        if isinstance(new_filter_query, QueryBuilder):
            new_filter_query = new_filter_query.build()

        return await self.client.send_request(
            f"{self.path}/Get",
            {"companyBranchId": str(branch_id),
             "groupId": str(group_id),
             "data": new_filter_query}
        )

    async def GetDetails(
            self,
            branch_id: SafeUUID | str,
            group_id: SafeUUID | str,
            data: SafeUUID | str
    ) -> HTTPResponse:
        """
        Endpoint: /CompanyBranchGroupSchedule/GetDetails

        Body:
        ``{
            "companyBranchId": branch_id,
            "groupId": group_id,
            "data": data
        }``
        """
        return await self.client.send_request(
            f"{self.path}/GetDetails",
            {"companyBranchId": str(branch_id),
             "groupId": str(group_id),
             "data": str(data)}
        )

    async def Create(
            self,
            branch_id: SafeUUID | str,
            group_id: SafeUUID | str,
            data: dict
    ) -> HTTPResponse:
        """
        Endpoint: /CompanyBranchGroupSchedule/Create

        Body:
        ``{
            "companyBranchId": branch_id,
            "data": data,
            "groupId": group_id
        }``

        :param branch_id: Branch ID
        :param group_id: Group ID
        :param data: Schedule data (groupId, LessonId, userIds, studentIds,
        teacherIds, count, date)
        """
        return await self.client.send_request(
            f"{self.path}/Create",
            {"companyBranchId": str(branch_id),
             "data": data,
             "groupId": str(group_id)}
        )

    async def Move(
            self,
            branch_id: SafeUUID | str,
            group_id: SafeUUID | str,
            data: dict
    ) -> HTTPResponse:
        """
        Endpoint: /CompanyBranchGroupSchedule/Move

        Body:
        ``{
            "companyBranchId": branch_id,
            "groupId": group_id,
            "data": {
                "id": "...",
                "date": "...",
                "comment": "..."
            }
        }``

        ВАЖНО: из переданной даты вычитаются 2 часа.
        """
        adjusted_data = data.copy()
        if "date" in adjusted_data and adjusted_data["date"]:
            try:
                # поддержка ISO формата
                original_date = datetime.fromisoformat(
                    adjusted_data["date"].replace("Z", "+00:00"))
                adjusted_date = original_date - timedelta(hours=2)
                adjusted_data["date"] = adjusted_date.isoformat().replace(
                    "+00:00", "Z")
            except Exception as e:
                raise ValueError(
                    f"Invalid date format for 'date': {adjusted_data['date']} ({e})")

        return await self.client.send_request(
            f"{self.path}/Move",
            {"companyBranchId": str(branch_id),
             "groupId": str(group_id),
             "data": adjusted_data}
        )

    async def Remove(
            self,
            branch_id: SafeUUID | str,
            group_id: SafeUUID | str,
            lesson_id: SafeUUID | str
    ) -> HTTPResponse:
        """
        Endpoint: /CompanyBranchGroupSchedule/Remove

        Body:
        ``{
            "companyBranchId": branch_id,
            "groupId": group_id,
            "data": lesson_id
        }``
        """
        return await self.client.send_request(
            f"{self.path}/Remove",
            {"companyBranchId": str(branch_id),
             "groupId": str(group_id),
             "data": str(lesson_id)}
        )


class BoundGroupScheduleMethods:
    def __init__(self, methods: GroupScheduleMethods,
                 branch_id: SafeUUID | str):
        self.methods = methods
        self.branch_id = branch_id

    async def Get(self, group_id: SafeUUID | str, filter_query=None):
        return await self.methods.Get(self.branch_id, group_id, filter_query)

    async def GetDetails(self, group_id: SafeUUID | str, data: SafeUUID | str):
        return await self.methods.GetDetails(self.branch_id, group_id, data)

    async def Create(self, group_id: SafeUUID | str, data: dict):
        return await self.methods.Create(self.branch_id, group_id, data)

    async def Move(self, group_id: SafeUUID | str, data: dict):
        return await self.methods.Move(self.branch_id, group_id, data)

    async def Remove(self, group_id: SafeUUID | str, lesson_id: SafeUUID | str):
        return await self.methods.Remove(self.branch_id, group_id, lesson_id)


class GroupScheduleClass(BaseClass[GroupScheduleMethods]):
    BranchId: SafeUUID

    def __init__(self, client: "PlatformClient", branch_id: SafeUUID | str,
                 group_id: SafeUUID | str):
        super().__init__(client, group_id, GroupScheduleMethods)
        self.BranchId = branch_id

    async def Get(self):
        return await self.methods.Get(self.BranchId, self.Id)

    async def GetDetails(self, data: SafeUUID | str):
        return await self.methods.GetDetails(self.BranchId, self.Id, data)

    async def Create(self, data: dict):
        return await self.methods.Create(self.BranchId, self.Id, data)

    async def Move(self, data: dict):
        return await self.methods.Move(self.BranchId, self.Id, data)

    async def Remove(self, lesson_id: SafeUUID | str):
        return await self.methods.Remove(self.BranchId, self.Id, lesson_id)
