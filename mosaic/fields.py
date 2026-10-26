"""Static classification tables: SCImago subject areas and ANZSRC Fields of Research.

CORE ranks venues with ANZSRC "Field of Research" (FoR) codes: the 2020 scheme
(46xx, used by conference rankings) and the 2008 scheme (08xx and friends, used
by the CORE2020 journal list). To let CORE-only venues take part in the
interdisciplinary intersection, each FoR code is mapped onto the SCImago
subject area / category vocabulary.
"""

# SCImago subject area codes (used for links to scimagojr.com rankings).
SCIMAGO_AREAS = {
    "Multidisciplinary": 1000,
    "Agricultural and Biological Sciences": 1100,
    "Arts and Humanities": 1200,
    "Biochemistry, Genetics and Molecular Biology": 1300,
    "Business, Management and Accounting": 1400,
    "Chemical Engineering": 1500,
    "Chemistry": 1600,
    "Computer Science": 1700,
    "Decision Sciences": 1800,
    "Earth and Planetary Sciences": 1900,
    "Economics, Econometrics and Finance": 2000,
    "Energy": 2100,
    "Engineering": 2200,
    "Environmental Science": 2300,
    "Immunology and Microbiology": 2400,
    "Materials Science": 2500,
    "Mathematics": 2600,
    "Medicine": 2700,
    "Neuroscience": 2800,
    "Nursing": 2900,
    "Pharmacology, Toxicology and Pharmaceutics": 3000,
    "Physics and Astronomy": 3100,
    "Psychology": 3200,
    "Social Sciences": 3300,
    "Veterinary": 3400,
    "Dentistry": 3500,
    "Health Professions": 3600,
}

CS = "Computer Science"

# ANZSRC FoR names, for display ("main topics" of CORE-only venues).
FOR_NAMES = {
    # 2020 scheme - Division 46
    "46": "Information and computing sciences",
    "CSE": "Computer science and engineering",
    "4601": "Applied computing",
    "4602": "Artificial intelligence",
    "4603": "Computer vision and multimedia computation",
    "4604": "Cybersecurity and privacy",
    "4605": "Data management and data science",
    "4606": "Distributed computing and systems software",
    "4607": "Graphics, augmented reality and games",
    "4608": "Human-centred computing",
    "4609": "Information systems",
    "4610": "Library and information studies",
    "4611": "Machine learning",
    "4612": "Software engineering",
    "4613": "Theory of computation",
    "4699": "Other information and computing sciences",
    # 2008 scheme - divisions
    "01": "Mathematical sciences",
    "02": "Physical sciences",
    "03": "Chemical sciences",
    "04": "Earth sciences",
    "05": "Environmental sciences",
    "06": "Biological sciences",
    "07": "Agricultural and veterinary sciences",
    "08": "Information and computing sciences",
    "09": "Engineering",
    "10": "Technology",
    "11": "Medical and health sciences",
    "12": "Built environment and design",
    "13": "Education",
    "14": "Economics",
    "15": "Commerce, management, tourism and services",
    "16": "Studies in human society",
    "17": "Psychology and cognitive sciences",
    "18": "Law and legal studies",
    "19": "Studies in creative arts and writing",
    "20": "Language, communication and culture",
    "21": "History and archaeology",
    "22": "Philosophy and religious studies",
    # 2008 scheme - groups
    "0101": "Pure mathematics",
    "0102": "Applied mathematics",
    "0103": "Numerical and computational mathematics",
    "0104": "Statistics",
    "0201": "Astronomical and space sciences",
    "0307": "Theoretical and computational chemistry",
    "0406": "Physical geography and environmental geoscience",
    "0601": "Biochemistry and cell biology",
    "0606": "Physiology",
    "0608": "Zoology",
    "0799": "Other agricultural and veterinary sciences",
    "0801": "Artificial intelligence and image processing",
    "0802": "Computation theory and mathematics",
    "0803": "Computer software",
    "0804": "Data format",
    "0805": "Distributed computing",
    "0806": "Information systems",
    "0807": "Library and information studies",
    "0899": "Other information and computing sciences",
    "0903": "Biomedical engineering",
    "0906": "Electrical and electronic engineering",
    "0909": "Geomatic engineering",
    "0910": "Manufacturing engineering",
    "0913": "Mechanical engineering",
    "1005": "Communications technologies",
    "1099": "Other technology",
    "1103": "Clinical sciences",
    "1106": "Human movement and sports science",
    "1203": "Design practice and management",
    "1303": "Specialist studies in education",
    "1499": "Other economics",
    "1503": "Business and management",
    "1608": "Sociology",
    "1701": "Psychology",
    "1702": "Cognitive sciences",
    "1801": "Law",
    "1902": "Film, television and digital media",
    "2003": "Language studies",
    "2004": "Linguistics",
    "2201": "Applied ethics",
    "2202": "History and philosophy of specific fields",
    "2203": "Philosophy",
}

