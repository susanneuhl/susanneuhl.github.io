import re

file_path = '/Users/henryuhl/Documents/GitHub/susanneuhl.github.io/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Identify the three main lists (Schauspiel, Oper, Film)
lists = re.split(r'(<h2>(?:Schauspiel|Oper|Film)</h2>\s*<ul>)', content)

# There should be 7 parts (before lists, title1, list1, title2, list2, title3, list3, after)
# But let's be more robust: find all <ul> tags after <h2> titles
li_regex = re.compile(r'(<li[^>]*onclick=[^>]*>)')

def process_list(list_content, list_index):
    items = re.split(r'(</li>)', list_content)
    li_count = 0
    new_items = []
    
    for item in items:
        if '<li' in item:
            li_count += 1
            # For the first 2 items in each list (visible row)
            if li_count <= 2:
                # Remove 'reveal' class
                item = item.replace(' class="reveal"', '')
                item = item.replace(' class="reveal "', ' ')
                
                # Ensure high priority
                item = re.sub(r'fetchpriority="[^"]*"', 'fetchpriority="high"', item)
                item = re.sub(r'loading="[^"]*"', 'loading="eager"', item)
                
                # Check picture content for img tags too
                if 'fetchpriority' not in item:
                    item = item.replace('<img ', '<img fetchpriority="high" ')
                if 'loading' not in item:
                    item = item.replace('<img ', '<img loading="eager" ')
            else:
                # All other items: reveal + lazy
                if 'class="reveal"' not in item:
                    if 'class="' in item:
                        item = item.replace('class="', 'class="reveal ')
                    else:
                        item = item.replace('<li ', '<li class="reveal" ')
                
                # Ensure low priority
                item = re.sub(r'fetchpriority="[^"]*"', 'fetchpriority="low"', item)
                item = re.sub(r'loading="[^"]*"', 'loading="lazy"', item)
                
                # Ensure picture content for img tags too
                if 'fetchpriority' not in item:
                    item = item.replace('<img ', '<img fetchpriority="low" ')
                if 'loading' not in item:
                    item = item.replace('<img ', '<img loading="lazy" ')
                    
        new_items.append(item)
    
    return "".join(new_items)

# Re-identify lists and process them
# We find content between <ul> and </ul>
parts = re.split(r'(<ul[^>]*>|</ul>)', content)
processed_parts = []
ul_found_count = 0

for part in parts:
    if part.startswith('<ul'):
        ul_found_count += 1
        processed_parts.append(part)
    elif ul_found_count > 0 and not part.startswith('</ul'):
        # Process items inside the <ul>
        processed_parts.append(process_list(part, ul_found_count))
        ul_found_count = 0 # reset for next ul
    else:
        processed_parts.append(part)

final_content = "".join(processed_parts)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(final_content)






