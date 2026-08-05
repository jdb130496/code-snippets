import re

with open(r'D:\Downloads\copilot-chat.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Split into blocks at each "You said:" or "Copilot said:"
blocks = re.split(r'(?=You said:|Copilot said:)', content)

# Deduplicate preserving first occurrence order
seen = set()
result = []
for block in blocks:
    stripped = block.strip()
    if stripped and stripped not in seen:
        seen.add(stripped)
        result.append(block)

output = ''.join(result)

with open(r'D:\Downloads\copilot-chat-clean.md', 'w', encoding='utf-8') as f:
    f.write(output)

print(f'Original blocks: {len(blocks)}')
print(f'After dedup: {len(result)}')
print(f'Duplicates removed: {len(blocks) - len(result)}')
