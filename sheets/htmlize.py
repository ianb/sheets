import sys
import types
import re
import ast
import astor
from tempita import HTMLTemplate, html, html_quote
from functools import singledispatch

def strip_html(x):
    x = str(x)
    x = re.sub(r'<.*?>', '', x)
    x = x.replace('&lt;', '<')
    x = x.replace('&gt;', '>')
    x = x.replace('&quot;', '"')
    x = x.replace('&amp;', '&')
    return x

def htmlize_plain(x):
    x = str(x)
    x = html_quote(x)
    x = x.replace('\n', '<br/>\n')
    x = re.sub(r'  ', ' &nbsp;', x)
    return html('<code>%s</code>' % x)

htmlize_dispatched = singledispatch(htmlize_plain)

def htmlize(x):
    if hasattr(x, '_repr_html_'):
        return html(x._repr_html_())
    return htmlize_dispatched(x)

htmlize.register = htmlize_dispatched.register
htmlize.dispatch = htmlize_dispatched.dispatch

@singledispatch
def htmlize_repr_dispatched(x):
    if htmlize.dispatch(type(x)) is htmlize_plain:
        return htmlize(repr(x))
    return htmlize(x)

def htmlize_repr(x):
    if hasattr(x, '_repr_html_'):
        return html(x._repr_html_())
    return htmlize_repr_dispatched(x)

htmlize_repr.register = htmlize_repr_dispatched.register
htmlize_repr.dispatch = htmlize_repr_dispatched.dispatch

@htmlize_repr.register(str)
def htmlize_repr_string(x):
    return htmlize(repr(x))

@singledispatch
def htmlize_short_repr(x, maxlen=40):
    if (htmlize_repr.dispatch(type(x)) is not htmlize_repr or
            htmlize.dispatch(type(x)) is not htmlize_plain):
        r = htmlize_repr(x)
        if not isinstance(r, html):
            r = html(r)
    else:
        r = repr(x)
    if isinstance(r, html) and len(strip_html(r)) > maxlen:
        # We can't easily strip down HTML, so punt with a normal repr
        r = repr(x)
    if not isinstance(r, html) and len(r) > maxlen:
        r = html('<span title="%s"><code>%s...%s</code></span>' % (
            html_quote(r), html_quote(r[:maxlen - 10]), html_quote(r[-10:])))
    if not isinstance(r, html):
        r = html('<code>%s</code>' % html_quote(r))
    return r

@htmlize_short_repr.register(types.FunctionType)
def htmlize_short_repr_func(x, maxlen=40):
    r = html('<code>%s()</code>' % html_quote(x.__qualname__))
    r.self_naming = True
    return r

@htmlize_short_repr.register(type)
def htmlize_short_repr_class(x, maxlen=40):
    r = html('<code>class %s</code>' % html_quote(x.__name__))
    r.self_naming = True
    return r

@htmlize_short_repr.register((list, tuple))
def htmlize_short_repr_list(x, maxlen=40):
    if isinstance(x, list):
        startc, endc = '[', ']'
        trailing1 = False
    else:
        startc, endc = '(', ')'
        trailing1 = True
    list_maxlen = maxlen - 10
    s = [html(startc)]
    index = 0
    while True:
        if len(s) > 1:
            s.append(', ')
        s.append(htmlize_short_repr(x[index]))
        if sum(len(strip_html(item)) for item in s) > list_maxlen:
            s.pop()
            s.pop()
            s.append(html(', (%s more)' % (len(x) - index)))
            break
        index += 1
        if index >= len(x):
            break
    if len(x) == 1 and trailing1:
        s.append(', ')
    s.append(html(endc))
    new_s = []
    for item in s:
        if isinstance(item, html):
            new_s.append(str(item))
        else:
            new_s.append('<code>%s</code>' % html_quote(str(item)))
    return html(''.join(new_s))

def subber(type, template, **extra):
    tmpl = HTMLTemplate(template)

    def repl(x):
        return html(tmpl.substitute(x=x, htmlize=htmlize, htmlize_repr=htmlize_repr, **extra))
    htmlize.register(type, repl)
    return repl

subber(tuple, '''
<code>(</code>{{for index, item in enumerate(x)}}{{htmlize_repr(item)}}{{if index != len(x) - 1}}, {{endif}}{{endfor}}<code>)</code>
''')

subber(list, '''
<code>[</code>{{for index, item in enumerate(x)}}{{htmlize_repr(item)}}{{if index != len(x) - 1}}, {{endif}}{{endfor}}<code>]</code>
''')

subber(dict, '''
<code>{</code>{{for key in sorted(x)}}{{htmlize_repr(key)}}<code>: </code>{{htmlize_repr(x[key])}}, {{endfor}}<code>}</code>
''')

@htmlize.register(ast.AST)
def htmlize_ast(x):
    return htmlize_plain(astor.dump(x, indentation='  '))

def htmlize_print(*objects, sep=' ', end='\n', file=sys.stdout, flush=False, classname="print-output", passthrough=False):
    if passthrough and len(objects) == 1 and objects[0] is None:
        # Don't print, just like the CLI
        return objects[0]
    if file is not sys.stdout:
        # FIXME: should allow overwriting
        file = sys.stdout
    if file is not sys.stdout or not getattr(file, 'writehtml', None):
        # We shouldn't override this then
        return print(*objects, sep=sep, end=end, file=file, flush=flush)
    parts = []
    for ob in objects:
        parts.append(htmlize(ob))
        if len(parts) > 1 and sep and sep != ' ':
            parts.append(htmlize(sep))
    if end == '\n':
        body = '<div class="%s">%s</div>' % (classname, ' '.join(str(x) for x in parts))
        parts.append(html('<br />'))
    elif end:
        parts.append(htmlize(end))
        body = ' '.join(str(x) for x in parts)
    file.writehtml(body)
    if passthrough:
        return objects[0]

def print_expr(expr_string, expr_value):
    if expr_value is None:
        # Don't print anything, just like the CLI
        return None
    if not hasattr(sys.stdout, "writehtml"):
        print("Unexpected sys.stdout without .writehtml:", sys.stdout)
        return expr_value
    body = '<dl><dt><code>%s</code></dt><dd>%s</dd></dl>' % (
        html_quote(expr_string),
        htmlize(expr_value))
    sys.stdout.writehtml(body)
    return expr_value
