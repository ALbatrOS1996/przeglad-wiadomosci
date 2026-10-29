# Lista źródeł. scope decyduje, do której kategorii trafia wiadomość:
#   krk   – zawsze Kraków
#   pl    – polskie serwisy ogólne: Kraków / Polska / Europa / Świat wg słów kluczowych
#   world – serwisy zagraniczne i działy „świat”: Europa albo Świat wg słów kluczowych
#   eu    – serwisy europejskie: Europa (chyba że tekst wyraźnie dotyczy innego regionu)
# topic – podpowiedź tematu, gdy serwis jest tematyczny
# hours – jak daleko wstecz brać wpisy (ośrodki analityczne publikują rzadziej)
# gnews – kanał z Google News (sam nagłówek, link przekierowuje do źródła)

def gnews(query, lang="pl"):
    if lang == "pl":
        return f"https://news.google.com/rss/search?q={query}&hl=pl&gl=PL&ceid=PL:pl"
    return f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"


FEEDS = [
    # ── Kraków ──
    {"name": "LoveKraków", "url": "https://lovekrakow.pl/rss.xml", "scope": "krk", "w": 3},
    {"name": "Gazeta Krakowska", "url": "https://gazetakrakowska.pl/rss/gazetakrakowska.xml", "scope": "krk", "w": 2.5},
    {"name": "Radio Kraków", "url": "https://radiokrakow.pl/rss.xml", "scope": "krk", "w": 3},
    {"name": "RMF24 Kraków", "url": "https://www.rmf24.pl/regiony/krakow/feed", "scope": "krk", "w": 2.5},
    {"name": "Wyborcza Kraków", "url": "https://krakow.wyborcza.pl/pub/rss/krakow.xml", "scope": "krk", "w": 2},

    # ── Polska ──
    {"name": "PAP", "url": gnews("site:pap.pl+when:1d"), "scope": "pl", "w": 3.5, "gnews": True},
    {"name": "RMF24", "url": "https://www.rmf24.pl/fakty/polska/feed", "scope": "pl", "w": 3},
    {"name": "Interia", "url": "https://wydarzenia.interia.pl/feed", "scope": "pl", "w": 2},
    {"name": "Wirtualna Polska", "url": "https://wiadomosci.wp.pl/rss.xml", "scope": "pl", "w": 2},
    {"name": "Polsat News", "url": "https://www.polsatnews.pl/rss/wszystkie.xml", "scope": "pl", "w": 2},
    {"name": "TVN24", "url": "https://tvn24.pl/najnowsze.xml", "scope": "pl", "w": 2.5},
    {"name": "TVP Info", "url": "http://www.tvp.info/tvp.info/rss+xml.php", "scope": "pl", "w": 2},
    {"name": "Newsweek Polska", "url": "https://www.newsweek.pl/rss.xml", "scope": "pl", "w": 2.5},
    {"name": "Dziennik Gazeta Prawna", "url": "https://www.gazetaprawna.pl/.feed", "scope": "pl", "w": 2.5},
    {"name": "Rzeczpospolita", "url": "https://www.rp.pl/rss_main", "scope": "pl", "w": 2.5},
    {"name": "RMF24 Kultura", "url": "https://www.rmf24.pl/kultura/feed", "scope": "pl", "w": 2.5, "topic": "kultura"},
    {"name": "Onet Kultura", "url": "https://kultura.onet.pl/.feed", "scope": "pl", "w": 2, "topic": "kultura"},
    {"name": "RMF24 Ekonomia", "url": "https://www.rmf24.pl/ekonomia/feed", "scope": "pl", "w": 2.5, "topic": "gospodarka"},
    {"name": "money.pl", "url": "https://www.money.pl/rss/rss.xml", "scope": "pl", "w": 2.5, "topic": "gospodarka"},
    {"name": "Business Insider Polska", "url": "https://businessinsider.com.pl/.feed", "scope": "pl", "w": 2.5, "topic": "gospodarka"},
    {"name": "Bankier.pl", "url": "https://www.bankier.pl/rss/wiadomosci.xml", "scope": "pl", "w": 2, "topic": "gospodarka"},
    {"name": "RMF24 Nauka", "url": "https://www.rmf24.pl/nauka/feed", "scope": "pl", "w": 2.5, "topic": "nauka"},
    {"name": "Nauka w Polsce", "url": "https://naukawpolsce.pl/rss.xml", "scope": "pl", "w": 3, "topic": "nauka", "hours": 72},
    {"name": "National Geographic Polska", "url": "https://www.national-geographic.pl/rss", "scope": "pl", "w": 2.5, "topic": "nauka", "hours": 72},
    {"name": "Niebezpiecznik", "url": "https://niebezpiecznik.pl/feed/", "scope": "pl", "w": 3, "topic": "technologie", "hours": 96},
    {"name": "Demagog", "url": "https://demagog.org.pl/feed/", "scope": "pl", "w": 3, "topic": "fakty", "hours": 72},
    {"name": "Polski Instytut Dyplomacji Sportowej", "url": "https://pids.pl/feed/", "scope": "pl", "w": 3, "topic": "sport", "hours": 120},

    # ── Analizy: Europa / świat ──
    {"name": "OSW", "url": "https://www.osw.waw.pl/pl/rss.xml", "scope": "world", "w": 3.5, "topic": "polityka", "hours": 72},
    {"name": "PISM", "url": gnews("site:pism.pl+when:3d"), "scope": "world", "w": 3.5, "topic": "polityka", "gnews": True, "hours": 72},
    {"name": "Instytut Europy Środkowej", "url": "https://ies.lublin.pl/feed/", "scope": "eu", "w": 3.5, "topic": "polityka", "hours": 96},

    # ── Europa ──
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/world/europe/rss.xml", "scope": "eu", "w": 3.5},
    {"name": "The New York Times", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Europe.xml", "scope": "eu", "w": 3},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/europe-news/rss", "scope": "eu", "w": 3},
    {"name": "Deutsche Welle", "url": "https://rss.dw.com/rdf/rss-en-eu", "scope": "eu", "w": 3},
    {"name": "Euronews", "url": "https://www.euronews.com/rss?level=theme&name=news", "scope": "eu", "w": 2.5},
    {"name": "Politico Europe", "url": "https://www.politico.eu/feed/", "scope": "eu", "w": 3},
    {"name": "France 24", "url": "https://www.france24.com/en/europe/rss", "scope": "eu", "w": 2.5},
    {"name": "The Kyiv Independent", "url": "https://kyivindependent.com/feed/", "scope": "eu", "w": 2.5},
    {"name": "Radio Prague International", "url": "https://english.radio.cz/rss", "scope": "eu", "w": 2.5},

    # ── Świat ──
    {"name": "Reuters", "url": gnews("site:reuters.com+when:1d", "en"), "scope": "world", "w": 3.5, "gnews": True},
    {"name": "Associated Press", "url": gnews("site:apnews.com+when:1d", "en"), "scope": "world", "w": 3.5, "gnews": True},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "scope": "world", "w": 3.5},
    {"name": "The New York Times", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "scope": "world", "w": 3},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss", "scope": "world", "w": 3},
    {"name": "Deutsche Welle", "url": "https://rss.dw.com/rdf/rss-en-world", "scope": "world", "w": 2.5},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "scope": "world", "w": 2.5},
    {"name": "NPR", "url": "https://feeds.npr.org/1004/rss.xml", "scope": "world", "w": 2.5},
    {"name": "Financial Times", "url": "https://www.ft.com/world?format=rss", "scope": "world", "w": 3},
    {"name": "RMF24", "url": "https://www.rmf24.pl/fakty/swiat/feed", "scope": "world", "w": 3},
    {"name": "TVN24", "url": "https://tvn24.pl/swiat.xml", "scope": "world", "w": 2.5},
    {"name": "The New York Times", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml", "scope": "world", "w": 2.5, "topic": "kultura"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/culture/rss", "scope": "world", "w": 2.5, "topic": "kultura"},
    {"name": "The New York Times", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml", "scope": "world", "w": 2.5, "topic": "nauka"},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "scope": "world", "w": 3, "topic": "nauka"},
    {"name": "National Geographic", "url": gnews("site:nationalgeographic.com+when:3d", "en"), "scope": "world", "w": 2.5, "topic": "nauka", "gnews": True, "hours": 72},
]

