#!/usr/bin/env python3
################################################################################
##
## This file is part of BetterPonymotes.
## Copyright (c) 2015 Typhos.
##
## This program is free software: you can redistribute it and/or modify it
## under the terms of the GNU Affero General Public License as published by
## the Free Software Foundation, either version 3 of the License, or (at your
## option) any later version.
##
## This program is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
## for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
################################################################################

import logbook

import cssselect

import tinycss2

log = logbook.Logger(__name__)

# CSS parser. We use tinycss2/cssselect for "parsing" but as a result of
# imposing two simplifications we generally discard the results:
#
# - Stringify selectors in favor of regexp-based parsing, to avoid having to
#   deal with complex selector AST's for simple things. Since cssselect has
#   already had a pass over the rules, though, we can normalize the selector
#   strings substantially (eliminating excess whitespace).
#
# - Stringify properties in favor of more regexp-based parsing, since although
#   tinycss2 can often get us something sane to work with, it appears to fall
#   apart quickly: it doesn't give anything particularly useful for %-based
#   background-position properties as an example, at which point it's easier to
#   stringify again.

class Rule:
    def __init__(self, selector, properties):
        self.selector = selector
        self.properties = properties

    def __repr__(self):
        return "Rule(%r, %r)" % (self.selector, self.properties)

    def __str__(self):
        props = [str(p) for p in self.properties]
        return "%s { %s }" % (self.selector, "; ".join(props))

    def serialize(self):
        d = {"type": "rule", "selector": self.selector, "properties": [prop.serialize() for prop in self.properties]}
        return d

class KeyframesRule:
    def __init__(self, name, keyframes):
        self.name = name
        self.keyframes = keyframes

    def __repr__(self):
        return "KeyframesRule(%r, %r)" % (self.name, self.keyframes)

    def __str__(self):
        keyframes = [str(k) for k in self.keyframes]
        return "@keyframes %s { %s }" % (self.name, " ".join(keyframes))

    def serialize(self):
        d = {"type": "keyframes", "name": self.name, "keyframes": [k.serialize() for k in self.keyframes]}
        return d

class Keyframe:
    def __init__(self, percentage, properties):
        self.percentage = percentage
        self.properties = properties

    def __repr__(self):
        return "Keyframe(%r, %r)" % (self.percentage, self.properties)

    def __str__(self):
        props = [str(p) for p in self.properties]
        return "%s%% { %s }" % (self.percentage, " ".join(props))

    def serialize(self):
        d = {"percentage": self.percentage, "properties": [prop.serialize() for prop in self.properties]}
        return d

class Property:
    def __init__(self, name, value, important=False):
        self.name = name
        self.value = value
        self.important = important

    def __repr__(self):
        if self.important:
            return "Property(%r, %r, important=True)" % (self.name, self.value)
        else:
            return "Property(%r, %r)" % (self.name, self.value)

    def __str__(self):
        s = "%s: %s" % (self.name, self.value)
        if self.important:
            s += " !important"
        return s

    def serialize(self):
        d = {"property": self.name, "value": self.value}
        if self.important:
            d["important"] = True
        return d

def parse_stylesheet(css):
    rules = tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True)

    for rule in rules:
        if rule.type == "qualified-rule":
            yield from parse_rule(rule)
        elif rule.type == "at-rule":
            yield from parse_at_rule(rule)
        elif rule.type == "error":
            log.warning("Parse error: {}", rule)
        else:
            log.warning("Unrecognized rule type: {}", rule.type)

def parse_rule(rule):
    string = "".join([s.serialize() for s in rule.prelude])
    selectors = cssselect.parse(string)
    for sel in selectors:
        yield Rule(stringify_selector(sel), parse_properties(rule.content))

def parse_at_rule(rule):
    if rule.lower_at_keyword in ["keyframes", "-moz-keyframes", "-webkit-keyframes", "-o-keyframes", "-ms-keyframes"]:
        yield parse_keyframes(rule.prelude, rule.content)
    elif rule.lower_at_keyword in ["media"]:
        pass # Ignore
    else:
        log.warning("Unrecognized at-rule keyword: {}", rule.lower_at_keyword)

