from hashlib import sha256
import onesignal as onesignal_sdk
from django.conf import settings

onesignal_client = onesignal_sdk.Client(
    app_id=settings.ONE_SIGNAL_APP_ID,
    app_auth_key=settings.ONE_SIGNAL_API_KEY
)


def send_notification_to_user(user, notification):
    for device in user.devices.all():
        notification.set_parameter('ios_badgeType', 'Increase')
        notification.set_parameter('ios_badgeCount', '1')

        user_id_contents = (str(user.uuid) + str(user.id)).encode('utf-8')

        user_id = sha256(user_id_contents).hexdigest()

        notification.set_filters([
            {"field": "tag", "key": "user_id", "relation": "=", "value": user_id},
            {"field": "tag", "key": "device_uuid", "relation": "=", "value": device.uuid},
        ])

        onesignal_client.send_notification(notification)
