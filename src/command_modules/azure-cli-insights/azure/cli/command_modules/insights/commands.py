#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command

from ._client_factory import insights_client_factory, insights_management_client_factory

sdk_path = 'azure.cli.command_modules.insights.sdk.insightsclient.{}'
sdk_mgmt_path = 'azure.cli.command_modules.insights.sdk.insightsmanagementclient.{}'
custom_path = 'azure.cli.command_modules.insights.custom#{}'

cli_command(__name__, 'insights events list', custom_path.format('list_events'), None)
# list-digest and tenat list-digest are not available
cli_command(__name__, 'insights events list-digest-events', custom_path.format('list_digest_events'), None)
cli_command(__name__, 'insights events tenant list-digest-events', custom_path.format('list_tenant_digest_events'), None)
cli_command(__name__, 'insights events tenant list', custom_path.format('list_tenant_events'), None)

# factory = lambda _: insights_client_factory(**_).event_categories
# cli_command(__name__, 'insights events list-categories', 'azure.cli.command_modules.insights.sdk.insightsclient.insights_client.event_categories#EventCategoriesOperations.list', factory)

# factory = lambda x: _insights_client_factory(InsightsClient).usage_metric
# cli_command('insights list-usage', UsageMetricOperations.list, factory)

# factory = lambda _: insights_client_factory(**_).metrics
# cli_command(__name__, 'insights metrics list', sdk_path.format('metrics#MetricsOperations.list'), factory)

# factory = lambda _: insights_client_factory(**_).metric_definitions
# cli_command(__name__, 'insights metrics list-definitions', sdk_path.format('metric_definitions#MetricDefinitionsOperations.list'), factory)

# factory = lambda _: insights_management_client_factory(**_).alert_rules
# cli_command(__name__, 'insights alerts rule create', sdk_mgmt_path.format('alert_rules#AlertRulesOperations.create_or_update'), factory)
# cli_command(__name__, 'insights alerts rule update', sdk_mgmt_path.format('alert_rules#AlertRulesOperations.create_or_update'), factory)
# cli_command(__name__, 'insights alerts rule delete', sdk_mgmt_path.format('alert_rules#AlertRulesOperations.delete'), factory)
# cli_command(__name__, 'insights alerts rule show', sdk_mgmt_path.format('alert_rules#AlertRulesOperations.get'), factory)
# cli_command(__name__, 'insights alerts rule list', sdk_mgmt_path.format('alert_rules#AlertRulesOperations.list_by_resource_group'), factory)
# A helper command to generate alerts rule resource template
# cli_command(__name__, 'insights alerts rule TEMPLATE', custom_path.format('_generate_alerts_rule_template'), None)

# factory = lambda _: insights_management_client_factory(**_).alert_rule_incidents
# cli_command(__name__, 'insights alerts incident show', sdk_mgmt_path.format('alert_rule_incidents#AlertRuleIncidentsOperations.get'), factory)

# factory = lambda _: insights_management_client_factory(**_).incidents
# cli_command(__name__, 'insights alerts incident list', sdk_mgmt_path.format('incidents#IncidentsOperations.list_by_alert_rule'), factory)

# factory = lambda x: _insights_client_factory(InsightsClient).log
# cli_command('insights logs list', LogOperations.get, factory)

# factory = lambda x: _insights_client_factory(InsightsClient).log_definition
# cli_command('insights logs list-definitions', LogDefinitionOperations.get, factory)
