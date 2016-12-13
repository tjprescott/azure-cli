# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator 0.17.0.0
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class AutoscaleNotification(Model):
    """Autoscale notification.

    Variables are only populated by the server, and will be ignored when
    sending a request.

    :ivar operation: the operation associated with the notification and its
     value must be "scale". Default value: "Scale" .
    :vartype operation: str
    :param email: the email notification.
    :type email: :class:`EmailNotification
     <InsightsMgmt.models.EmailNotification>`
    :param webhooks: the collection of webhook notifications.
    :type webhooks: list of :class:`WebhookNotification
     <InsightsMgmt.models.WebhookNotification>`
    """ 

    _validation = {
        'operation': {'required': True, 'constant': True},
    }

    _attribute_map = {
        'operation': {'key': 'operation', 'type': 'str'},
        'email': {'key': 'email', 'type': 'EmailNotification'},
        'webhooks': {'key': 'webhooks', 'type': '[WebhookNotification]'},
    }

    operation = "Scale"

    def __init__(self, email=None, webhooks=None):
        self.email = email
        self.webhooks = webhooks
