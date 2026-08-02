#!/usr/bin/env python3
"""SUB Magazine word bank — music, fashion and subculture keywords.

Distilled from the SUB Magazine keyword bank (compiled 2026-07-19).
Multi-word names and proper nouns carry more weight when scoring news
items, so keep them intact rather than splitting into single words.
"""

ARTISTS = [
    "Sampha", "Tirzah", "Vegyn", "Fimiguerrero", "Shygirl", "Jeshi",
    "Obongjayar", "Knucks", "Berwyn", "ENNY", "Sainte", "p-rallel",
    "Overmono", "PinkPantheress", "Burial", "Wiley", "Skepta", "Jme",
    "Stormzy", "SOPHIE", "Kode9", "Jim Legxacy", "Dean Blunt", "Mica Levi",
    "Sega Bodega", "John Glacier", "Hak Baker", "Loyle Carner",
    "Little Simz", "Master Peace", "Lancey Foux", "Louis Culture",
    "Lord Apex", "Finn Foxell", "Nia Archives", "Mura Masa", "Four Tet",
    "Dizzee Rascal", "King Krule", "James Blake", "Mount Kimbie",
    "Jai Paul", "Aphex Twin", "Roots Manuva", "Goldie", "MJ Cole",
    "So Solid Crew", "Boy Better Know", "A. G. Cook", "Central Cee",
    "Arlo Parks", "Pa Salieu", "Black Midi", "Dry Cleaning", "Bar Italia",
    "Fat Dog", "Coucou Chloe", "Kelsey Lu", "Klein", "Coby Sey",
    "Greentea Peng", "Yazmin Lacey", "Joy Crookes", "Rachel Chinouriri",
    "Tiana Major9", "Ocean Wisdom", "Ghetts", "Kano", "Jammer",
    "P Money", "D Double E", "Flowdan", "Lady Leshurr", "Nadia Rose",
    "Stefflon Don", "Unknown T", "Russ Millions", "Tion Wayne",
    "Headie One", "Digga D", "Loski", "Suspect", "Potter Payper",
    "Clavish", "Fredo", "Nines", "M Huncho", "Nafe Smallz",
    "D-Block Europe", "K-Trap", "Giggs", "Kojey Radical", "Che Lingo",
    "GAIKA", "Flohio", "Bob Vylan", "Nova Twins", "Wu-Lu", "Kae Tempest",
    "George the Poet", "Sleaford Mods", "Yard Act", "Sherelle",
    "Sir Spyro", "The Bug", "Novelist", "Mumdance", "Kelela",
    "Olivia Dean", "Bru-C", "Hedex", "Bou", "Kings of the Rollers",
    "Digital Mystikz", "Mala", "Loefah", "Uncle Waffles", "Tyla",
    "Kabza De Small", "DJ Maphorisa", "Major League DJz", "Craig David",
    "Eliza Rose", "Sammy Virji", "venbee", "Piri", "Chase and Status",
    "Amelia Dimoldenberg", "Dave", "AJ Tracey", "Slowthai", "Ms Banks",
]

GENRES = [
    "grime", "UK drill", "drill", "jungle", "dubstep", "bassline",
    "UK garage", "UKG", "2-step", "speed garage", "future garage",
    "broken beat", "UK bass", "hyperpop", "glitchcore", "digicore",
    "pluggnb", "cloud rap", "jerk rap", "afroswing", "amapiano",
    "gqom", "kwaito", "afrobeats", "dancehall", "reggae", "dub",
    "soca", "highlife", "drum and bass", "drum & bass", "d&b", "dnb",
    "liquid d&b", "breakcore", "footwork", "deconstructed club",
    "neo-soul", "UK R&B", "trip-hop", "post-punk", "shoegaze",
    "dream-pop", "art-punk", "hardcore continuum", "pirate radio",
    "sound system", "dubplate", "garage revival", "jungle revival",
]

MUSIC_CULTURE = [
    "Rinse FM", "NTS Radio", "Boiler Room", "Keep Hush", "GRM Daily",
    "Mixtape Madness", "Link Up TV", "SBTV", "Trench Magazine",
    "Resident Advisor", "Mixmag", "Crack Magazine", "DJ Mag",
    "Notting Hill Carnival", "Glastonbury", "Wireless Festival",
    "Lovebox", "Fabric", "Printworks", "Drumsheds", "Corsica Studios",
    "Village Underground", "Colour Factory", "XOYO", "KOKO",
    "Peckham Audio", "Windmill Brixton", "Moth Club", "Jazz Cafe",
    "Electric Brixton", "Metalheadz", "Hyperdub", "XL Recordings",
    "Ninja Tune", "PC Music", "Rough Trade", "Mercury Prize",
    "MOBO", "Brit Award", "Brit Awards", "Top Boy", "Chicken Shop Date",
    "warehouse party", "warehouse rave", "club night", "grassroots venue",
]

