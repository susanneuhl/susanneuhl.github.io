import re
import os

file_path = '/Users/henryuhl/Documents/GitHub/susanneuhl.github.io/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add --lqip variable to all <li> items in the main grid
def add_lqip_var(match):
    li_tag = match.group(0)
    # Find the image name from the li content
    img_match = re.search(r'images/(?:thumbs|compressed)/([^.]+)\.', li_tag)
    if not img_match:
        return li_tag
    
    img_name = img_match.group(1)
    lqip_style = f' style="--lqip: url(\'images/tiny/{img_name}.jpg\')"'
    
    if 'style="' in li_tag:
        # Append to existing style
        return li_tag.replace('style="', f'style="--lqip: url(\'images/tiny/{img_name}.jpg\'); ')
    else:
        # Add style attribute before the first '>'
        return li_tag.replace('>', f'{lqip_style}>', 1)

# Only match <li> tags inside the main-container lists
# We search for <li> tags that contain an image reference
content = re.sub(r'<li[^>]*onclick=[^>]*>[\s\S]*?<img[^>]*>[\s\S]*?</li>', 
                lambda m: re.sub(r'<li([^>]*)>', add_lqip_var, m.group(0), count=1), 
                content)

# 2. Add image loading JS
image_load_js = """
        // Handle LQIP fade-in
        document.addEventListener('DOMContentLoaded', function() {
            const gridImages = document.querySelectorAll('.main-container li img');
            gridImages.forEach(img => {
                const li = img.closest('li');
                if (img.complete) {
                    li.classList.add('loaded');
                } else {
                    img.addEventListener('load', () => li.classList.add('loaded'));
                }
            });
        });
"""

# Inject before the end of the script block
content = content.replace('// Scroll Reveal Animation', image_load_js + '\n        // Scroll Reveal Animation')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)







