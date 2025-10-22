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

def scrape_staatsschauspiel_dresden():
    """Scrape Der Komet dates from Staatsschauspiel Dresden"""
    events = []
    
    # Try multiple URLs for Dresden
    urls = [
        "https://www.staatsschauspiel-dresden.de/spielplan/a-z/der-komet/",
        "https://tickets.staatsschauspiel-dresden.de/webshop/webticket/eventlist?production=709",
        "https://www.staatsschauspiel-dresden.de/spielplan/"
    ]
    
    for url in urls:
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
                                if parent_element:
                                    # Look for "Der Komet" in the surrounding context
                                    context_text = ""
                                    for i in range(5):  # Check up to 5 levels up
                                        if parent_element:
                                            context_text += parent_element.get_text() + " "
                                            parent_element = parent_element.parent
                                    
                                    # Only include if "Der Komet" is mentioned in context
                                    if re.search(r'der\s+komet|komet', context_text, re.I):
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
    
    return clean_and_sort_events(events)

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
        # DD. MMM without year (e.g., 17. Okt, 19. Nov)
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
        matches = re.findall(pattern, normalized_text)
        for match in matches:
            try:
                if len(match) == 5:  # With time
                    day, month, year, hour, minute = match
                    datetime_str = f"{year}-{month.zfill(2)}-{day.zfill(2)} {hour.zfill(2)}:{minute.zfill(2)}"
                    time_display = f"{hour}:{minute}"
                elif len(match) == 3 and match[1].isalpha():  # Month name with year
                    day, month_name, year = match
                    month = month_map.get(month_name, '01')
                    datetime_str = f"{year}-{month}-{day.zfill(2)} 19:30"
                    time_display = "19:30"
                elif len(match) == 2 and match[1].isalpha():  # Month name without year (e.g., "17. Okt")
                    day, month_name = match
                    month = month_map.get(month_name, '01')
                    # Assume current year or next year if date has passed
                    current_year = datetime.now().year
                    datetime_str = f"{current_year}-{month}-{day.zfill(2)} 19:30"
                    test_date = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                    if test_date < datetime.now():
                        # If date has passed, use next year
                        datetime_str = f"{current_year + 1}-{month}-{day.zfill(2)} 19:30"
                    year = datetime.strptime(datetime_str.split()[0], "%Y-%m-%d").year
                    time_display = "19:30"
                else:  # Without time (DD.MM.YYYY)
                    day, month, year = match[:3]
                    datetime_str = f"{year}-{month.zfill(2)}-{day.zfill(2)} 19:30"
                    time_display = "19:30"
                
                # Only future dates
                event_date = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                if event_date > datetime.now():
                    events.append({
                        "date": datetime_str,
                        "display_date": f"{day.zfill(2)}.{month.zfill(2) if isinstance(month, str) and month.isdigit() else month_map.get(month_name if 'month_name' in locals() else match[1], '01')}.{year}",
                        "display_time": time_display,
                        "ticket_url": base_url
                    })
            except Exception as e:
                continue
    
    return events

def extract_dates_from_element(element, base_url):
    """Extract dates from HTML elements"""
    return extract_dates_from_text(element.get_text(), base_url)

def clean_and_sort_events(events):
    """Remove duplicates and sort events"""
    unique_events = []
    seen_dates = set()
    
    for event in sorted(events, key=lambda x: x['date']):
        if event['date'] not in seen_dates:
            unique_events.append(event)
            seen_dates.add(event['date'])
    
    return unique_events[:20]


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
    match = re.search(r'(\d{1,2})[\.:](\d{2})', text)
    if not match:
        return "19:30"

    hour, minute = match.groups()
    return f"{hour.zfill(2)}:{minute.zfill(2)}"


def scrape_dnt_weimar_dumme_jahre():
    """Scrape Dumme Jahre dates from DNT Weimar"""
    events = []

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

    return clean_and_sort_events(events)

def scrape_oper_leipzig():
    """Scrape Undine dates from Oper Leipzig"""
    events = []
    
    url = "https://www.oper-leipzig.de/de/ensemble/person/susanne-uhl/1902"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache'
        }
        
        # Add random delay
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()
        
        # Look for Undine specifically in the full page text
        undine_events = extract_undine_dates_from_page(page_text, url)
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
                    events.extend(extract_dates_from_element(element, url))
            except Exception as e:
                print(f"Strategy failed for Oper Leipzig: {e}")
                continue
        
    except Exception as e:
        print(f"Error scraping Oper Leipzig: {e}")
    
    return clean_and_sort_events(events)

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
    
    return clean_and_sort_events(events)

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

def main():
    """Main scraping function"""
    try:
        shows_data = {
            "last_updated": datetime.now().isoformat(),
            "shows": {
                "dumme-jahre": {
                    "title": "Dumme Jahre",
                    "theater": "Deutsches Nationaltheater Weimar",
                    "image": "images/dumme-jahre.jpg",
                    "base_url": "https://www.dnt-weimar.de/de/programm/stueck-detail.php?SID=3520#event-tickets",
                    "events": scrape_dnt_weimar_dumme_jahre()
                },
                "sankt-falstaff": {
                    "title": "Sankt Falstaff",
                    "theater": "Theater Bonn",
                    "image": "images/sankt-falstaff.jpg",
                    "base_url": "https://www.theater-bonn.de/de/programm/sankt-falstaff/221198#dates-and-tickets",
                    "events": scrape_theater_bonn()
                },
                "der-komet": {
                    "title": "Der Komet",
                    "theater": "Staatsschauspiel Dresden",
                    "image": "images/der-komet.jpg",
                    "base_url": "https://tickets.staatsschauspiel-dresden.de/webshop/webticket/eventlist?production=709",
                    "events": scrape_staatsschauspiel_dresden()
                },
                "undine": {
                    "title": "Undine",
                    "theater": "Oper Leipzig",
                    "image": "images/undine.jpg",
                    "base_url": "https://www.oper-leipzig.de/de/ensemble/person/susanne-uhl/1902",
                    "events": scrape_oper_leipzig()
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
            print(f"  {show_data['title']}: {event_count} upcoming events")
            
    except Exception as e:
        print(f"Error in main function: {e}")
        # Create a minimal fallback JSON to prevent complete failure
        fallback_data = {
            "last_updated": datetime.now().isoformat(),
            "shows": {
                "sankt-falstaff": {
                    "title": "Sankt Falstaff",
                    "theater": "Theater Bonn",
                    "image": "images/sankt-falstaff.jpg",
                    "base_url": "https://www.theater-bonn.de/de/programm/sankt-falstaff/221198#dates-and-tickets",
                    "events": []
                },
                "der-komet": {
                    "title": "Der Komet",
                    "theater": "Staatsschauspiel Dresden",
                    "image": "images/der-komet.jpg",
                    "base_url": "https://tickets.staatsschauspiel-dresden.de/webshop/webticket/eventlist?production=709",
                    "events": []
                },
                "undine": {
                    "title": "Undine",
                    "theater": "Oper Leipzig",
                    "image": "images/undine.jpg",
                    "base_url": "https://www.oper-leipzig.de/de/ensemble/person/susanne-uhl/1902",
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
