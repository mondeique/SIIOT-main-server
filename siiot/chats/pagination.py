from core.pagination import SiiotCursorPagination


class BuyerOpenChatRoomPagination(SiiotCursorPagination):
    page_size = 10
    ordering = ('-created_at',)
