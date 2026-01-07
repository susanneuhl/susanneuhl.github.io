import re

file_path = '/Users/henryuhl/Documents/GitHub/susanneuhl.github.io/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add 'reveal' class to all <li> tags that don't have a class yet, or append to existing class
def add_reveal_class(match):
    li_start = match.group(1)
    attrs = match.group(2)
    
    if 'class="' in attrs:
        # Append to existing class
        new_attrs = re.sub(r'class="([^"]*)"', r'class="\1 reveal"', attrs)
    else:
        # Add class attribute
        new_attrs = attrs + ' class="reveal"'
    
    return f'<{li_start}{new_attrs}'

# Regex to find <li> tags
# We want to match <li followed by attributes
updated_content = re.sub(r'<(li)(\s+[^>]*|)>', add_reveal_class, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(updated_content)