# ── Słowa kluczowe (małe litery, dopasowanie po początku wyrazu) ──
KRAKOW = ["krak", "cracow", "małopol", "malopol", "nowej huc", "nowa huta", "nowej hucie", "wieliczk", "wawel", "podgórz",
          "zakopan", "tarnow", "tarnów", "nowy sącz", "nowym sączu", "oświęcim", "balice", "mpk", "miszalski", "skawin", "niepołomic"]

EUROPE = ["europ", "unia europ", "ue ", "unii europ", "eu ", "brussels", "bruksel", "nato", "von der leyen", "kallas",
          "niemc", "niemie", "german", "berlin", "merz", "bundes", "franc", "french", "paryż", "paris", "macron", "włoch", "włosz", "włosk", "ital", "rzym",
          "rome", "meloni", "hiszpan", "spain", "spanish", "madryt", "madrid", "sánchez", "portugal", "lizbon", "lisbon",
          "holand", "niderland", "dutch", "netherlands", "amsterdam", "belgi", "austri", "wiedeń", "wiedniu", "vienna", "szwajcar",
          "swiss", "switzerland", "czech", "czes", "praga", "pradze", "prague", "babiš", "babis", "słowac", "slovak", "fico", "węgr", "węgier", "hungar",
          "budapeszt", "budapest", "orbán", "orban", "rumun", "romania", "bukareszt", "bułgar", "bulgari", "grec", "greek", "greece",
          "aten", "athens", "chorwa", "croat", "serb", "belgrad", "bośni", "bosnia", "słoweni", "sloveni", "albani", "macedon",
          "kosow", "kosovo", "czarnogór", "monteneg", "litw", "lithuan", "wilno", "vilnius", "łotw", "latvi", "ryga", "riga",
          "eston", "tallin", "finl", "finn", "helsin", "szwec", "swed", "sztokholm", "stockholm", "norw", "oslo", "dania", "danii", "duńs",
          "denmark", "danish", "kopenhag", "copenhagen", "islandi", "iceland", "irland", "ireland", "irish", "dublin", "brytyj",
          "wielka brytania", "wielkiej brytanii", "britain", "british", "england", "angli", "szkoc", "scotland", "london", "londyn",
          "starmer", "ukrai", "kijów", "kijow", "kyiv", "kiev", "zełensk", "zelensk", "charków", "kharkiv", "odessa", "odesie", "rosj", "russia",
          "rosyj", "moskw", "moscow", "kreml", "kremlin", "putin", "białoru", "belarus", "łukaszenk", "lukashenk", "mołdaw", "moldov",
          "gruzj", "tbilis", "armeni", "azerbejd", "azerbaij", "turcj", "turkey", "türkiye", "turecki", "turkish", "erdogan",
          "erdoğan", "stambuł", "istanbul", "cypr", "cyprus", "malta", "malcie", "luksemb", "luxembourg", "watykan", "vatican", "papież", "pope",
          "strasbourg", "strasburg", "schengen", "eurostrefa", "eurozone", "ecb", "ebc"]