# FoR code -> list of (SCImago area, SCImago category or None).
FOR_TO_SCIMAGO = {
    "46": [(CS, "Computer Science (miscellaneous)")],
    "CSE": [(CS, "Computer Science (miscellaneous)")],
    "4699": [(CS, "Computer Science (miscellaneous)")],
    "4601": [(CS, "Computer Science Applications")],
    "4602": [(CS, "Artificial Intelligence")],
    "4603": [(CS, "Computer Vision and Pattern Recognition")],
    "4604": [(CS, "Computer Networks and Communications")],
    "4605": [(CS, "Information Systems")],
    "4606": [(CS, "Computer Networks and Communications"), (CS, "Hardware and Architecture"), (CS, "Software")],
    "4607": [(CS, "Computer Graphics and Computer-Aided Design")],
    "4608": [(CS, "Human-Computer Interaction")],
    "4609": [(CS, "Information Systems")],
    "4610": [("Social Sciences", "Library and Information Sciences")],
    "4611": [(CS, "Artificial Intelligence")],
    "4612": [(CS, "Software")],
    "4613": [(CS, "Computational Theory and Mathematics"), ("Mathematics", "Theoretical Computer Science")],
    "08": [(CS, "Computer Science (miscellaneous)")],
    "0899": [(CS, "Computer Science (miscellaneous)")],
    "0801": [(CS, "Artificial Intelligence"), (CS, "Computer Vision and Pattern Recognition")],
    "0802": [(CS, "Computational Theory and Mathematics"), ("Mathematics", "Theoretical Computer Science")],
    "0803": [(CS, "Software")],
    "0804": [(CS, "Information Systems")],
    "0805": [(CS, "Computer Networks and Communications")],
    "0806": [(CS, "Information Systems")],
    "0807": [("Social Sciences", "Library and Information Sciences")],
    "1702": [("Psychology", None), ("Neuroscience", None)],
}

# 2008 two-digit division -> SCImago area, used when a code has no explicit entry.
FOR_DIVISION_TO_AREA = {
    "01": ["Mathematics"],
    "02": ["Physics and Astronomy"],
    "03": ["Chemistry"],
    "04": ["Earth and Planetary Sciences"],
    "05": ["Environmental Science"],
    "06": ["Agricultural and Biological Sciences"],
    "07": ["Agricultural and Biological Sciences"],
    "09": ["Engineering"],
    "10": ["Engineering"],
    "11": ["Medicine"],
    "12": ["Engineering"],
    "13": ["Social Sciences"],
    "14": ["Economics, Econometrics and Finance"],
    "15": ["Business, Management and Accounting"],
    "16": ["Social Sciences"],
    "17": ["Psychology"],
    "18": ["Social Sciences"],
    "19": ["Arts and Humanities"],
    "20": ["Arts and Humanities"],
    "21": ["Arts and Humanities"],
    "22": ["Arts and Humanities"],
}


def for_to_scimago(code):
    """Return the (area, category-or-None) pairs a FoR code maps onto."""
    if code in FOR_TO_SCIMAGO:
        return FOR_TO_SCIMAGO[code]
    if code.startswith("46"):
        return FOR_TO_SCIMAGO["46"]
    if code.startswith("08"):
        return FOR_TO_SCIMAGO["08"]
    return [(area, None) for area in FOR_DIVISION_TO_AREA.get(code[:2], [])]


def for_name(code):
    return FOR_NAMES.get(code) or FOR_NAMES.get(code[:2]) or f"FoR {code}"