FASHION = [
    "Martine Rose", "Mowalola", "Knwls", "Nensi Dojaka", "Ahluwalia",
    "Saul Nash", "Stefan Cooke", "Robyn Lynch", "Bianca Saunders",
    "JW Anderson", "Burberry", "Simone Rocha", "Dilara Findikoglu",
    "Chet Lo", "Chopova Lowena", "Charles Jeffrey", "Loverboy",
    "Craig Green", "Grace Wales Bonner", "Wales Bonner",
    "Kiko Kostadinov", "Samuel Ross", "A-Cold-Wall", "Nicholas Daley",
    "Conner Ives", "Corteiz", "Clint419", "Palace Skateboards",
    "Supreme", "Stussy", "Carhartt WIP", "Trapstar", "Benjart",
    "Hoodrich", "Always Do What You Should Do", "ADWYSD", "Jehu-Cal",
    "Minus Two", "Places+Faces", "Unknown London", "Broken Planet",
    "Kick Game", "Wavey Garms", "Duke's Cupboard", "Classic Football Shirts",
    "Beyond Retro", "Rokit", "Depop", "Vinted", "Grailed",
    "Portobello Road", "Camden Market", "Brick Lane", "Spitalfields",
    "Broadway Market", "Dover Street Market", "Selfridges", "Machine-A",
    "LN-CC", "End Clothing", "Footpatrol", "London Fashion Week",
    "Fashion East", "Central Saint Martins", "London College of Fashion",
    "Vivienne Westwood", "Nike Shox", "Air Max 95", "Wallabee", "Clarks",
    "Adidas Samba", "Stone Island", "streetwear", "gorpcore",
    "terrace casuals", "Y2K", "vintage resale", "archive fashion",
    "Nick Knight", "Tyrone Lebon", "Harley Weir", "Campbell Addy",
    "Ib Kamara", "Edward Enninful", "i-D", "Dazed", "The Face",
]

SUBCULTURES = [
    "Southbank Undercroft", "Long Live Southbank", "Slam City Skates",
    "Palace skate", "skate culture", "skateboarding", "Blondey McCoy",
    "Tom Knox", "Helena Long", "five-a-side", "cage football",
    "Sunday League", "non-league", "terrace culture", "groundhopping",
    "York Hall", "fixed-gear", "Brick Lane Bikes", "BMX",
    "chicken shop", "Morley's", "Sam's Chicken", "Chicken Cottage",
    "barbershop culture", "fine-line tattoo", "Sang Bleu",
    "Leake Street", "Bold Tendencies", "South London Gallery",
    "Peckham 24", "Copeland Gallery", "street art", "estate culture",
    "council estate", "postcode", "ends culture", "road rap",
    "Simon Wheatley", "Vicky Grout", "Jenn Nkiru", "zine",
    "Sink The Pink", "Pxssy Palace", "BBZ", "ballroom culture",
    "vogue ball", "queer club night", "day party", "gentrification",
    "venue closure", "youth club", "grime documentary",
]

CATEGORIES = {
    "music": ARTISTS + GENRES + MUSIC_CULTURE,
    "fashion": FASHION,
    "subculture": SUBCULTURES,
}

ALL_KEYWORDS = sorted(set(k for kws in CATEGORIES.values() for k in kws))

# Generic single words that need company before an item counts as a match
# (avoids e.g. every article containing the word "drill" or "dave" firing).
WEAK_ALONE = {
    "drill", "jungle", "dub", "reggae", "dancehall", "grime", "zine",
    "streetwear", "skateboarding", "gentrification", "postcode",
    "dave", "klein", "burberry", "supreme", "stussy", "clarks", "goldie",
    "y2k", "bmx", "dnb", "ukg",
    # Publication and platform names: these appear in the boilerplate of the
    # very feeds we read (a Dazed article always says "Dazed"), so on their
    # own they say nothing about whether a story is SUB-relevant.
    "dazed", "i-d", "the face", "mixmag", "dj mag", "nme", "hypebeast",
    "crack magazine", "resident advisor", "notion", "wonderland",
    "selfridges", "harrods", "depop", "vinted", "grailed",
}
