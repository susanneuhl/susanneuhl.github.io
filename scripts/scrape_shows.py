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

def scrape_staatsschauspiel_dresden():
    """Scrape Der Komet dates from Staatsschauspiel Dresden"""
    # Try multiple URLs for Dresden
    urls = [
        "https://www.staatsschauspiel-dresden.de/spielplan/a-z/der-komet/",
        "https://tickets.staatsschauspiel-dresden.de/webshop/webticket/eventlist?production=709",
        "https://www.staatsschauspiel-dresden.de/spielplan/"
    ]
    
    events = []
    
    for url in urls:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
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
                except:
                    continue
                    
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            continue
    
    # Manual fallback with known dates (you can add more as they become available)
    if not events:
        # Add known dates - these should be updated manually until scraping works
        known_events = [
            {
                "date": "2025-09-20 19:30",
                "display_date": "20.09.2025",
                "display_time": "19:30",
                "ticket_url": "https://www.staatsschauspiel-dresden.de/spielplan/a-z/der-komet/"
            },
            {
                "date": "2025-10-02 19:30",
                "display_date": "02.10.2025",
                "display_time": "19:30",
                "ticket_url": "https://www.staatsschauspiel-dresden.de/spielplan/a-z/der-komet/"
            }
            # Add more known dates here as they're announced
        ]
        events.extend(known_events)
    
    # Clean and return events
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
    
    # Enhanced date patterns for German
    patterns = [
        # DD.MM.YYYY with time
        r'(\d{1,2})\.(\d{1,2})\.(\d{4}).*?(\d{1,2})[:\.](\d{2})',
        # DD.MM.YYYY without time  
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
        # DD. MMM YYYY (e.g., 20. September 2025)
        r'(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*(\d{4})',
    ]
    
    month_map = {
        'Januar': '01', 'Februar': '02', 'März': '03', 'April': '04',
        'Mai': '05', 'Juni': '06', 'Juli': '07', 'August': '08',
        'September': '09', 'Oktober': '10', 'November': '11', 'Dezember': '12'
    }
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                if len(match) == 5:  # With time
                    day, month, year, hour, minute = match
                    datetime_str = f"{year}-{month.zfill(2)}-{day.zfill(2)} {hour.zfill(2)}:{minute.zfill(2)}"
                    time_display = f"{hour}:{minute}"
                elif len(match) == 3 and match[1].isalpha():  # Month name
                    day, month_name, year = match
                    month = month_map.get(month_name, '01')
                    datetime_str = f"{year}-{month}-{day.zfill(2)} 19:30"
                    time_display = "19:30"
                else:  # Without time
                    day, month, year = match[:3]
                    datetime_str = f"{year}-{month.zfill(2)}-{day.zfill(2)} 19:30"
                    time_display = "19:30"
                
                # Only future dates
                event_date = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                if event_date > datetime.now():
                    events.append({
                        "date": datetime_str,
                        "display_date": f"{day.zfill(2)}.{month.zfill(2) if month.isdigit() else month_map.get(match[1], '01')}.{year}",
                        "display_time": time_display,
                        "ticket_url": base_url
                    })
            except:
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
    
    return unique_events[:10]

def scrape_staatstheater_braunschweig():
    """Scrape La traviata dates from Staatstheater Braunschweig"""
    url = "https://staatstheater-braunschweig.de/produktion/la-traviata-8542"
    
    events = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()
        
        # Look for La traviata specifically in the full page text
        traviata_events = extract_traviata_dates_from_page(page_text, url)
        events.extend(traviata_events)
        
    except Exception as e:
        print(f"Error scraping Staatstheater Braunschweig: {e}")
    
    # Manual fallback with known dates from the website
    if not events:
        known_events = [
            {"date": "2025-08-26 19:30", "display_date": "26.08.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-08-27 19:30", "display_date": "27.08.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-08-28 19:30", "display_date": "28.08.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-08-29 19:30", "display_date": "29.08.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-08-30 19:30", "display_date": "30.08.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-08-31 14:30", "display_date": "31.08.2025", "display_time": "14:30", "ticket_url": url},
            {"date": "2025-08-31 19:30", "display_date": "31.08.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-09-02 19:30", "display_date": "02.09.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-09-03 19:30", "display_date": "03.09.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-09-04 19:30", "display_date": "04.09.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-09-05 19:30", "display_date": "05.09.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-09-06 19:30", "display_date": "06.09.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-09-07 19:30", "display_date": "07.09.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-09-09 19:30", "display_date": "09.09.2025", "display_time": "19:30", "ticket_url": url},
            {"date": "2025-09-10 19:30", "display_date": "10.09.2025", "display_time": "19:30", "ticket_url": url}
        ]
        events.extend(known_events)
    
    return clean_and_sort_events(events)

def extract_traviata_dates_from_page(page_text, base_url):
    """Specifically look for La traviata dates in page text"""
    events = []
    
    lines = page_text.split('\n')
    
    for i, line in enumerate(lines):
        if re.search(r'la\s+traviata|traviata', line, re.I):
            search_text = ' '.join(lines[max(0, i-2):i+5])
            events.extend(extract_dates_from_text(search_text, base_url))
    
    return events

def main():
    """Main scraping function"""
    shows_data = {
        "last_updated": datetime.now().isoformat(),
        "shows": {
            "la-traviata": {
                "title": "La traviata",
                "theater": "Staatstheater Braunschweig (Burgplatz Open Air)",
                "image": "images/la-traviata.jpg",
                "base_url": "https://staatstheater-braunschweig.de/produktion/la-traviata-8542",
                "events": scrape_staatstheater_braunschweig()
            },
            "der-komet": {
                "title": "Der Komet",
                "theater": "Staatsschauspiel Dresden",
                "image": "images/der-komet.jpg",
                "base_url": "https://tickets.staatsschauspiel-dresden.de/webshop/webticket/eventlist?production=709",
                "events": scrape_staatsschauspiel_dresden()
            }
        }
    }
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save to JSON file
    with open('data/shows.json', 'w', encoding='utf-8') as f:
        json.dump(shows_data, f, ensure_ascii=False, indent=2)
    
    print(f"Scraping completed. Found shows:")
    for show_id, show_data in shows_data['shows'].items():
        event_count = len(show_data['events'])
        print(f"  {show_data['title']}: {event_count} upcoming events")

if __name__ == "__main__":
    main()
