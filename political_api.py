import re
import xml.etree.ElementTree as ET
from datetime import datetime

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=Kenya+politics+Kenya&hl=en-KE&gl=KE&ceid=KE:en",
    "https://news.google.com/rss/search?q=Kenya+protests+strikes&hl=en-KE&gl=KE&ceid=KE:en",
]

UNREST_KEYWORDS = [
    "protest", "strike", "riot", "demonstration", "violence", "unrest",
    "curfew", "tension", "boycott", "barricade", "clash", "chaos",
    "disruption", "shutdown", "political crisis", "instability",
    "standoff", "rally", "march", "blockade", "lockdown",
]

STABLE_KEYWORDS = [
    "peace", "calm", "stable", "normal", "agreement", "dialogue",
    "talks", "resolution", "ceasefire", "truce",
]

ELECTION_KEYWORDS = [
    "election", "campaign", "voter", "poll", "ballot", "IEBC",
]


def _fetch_rss(url, timeout=10):
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = []
        for item in root.iter("item"):
            title = item.findtext("title", "")
            desc = item.findtext("description", "")
            pubdate = item.findtext("pubDate", "")
            items.append({"title": title, "description": desc, "date": pubdate})
        return items
    except Exception:
        return None

def _classify_headlines(items):
    if not items:
        return None, []

    unrest_score = 0
    stable_score = 0
    election_score = 0
    matched = []

    for item in items:
        text = (item["title"] + " " + item["description"]).lower()
        for kw in UNREST_KEYWORDS:
            if kw in text:
                unrest_score += 1
                matched.append(item["title"])
                break
        for kw in STABLE_KEYWORDS:
            if kw in text:
                stable_score += 1
                break
        for kw in ELECTION_KEYWORDS:
            if kw in text:
                election_score += 1
                break

    return (unrest_score, stable_score, election_score), matched


def get_political_status():
    now = datetime.now()
    month = now.month
    year = now.year

    all_items = []
    for feed in RSS_FEEDS:
        items = _fetch_rss(feed)
        if items:
            all_items.extend(items)

    if all_items:
        scores, matched = _classify_headlines(all_items)
        if scores:
            unrest_score, stable_score, election_score = scores
            total = unrest_score + stable_score + 1

            if unrest_score > stable_score and unrest_score >= 3:
                status = "unstable"
                if election_score > unrest_score / 2:
                    summary = "Election-related tensions reported. Exercise caution."
                else:
                    summary = "Political unrest detected. Travel may be affected."
            elif election_score >= 3:
                status = "uncertain"
                summary = "Election period. Fare hikes and route disruptions possible."
            elif stable_score > unrest_score * 2:
                status = "stable"
                summary = "Political climate appears calm. Travel conditions normal."
            else:
                status = "stable"
                summary = "No significant political disruptions detected."

            safety_map = {
                "stable": "Safe to travel. Normal conditions.",
                "uncertain": "Exercise caution. Monitor local news.",
                "unstable": "Avoid non-essential travel. Check routes before travelling.",
            }
            fare_map = {
                "stable": "Normal fare rates expected.",
                "uncertain": "Fare hikes possible due to political activity.",
                "unstable": "High probability of fare hikes. Plan for surcharges.",
            }

            return {
                "status": status,
                "summary": summary,
                "safety": safety_map[status],
                "fare_outlook": fare_map[status],
                "headlines": matched[:5],
                "source": "News analysis",
            }

    return _fallback_status(month, year)


def _fallback_status(month, year):
    if year % 5 == 2 and month >= 6:
        return {
            "status": "uncertain",
            "summary": "General election year. Political activity heightened.",
            "safety": "Exercise caution. Avoid large political gatherings.",
            "fare_outlook": "Fare hikes common during campaign and election periods.",
            "headlines": [],
            "source": "Seasonal pattern",
        }

    if month in [3, 7, 8, 12]:
        return {
            "status": "stable",
            "summary": "No major political disruptions reported.",
            "safety": "Safe to travel. Normal conditions.",
            "fare_outlook": "Normal fare rates expected.",
            "headlines": [],
            "source": "Seasonal pattern",
        }

    return {
        "status": "stable",
        "summary": "Political climate appears calm.",
        "safety": "Safe to travel. Normal conditions.",
        "fare_outlook": "Normal fare rates expected.",
        "headlines": [],
        "source": "Default",
    }
