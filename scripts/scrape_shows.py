#!/usr/bin/env python3
"""
Theater Show Scraper for Susanne Uhl Website
Scrapes current show dates from theater websites
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import os
import time
import random
from urllib.parse import urljoin

MONTH_MAP = {
    'januar': '01', 'jan': '01',
    'februar': '02', 'feb': '02',
    'märz': '03', 'maerz': '03', 'mär': '03', 'maer': '03',
    'april': '04', 'apr': '04',
    'mai': '05',
    'juni': '06', 'jun': '06',
    'juli': '07', 'jul': '07',
    'august': '08', 'aug': '08',
    'september': '09', 'sept': '09', 'sep': '09',
    'oktober': '10', 'okt': '10',
    'november': '11', 'nov': '11',
    'dezember': '12', 'dez': '12'
}

def extract_director(text):
    """Extract director from text like 'Regie: Name Name'"""
    # Normalize whitespace first
    text = re.sub(r'\s+', ' ', text)
    
    # Pattern 1: Explicit "Regie: Name" (Case sensitive to avoid common words)
    # Match: Regie[:] [Space] Name(TitleCase) [Space] Name(TitleCase)
    # We allow Umlauts and accents
    match = re.search(r'Regie:?\s*([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)', text)
    if match:
        return match.group(1)
    
    # Pattern 2: "Inszenierung: Name" or "Inszenierung von Name"
    # Also matches "Inszenierungen von..."
    match = re.search(r'Inszenierung(?:en)?(?:\s+von|:)?\s*([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)', text, re.IGNORECASE)
    if match:
        name = match.group(1)
        # Filter out common false positives like "Von Shakespeare" if "von" was not consumed
        if name.lower() not in ['von shakespeare', 'von ewald']:
            return name
        
    return None

def extract_author(text):
    """Extract author from text like 'von Lew Tolstoi / Armin Petras' or 'von Ewald Palmetshofer'"""
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Pattern 1: "von Name Name / Name Name" (multiple authors)
    match = re.search(r'von\s+([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+(?:\s*/\s*[A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)*)', text)
    if match:
        author_str = match.group(1)
        # Filter out phrases like "frei nach"
        if 'frei nach' not in author_str.lower():
            return author_str
    
    # Pattern 2: "von Name Name frei nach..." (extract only the adapter)
    match = re.search(r'von\s+([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)\s+frei\s+nach', text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return None

def extract_duration(text):
    """Extract duration from text like 'Dauer: ca. 5 Stunden' or '3h 30min' or '2 3/4 Stunden'"""
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Pattern 0: "Dauer: X Y/Z Stunden | N Pause(n)" (with fractions like 2 3/4)
    match = re.search(r'Dauer:?\s*(?:ca\.?)?\s*(\d+)\s*(\d+/\d+)?\s*Stunden?\s*\|\s*(\d+)\s*Pausen?', text, re.IGNORECASE)
    if match:
        hours = match.group(1)
        fraction = match.group(2)
        pauses = match.group(3)
        if fraction:
            return f"{hours} {fraction}h ({pauses} Pause)"
        return f"{hours}h ({pauses} Pause)"
    
    # Pattern 1: "Dauer ca. X Stunden — Y Pausen"
    match = re.search(r'Dauer:?\s*(?:ca\.?)?\s*(\d+)\s*Stunden?(?:\s*—\s*(\w+)\s*Pausen?)?', text, re.IGNORECASE)
    if match:
        hours = match.group(1)
        pauses = match.group(2)
        if pauses:
            # Convert "zwei" -> "2" if needed
            pause_map = {'eine': '1', 'zwei': '2', 'drei': '3', 'vier': '4'}
            pause_num = pause_map.get(pauses.lower(), pauses)
            return f"ca. {hours}h ({pause_num} Pausen)"
        # Check for minutes after
        minute_match = re.search(r'(\d+)\s*(?:Minuten?|min)', text[match.end():match.end()+50], re.IGNORECASE)
        if minute_match:
            return f"{hours}h {minute_match.group(1)}min"
        return f"ca. {hours}h"
    
    # Pattern 2: "X Stunden Y Minuten — eine Pause" (ohne "Dauer")
    match = re.search(r'(\d+)\s*Stunden?\s*(\d+)\s*Minuten?(?:\s*—?\s*(\w+)\s*Pausen?)?', text, re.IGNORECASE)
    if match:
        hours = match.group(1)
        minutes = match.group(2)
        pauses = match.group(3)
        if pauses:
            pause_map = {'eine': '1', 'zwei': '2', 'drei': '3', 'vier': '4'}
            pause_num = pause_map.get(pauses.lower(), pauses)
            return f"{hours}h {minutes}min ({pause_num} Pause)"
        return f"{hours}h {minutes}min"
    
    # Pattern 3: "Dauer: X Minuten"
    match = re.search(r'Dauer:?\s*(?:ca\.?)?\s*(\d+)\s*(?:Minuten?|min)', text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}min"
    
    # Pattern 4: Standalone "ca. X Stunden — Y Pausen" (ohne "Dauer")
    match = re.search(r'ca\.?\s*(\d+)\s*Stunden?(?:\s*—\s*(\w+)\s*Pausen?)?', text, re.IGNORECASE)
    if match:
        hours = match.group(1)
        pauses = match.group(2)
        if pauses:
            pause_map = {'eine': '1', 'zwei': '2', 'drei': '3', 'vier': '4'}
            pause_num = pause_map.get(pauses.lower(), pauses)
            return f"ca. {hours}h ({pause_num} Pausen)"
        return f"ca. {hours}h"
    
    # Pattern 5: "Xh Ymin"
    match = re.search(r'(\d+)\s*h\s*(\d+)\s*min', text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}h {match.group(2)}min"
    
    return None

def scrape_staatsschauspiel_dresden():
    """Scrape Der Komet dates from Staatsschauspiel Dresden"""
    events = []
    director = None
    duration = None
    author = None
    
    # Try multiple URLs for Dresden
    urls = [
        "https://www.staatsschauspiel-dresden.de/spielplan/a-z/der-komet/",
        "https://tickets.staatsschauspiel-dresden.de/webshop/webticket/eventlist?production=709",
        "https://www.staatsschauspiel-dresden.de/spielplan/"
    ]
    
    for url in urls:
        try:
            # ... headers and response handling ...
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache'
            }
            
            # Add random delay to avoid being blocked
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text(separator=' ')
            
            # Try to extract director if not found yet
            # Only try to extract director from the specific production page
            if "spielplan/a-z/" in url and not director:
                director = extract_director(page_text)
                if not duration:
                    duration = extract_duration(page_text)
                if not author:
                    # For "Der Komet", look for "nach dem Buch von Durs Grünbein"
                    match = re.search(r'nach\s+dem\s+Buch\s+von\s+([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)', page_text, re.IGNORECASE)
                    if match:
                        author = match.group(1)
            
            # Look for structured meta tags with startDate
            meta_tags = soup.find_all('meta', attrs={'itemprop': 'startDate'})
            for meta_tag in meta_tags:
                try:
                    start_date = meta_tag.get('content')
                    if start_date:
                        # Parse ISO format: 2025-09-20T19:30:00
                        if 'T' in start_date:
                            date_part, time_part = start_date.split('T')
                            year, month, day = date_part.split('-')
                            hour, minute, _ = time_part.split(':')
                            
                            datetime_str = f"{year}-{month}-{day} {hour}:{minute}"
                            
                            # Only future dates
                            event_date = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                            if event_date > datetime.now():
                                # Check if this meta tag is within the Der Komet section
                                parent_element = meta_tag.parent
                                is_komet = False
                                
                                if parent_element:
                                    # Look for "Der Komet" in the surrounding context
                                    context_text = ""
                                    curr = parent_element
                                    for i in range(5):  # Check up to 5 levels up
                                        if curr:
                                            context_text += curr.get_text() + " "
                                            curr = curr.parent
                                    
                                    if re.search(r'der\s+komet|komet', context_text, re.I):
                                        is_komet = True
                                    
                                if is_komet:
                                    events.append({
                                        "date": datetime_str,
                                        "display_date": f"{day}.{month}.{year}",
                                        "display_time": f"{hour}:{minute}",
                                        "ticket_url": url
                                    })
                                    print(f"Found Der Komet date: {day}.{month}.{year} {hour}:{minute}")
                except Exception as e:
                    print(f"Error parsing meta tag: {e}")
                    continue
            
            # If no structured data found, try text-based approach
            if not events:
                page_text = soup.get_text()
                
                # Look for Der Komet specifically in the full page text
                komet_events = extract_komet_dates_from_page(page_text, url)
                events.extend(komet_events)
                
                # Also try structured approaches
                strategies = [
                    # Look for calendar/date containers
                    lambda soup: soup.find_all(['div', 'section', 'article'], 
                                             class_=re.compile(r'calendar|spielplan|termine|events', re.I)),
                    # Look for specific date patterns in links
                    lambda soup: soup.find_all('a', href=re.compile(r'termin|date|event')),
                    # Look for table rows that might contain dates
                    lambda soup: soup.find_all('tr'),
                ]
                
                for strategy in strategies:
                    try:
                        elements = strategy(soup)
                        for element in elements:
                            events.extend(extract_dates_from_element(element, url))
                    except Exception as e:
                        print(f"Strategy failed for {url}: {e}")
                        continue
                    
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            continue
    
    return clean_and_sort_events(events), director, duration, author

def extract_komet_dates_from_page(page_text, base_url):
    """Specifically look for Der Komet dates in page text"""
    events = []
    
    # Split text into lines for better processing
    lines = page_text.split('\n')
    
    for i, line in enumerate(lines):
        # If line mentions "Der Komet" or "Komet", look for dates in surrounding lines
        if re.search(r'der\s+komet|komet', line, re.I):
            # Check current line and next few lines for dates
            search_text = ' '.join(lines[max(0, i-2):i+5])
            events.extend(extract_dates_from_text(search_text, base_url))
    
    return events

def extract_dates_from_text(text, base_url):
    """Extract dates from text content"""
    events = []
    
    # Normalize whitespace to help with multiline dates
    # Replace multiple whitespaces/newlines with single space
    normalized_text = re.sub(r'\s+', ' ', text)
    
    # Enhanced date patterns for German
    patterns = [
        # DD.MM.YYYY with time
        r'(\d{1,2})\.(\d{1,2})\.(\d{4}).*?(\d{1,2})[:\.](\d{2})',
        # DD.MM.YYYY without time  
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
        # DD. MMM YYYY (e.g., 20. September 2025)
        r'(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*(\d{4})',
        # DD MMM YYYY without dot (e.g., 17 Okt 2025)
        r'(\d{1,2})\s+(Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez|Januar|Februar|März|April|Juni|Juli|August|September|Oktober|November|Dezember)\s+(\d{4})',
        # DD. MMM without year (e.g., 17. Okt, 19. Nov) - BUT careful with Premiere dates
        r'(\d{1,2})\.\s*(Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez|Januar|Februar|März|April|Juni|Juli|August|September|Oktober|November|Dezember)',
        # DD MMM without year or dot (e.g., 17 Okt)
        r'(\d{1,2})\s+(Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)\s+(?!202)',
    ]
    
    month_map = {
        'Januar': '01', 'Februar': '02', 'März': '03', 'April': '04',
        'Mai': '05', 'Juni': '06', 'Juli': '07', 'August': '08',
        'September': '09', 'Oktober': '10', 'November': '11', 'Dezember': '12',
        'Jan': '01', 'Feb': '02', 'Mär': '03', 'Apr': '04',
        'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09',
        'Okt': '10', 'Nov': '11', 'Dez': '12'
    }
    
    for pattern in patterns:
        for match in re.finditer(pattern, normalized_text):
            try:
                groups = match.groups()
                time_display = None # No default fallback
                
                if len(groups) == 5:  # With time (DD.MM.YYYY HH:MM)
                    day, month, year, hour, minute = groups
                    datetime_str = f"{year}-{month.zfill(2)}-{day.zfill(2)} {hour.zfill(2)}:{minute.zfill(2)}"
                    time_display = f"{hour}:{minute}"
                
                else: # Without time in the match
                    if len(groups) == 3 and groups[1].isalpha():  # Month name with year
                        day, month_name, year = groups
                        month = month_map.get(month_name, '01')
                    elif len(groups) == 2 and groups[1].isalpha():  # Month name without year (e.g., "17. Okt")
                        day, month_name = groups
                        month = month_map.get(month_name, '01')
                        current_year = datetime.now().year
                        
                        # Use a temporary year for now to construct date object
                        temp_year = current_year
                        try:
                            test_date = datetime.strptime(f"{temp_year}-{month}-{day.zfill(2)}", "%Y-%m-%d")
                            if test_date < datetime.now() - timedelta(days=90):
                                year = temp_year + 1
                            else:
                                year = temp_year
                        except ValueError:
                            continue
                            
                    else:  # Without time (DD.MM.YYYY)
                        day, month, year = groups[:3]
                        
                    # Look for time after the date match
                    end_pos = match.end()
                    text_after = normalized_text[end_pos:end_pos+100]
                    
                    # Pattern for time: HH:MM or HH.MM (optionally with Uhr)
                    time_match = re.search(r'(?:\bum\s+)?(\d{1,2})[:\.](\d{2})(?:\s*Uhr)?', text_after)
                    if time_match:
                        h, m = time_match.groups()
                        time_display = f"{h.zfill(2)}:{m.zfill(2)}"
                        datetime_str = f"{year}-{month.zfill(2)}-{day.zfill(2)} {time_display}"
                    else:
                        # If no time found, skip this event
                        continue

                # Only future dates
                if time_display:
                    event_date = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                    if event_date > datetime.now():
                        events.append({
                            "date": datetime_str,
                            "display_date": f"{day.zfill(2)}.{month.zfill(2) if isinstance(month, str) and month.isdigit() else month_map.get(month_name if 'month_name' in locals() else groups[1], '01')}.{year}",
                            "display_time": time_display,
                            "ticket_url": base_url
                        })
            except Exception as e:
                # print(f"Error parsing date match: {e}")
                continue
    
    return events

def extract_dates_from_element(element, base_url):
    """Extract dates from HTML elements"""
    return extract_dates_from_text(element.get_text(), base_url)

def clean_and_sort_events(events):
    """Remove duplicates and sort events, prioritizing specific times over 19:30 default"""
    events_by_day = {}
    
    for event in events:
        # Date string YYYY-MM-DD
        date_str = event['date'].split(' ')[0]
        time_str = event['display_time']
        
        if date_str not in events_by_day:
            events_by_day[date_str] = []
            
        current_day_events = events_by_day[date_str]
        
        # Check if we already have this specific time
        if any(e['display_time'] == time_str for e in current_day_events):
            continue
            
        # Logic to handle 19:30 default vs specific times
        if time_str == "19:30":
            # Only add 19:30 if we don't have any other time for this day yet
            # This assumes 19:30 is likely a fallback if specific times exist
            if not current_day_events:
                current_day_events.append(event)
        else:
            # We have a specific time (not 19:30). 
            # Remove any existing 19:30 entry as it was likely a fallback
            events_by_day[date_str] = [e for e in current_day_events if e['display_time'] != "19:30"]
            events_by_day[date_str].append(event)
    
    # Flatten and sort
    final_events = []
    for day_events in events_by_day.values():
        final_events.extend(day_events)
    
    return sorted(final_events, key=lambda x: x['date'])[:20]


def parse_german_date(date_text):
    """Parse German date text like '29. November 2025' into ISO format date"""
    # Normalize whitespace
    clean_text = re.sub(r'\s+', ' ', date_text.strip())

    # Match formats like '29. November 2025'
    match = re.search(r'(\d{1,2})\.\s*([A-Za-zäöüÄÖÜ]+)\s*(\d{4})', clean_text)
    if not match:
        return None

    day, month_name, year = match.groups()
    month_key = month_name.lower()

    # Normalize umlauts for lookup
    month_key = month_key.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')

    month = MONTH_MAP.get(month_key)
    if not month:
        return None

    return f"{year}-{month}-{day.zfill(2)}"


def extract_time(text):
    """Extract time like '19.30 Uhr' or '19:30 Uhr'"""
    # Prefer explicit times in the text
    match = re.search(r'(\d{1,2})[\.:](\d{2})\s*Uhr', text, re.IGNORECASE)
    if not match:
        # Try without 'Uhr' but careful not to match dates
        match = re.search(r'(?<!\d\.)(\d{1,2})[\.:](\d{2})(?!\.\d{4})', text)
    
    if not match:
        return None  # No default fallback

    hour, minute = match.groups()
    return f"{hour.zfill(2)}:{minute.zfill(2)}"


def scrape_dnt_weimar_dumme_jahre():
    """Scrape Dumme Jahre dates from DNT Weimar"""
    events = []
    director = None
    duration = None

    url = "https://www.dnt-weimar.de/de/programm/stueck-detail.php?SID=3520"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache'
        }

        time.sleep(random.uniform(1, 3))

        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to extract director
        director = extract_director(soup.get_text(separator=' '))

        event_container = soup.find('div', id='event-tickets')
        if event_container:
            for item in event_container.find_all('div', class_=re.compile(r'event-date-item')):
                try:
                    text = item.get_text(separator=' ', strip=True)
                    if not text:
                        continue

                    date_str = parse_german_date(text)
                    if not date_str:
                        continue

                    time_str = extract_time(text)

                    event_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    if event_datetime <= datetime.now():
                        continue

                    ticket_link = item.find('a', href=True)
                    ticket_url = urljoin(url, ticket_link['href']) if ticket_link else url

                    events.append({
                        "date": f"{date_str} {time_str}",
                        "display_date": datetime.strftime(event_datetime, "%d.%m.%Y"),
                        "display_time": time_str,
                        "ticket_url": ticket_url
                    })
                except Exception as e:
                    print(f"Error parsing DNT event item: {e}")
                    continue

        if not events:
            page_text = soup.get_text()
            events.extend(extract_dates_from_text(page_text, url))

    except Exception as e:
        print(f"Error scraping DNT Weimar: {e}")

    return clean_and_sort_events(events), director, duration

def scrape_oper_leipzig():
    """Scrape Undine dates from Oper Leipzig"""
    events = []
    director = None
    duration = None
    author = None
    
    # URL for dates (Susanne Uhl profile)
    url_dates = "https://www.oper-leipzig.de/de/ensemble/person/susanne-uhl/1902"
    # URL for details (Undine program page) - explicitly for director
    url_details = "https://www.oper-leipzig.de/de/programm/undine/611"
    
    # 1. Fetch details page for director
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache'
        }
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url_details, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        page_text_details = soup.get_text(separator=' ')
        director = extract_director(page_text_details)
        duration = extract_duration(page_text_details)
        
        # For operas, the composer is usually listed as "h4" with the composer name
        # Let's look for "Albert Lortzing" specifically or extract from page structure
        composer_h4 = soup.find('h4', string=re.compile(r'Albert Lortzing', re.I))
        if composer_h4:
            author = composer_h4.get_text(strip=True)
        
        print(f"Found Undine director: {director}")
        if author:
            print(f"Found Undine composer: {author}")
        
    except Exception as e:
        print(f"Error fetching Undine details: {e}")

    # 2. Fetch dates from profile page
    try:
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url_dates, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text(separator=' ')
        
        # Look for Undine specifically in the full page text
        undine_events = extract_undine_dates_from_page(page_text, url_dates)
        events.extend(undine_events)
        
        # Try additional scraping strategies
        strategies = [
            lambda soup: soup.find_all(['div', 'section'], class_=re.compile(r'calendar|spielplan|termine', re.I)),
            lambda soup: soup.find_all('a', href=re.compile(r'termin|date|event')),
            lambda soup: soup.find_all('tr'),
        ]
        
        for strategy in strategies:
            try:
                elements = strategy(soup)
                for element in elements:
                    events.extend(extract_dates_from_element(element, url_dates))
            except Exception as e:
                print(f"Strategy failed for Oper Leipzig: {e}")
                continue
        
    except Exception as e:
        print(f"Error scraping Oper Leipzig: {e}")
    
    return clean_and_sort_events(events), director, duration, author

def extract_undine_dates_from_page(page_text, base_url):
    """Specifically look for Undine dates in page text"""
    events = []
    
    lines = page_text.split('\n')
    
    for i, line in enumerate(lines):
        if re.search(r'undine', line, re.I):
            search_text = ' '.join(lines[max(0, i-2):i+5])
            events.extend(extract_dates_from_text(search_text, base_url))
    
    return events

def scrape_theater_bonn():
    """Scrape Sankt Falstaff dates from Theater Bonn"""
    events = []
    director = None
    duration = None
    author = None
    
    url = "https://www.theater-bonn.de/de/programm/sankt-falstaff/221198"
    ticket_url = "https://www.theater-bonn.de/de/programm/sankt-falstaff/221198#dates-and-tickets"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        }
        
        # Add random delay to avoid being blocked
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to extract director and duration
        page_text = soup.get_text(separator=' ')
        director = extract_director(page_text)
        duration = extract_duration(page_text)
        author = extract_author(page_text)
        
        # Look for structured event data (similar to Dresden approach)
        # Theater Bonn might use structured data markup
        meta_tags = soup.find_all('meta', attrs={'itemprop': 'startDate'})
        for meta_tag in meta_tags:
            try:
                start_date = meta_tag.get('content')
                if start_date:
                    # Parse ISO format: 2025-10-17T19:30:00
                    if 'T' in start_date:
                        date_part, time_part = start_date.split('T')
                        year, month, day = date_part.split('-')
                        hour, minute, _ = time_part.split(':')
                        
                        datetime_str = f"{year}-{month}-{day} {hour}:{minute}"
                        
                        # Only future dates
                        event_date = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                        if event_date > datetime.now():
                            events.append({
                                "date": datetime_str,
                                "display_date": f"{day}.{month}.{year}",
                                "display_time": f"{hour}:{minute}",
                                "ticket_url": ticket_url
                            })
                            print(f"Found Sankt Falstaff date: {day}.{month}.{year} {hour}:{minute}")
            except Exception as e:
                print(f"Error parsing meta tag: {e}")
                continue
        
        # Try to find event dates in specific containers
        # Look for date/time patterns in the page
        date_containers = soup.find_all(['div', 'article', 'section'], 
                                       class_=re.compile(r'event|termin|date|calendar|spielplan', re.I))
        
        for container in date_containers:
            try:
                container_text = container.get_text()
                # Check if this container is related to Sankt Falstaff
                if re.search(r'falstaff|sankt', container_text, re.I):
                    events.extend(extract_dates_from_text(container_text, ticket_url))
            except Exception as e:
                print(f"Error parsing container: {e}")
                continue
        
        # Theater Bonn specific: look for date cards/items in a grid
        # The dates might be in a list structure with specific classes
        date_items = soup.find_all(['div', 'li', 'article'], 
                                   class_=re.compile(r'date|item|card|event-list', re.I))
        
        for item in date_items:
            try:
                item_text = item.get_text()
                # Extract dates from these items
                events.extend(extract_dates_from_text(item_text, ticket_url))
            except Exception as e:
                continue
        
        # Theater Bonn specific: Look for "Termine und Karten" section
        termine_section = soup.find(['section', 'div'], id=re.compile(r'dates|termine', re.I))
        if not termine_section:
            # Try by heading
            termine_heading = soup.find(['h2', 'h3'], string=re.compile(r'termine.*karten', re.I))
            if termine_heading:
                termine_section = termine_heading.find_parent(['section', 'div'])
        
        if termine_section:
            # Extract dates only from the termine section
            section_text = termine_section.get_text()
            events.extend(extract_dates_from_text(section_text, ticket_url))
        
        # If no events found with structured approach, try text-based extraction
        if not events:
            page_text = soup.get_text()
            falstaff_events = extract_falstaff_dates_from_page(page_text, ticket_url)
            events.extend(falstaff_events)
        
        # Additional strategy: look for links with "karten" (tickets) text
        ticket_links = soup.find_all('a', href=re.compile(r'karten|ticket', re.I))
        for link in ticket_links:
            try:
                # Check context around the link
                parent = link.parent
                if parent:
                    context = parent.get_text()
                    if re.search(r'falstaff', context, re.I):
                        events.extend(extract_dates_from_text(context, ticket_url))
            except Exception as e:
                continue
        
    except Exception as e:
        print(f"Error scraping Theater Bonn: {e}")
    
    return clean_and_sort_events(events), director, duration, author

def extract_falstaff_dates_from_page(page_text, base_url):
    """Specifically look for Sankt Falstaff dates in page text"""
    events = []
    
    lines = page_text.split('\n')
    
    for i, line in enumerate(lines):
        # If line mentions "Falstaff" or "Sankt Falstaff", look for dates in surrounding lines
        if re.search(r'falstaff|sankt\s+falstaff', line, re.I):
            # Check current line and next few lines for dates
            search_text = ' '.join(lines[max(0, i-2):i+5])
            events.extend(extract_dates_from_text(search_text, base_url))
    
    return events

def scrape_dhaus_krieg_und_frieden():
    """Scrape Krieg und Frieden dates from Düsseldorfer Schauspielhaus"""
    events = []
    director = None
    duration = None
    author = None
    
    url = "https://www.dhaus.de/programm/a-z/krieg-und-frieden/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache'
        }
        
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text(separator=' ')
        
        # Extract director, duration, and author
        director = extract_director(page_text)
        duration = extract_duration(page_text)
        author = extract_author(page_text)
        
        # Manually scan for D'Haus format: "Mi, 18.02. / 16:00 – 21:00"
        # Since year is missing, we must infer it (starts 2026)
        
        page_text_norm = re.sub(r'\s+', ' ', page_text)
        
        # Pattern: DayName, DD.MM. / HH:MM
        # Example: Mi, 18.02. / 16:00
        pattern = r'[a-zA-Z]{2},\s*(\d{1,2})\.(\d{1,2})\.\s*/\s*(\d{1,2})[:\.](\d{2})'
        
        current_year = 2026 # Premiere is Feb 2026
        
        for match in re.finditer(pattern, page_text_norm):
            try:
                day, month, hour, minute = match.groups()
                
                # Logic for year transition: if month is suddenly much smaller than prev, increment year?
                # But here we are mostly in 2026. If we see Dec/Nov, it might be 2025?
                # Given Premiere is Feb 2026, let's assume 2026 for now.
                # If we were running this in late 2025, Jan/Feb would be next year.
                
                # Dynamic year detection
                # If current month (real time) is > 6 and event month < 6, add 1 to current year
                # But here we know it starts 2026.
                
                # Let's use a safe logic: if date < now, add 1 year
                # But we are in Jan 2026 (simulated).
                
                # Assume 2026 for detected dates as a baseline
                year = 2026
                
                datetime_str = f"{year}-{month.zfill(2)}-{day.zfill(2)} {hour.zfill(2)}:{minute.zfill(2)}"
                
                event_date = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                
                # If we parsed a date in the past (e.g. jan 2026 when it is feb 2026), ignore or adjust?
                # Just filter out past dates
                if event_date > datetime.now():
                    events.append({
                        "date": datetime_str,
                        "display_date": f"{day.zfill(2)}.{month.zfill(2)}.{year}",
                        "display_time": f"{hour.zfill(2)}:{minute.zfill(2)}",
                        "ticket_url": url
                    })
                    print(f"Found Krieg und Frieden date: {day}.{month}.{year} {hour}:{minute}")
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Error scraping D'haus: {e}")
        
    return clean_and_sort_events(events), director, duration, author

def main():
    """Main scraping function"""
    try:
        # Get data with directors, duration, and authors
        dumme_jahre_events, dumme_jahre_director, dumme_jahre_duration = scrape_dnt_weimar_dumme_jahre()
        sankt_falstaff_events, sankt_falstaff_director, sankt_falstaff_duration, sankt_falstaff_author = scrape_theater_bonn()
        komet_events, komet_director, komet_duration, komet_author = scrape_staatsschauspiel_dresden()
        undine_events, undine_director, undine_duration, undine_author = scrape_oper_leipzig()
        krieg_frieden_events, krieg_frieden_director, krieg_frieden_duration, krieg_frieden_author = scrape_dhaus_krieg_und_frieden()
        
        shows_data = {
            "last_updated": datetime.now().isoformat(),
            "shows": {
                "dumme-jahre": {
                    "title": "Dumme Jahre",
                    "theater": "Deutsches Nationaltheater Weimar",
                    "director": dumme_jahre_director,
                    "duration": dumme_jahre_duration,
                    "image": "images/dumme-jahre.jpg",
                    "base_url": "https://www.dnt-weimar.de/de/programm/stueck-detail.php?SID=3520#event-tickets",
                    "events": dumme_jahre_events
                },
                "sankt-falstaff": {
                    "title": "Sankt Falstaff",
                    "theater": "Theater Bonn",
                    "director": sankt_falstaff_director,
                    "author": sankt_falstaff_author,
                    "duration": sankt_falstaff_duration,
                    "image": "images/sankt-falstaff.jpg",
                    "base_url": "https://www.theater-bonn.de/de/programm/sankt-falstaff/221198#dates-and-tickets",
                    "events": sankt_falstaff_events
                },
                "der-komet": {
                    "title": "Der Komet",
                    "theater": "Staatsschauspiel Dresden",
                    "director": komet_director,
                    "author": komet_author,
                    "duration": komet_duration,
                    "image": "images/der-komet.jpg",
                    "base_url": "https://tickets.staatsschauspiel-dresden.de/webshop/webticket/eventlist?production=709",
                    "events": komet_events
                },
                "undine": {
                    "title": "Undine",
                    "theater": "Oper Leipzig",
                    "director": undine_director,
                    "author": undine_author,
                    "duration": undine_duration,
                    "image": "images/undine.jpg",
                    "base_url": "https://www.oper-leipzig.de/de/ensemble/person/susanne-uhl/1902",
                    "events": undine_events
                },
                "krieg-und-frieden": {
                    "title": "Krieg und Frieden",
                    "theater": "Düsseldorfer Schauspielhaus",
                    "director": krieg_frieden_director,
                    "author": krieg_frieden_author,
                    "duration": krieg_frieden_duration,
                    "image": "images/thumbs/krieg-und-frieden.jpg",
                    "base_url": "https://www.dhaus.de/programm/a-z/krieg-und-frieden/",
                    "events": krieg_frieden_events
                }
            }
        }
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Save to JSON file
        with open('data/shows.json', 'w', encoding='utf-8') as f:
            json.dump(shows_data, f, ensure_ascii=False, indent=2)
        
        print(f"Scraping completed successfully. Found shows:")
        for show_id, show_data in shows_data['shows'].items():
            event_count = len(show_data['events'])
            director_info = f" (Regie: {show_data['director']})" if show_data['director'] else ""
            print(f"  {show_data['title']}{director_info}: {event_count} upcoming events")
            
    except Exception as e:
        print(f"Error in main function: {e}")
        # Create a minimal fallback JSON to prevent complete failure
        fallback_data = {
            "last_updated": datetime.now().isoformat(),
            "shows": {
                "sankt-falstaff": {
                    "title": "Sankt Falstaff",
                    "theater": "Theater Bonn",
                    "director": None,
                    "author": None,
                    "duration": None,
                    "image": "images/sankt-falstaff.jpg",
                    "base_url": "https://www.theater-bonn.de/de/programm/sankt-falstaff/221198#dates-and-tickets",
                    "events": []
                },
                "der-komet": {
                    "title": "Der Komet",
                    "theater": "Staatsschauspiel Dresden",
                    "director": None,
                    "author": None,
                    "duration": None,
                    "image": "images/der-komet.jpg",
                    "base_url": "https://tickets.staatsschauspiel-dresden.de/webshop/webticket/eventlist?production=709",
                    "events": []
                },
                "undine": {
                    "title": "Undine",
                    "theater": "Oper Leipzig",
                    "director": None,
                    "author": None,
                    "duration": None,
                    "image": "images/undine.jpg",
                    "base_url": "https://www.oper-leipzig.de/de/ensemble/person/susanne-uhl/1902",
                    "events": []
                },
                "krieg-und-frieden": {
                    "title": "Krieg und Frieden",
                    "theater": "Düsseldorfer Schauspielhaus",
                    "director": None,
                    "author": None,
                    "duration": None,
                    "image": "images/thumbs/krieg-und-frieden.jpg",
                    "base_url": "https://www.dhaus.de/programm/a-z/krieg-und-frieden/",
                    "events": []
                }
            }
        }
        
        os.makedirs('data', exist_ok=True)
        with open('data/shows.json', 'w', encoding='utf-8') as f:
            json.dump(fallback_data, f, ensure_ascii=False, indent=2)
        print("Created fallback JSON due to error")

if __name__ == "__main__":
    main()
