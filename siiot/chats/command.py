# -*- encoding: utf-8 -*-

_command_dict = {}


def register_command():
    def decorator(command_class):
        if command_class.command_code in _command_dict:
            raise Exception(u"Failed to register {}; "
                            u"command with name {} is already registered".format(command_class.__name__,
                                                                                 command_class.command_code))
        _command_dict[command_class.command_code] = command_class
        return command_class

    return decorator


def get_command_class(command_code):
    return _command_dict.get(command_code, None)


class CommandBase(object):
    def __init__(self, params=None, postback_message_code=''):
        if params is None:
            params = {}
        self.command_code = ''
        self.params = params
        self.postback_message_code = postback_message_code


@register_command()
class CloseWindowCommand(CommandBase):
    command_code = 'close_window'
    description = '창 닫기'


@register_command()
class DeepLinkCommand(CommandBase):
    command_code = 'start_deeplink'
    description = 'Deep Link 로 즉시 이동합니다.'

    def __init__(self, uri):
        super(DeepLinkCommand, self).__init__(params={'uri': uri})


@register_command()
class QuestionConfigurationCommand(CommandBase):
    command_code = 'start_question_configuration'
    description = '문제 상세정보 설정 UI를 띄웁니다.'


@register_command()
class RequestTextPostbackCommand(CommandBase):
    command_code = 'request_text_postback'
    description = '1회성 텍스트 입력을 요청합니다. 닉네임 설정 등 많은 Flow에서 사용합니다.'


@register_command()
class ChangeChatInputVisibilityCommand(CommandBase):
    command_code = 'change_chat_input_visibility'
    description = '채팅 기능 활성화 '


@register_command()
class EnableAnswerEditorCommand(CommandBase):
    command_code = 'enable_answer_editor'
    description = '답변 입력창 활성화 '


@register_command()
class DisableAnswerEditorCommand(CommandBase):
    command_code = 'disable_answer_editor'
    description = '답변 입력창 비활성화 '