def parse_keyframes(prelude, content):
    # Find the one IdentToken in the prelude we expect, that signifies the
    # name of the animation. Ignore whitespace.
    name = None
    for token in prelude:
        if token.type == "whitespace":
            pass
        elif token.type == "ident" and name is None:
            name = token.value
        else:
            log.warning("Unexpected token found in @keyframes prelude: {}", token)

    keyframes = []

    # Expect a list of PercentageToken + CurlyBracketsBlock tokens.
    p = None
    for token in content:
        if token.type == "whitespace":
            pass
        elif token.type == "percentage":
            if p is None:
                p = token.int_value if token.is_integer else token.value
            else:
                log.warning("Extra percentage token found in @keyframes content: {}", token)
        elif token.type == "{} block":
            if p is None:
                log.warning("Curly bracket block found in @keyframes content without preceding percentage token in @keyframes content: {}", token)
            else:
                properties = parse_properties(token.content)
                keyframes.append(Keyframe(p, properties))
                p = None
        else:
            log.warning("Unknown token found in @keyframes content: {}", token)

    return KeyframesRule(name, keyframes)

def parse_properties(tokens):
    asts = tinycss2.parse_declaration_list(tokens, skip_comments=True, skip_whitespace=True)
    d = []
    for prop in asts:
        value = "".join([t.serialize() for t in prop.value]).strip()
        # We don't bother simplifying repeated properties in the same block,
        # since we have to implement a similar but more complete pass later
        # anyway.
        d.append(Property(prop.lower_name, value, prop.important))
    return d

def stringify_selector(sel):
    s = stringify_selector_tree(sel.parsed_tree)
    if s is None:
        return None
    if sel.pseudo_element is not None:
        if isinstance(sel.pseudo_element, cssselect.parser.FunctionalPseudoElement):
            # sel.pseudo_element.arguments is a list of tokens, which we don't
            # want to try to handle.
            log.warning("Don't know how to handle functional pseudo element: {}", sel.pseudo_element)
            return None
        else:
            s += "::" + sel.pseudo_element
    return s

def stringify_selector_tree(tree):
    if isinstance(tree, cssselect.parser.Class):
        left = stringify_left(tree.selector)
        return "%s.%s" % (left, tree.class_name)

    # Should not actually occur in the selector tree
    #elif isinstance(tree, cssselect.parser.FunctionalPseudoElement):
    #    log.warning("Unhandled selector parse node: {}", tree)

    elif isinstance(tree, cssselect.parser.Function):
        args = " ".join(token.value for token in tree.arguments)
        return "%s:%s(%s)" % (stringify_selector_tree(tree.selector), tree.name, args)

    elif isinstance(tree, cssselect.parser.Pseudo):
        return "%s:%s" % (stringify_selector_tree(tree.selector), tree.ident)

    elif isinstance(tree, cssselect.parser.Negation):
        left = stringify_selector_tree(tree.selector)
        right = stringify_selector_tree(tree.subselector)
        return "%s:not(%s)" % (left, right)

    elif isinstance(tree, cssselect.parser.Attrib):
        if tree.namespace is not None:
            log.warning("Don't know how to handle attrib namespace: {}", tree)
        left = stringify_left(tree.selector)
        if tree.operator == "exists":
            return "%s[%s]" % (left, tree.attrib)
        else:
            return "%s[%s%s%r]" % (left, tree.attrib, tree.operator, tree.value)

    elif isinstance(tree, cssselect.parser.Element):
        if tree.namespace is not None:
            log.warning("Don't know how to handle element namespace: {}", tree)
        return tree.element or "*"

    elif isinstance(tree, cssselect.parser.Hash):
        # Special case to avoid "*#id" output
        left = stringify_left(tree.selector)
        return "%s#%s" % (left, tree.id)

    elif isinstance(tree, cssselect.parser.CombinedSelector):
        left = stringify_selector_tree(tree.selector)
        right = stringify_selector_tree(tree.subselector)
        if tree.combinator == " ":
            return "%s %s" % (left, right)
        else:
            return "%s %s %s" % (left, tree.combinator, right)

    else:
        log.warning("Unknown selector parse class: {}", tree)

def stringify_left(tree):
    # Special case to avoid output like "*.class" and "*#id"
    if isinstance(tree, cssselect.parser.Element) and tree.element is None:
        return ""
    else:
        return stringify_selector_tree(tree)
