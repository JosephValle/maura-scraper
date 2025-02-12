import os


KEYWORDS = [
    # Nuclear Energy
    "capacity factor",
    "unit capability factor",
    "safety system performance",
    "fuel performance",
    "small modular reactor",
    "microreactor",
    "advanced nuclear reactor",
    "fusion energy",
    "nuclear propulsion",
    "nuclear microgrid",
    "radioisotope thermoelectric generator",
    "high-assay low-enriched uranium",
    "thorium reactor",
    "nuclear thermal propulsion",
    "nuclear-enabled",
    "uranium enrichment",

    # Defense Tech
    "hypersonic",
    "hypersonics",
    "directed energy weapons",
    "quantum computing",
    "quantum science",
    "artificial intelligence",
    "AI",
    "machine learning in defense",
    "autonomous defense systems",
    "unmanned systems",
    "defense logistics",
    "military cybersecurity",
    "electronic warfare",
    "zero trust security",
    "counter-drone",
    "stealth technology",
    "ISR (intelligence, surveillance, reconnaissance)",
    "defense supply chain",
    "additive manufacturing in defense",
    "dual-use technology",
    "space-based defense",
    "warfighter technology",

    # Space Industry
    "small satellite",
    "cubesat",
    "commercial spaceflight",
    "space propulsion",
    "lunar economy",
    "asteroid mining",
    "deep space exploration",
    "rapid prototyping",
    "critical technology",
    "biotechnology",
    "advanced materials",
    "5G in space",
    "orbital manufacturing",
    "low Earth orbit economy",
    "Mars mission",
    "lunar lander",
    "space station module",
    "Musk",
    "SpaceX",
    "Blue Origin",
    "Rocket Lab",
    "Sierra Space",
    "Relativity Space",
    "Astra",
    "Terran Orbital",
    "Firefly Aerospace",
    "Planet Labs"

    # COMPANIES

    # Space Industry
    "Rocket Lab",
    "Relativity Space",
    "Astra",
    "Firefly Aerospace",
    "Sierra Space",
    "Terran Orbital",
    "Planet Labs",
    "Impulse Space",
    "Redwire Space",
    "Blue Canyon Technologies",
    "AstroForge",
    "Orbit Fab",
    "The Exploration Company",
    "Vast Space",
    "Exotrail",
    "Sidus Space",
    "Momentus",
    "ABL Space Systems",
    "Vaya Space",
    "ISAR Aerospace",
    "Gilmour Space Technologies",

    # Nuclear Energy
    "NuScale Power",
    "X-energy",
    "Oklo",
    "Kairos Power",
    "TerraPower",
    "Ultra Safe Nuclear Corporation",
    "Radiant Nuclear",
    "Moltex Energy",
    "Elysium Industries",
    "ThorCon Power",
    "ARC Clean Energy",
    "BWXT Advanced Technologies",
    "Seaborg Technologies",
    "Last Energy",
    "Copenhagen Atomics",

    # Defense Tech
    "Shield AI",
    "Anduril Industries",
    "Kratos Defense & Security",
    "Epirus",
    "Palantir Technologies",
    "Hawkeye 360",
    "Vantage Robotics",
    "Echodyne",
    "Skydio",
    "Fortem Technologies",
    "Rebellion Defense",
    "Ghost Robotics",
    "Plymouth Rock Technologies",
    "Saronic",
    "Sarcos Technology and Robotics",
    "Dedrone",
    "D-Fend Solutions",
    "Darkhive",
    "Icarus Aerospace",
    "SpearUAV"
]


RSS_FEEDS = [
    # Nuclear Energy
    "https://world-nuclear-news.org/RSS",
    "https://www.energy.gov/ne/rss.xml", # Unoperational
    "https://www.iaea.org/newscenter/news/rss",
    "https://www.neimagazine.com/rss/news/",
    "https://www.nuclearnewswire.com/feed/",
    "https://www.nuclearpowerdaily.com/rss/",
    "https://www.nrc.gov/reading-rm/doc-collections/news/rss.xml",
    "https://www.ans.org/news/rss/", # Unoperational

    # Defense Technology
    "https://www.defensenews.com/rss/news/", # Unoperational
    "https://breakingdefense.com/feed/",
    "https://www.defense.gov/News/Press-Releases/rss/", # Unoperational
    "https://www.militaryaerospace.com/rss", # Unoperational
    "https://www.nationaldefensemagazine.org/rss", # Unoperational
    "https://www.defenseone.com/rss/", # Unoperational
    "https://www.janes.com/defence-news/rss", # Unoperational
    "https://www.defenseworld.net/rss/",
    "https://www.army-technology.com/feed/",
    "https://www.naval-technology.com/feed/",
    "https://www.airforce-technology.com/feed/",
    "https://www.spacewar.com/rss/", # Unoperational
    "https://www.defenseindustrydaily.com/feed/",
    "https://www.defense-aerospace.com/rss.html", # Unoperational
    
    # Space Industry
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "https://spacenews.com/feed/",
    "https://www.space.com/feeds/all",
    "https://arstechnica.com/category/space/feed/",
    "https://spacepolicyonline.com/feed/",
    "https://www.thespacereview.com/rss.xml", # Unoperational
    "https://www.parabolicarc.com/feed/", # Unoperational
    "https://spaceref.com/rss.xml", # Unoperational
    "https://www.orbitaltoday.com/feed/",
    "https://spacewatch.global/feed/",
    "https://www.spacelegalissues.com/feed/", # Unoperational
    "https://spaceq.ca/feed/",
    "https://www.spacepolicyonline.com/feed/",
    "https://www.spaceintelreport.com/feed/",
    "https://spacewatch.global/feed/",
    "https://www.spaceitbridge.com/feed/", # Unoperational
]


# Database configuration (using a local SQLite file)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "articles.db")

# Only consider articles from the past X days (e.g., 30 days)
DAYS_LIMIT = 30

# Scheduler or scraping time (placeholder):
SCRAPE_TIME = "12:00"  # Daily at 12:00 local time (could be used with cron or APScheduler)
