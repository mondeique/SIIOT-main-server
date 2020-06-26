# -*- encoding: utf-8 -*-
from core.mbunch import mbunchify


def get_mocked_serializer_context(user, room, client_handler_version):
    return mbunchify({'request': {'user': user},
                      'room_id': room.id,
                      'room': room,
                      'client_handler_version': client_handler_version})
