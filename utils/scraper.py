import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from urllib.parse import urlparse

def scrape_website(url, output_file=None, delay=1):
    """
    Scrape a website for FAQ or support data
    
    Args:
        url (str): URL of the website to scrape
        output_file (str, optional): Path to save the scraped data as JSON
        delay (int, optional): Delay between requests in seconds
        
    Returns:
        list: List of dictionaries containing scraped data
    """
    try:
        # Get domain name for logging
        domain = urlparse(url).netloc
        print(f"Scraping {domain}...")
        
        # Send HTTP request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find FAQ sections (this is a basic implementation and may need customization per site)
        # Try common FAQ patterns
        faq_data = []
        
        # Pattern 1: Look for FAQ sections with dt/dd elements
        faq_sections = soup.find_all(['dt', 'h3', 'h4'], class_=['faq-question', 'question', 'faq-title'])
        
        for section in faq_sections:
            question = section.get_text().strip()
            # Try to find the answer in the next sibling
            answer_tag = section.find_next(['dd', 'div', 'p'], class_=['faq-answer', 'answer'])
            
            if answer_tag:
                answer = answer_tag.get_text().strip()
                faq_data.append({
                    'question': question,
                    'answer': answer,
                    'source': url
                })
        
        # Pattern 2: Look for FAQ sections with specific classes
        faq_items = soup.find_all('div', class_=['faq-item', 'question-answer', 'faq-qa'])
        
        for item in faq_items:
            question_tag = item.find(['h3', 'h4', 'div', 'strong'], class_=['question', 'faq-question'])
            answer_tag = item.find(['div', 'p'], class_=['answer', 'faq-answer'])
            
            if question_tag and answer_tag:
                question = question_tag.get_text().strip()
                answer = answer_tag.get_text().strip()
                faq_data.append({
                    'question': question,
                    'answer': answer,
                    'source': url
                })
        
        # Pattern 3: Look for accordion-style FAQs (common in ecommerce sites)
        accordion_items = soup.find_all(['div', 'section', 'article'], class_=['accordion', 'accordion-item', 'faq-accordion'])
        
        for item in accordion_items:
            question_tag = item.find(['button', 'h3', 'h4', 'div', 'a'], 
                                    class_=['accordion-button', 'accordion-header', 'accordion-title'])
            answer_tag = item.find(['div', 'section'], 
                                  class_=['accordion-content', 'accordion-body', 'accordion-panel'])
            
            if question_tag and answer_tag:
                question = question_tag.get_text().strip()
                answer = answer_tag.get_text().strip()
                faq_data.append({
                    'question': question,
                    'answer': answer,
                    'source': url
                })
        
        # Pattern 4: Generic pattern looking for common FAQ headers followed by content
        headers = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'FAQ|Frequently Asked Questions|Common Questions', re.I))
        
        for header in headers:
            # Find all question-like elements after this header
            next_header = header.find_next(['h2', 'h3', 'h4'])
            questions = header.find_next_siblings(['h5', 'h6', 'strong', 'b', 'p'], limit=20)
            
            for q_tag in questions:
                # Check if we've reached the next section header
                if next_header and q_tag.find_previous(['h2', 'h3', 'h4']) != header:
                    break
                    
                # Look for question-like text
                if re.search(r'\?$', q_tag.get_text().strip()):
                    question = q_tag.get_text().strip()
                    # Look for answer in the next paragraphs
                    answer_tags = []
                    next_element = q_tag.find_next(['p'])
                    
                    # Collect answer paragraphs until we hit another question or heading
                    while next_element and not re.search(r'\?$', next_element.get_text().strip()) and next_element.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        answer_tags.append(next_element.get_text().strip())
                        next_element = next_element.find_next(['p'])
                    
                    if answer_tags:
                        answer = ' '.join(answer_tags)
                        faq_data.append({
                            'question': question,
                            'answer': answer,
                            'source': url
                        })
        
        # Pattern 5: E-commerce specific patterns
        # Shopify-specific pattern
        if 'shopify.com' in url:
            faq_sections = soup.find_all(['section', 'div'], class_=['faq', 'faqs'])
            for section in faq_sections:
                questions = section.find_all(['h4', 'h5', 'strong'])
                for q in questions:
                    question = q.get_text().strip()
                    # Find answer in next sibling paragraph
                    answer_p = q.find_next('p')
                    if answer_p:
                        answer = answer_p.get_text().strip()
                        faq_data.append({
                            'question': question,
                            'answer': answer,
                            'source': url
                        })
        
        # Final faq count
        print(f"Scraped {len(faq_data)} FAQ items from {domain}")
        
        # Clean and dedup data
        clean_data = []
        seen_questions = set()
        
        for item in faq_data:
            # Clean question and answer
            question = re.sub(r'\s+', ' ', item['question']).strip()
            answer = re.sub(r'\s+', ' ', item['answer']).strip()
            
            # Skip too short or too long content
            if len(question) < 10 or len(answer) < 20 or len(question) > 500 or len(answer) > 2000:
                continue
                
            # Deduplicate based on question
            if question.lower() not in seen_questions:
                seen_questions.add(question.lower())
                clean_data.append({
                    'question': question,
                    'answer': answer,
                    'source': url
                })
        
        print(f"After cleaning: {len(clean_data)} FAQ items")
        
        # Save to file if specified
        if output_file and clean_data:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(clean_data, f, indent=2)
            print(f"Saved scraped data to {output_file}")
        
        return clean_data
    
    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return []

def scrape_multiple_urls(urls, output_dir="data/scraped", delay=2):
    """
    Scrape multiple URLs and save the data to separate JSON files
    
    Args:
        urls (list): List of URLs to scrape
        output_dir (str, optional): Directory to save the scraped data
        delay (int, optional): Delay between requests in seconds
        
    Returns:
        dict: Dictionary with URLs as keys and scraped data as values
    """
    all_data = {}
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for url in urls:
        # Generate output filename from URL
        domain = urlparse(url).netloc.replace('.', '_')
        path = urlparse(url).path.replace('/', '_').replace('.', '_')
        output_file = os.path.join(output_dir, f"{domain}{path}.json")
        
        # Scrape the URL
        scraped_data = scrape_website(url, output_file, delay)
        all_data[url] = scraped_data
        
        # Add delay between requests
        if delay > 0 and url != urls[-1]:  # Don't delay after the last URL
            print(f"Waiting {delay} seconds before next request...")
            time.sleep(delay)
    
    return all_data

if __name__ == "__main__":
    # Example usage
    test_urls = [
        "https://www.example.com/faq",
        "https://www.example.com/support"
    ]
    scrape_multiple_urls(test_urls) 