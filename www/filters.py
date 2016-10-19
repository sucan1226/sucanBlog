#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-10-04 13:24
# @Author  : sucan (416570018@qq.com)
# @Version : 1.0

import mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter

class HighlightRenderer(mistune.Renderer):

    def block_code(self, code, lang):
        guess = 'python3'
        if code.lstrip().startswith('<?php'):
            guess = 'php'
        elif code.lstrip().startswith('<'):
            guess = 'html'
        elif code.lstrip().startswith(('function', 'var', '$')):
            guess = 'javascript'

        lexer = get_lexer_by_name(lang or guess, stripall=True)
        return highlight(code, lexer, HtmlFormatter())

# 因为页面经常用md渲染，所以定义为常量，不用在函数内重复申请释放内存
markdown = mistune.Markdown(renderer=HighlightRenderer(), hard_wrap=True)


def marked_filter(content):
    return markdown(content)
