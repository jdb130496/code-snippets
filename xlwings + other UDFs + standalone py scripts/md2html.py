# wa2html.py
import markdown, pathlib

md = pathlib.Path(r'D:\Downloads\WhatsApp_Chat_with_Meta_AI.md').read_text(encoding='utf-8')
body = markdown.markdown(md, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br'])

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: Calibri; max-width: 960px; margin: 40px auto; line-height: 1.6; background: #1e1e1e; color: #d4d4d4 }}
  h1   {{ color: #569cd6 }}
  h3   {{ margin-top: 1.4em; margin-bottom: 0 }}
  em   {{ color: #888; font-size: 0.85em }}
  hr   {{ border: none; border-top: 1px solid #333; margin: 1em 0 }}
  code {{ background: #2d2d2d; padding: 2px 5px; border-radius: 3px; font-family: Consolas }}
  pre  {{ background: #2d2d2d; padding: 12px; border-radius: 6px; overflow-x: auto }}
</style></head>
<body>{body}</body></html>"""

out = pathlib.Path(r'D:\Downloads\chat.html')
out.write_text(html, encoding='utf-8')
print(f'Done -> {out}')
