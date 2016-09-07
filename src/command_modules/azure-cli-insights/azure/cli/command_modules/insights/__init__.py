#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
# Add command module logic to this package.

import azure.cli.command_modules.insights._help # pylint: disable=unused-import

def load_params(_):
    import azure.cli.command_modules.insights._params #pylint: disable=redefined-outer-name

def load_commands():
    import azure.cli.command_modules.insights.commands #pylint: disable=redefined-outer-name
