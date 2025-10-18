def exec_python(code):
    is_exit = False
    stdout = ''

    def _exit():
        raise SystemExit()

    def _print(*values, sep=" ", end="\n", file=None, flush=False):
        nonlocal stdout
        out = []
        for a in values:
            out.append(repr(a))
        line = sep.join(out) + end
        stdout += line

    try:
        exec(code, {'exit': _exit, 'print': _print})
    except SystemExit:
        is_exit = True
    return stdout, is_exit


code = '''
import wps365

print(1, 'a')
wps365.search_one_user("123")
exit()
print("nihao世界")
'''
stdout, is_exit = exec_python(code)
print('stdout:', stdout)
print('is_exit:', is_exit)
