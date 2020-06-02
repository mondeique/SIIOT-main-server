# -*- encoding: utf-8 -*-
"""
This file was generated with the custommenu management command, it contains
the classes for the admin menu, you can customize this class as you want.

To activate your custom menu add the following to your settings.py::
    ADMIN_TOOLS_MENU = 'mathpresso.menu.CustomMenu'
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from wpadmin.menu.menus import items, Menu
from wpadmin.utils import get_admin_site_name


class TitleMenuItem(items.MenuItem):
    def is_selected(self, request):
        return False


# Superadmin

class AdminTopMenu(Menu):

    def init_with_context(self, context):
        admin_site_name = get_admin_site_name(context)

        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            from django.contrib.sites.models import Site
            site_name = Site.objects.get_current().name + ' 최고관리자'
        else:
            site_name = 'Site'

        self.children += [
            TitleMenuItem(
                title=site_name,
                url=reverse('%s:index' % admin_site_name),
                icon='fa-bullseye',
                css_styles='font-size: 1.5em;',
            ),
            items.UserTools(
                css_styles='float: right;',
                is_user_allowed=lambda user: user.is_staff,
            ),
        ]


class AdminLeftMenu(Menu):
    """
    Custom Menu for mathpresso admin site.
    """

    def is_user_allowed(self, user):
        """
        Only users that are staff are allowed to see this menu.
        """
        return user.is_superuser

    def init_with_context(self, context):

        if self.is_user_allowed(context.get('request').user):

            admin_site_name = get_admin_site_name(context)

            self.children += [
                items.MenuItem(
                    title='Dashboard',
                    icon='fa-tachometer',
                    url=reverse('%s:index' % admin_site_name),
                    description='Dashboard',
                ),
                items.AppList(
                    title='Applications',
                    description='Applications',
                    exclude=('django.contrib.*',),
                    icon='fa-tasks',
                ),
                items.AppList(
                    title='Administration',
                    description='Administration',
                    models=('django.contrib.*',),
                    icon='fa-cog',
                ),
            ]


# staff

class StaffTopMenu(Menu):

    def init_with_context(self, context):
        admin_site_name = get_admin_site_name(context)

        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            from django.contrib.sites.models import Site
            site_name = Site.objects.get_current().name + ' 스태프'
        else:
            site_name = 'Site'

        self.children += [
            TitleMenuItem(
                title=site_name,
                url=reverse('%s:index' % admin_site_name),
                icon='fa-bullseye',
                css_styles='font-size: 1.5em;',
            ),
            items.UserTools(
                css_styles='float: right;',
                is_user_allowed=lambda user: user.is_staff,
            ),
        ]


class StaffLeftMenu(Menu):
    """
    Custom Menu for mathpresso admin site.
    """

    def is_user_allowed(self, user):
        """
        Only users that are staff are allowed to see this menu.
        """
        return user.is_staff

    def init_with_context(self, context):

        if self.is_user_allowed(context.get('request').user):

            admin_site_name = get_admin_site_name(context)

            self.children += [
                # items.MenuItem(
                #     title='통계',
                #     url='http://mathpresso-dashboard.s3-website.ap-northeast-2.amazonaws.com/dashboard',
                #     icon='fa-line-chart',
                # ),
                items.MenuItem(
                    title='Dashboard',
                    url=reverse('%s:index' % admin_site_name),
                    icon='fa-tachometer',
                ),
                items.ModelList(
                    title='회원 관리',
                    models=(
                        'accounts.admin.*',
                        'accounts.models.StudentProfile',
                        'accounts.models.TeacherProfile',
                        'accounts.models.TeacherUniversity',
                        'logs.models.UniversityIDCardLog',
                        'payments.pocket.*',
                        'accounts.coin.*',
                    ),
                    url=reverse('staff:accounts_student_changelist'),
                    icon='fa-users',
                ),
                items.ModelList(
                    title='질문 관리',
                    models=('questions.*',),
                    url=reverse('staff:questions_question_changelist'),
                    icon='fa-question-circle',
                ),
                items.ModelList(
                    title='1:1 문의 관리',
                    models=(
                        'support.models.Opinion',
                        'support.models.Contact',),
                    url=reverse('staff:support_contact_changelist'),
                    icon='fa-envelope-o',
                ),
                # items.MenuItem(
                #     title='서포트 관리',
                #     models=('support.QandaSupport',),
                #     url='/staff/qanda_support/',
                #     icon='fa-envelope-o',
                # ),
                items.MenuItem(
                    title='푸쉬 ID 발송',
                    models=('notifications.Notification',),
                    url='/api/v3/notification/bulk/',
                    icon='fa-bell-o',
                ),
                items.MenuItem(
                    title='푸쉬 Query 발송',
                    models=('notifications.Notification',),
                    url='/api/v3/notification/range/',
                    icon='fa-bell-o',
                ),
                items.ModelList(
                    title='운영',
                    models=(
                        'support.models.Official',
                        'support.models.FAQ',
                        'support.models.TeacherFAQ',
                        'notices.*',
                        'memos.*',),
                    url=reverse('staff:support_official_changelist'),
                    icon='fa-briefcase',
                ),
                items.ModelList(
                    title='데이터 관리',
                    models=(
                        'versions.models.Version',
                        'constants.models.*',),
                    url=reverse('staff:versions_version_changelist'),
                    icon='fa-android',
                ),
                items.ModelList(
                    title='아이템 관리',
                    models=(
                        'payments.items.*',),
                    url=reverse('staff:items_item_changelist'),
                    icon='fa-archive',
                ),
                items.ModelList(
                    title='유료 상품 관리',
                    models=(
                        'payments.memberships.*',
                        'payments.pencils.*',
                        'payments.credit.*'
                    ),
                    url=reverse('staff:memberships_studentmembership_changelist'),
                    icon='fa-won',
                ),
                items.ModelList(
                    title='쿠폰 관리',
                    models=(
                        'payments.coupons.*',),
                    icon='fa-credit-card',
                ),
                items.ModelList(
                    title='기프티콘 관리',
                    models=(
                        'store.models.StoreProduct',
                        'store.models.StoreCoupon'
                    ),
                    url=reverse('staff:gifticon_withdrawallog_changelist'),
                    icon='fa-gift',
                ),
                items.ModelList(
                    title='결제 내역 관리',
                    models=('payments.models.*',),
                    url=reverse('staff:payments_order_changelist'),
                    icon='fa-file-text',
                ),
                items.ModelList(
                    title='Push 알림',
                    models=('notifications.models.Notification',
                            'notifications.models.NotificationUserLog',
                            'notifications.models.TargetNotification',
                            'notifications.models.ReservedNotification',
                            ),
                    url=reverse('staff:notifications_notification_changelist'),
                    icon='fa-bell-o',
                ),
                items.ModelList(
                    title='wifi 관리',
                    models=('franchise.wifi.models.*',),
                    url=reverse('staff:wifi_wifimembershipclient_changelist'),
                    icon='fa-wifi',
                ),
                items.ModelList(
                    title='로그',
                    models=(
                        'logs.models.*',
                        'tracker.models.*'),
                    exclude=(
                        'logs.models.RegistrationDevice',
                    ),
                    url=reverse('staff:logs_studentcreditlog_changelist'),
                    icon='fa-file-text',
                ),
                # items.ModelList(
                #     title='뱃지',
                #     models=('accounts.badge.models.*',),
                #     url=reverse('staff:badge_teacherbadgerequest_changelist'),
                #     icon='fa-file-text',
                # ),
                items.ModelList(
                    title=_('프랜차이즈'),
                    models=('franchise.models.*',),
                    url=reverse('staff:franchise_franchiseclient_changelist'),
                    icon='fa-building',
                ),
            ]
