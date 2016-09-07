# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def insights_management_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.command_modules.insights.sdk.insightsmanagementclient import \
        InsightsManagementClient
    return get_mgmt_service_client(InsightsManagementClient)

def insights_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.command_modules.insights.sdk.insightsclient import InsightsClient
    return get_mgmt_service_client(InsightsClient)
