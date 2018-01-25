# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function, unicode_literals

from enum import Enum

from prompt_toolkit.completion import Completer, Completion

import azclishell.configuration
from azclishell.argfinder import ArgsFinder
from azclishell.command_tree import in_tree
from azclishell.layout import get_scope
from azclishell.util import parse_quotes

from azure.cli.core.parser import AzCliCommandParser

SELECT_SYMBOL = azclishell.configuration.SELECT_SYMBOL


def initialize_command_table_attributes(completer):
    from azclishell._dump_commands import LoadFreshTable
    completer.cmdtab = LoadFreshTable(completer.shell_ctx).command_table
    if completer.cmdtab:
        completer.parser.load_command_table(completer.cmdtab)
        completer.argsfinder = ArgsFinder(completer.parser)


def error_pass(_, message):  # pylint: disable=unused-argument
    return


def dynamic_param_logic(text):
    """ validates parameter values for dynamic completion """
    is_param = False
    started_param = False
    prefix = ""
    param = ""
    txtspt = text.split()
    if txtspt:
        param = txtspt[-1]
        if param.startswith("-"):
            is_param = True
        elif len(txtspt) > 2 and txtspt[-2]\
                and txtspt[-2].startswith('-'):
            is_param = True
            param = txtspt[-2]
            started_param = True
            prefix = txtspt[-1]
    return is_param, started_param, prefix, param


def gen_dyn_completion(comp, started_param, prefix, text):
    """ how to validate and generate completion for dynamic params """
    if len(comp.split()) > 1:
        completion = '\"' + comp + '\"'
    else:
        completion = comp
    if started_param:
        if comp.lower().startswith(prefix.lower()) and comp not in text.split():
            yield Completion(completion, -len(prefix))
    else:
        yield Completion(completion, -len(prefix))


def sort_completions(completions_gen):
    """ sorts the completions """

    def _get_weight(val):
        """ weights the completions with required things first the lexicographically"""
        priority = ''
        if val.display_meta and val.display_meta.startswith('[REQUIRED]'):
            priority = ' '  # a space has the lowest ordinance
        return priority + val.text

    return sorted(completions_gen, key=_get_weight)


class CompletionMode(Enum):  # pylint: disable=too-few-public-methods
    command = 'command'
    parameter = 'parameter'
    value = 'value'
    none = 'none'  # used when user strays off the command path


