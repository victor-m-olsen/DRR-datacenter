#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _
import logging
logger = logging.getLogger(__name__)

if "notification" in settings.INSTALLED_APPS:
    import notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.models.NoticeType.create(
            "user_follow",
            _("User following you"),
            _("Another user has started following you"))
        notification.models.NoticeType.create(
            "account_approve",
            _("User requested access"),
            _("A new user has requested access to the site"))
        notification.models.NoticeType.create(
            "account_active",
            _("Account activated"),
            _("This account is now active and can log in the site"))
        notification.models.NoticeType.create(
            "request_add_organization",
            _("Request add organization"),
            _("A visitor has requested to add organization"))

    signals.post_syncdb.connect(
        create_notice_types,
        sender=notification.models)
    logger.info(
        "Notifications Configured for geonode.people.managment.commands")
else:
    logger.info(
        "Skipping creation of NoticeTypes for geonode.people.management.commands, \
        since notification app was not found.")