WORLD = ["usa", "stany zjednoczone", "stanów zjednoczonych", "amerykań", "american", "u.s.", "trump", "biały dom", "białego domu",
         "white house", "waszyngton", "washington", "congress", "chin", "china", "chinese", "pekin", "beijing",
         "xi jinping", "japon", "japan", "tokio", "tokyo", "indi", "delhi", "modi", "korea", "iran", "teheran", "tehran", "izrael",
         "israel", "netanjahu", "netanyahu", "gaza", "gazie", "palest", "hamas", "hezbol", "liban", "leban", "syri", "iraq", "irak",
         "afgan", "afghan", "taliban", "pakistan", "afryk", "africa", "brazyl", "brazil", "lula", "meksyk", "mexic", "kanad",
         "canad", "australi", "argentyn", "argentin", "wenezuel", "venezuel", "onz", "united nations", "kolumbi", "colombi",
         "nigeri", "egip", "egypt", "sudan", "saudi", "arabi", "jemen", "yemen", "katar", "qatar", "emirat", "tajwan", "taiwan",
         "wietnam", "vietnam", "indonez", "filipin", "philippin", "peru", "chile", "kuba", "kubie", "kubań", "cuba", "haiti", "kenia", "kenya",
         "etiop", "ethiop", "kongo", "congo", "somali", "tajland", "thailand", "birma", "birmie", "myanmar", "bangladesz", "bangladesh",
         "nowa zelandia", "new zealand", "kalifornia", "california", "nowy jork", "new york", "texas", "teksas", "florid",
         "ekwador", "ecuador", "boliwi", "bolivia", "maroko", "morocco", "algier", "tunezj", "libi", "jordan", "kazach", "kazakh"]

