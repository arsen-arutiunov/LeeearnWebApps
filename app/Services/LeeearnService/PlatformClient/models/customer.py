from http.client import HTTPResponse
from typing import TYPE_CHECKING

from ..query_builder import QueryBuilder
from ..types import SafeUUID
from ._default import BaseMethods, BaseClass

if TYPE_CHECKING:
    from ..client import PlatformClient


class CustomerMethods(BaseMethods):
    path = "/CompanyBranchCustomer"

    async def GetList(self, branch_id: SafeUUID | str, filter_query: None | dict | QueryBuilder = None, is_my: bool = False):
        """
        Endpoint: /CompanyBranchCustomer/Get(My)

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
            { "companyBranchId": str(branch_id), "data": new_filter_query }
        )

    async def GetDetails(self, branch_id: SafeUUID | str, customer_id: SafeUUID | str) -> HTTPResponse:
        """
        Endpoint: /CompanyBranchCustomer/GetDetails

        Body:
        ``{ "companyBranchId": branch_id, "customerId": customer_id }``

        :param branch_id: Branch ID
        :param customer_id: Customer ID
        """
        return await self.client.send_request(
            f"{self.path}/GetDetails",
            { "companyBranchId": str(branch_id), "customerId": str(customer_id) }
        )

    async def GetCustomerGroups(
            self,
            branch_id: SafeUUID | str,
            customer_id: SafeUUID | str,
            filter_query: None | dict | QueryBuilder = None
    ) -> HTTPResponse:
        """
        Endpoint: /CompanyBranchCustomer/GetCustomerGroups

        Body:
        ``{
            "companyBranchId": branch_id,
            "customerId": customer_id,
            "data": filter_query
        }``

        :param branch_id: Branch ID
        :param customer_id: Customer ID
        :param filter_query: Optional filter
        """
        new_filter_query = filter_query or {}
        if isinstance(new_filter_query, QueryBuilder):
            new_filter_query = new_filter_query.build()

        return await self.client.send_request(
            f"{self.path}/GetCustomerGroups",
            {
                "companyBranchId": str(branch_id),
                "customerId": str(customer_id),
                "data": new_filter_query
            }
        )


class BoundCustomerMethods:
    def __init__(self, methods: CustomerMethods, branch_id: SafeUUID | str):
        self.methods = methods
        self.branch_id = branch_id

    async def GetList(self, filter_query=None, is_my: bool = False):
        return await self.methods.GetList(self.branch_id, filter_query, is_my=is_my)

    async def GetDetails(self, customer_id: SafeUUID | str):
        return await self.methods.GetDetails(self.branch_id, customer_id)

    async def GetCustomerGroups(self, customer_id: SafeUUID | str, filter_query=None):
        return await self.methods.GetCustomerGroups(
            self.branch_id,
            customer_id,
            filter_query=filter_query
        )


class CustomerClass(BaseClass[CustomerMethods]):
    BranchId: SafeUUID

    def __init__(self, client: "PlatformClient", branch_id: SafeUUID | str, customer_id: SafeUUID | str):
        super().__init__(client, customer_id, CustomerMethods)
        self.BranchId = branch_id

    async def GetDetails(self):
        return await self.methods.GetDetails(self.BranchId, self.Id)

    async def GetCustomerGroups(self, filter_query=None):
        return await self.methods.GetCustomerGroups(self.BranchId, self.Id, filter_query)
