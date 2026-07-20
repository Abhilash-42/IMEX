import feedparser
import requests
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import re
from sqlalchemy.orm import Session

from database.models import Event, Port, Supplier
from database.session import SessionLocal
from services.open_meteo import get_weather_events

logger = logging.getLogger(__name__)

class RSSIngestionService:
    def __init__(self):
        self.feeds = [
            "http://feeds.reuters.com/reuters/topNews",
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "https://www.cnbc.com/id/10001147/device/rss/rss.html",
            "https://www.supplychainbrain.com/rss/topic/40-news",
        ]
        
        # Keywords for supply chain disruptions
        self.disruption_keywords = {
            "port": ["port closure", "port shutdown", "port strike", "congestion"],
            "weather": ["hurricane", "flood", "earthquake", "tsunami", "storm", "typhoon", "cyclone"],
            "geopolitical": ["sanctions", "embargo", "trade war", "tariff", "conflict"],
            "labor": ["strike", "walkout", "labor dispute", "union"],
            "supply": ["shortage", "disruption", "delay", "backlog", "bottleneck"]
        }
        
        # Port locations for mapping
        self.major_ports = {
            "Shanghai": {"country": "China", "lat": 31.2304, "lng": 121.4737},
            "Singapore": {"country": "Singapore", "lat": 1.3521, "lng": 103.8198},
            "Rotterdam": {"country": "Netherlands", "lat": 51.9244, "lng": 4.4777},
            "Antwerp": {"country": "Belgium", "lat": 51.2602, "lng": 4.4025},
            "Hong Kong": {"country": "China", "lat": 22.3193, "lng": 114.1694},
            "Los Angeles": {"country": "USA", "lat": 34.0522, "lng": -118.2437},
            "Long Beach": {"country": "USA", "lat": 33.7701, "lng": -118.1937},
            "Hamburg": {"country": "Germany", "lat": 53.5511, "lng": 9.9937},
            "Busan": {"country": "South Korea", "lat": 35.1796, "lng": 129.0756},
            "Qingdao": {"country": "China", "lat": 36.0671, "lng": 120.3826},
            "Guangzhou": {"country": "China", "lat": 23.1291, "lng": 113.2644},
            "Shenzhen": {"country": "China", "lat": 22.5431, "lng": 114.0579},
            "Tianjin": {"country": "China", "lat": 39.0842, "lng": 117.2007},
            "Osaka": {"country": "Japan", "lat": 34.6937, "lng": 135.5023},
            "Tokyo": {"country": "Japan", "lat": 35.6762, "lng": 139.6503},
        }
    
    def fetch_feed(self, feed_url: str) -> List[Dict]:
        """Fetch and parse RSS feed"""
        try:
            feed = feedparser.parse(feed_url)
            entries = []
            for entry in feed.entries[:20]:  # Limit to 20 latest entries
                entries.append({
                    "title": entry.get("title", ""),
                    "description": entry.get("summary", entry.get("description", "")),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", entry.get("date", "")),
                    "source": feed.feed.get("title", "Unknown")
                })
            return entries
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}")
            return []
    
    def detect_disruption(self, article: Dict) -> Optional[Dict]:
        """Detect supply chain disruption from article"""
        text = f"{article['title']} {article['description']}".lower()
        
        for category, keywords in self.disruption_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    # Extract location
                    location = self.extract_location(text)
                    
                    # Determine severity (0-100)
                    severity = self.calculate_severity(text, category)
                    
                    # Estimate duration
                    duration = self.estimate_duration(text)
                    
                    return {
                        "title": article["title"],
                        "description": article["description"],
                        "source": article["source"],
                        "source_url": article["link"],
                        "event_type": category,
                        "location": location,
                        "severity": severity,
                        "estimated_duration_days": duration,
                        "published": article["published"]
                    }
        return None
    
    def extract_location(self, text: str) -> str:
        """Extract location from text"""
        for port_name in self.major_ports.keys():
            if port_name.lower() in text:
                return port_name
        
        # Check for country names
        countries = ["China", "USA", "US", "United States", "Germany", "Japan", 
                    "South Korea", "UK", "United Kingdom", "France", "India"]
        for country in countries:
            if country.lower() in text:
                return country
        
        return "Unknown"
    
    def calculate_severity(self, text: str, category: str) -> float:
        """Calculate severity score 0-100"""
        severity = 50  # Base severity
        
        # Adjust based on keywords
        severe_keywords = ["major", "severe", "critical", "catastrophic", "emergency", "shutdown", "closure"]
        for keyword in severe_keywords:
            if keyword in text:
                severity += 15
        
        # Adjust based on category
        category_weights = {
            "port": 20,
            "weather": 15,
            "geopolitical": 25,
            "labor": 10,
            "supply": 10
        }
        severity += category_weights.get(category, 0)
        
        return min(100, severity)
    
    def estimate_duration(self, text: str) -> int:
        """Estimate disruption duration in days"""
        # Default duration
        duration = 7
        
        # Check for duration indicators
        day_patterns = [
            (r"(\d+)\s*day", 1),
            (r"(\d+)\s*week", 7),
            (r"(\d+)\s*month", 30),
            (r"(\d+)\s*hour", 1)
        ]
        
        for pattern, multiplier in day_patterns:
            match = re.search(pattern, text)
            if match:
                duration = int(match.group(1)) * multiplier
                break
        
        return duration
    
    def process_articles(self, db: Session) -> List[Event]:
        """Process all RSS feeds and create events"""
        events = []
        
        for feed_url in self.feeds:
            articles = self.fetch_feed(feed_url)
            for article in articles:
                disruption = self.detect_disruption(article)
                if disruption:
                    # Check if event already exists
                    existing = db.query(Event).filter(
                        Event.title == disruption["title"],
                        Event.source == disruption["source"]
                    ).first()
                    
                    if not existing:
                        # Create new event
                        event = Event(
                            title=disruption["title"],
                            description=disruption["description"],
                            event_type=disruption["event_type"],
                            severity=disruption["severity"],
                            location=disruption["location"],
                            start_date=datetime.now(),
                            estimated_duration_days=disruption["estimated_duration_days"],
                            source=disruption["source"],
                            source_url=disruption["source_url"]
                        )
                        
                        # Find matching port
                        if disruption["location"] in self.major_ports:
                            port_data = self.major_ports[disruption["location"]]
                            port = db.query(Port).filter(Port.name == disruption["location"]).first()
                            if port:
                                event.port_id = port.id
                        
                        db.add(event)
                        db.commit()
                        db.refresh(event)
                        events.append(event)
                        logger.info(f"New disruption detected: {event.title}")
        
        return events
    
    def ingest_weather_events(self, db: Session):
        """Ingest weather events from Open-Meteo"""
        weather_events = get_weather_events()
        
        for weather in weather_events:
            # Check if event already exists
            existing = db.query(Event).filter(
                Event.title == weather["title"],
                Event.source == "Open-Meteo"
            ).first()
            
            if not existing:
                # Find matching port
                port = None
                for port_name in self.major_ports.keys():
                    if port_name.lower() in weather["location"].lower():
                        port = db.query(Port).filter(Port.name == port_name).first()
                        break
                
                event = Event(
                    title=weather["title"],
                    description=weather["description"],
                    event_type="weather",
                    severity=weather["severity"],
                    location=weather["location"],
                    start_date=datetime.now(),
                    estimated_duration_days=weather["estimated_duration_days"],
                    source="Open-Meteo"
                )
                if port:
                    event.port_id = port.id
                
                db.add(event)
                db.commit()
                logger.info(f"New weather event detected: {event.title}")

# Singleton instance
rss_service = RSSIngestionService()