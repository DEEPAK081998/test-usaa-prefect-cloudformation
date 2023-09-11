from notifications import notification_handler


def lambda_handler(event, context):
    """
    Main Driver function
    """
    # send notification to the required webhooks
    notification_handler.send_notification(event=event)
