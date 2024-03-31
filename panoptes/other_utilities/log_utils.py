import re

def ansi_to_html(text):
    # ANSI escape regex
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    # mapping of ANSI codes to HTML
    ansi_to_html_map = {
        '\033[1m': '<span style="font-weight:bold;">',  # bold
        '\033[4m': '<span style="text-decoration:underline;">',  # underline
        '\033[31m': '<span style="color:red;">',  # red
        '\033[32m': '<span style="color:green;">',  # green
        '\033[93m': '<span style="color:#FFBF00;">',  # yellow
        '\033[0m': '</span>',  # reset
    }

    for ansi, html in ansi_to_html_map.items():
        text = text.replace(ansi, html)

    # Remove any remaining ANSI
    text = ansi_escape.sub('', text)

    return text