POLAND = ["poland", "polish", "warsaw", "tusk", "nawrocki", "nawrockiego", "sikorski", "kosiniak"]

TOPICS = {
    "polityka": ["rząd", "rządu", "minist", "premier", "prezydent", "sejm", "senat", "partia", "partii", "wybor", "koalicj",
                 "opozycj", "ustaw", "parlament", "polityk", "kampani", "government", "minister", "president", "election",
                 "parliament", "party", "vote", "lawmakers", "policy", "sanction", "sankcj", "dyploma", "diplomat", "summit",
                 "szczyt", "negocjac", "negotiat", "referend", "pis ", "psl", "konfedera", "lewic"],
    "bezpieczeństwo": ["wojn", "war ", "war,", "wojsk", "armi", "army", "military", "atak", "attack", "dron", "drone", "rakiet",
                       "missile", "ostrzał", "strike", "żołnierz", "soldier", "obron", "defen", "nato", "front", "ofensyw",
                       "offensive", "ceasefire", "rozejm", "bomb", "terror", "zamach"],
    "gospodarka": ["gospodar", "econom", "inflacj", "inflation", "stopy procent", "interest rate", "bank", "giełd", "stock",
                   "market", "rynek", "rynku", "firm", "company", "spółk", "budżet", "budget", "podat", "tax", "ceny", "cen ", "cenach", "price",
                   "eksport", "export", "import", "cło", "cła", "tariff", "trade", "handel", "pkb", "gdp", "zatrudn", "bezroboc",
                   "wynagrodz", "płac", "emerytur", "inwest", "invest", "biznes", "business", "energi", "energy", "ropa", "oil",
                   "gaz ", "kredyt", "złot", "euro ", "dolar", "nbp", "fed ", "ebc", "ecb", "przemysł", "industry", "zbóż"],
    "kultura": ["kultur", "culture", "film", "kino", "cinema", "muzeum", "museum", "wystaw", "exhibit", "teatr", "theatre",
                "theater", "koncert", "concert", "muzyk", "music", "album", "książk", "book", "literat", "pisarz", "writer",
                "noblist", "nagrod", "award", "prize", "festiwal", "festival", "sztuk", "art ", "artist", "artyst", "opera",
                "zabyt", "heritage", "serial", "netflix", "aktor", "actor", "reżyser", "director", "galeri", "gallery",
                "architekt", "architect", "fotograf", "poet", "poezj", "tanie", "balet", "ballet", "pisarka"],
    "nauka": ["nauk", "science", "scien", "badacz", "badan", "research", "naukowc", "researchers", "study", "odkry", "discover",
              "kosm", "space", "nasa", "esa", "planet", "astronom", "archeolog", "archaeolog", "fizy", "physic", "biolog",
              "chemi", "genet", "dna", "ewolucj", "evolution", "dinozaur", "dinosaur", "uniwersyt", "universit", "uczelni",
              "teleskop", "telescope", "skamie", "fossil", "gatun", "species"],
    "zdrowie": ["zdrow", "health", "szpital", "hospital", "lekarz", "doctor", "nfz", "pacjent", "patient", "chorob", "disease",
                "wirus", "virus", "szczepi", "vaccin", "nowotw", "cancer", "rak ", "lek ", "leki", "drug", "epidem", "medyc",
                "medic", "grypa", "flu"],
    "klimat": ["klimat", "climate", "środowisk", "environment", "przyrod", "nature", "zwierz", "animal", "smog", "powietrz",
               "pollution", "zanieczyszcz", "upał", "heat", "powódź", "powodz", "flood", "susz", "drought", "huragan",
               "hurricane", "tajfun", "typhoon", "pożar las", "wildfire", "emisj", "emission", "oze", "renewable", "las ",
               "lasy", "forest", "ocean", "lodowc", "glacier", "pogod", "weather", "trzęsienie", "earthquake", "cop3"],
    "technologie": ["technolog", "tech", " ai ", "sztuczn", "artificial intelligence", "openai", "google", "apple",
                    "microsoft", "meta ", "smartfon", "smartphone", "cyber", "haker", "hacker", "wyciek", "leak", "dane osob",
                    "internet", "aplikacj", "app ", "oprogramow", "software", "chip", "półprzewod", "semiconductor", "robot",
                    "startup", "phishing", "oszust", "scam", "elon musk", "tesla", "spacex", "kryptowal", "crypto", "bitcoin"],
    "sport": ["sport ", "sportu", "sportowc", "sports", "mecz", "match", "piłk", "football", "soccer", "liga", "league", "mistrz", "champion", "olimp",
              "olymp", "turniej", "tournament", "tenis", "tennis", "siatk", "volleyball", "skoki", "reprezentacj",
              "trener", "coach", "zawodni", "player", "wisła", "cracovi", "lewandowsk", "świątek", "swiatek", "hurkacz",
              "f1", "formuła", "kolarz", "cycling", "maraton", "marathon", "nba", "nfl", "mundial", "world cup", "euro 20",
              "ekstraklas", "gol ", "goal", "stadion", "stadium", "koszyk", "hokej", "hockey", "żużel", "skoczn"],
    "społeczeństwo": ["społecz", "social", "society", "edukacj", "educat", "szkoł", "school", "uczni", "student", "nauczyciel",
                      "teacher", "rodzin", "family", "dzieci", "children", "senior", "migrant", "migracj", "uchodźc",
                      "refugee", "protest", "strajk", "strike", "kościół", "church", "relig", "mieszka", "resident",
                      "transport", "komunikac", "tramwaj", "tram", "autobus", "kolej", "rail", "pociąg", "train",
                      "mieszkan", "housing", "czynsz", "rent", "wypad", "accident", "policj", "police", "sąd", "court",
                      "prokurat", "wyrok", "verdict", "przestęp", "crime", "zabójst", "murder", "ratown", "straż",
                      "inwestycj miejsk", "remont", "budow", "drog", "road", "rower", "bike", "park", "festyn",
                      "1 listopada", "wszystkich świętych", "cmentarz", "cemeter", "ślub", "kobiet", "women", "prawa człowieka",
                      "human rights", "ubóst", "pover", "bezdomn", "homeless"],
}

TOPIC_LABELS = {
    "polityka": "Polityka", "bezpieczeństwo": "Bezpieczeństwo", "gospodarka": "Gospodarka", "kultura": "Kultura",
    "nauka": "Nauka", "zdrowie": "Zdrowie", "klimat": "Klimat i przyroda", "technologie": "Technologie", "sport": "Sport",
    "społeczeństwo": "Społeczeństwo", "fakty": "Fact-checking",
}
