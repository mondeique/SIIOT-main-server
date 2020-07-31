from django.shortcuts import render
from .slack import *


def home(request):
    return render(request, 'landingHome.html')


def alert_slack(request):
    return slack_message("유저가 구글 플레이 스토어 다운로드 링크를 눌렀습니다.")