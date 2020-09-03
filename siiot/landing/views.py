from django.shortcuts import render, redirect
from .slack import *


def home(request):
    return render(request, 'landingHome.html')


def alert_slack(request):
    return slack_message("유저가 구글 플레이 스토어 다운로드 링크를 눌렀습니다.")


def homefiting_alert_slack(request):
    slack_message("누군가가 홈피팅 카카오톡 링크로 접속했습니다.")
    return redirect('http://pf.kakao.com/_xdxixcyxb/chat')