# pylint: disable=too-many-instance-attributes
class AzCompleter(Completer):
    """ Completes Azure CLI commands """

    def __init__(self, shell_ctx, commands, global_params=True):
        self.shell_ctx = shell_ctx
        # dictionary of command to descriptions
        self.command_description = commands.descrip
        # from a command to a list of parameters
        self.command_parameters = commands.command_param
        # a list of all the possible parameters
        self.completable_param = commands.completable_param
        # the command tree
        self.command_tree = commands.command_tree
        # a dictionary of parameter (which is command + " " + parameter name)
        # to a description of what it does
        self.param_description = commands.param_descript
        # a dictionary of command to examples of how to use it
        self.command_examples = commands.command_example
        # a dictionary of commands with parameters with multiple names (e.g. {'vm create':{-n: --name}})
        self.same_param_doubles = commands.same_param_doubles or {}

        self.branch = self.command_tree
        self.curr_command = ""

        self.global_param = commands.global_param if global_params else []
        self.output_choices = commands.output_choices if global_params else []
        self.output_options = commands.output_options if global_params else []
        self.global_param_descriptions = commands.global_param_descriptions if global_params else []

        self.global_parser = AzCliCommandParser(add_help=False)
        self.global_parser.add_argument_group('global', 'Global Arguments')
        self.parser = AzCliCommandParser(parents=[self.global_parser])
        self.cmdtab = None

        self.completion_mode = CompletionMode.command
        self.prev_text_before_cursor = ''

    def _validate_command_completion(self, possible_match, prefix):
        return possible_match.startswith(prefix)

    def _validate_param_completion(self, possible_match, prefix, text_before_cursor, check_double=True):
        """ validates that a possible match should be completed """
        # most obvious - the possible match needs to start with the prefix
        if not possible_match.startswith(prefix):
            return False

        position = possible_match.startswith(prefix) and not text_before_cursor[-1].isspace()
        # cancels parameters that are already in the in line
        canceling_positions = possible_match != prefix and possible_match not in text_before_cursor.split()

        found_double = True
        # checks for aliasing of parameters

        if check_double:
            for double_sets in self.same_param_doubles.get(self.curr_command, []):
                # if the parameter is in any of the sets
                if possible_match in double_sets:
                    # if any of the other aliases are in the line already
                    found_double = not any(
                        alias in text_before_cursor.split() and alias != possible_match for alias in double_sets)

        return position and canceling_positions and found_double

    def get_completions(self, document, complete_event):

        def format_command(text):
            """ reformat the text to be stripped of noise """
            # remove az if there
            text = text.replace('az', '')
            # disregard defaulting symbols
            if text and SELECT_SYMBOL['scope'] == text[0:2]:
                text = text.replace(SELECT_SYMBOL['scope'], '')
            # plug in the scope if set
            scope = get_scope()
            text = '{} {}'.format(scope, text) if scope else text or ' '
            # ensure text is lower for completion purposes
            return text.lower()

        def increment_command_branch(text):

            tokens = text.split()
            last_token = tokens[-1] if tokens else []
            try:
                self.branch = self.branch.children[last_token]

                # if we've reached a leaf node in the command tree, we can automatically
                # switch to parameter completion mode
                if not self.branch.children:
                    self.completion_mode = CompletionMode.parameter
            except KeyError:
                # disable completions if the user specifies something that isnt a key
                self.completion_mode = CompletionMode.none

        def refresh_command_branch(text):
            self.completion_mode = CompletionMode.command
            self.branch = self.command_tree
            command_tokens = []
            for token in text.split():
                if token.startswith('-'):
                    break
                command_tokens.append(token)

            for token in command_tokens[:-1]:
                try:
                    self.branch = self.branch.children[token]
                except KeyError:
                    self.completion_mode = CompletionMode.none

            # the last token might be incomplete
            if token in self.branch.children:
                self.branch = self.branch.children[token]

        def requires_refresh():
            # since get_completions only runs when a new character is added, we have to check
            # for use of backspace.
            return len(document.text_before_cursor) <= len(self.prev_text_before_cursor)

        def handle_prefix(prefix):
            if prefix.startswith('-'):
                self.completion_mode = CompletionMode.parameter

        def handle_space():
            if self.completion_mode == CompletionMode.command:
                # while in command completion mode, any space triggers an attempt to move up in the command tree
                increment_command_branch(text)
            elif self.completion_mode == CompletionMode.parameter:
                # TODO: More logic here--flags won't automatically switch to value...
                self.completion_mode = CompletionMode.value

        text = format_command(document.text_before_cursor)
        prefix = text.split()[-1] if text[-1] != ' ' else ''

        if requires_refresh():
            # if backspace was used a complete refresh is needed regardless of completion mode
            refresh_command_branch(text)

        if prefix:
            handle_prefix(prefix)
        else:
            handle_space()

        # Only attempt to apply the relevant completions
        if self.completion_mode == CompletionMode.command:
            # Command Completions
            for cmd in sort_completions(self.generate_command_completions(text, prefix)):
                yield cmd

        elif self.completion_mode == CompletionMode.value:
            # Value Completions
            for val in sort_completions(self.generate_param_value_completions(text, prefix)):
                yield val

        elif self.completion_mode == CompletionMode.parameter:
            # Parameter Completions
            for param in sort_completions(self.generate_param_name_completions(text, prefix)):
                yield param

            for param in sort_completions(self.generate_global_param_completions(text, prefix)):
                yield param

        self.prev_text_before_cursor = document.text_before_cursor

    def generate_command_completions(self, text, prefix):
        """ whether is a space or no text typed, send the current branch """
        for child in self.branch.children:
            if self._validate_command_completion(child, prefix):
                yield Completion(str(child), -len(prefix))

    def generate_param_name_completions(self, text, prefix):
        """ generates parameter name completions """

        def yield_param_completion(param, last_word):
            """ yields a parameter """
            return Completion(param, -len(last_word), display_meta=self.param_description.get(
                self.curr_command + " " + str(param), '').replace('\n', ''))

        # ONCE PARAMETERS are loaded into the command tree, this should be easy to get
        parameters = self.branch.get('parameters') or {}

        #for param in parameters:
        #    if self._validate_param_completion(param, last_word, text) and not param.startswith("--"):
        #        yield yield_param_completion(param, last_word)

        #if self.curr_command in self.command_parameters:  # Everything should, map to empty list
        #    for param in self.command_parameters[self.curr_command]:
        #        if self._validate_param_completion(param, last_word, text):
        #            yield yield_param_completion(param, last_word)

    # pylint: disable=too-many-branches
    def generate_param_value_completions(self, text, prefix):
        """ generates the dynamic values, like the names of resource groups """

        def gen_enum_completions(arg_name, text, started_param, prefix):
            """ generates dynamic enumeration completions """
            try:  # if enum completion
                for choice in self.cmdtab[
                        self.curr_command].arguments[arg_name].choices:
                    if started_param:
                        if choice.lower().startswith(prefix.lower())\
                           and choice not in text.split():
                            yield Completion(choice, -len(prefix))
                    else:
                        yield Completion(choice, -len(prefix))

            except TypeError:  # there is no choices option
                pass

        def get_arg_name(is_param, param):
            """ gets the argument name used in the command table for a parameter """
            if self.curr_command in self.cmdtab and is_param:
                for arg in self.cmdtab[self.curr_command].arguments:

                    for name in self.cmdtab[self.curr_command].arguments[arg].options_list:
                        if name == param:
                            return arg

        def mute_parse_args(text):
            """ mutes the parser error when parsing, the puts it back """
            error = AzCliCommandParser.error
            AzCliCommandParser.error = error_pass

            parse_args = self.argsfinder.get_parsed_args(
                parse_quotes(text, quotes=False, string=False))

            AzCliCommandParser.error = error
            return parse_args

        try:  # pylint: disable=too-many-nested-blocks

            is_param, started_param, prefix, param = dynamic_param_logic(text)

            # command table specific name
            arg_name = self.get_arg_name(is_param, param)

            if arg_name and ((text.split()[-1].startswith('-') and text[-1].isspace()) or
                             text.split()[-2].startswith('-')):

                for comp in gen_enum_completions(arg_name, text, started_param, prefix):
                    yield comp

                parse_args = mute_parse_args(text)

                # there are 3 formats for completers the cli uses
                # this try catches which format it is
                if self.cmdtab[self.curr_command].arguments[arg_name].completer:
                    try:
                        for comp in self.cmdtab[self.curr_command].arguments[arg_name].completer(
                                prefix=prefix, action=None, parsed_args=parse_args):

                            for comp in gen_dyn_completion(
                                    comp, started_param, prefix, text):
                                yield comp
                    except TypeError:
                        try:
                            for comp in self.cmdtab[self.curr_command].\
                                    arguments[arg_name].completer(prefix=prefix):

                                for comp in gen_dyn_completion(
                                        comp, started_param, prefix, text):
                                    yield comp
                        except TypeError:
                            try:
                                for comp in self.cmdtab[self.curr_command].\
                                        arguments[arg_name].completer():

                                    for comp in gen_dyn_completion(
                                            comp, started_param, prefix, text):
                                        yield comp

                            except TypeError:
                                pass  # other completion method used

        # if the user isn't logged in
        except Exception:  # pylint: disable=broad-except
            pass

    def generate_global_param_completions(self, text, prefix):
        """ Global parameter stuff hard-coded in """
        txtspt = text.split()
        if txtspt and len(txtspt) > 0:
            for param in self.global_param:
                # for single dash global parameters
                if txtspt[-1].startswith('-') \
                        and not txtspt[-1].startswith('--') and \
                        param.startswith('-') and not param.startswith('--') and\
                        self._validate_param_completion(param, txtspt[-1], text, check_double=False):
                    yield Completion(
                        param, -len(txtspt[-1]),
                        display_meta=self.global_param_descriptions[param])
                # for double dash global parameters
                elif txtspt[-1].startswith('--') and \
                        self._validate_param_completion(param, txtspt[-1], text, check_double=False):
                    yield Completion(
                        param, -len(txtspt[-1]),
                        display_meta=self.global_param_descriptions[param])
            # if there is an output, gets the options without user typing
            if txtspt[-1] in self.output_options:
                for opt in self.output_choices:
                    yield Completion(opt)
            # if there is an output option, if they have started typing
            if len(txtspt) > 1 and\
                    txtspt[-2] in self.output_options:
                for opt in self.output_choices:
                    if self._validate_param_completion(opt, txtspt[-1], text, check_double=False):
                        yield Completion(opt, -len(txtspt[-1]))

    def is_completable(self, symbol):
        """ whether the word can be completed as a command or parameter """
        return symbol in self.command_parameters or symbol in self.param_description.keys()

    def has_description(self, param):
        """ if a parameter has a description """
        return param in self.param_description.keys() and \
            not self.param_description[param].isspace()
