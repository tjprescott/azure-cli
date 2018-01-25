# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class CommandTree(object):
    """ a command tree """
    def __init__(self, data, children=None):
        self.data = data
        self.children = children or {}

    def add_child(self, child):
        """ adds a child to this branch """
        assert isinstance(child, CommandTree)
        if not self.children:
            self.children = []
        self.children.append(child)

    def has_child(self, name):
        """ whether this has a child """
        return name in self.children or {}


class CommandHead(CommandTree):
    """ represents the head of the tree, no data"""

    def __init__(self, children=None):
        CommandTree.__init__(self, None, children=[])

    def get_subbranch(self, data):
        """ returns the subbranch of a command """
        data_split = data.split()
        kids = self.children
        for word in data_split:
            kid = kids[word]
            kids = kid.children

        return self._get_subbranch_help(kids, [])

    def _get_subbranch_help(self, to_check, acc):
        check_next = []
        if not to_check:
            return acc
        for branch in to_check:
            if not branch:
                continue
            else:
                acc.append(branch.data)
                if branch.children:
                    check_next.extend(branch.children)
        self._get_subbranch_help(check_next, acc)
        return acc


class CommandBranch(CommandTree):
    """ represents a branch of the tree """
    def __init__(self, data, children=None):
        CommandTree.__init__(self, data, children)


def generate_tree(commands):
    """ short cut to make a tree """
    data = commands.split()[::-1]
    first = True
    prev = None
    node = None
    for kid in data:
        node = CommandTree(kid)
        if first:
            first = False
            prev = node
        else:
            node.add_child(prev)
    return node


def in_tree(tree, cmd):
    """ if a command is in the tree """
    data = cmd.split(' ')
    if not data:
        return True
    try:
        if tree.data:
            if data[0] == tree.data:
                for datum in data[1:]:
                    if tree.has_child(datum):
                        tree = tree.children[datum]
                    else:
                        return False
            else:
                return False
        else:
            for datum in data:
                if tree.has_child(datum):
                    tree = tree.children[datum]
                else:
                    return False
    except ValueError:
        return False
    return True
