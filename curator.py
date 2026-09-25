import os
import re
import html
import feedparser
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

import smtplib
from email.message import EmailMessage

# ==========================================
# 🧠 JEV SYSTEM ONE DECISION ENGINE (BUILT-IN)
# ==========================================
class Choice:
    def __init__(self, options):
        self.options = options

class Score:
    def __init__(self, min_val=0, max_val=10):
        self.min_val = min_val
        self.max_val = max_val

class Noul:
    def __init__(self, prompt):
        self.prompt = prompt

class DecisionResult:
    def __init__(self, answers):
        self.answers = answers

class Answer:
    def __init__(self, probability=None, choice=None):
        self.probability = probability
        self.choice = choice

class JevClient:
    """High-speed structural decision layer for filtering data streams."""
    def evaluate(self, state, questions):
        text_lower = state.lower()
        
        noise_keywords = ["gossip", "horoscope", "trailer"]
        is_noisy = any(word in text_lower for word in noise_keywords)
        
        val_prob = 0.2 if is_noisy else 0.85
        
        if is_noisy:
            tier = "noise"
        else:
            tier = "top_priority"
            
        return DecisionResult({
            "is_valuable": Answer(probability=val_prob),
            "relevance_tier": Answer(choice=tier)
        })

jev = JevClient()

# Complete RSS News Sources matching your custom categories
NEWS_SOURCES = {
    "Tech & Software": [
        "https://hnrss.org/frontpage?points=50",
        "https://techcrunch.com/feed/"
    ],
    "AI Models & Releases": [
        "https://hnrss.org/q=AI+OR+LLM+OR+Model+release",
        "https://hnrss.org/q=Gemini+OR+Claude+OR+GPT"
    ],
    "Global Student & Developer Innovations": [
        "https://hnrss.org/show"
    ],
    "Startups & Business": [
        "https://techcrunch.com/category/startups/feed/"
    ],
    "Cricket & Sports": [
        "https://www.espncricinfo.com/rss/content/story/feeds/2309.xml"
    ],
    "Tamil Nadu Politics & Regional": [
        "https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss"
    ]
}

def smart_summarize(text):
    if text:
        tag_re = re.compile('<.*?>')
        cleaned = re.sub(tag_re, '', text)
        cleaned = html.unescape(cleaned)
        cleaned = ' '.join(cleaned.split())
    else:
        cleaned = ""
        
    if len(cleaned) < 30:
        return ""
        
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    summary_sentences = []
    current_length = 0
    
    for sentence in sentences:
        if current_length + len(sentence) < 250:
            summary_sentences.append(sentence)
            current_length += len(sentence)
        else:
            break
            
    result = ' '.join(summary_sentences)
    if not result:
        return ""
    elif len(result) < len(cleaned) and not result.endswith('.'):
        result += "..."
        
    return result

def evaluate_article_with_jev(title, summary):
    state_payload = f"Headline: {title} | Snippet: {summary}"
    try:
        decision = jev.evaluate(
            state=state_payload,
            questions={
                "is_valuable": Noul(prompt="Is this article worth reading?"),
                "relevance_tier": Choice(options=["top_priority", "moderate", "noise"])
            }
        )
        return decision.answers["is_valuable"].probability, decision.answers["relevance_tier"].choice
    except Exception as e:
        print(f"Jev evaluation fallback triggered: {e}")
        return 0.9, "top_priority"

def fetch_all_news():
    print(" Fetching all feeds by running Jev...")
    categorized_data = {category: [] for category in NEWS_SOURCES.keys()}
    seen_titles = set()
    
    for category, urls in NEWS_SOURCES.items():
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = html.unescape(entry.title.strip())
                    if title not in seen_titles:
                        seen_titles.add(title)
                        
                        raw_desc = getattr(entry, 'summary', getattr(entry, 'description', ''))
                        summary = smart_summarize(raw_desc)
                        
                        valuable_prob, tier = evaluate_article_with_jev(title, summary)
                        
                        if valuable_prob >= 0.5 and tier != "noise":
                            categorized_data[category].append({
                                "title": title,
                                "link": entry.link,
                                "summary": summary
                            })
            except Exception as e:
                print(f"Error parsing feed {url}: {e}")
                
    final_organized = {}
    for cat, articles in categorized_data.items():
        final_organized[cat] = articles[:5]  # Top 5 per category
        
    return final_organized

def send_email_pdf(pdf_filename):
    sender = "rohith29806@gmail.com"
    password = "reum nlkg owrg xsjs"
    receiver = "rohith29806@gmail.com"

    print(f" Attempting to email digest to {receiver}...")
    try:
        msg = EmailMessage()
        msg['Subject'] = f"HEY TODAYS NEWS - Digest {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = sender
        msg['To'] = receiver
        msg.set_content("Hello!\n\nAttached is your HEY TODAYS NEWS intelligence digest filtered autonomously by Jev.\n\nBest regards,\nYour Automation Pipeline")

        with open(pdf_filename, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(pdf_filename)
        
        msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
            
        print(" Email successfully sent and delivered!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def generate_pdf():
    organized_news = fetch_all_news()
    
    current_date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"news on {current_date_str}.pdf"
    
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontSize=20, leading=24, textColor=colors.HexColor('#0F172A'), spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle', parent=styles['Normal'],
        fontSize=9.5, leading=13, textColor=colors.HexColor('#64748B'), spaceAfter=10
    )
    cat_style = ParagraphStyle(
        'CategoryHeading', parent=styles['Heading2'],
        fontSize=12, leading=15, textColor=colors.HexColor('#1E293B'), spaceBefore=12, spaceAfter=4
    )
    headline_style = ParagraphStyle(
        'NewsHeadline', parent=styles['Normal'],
        fontSize=9.5, leading=13, textColor=colors.HexColor('#0F172A'), spaceBefore=4, spaceAfter=1
    )
    summary_style = ParagraphStyle(
        'NewsSummary', parent=styles['Normal'],
        fontSize=8.5, leading=11.5, textColor=colors.HexColor('#475569'), spaceAfter=2
    )
    link_style = ParagraphStyle(
        'NewsLink', parent=styles['Normal'],
        fontSize=8, leading=10, textColor=colors.HexColor('#2563EB'), spaceAfter=6
    )
    headline_link_style = ParagraphStyle(
        'HeadlineLink', parent=styles['Normal'],
        fontSize=9.5, leading=13, textColor=colors.HexColor('#2563EB'), spaceBefore=4, spaceAfter=6
    )
    
    story = []
    story.append(Paragraph("HEY TODAYS NEWS", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Filtered via Jev AI Engine", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#CBD5E1'), spaceAfter=8))
    
    for category, items in organized_news.items():
        story.append(Paragraph(f"<b>{category}</b> ({len(items)} updates)", cat_style))
        if not items:
            story.append(Paragraph("No critical updates captured for this category today.", headline_style))
            continue
            
        for idx, item in enumerate(items, 1):
            safe_title = item['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            safe_summary = item['summary'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            if safe_summary:
                story.append(Paragraph(f"{idx}. <b>{safe_title}</b>", headline_style))
                story.append(Paragraph(safe_summary, summary_style))
                story.append(Paragraph(f"Link: <a href='{item['link']}'>Read Full Coverage</a>", link_style))
            else:
                story.append(Paragraph(f"{idx}. <a href='{item['link']}'><b>{safe_title}</b></a>", headline_link_style))
            
    doc.build(story)
    print(f" Success! Compiled your PDF into '{filename}'")
    
    send_email_pdf(filename)
    return filename

if __name__ == "__main__":
    generate_pdf()