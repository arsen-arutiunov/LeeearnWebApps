from .Settings import Settings
from .TicketFields import TicketFields
from .Tickets import Tickets


class TicketFlow:
    def __init__(self, db_instance):
        self.db = db_instance

        self.Settings = Settings(self.db)
        self.Tickets = Tickets(self.db)
        self.TicketFields = TicketFields(self.db)