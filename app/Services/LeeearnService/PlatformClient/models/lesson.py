from http.client import HTTPResponse
from typing import TYPE_CHECKING

from ._default import BaseMethods, BaseClass
from ..query_builder import QueryBuilder
from ..types import SafeUUID

if TYPE_CHECKING:
    from ..client import PlatformClient


class LessonMethods(BaseMethods):
    path = "/CompanyBranchLesson"

    async def GetList(self, branch_id: SafeUUID | str, filter_query: None | dict | QueryBuilder = None, is_my: bool = False):
        """
        Endpoint: /CompanyBranchLesson/Get(My)

        Body:
        ``{ "companyBranchId": branch_id, "data": filter_query }``
        """
        new_filter_query = filter_query or {}
        if isinstance(new_filter_query, QueryBuilder):
            new_filter_query = new_filter_query.build()

        path = "Get"
        if is_my: path += "My"

        return await self.client.send_request(
            f"{self.path}/{path}",
            {"companyBranchId": str(branch_id), "data": new_filter_query}
        )

    async def GetDetails(
        self,
        branch_id: SafeUUID | str,
        lesson_id: SafeUUID | str
    ) -> HTTPResponse:
        """
        Endpoint: /CompanyBranchLesson/CompanyBranchLesson/GetDetails

        Body:
        {
            "companyBranchId": branch_id,
            "lessonId": lesson_id
        }
        """
        return await self.client.send_request(
            f"{self.path}/GetDetails",
            {
                "companyBranchId": str(branch_id),
                "lessonId": str(lesson_id)
            }
        )


class BoundLessonMethods:
    def __init__(self, methods: LessonMethods, branch_id: SafeUUID | str):
        self.methods = methods
        self.branch_id = branch_id

    async def GetList(self, filter_query=None, is_my: bool = False):
        return await self.methods.GetList(self.branch_id, filter_query, is_my=is_my)

    async def GetDetails(self, lesson_id: SafeUUID | str):
        return await self.methods.GetDetails(self.branch_id, lesson_id)


class LessonClass(BaseClass[LessonMethods]):
    BranchId: SafeUUID

    def __init__(self, client: "PlatformClient", branch_id: SafeUUID | str, lesson_id: SafeUUID | str):
        super().__init__(client, lesson_id, LessonMethods)
        self.BranchId = branch_id

    async def GetDetails(self):
        return await self.methods.GetDetails(self.BranchId, self.Id)
