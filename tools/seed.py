"""Generate a large, realistic library_data.json by driving the real Library class.

Usage: python seed.py <project_dir> <out_json>
Every loan, return and fine below goes through Library.issue_book / return_book / pay_fine,
so the data obeys exactly the same rules as the CLI.
"""
import json
import random
import sys
from collections import defaultdict
from datetime import date, timedelta

sys.path.insert(0, sys.argv[1])
from library import Book, ReferenceBook, StudentMember, FacultyMember, GuestMember, Library, LibraryError  # noqa: E402
from library.transaction import Transaction  # noqa: E402

rng = random.Random(20261122)
TODAY = date(2026, 11, 22)
START = date(2025, 5, 26)

# ----------------------------------------------------------------------------- names
FIRST = """Aarav Aditi Akash Ananya Arjun Aishwarya Bhavya Chaitanya Deepika Dev Divya Farhan Gautam Gayatri
Harini Harsh Ishaan Isha Jahnavi Karthik Kavya Keerthana Krishna Lakshmi Manish Meghana Mohit Nandini Naveen
Neha Nikhil Nithya Pooja Pranav Prateek Priya Rahul Rajesh Ramya Rohan Rohit Sai Sakshi Sanjay Saranya Shreya
Siddharth Sneha Sowmya Srinivas Sruthi Suresh Swathi Tanvi Tarun Uday Vaishnavi Varun Vignesh Vikram Yamini
Abhishek Anirudh Bhargav Charan Dhruv Hemanth Jayanth Kiran Lokesh Madhav Nakul Omkar Parth Raghav Sahil Tejas
Aparna Bhoomika Charitha Dhanya Esha Gowri Hamsa Indu Jyothi Kritika Lavanya Mrudula Niharika Pallavi Rashmi
Shalini Tejaswini Varsha Zoya Aman Imran Joseph Rizwan Ayesha Mariam Sarah Daniel Kevin Anjali Riya Simran""".split()
LAST = """Reddy Sharma Iyer Nair Rao Kumar Gupta Menon Pillai Patel Singh Joshi Mehta Krishnan Subramanian
Venkatesh Chatterjee Banerjee Das Mukherjee Agarwal Bhat Shetty Hegde Naidu Choudhary Verma Mishra Pandey
Srinivasan Raman Ganesan Kulkarni Deshpande Patil Jain Kapoor Malhotra Saxena Thomas Fernandes Dsouza Khan
Ahmed Varma Goud Yadav Chowdary Prasad Murthy Shankar Raghavan Natarajan Bose Sen Ghosh Dutta Kamath Pai""".split()
INTL_AUTH = """Smith Johnson Williams Brown Miller Davis Wilson Anderson Taylor Moore Martin Thompson White Harris
Clark Lewis Walker Young Allen King Wright Scott Hill Green Adams Baker Nelson Carter Mitchell Roberts Turner
Phillips Campbell Parker Evans Edwards Collins Stewart Morris Rogers Reed Cook Morgan Bell Murphy Bailey Cooper
Richardson Cox Howard Ward Peterson Gray James Watson Brooks Kelly Sanders Price Bennett Wood Barnes Ross
Henderson Coleman Jenkins Perry Powell Long Patterson Hughes Flores Butler Simmons Foster Bryant Alexander
Russell Griffin Hayes Myers Ford Hamilton Graham Sullivan Wallace Woods Cole West Jordan Owens Reynolds Fisher
Ellis Harrison Gibson Mcdonald Marshall Ortiz Gomez Murray Freeman Wells Webb Simpson Stevens Tucker Porter
Hunter Hicks Crawford Henry Boyd Mason Kennedy Warren Dixon Burns Gordon Shaw Holmes Rice Robertson Hunt Black
Daniels Palmer Mills Nichols Grant Knight Ferguson Rose Stone Hawkins Dunn Perkins Hudson Spencer Gardner
Stephens Payne Pierce Berry Matthews Arnold Wagner Willis Ray Watkins Olson Carroll Duncan Snyder Hart Cunningham
Bradley Lane Andrews Ruiz Harper Fox Riley Armstrong Carpenter Weaver Greene Lawrence Elliott Chavez Sims Austin
Peters Kelley Franklin Lawson Fields Ryan Schmidt Carr Castillo Wheeler Chapman Oliver Montgomery Richards
Williamson Johnston Banks Meyer Bishop Mccoy Howell Morrison Hansen Fernandez Garza Harvey Little Burton Stanley
Nguyen George Jacobs Reid Fuller Lynch Dean Gilbert Romero Welch Larson Frazier Burke Hanson Day Mendoza Moreno
Bowman Medina Fowler Brewer Hoffman Carlson Silva Pearson Holland Douglas Fleming Jensen Vargas Byrd Davidson
Hopkins May Terry Herrera Wade Soto Walters Curtis Neal Caldwell Lowe Jennings Barnett Graves Jimenez Horton
Shelton Barrett Obrien Castro Sutton Gregory Mckinney Lucas Miles Craig Rodriquez Chambers Holt Lambert Fletcher
Watts Bates Hale Rhodes Pena Beck Newman Haynes Mcdaniel Mendez Bush Vaughn Parks Dawson Santiago Norris Hardy
Love Steele Curry Powers Schultz Barker Guzman Page Munoz Ball Keller Chandler Weber Leonard Walsh Lyons Ramsey
Wolfe Schneider Mullins Benson Sharp Bowen Daniel Barber Cummings Hines Baldwin Griffith Valdez Hubbard Salazar
Reeves Warner Stevenson Burgess Santos Tate Cross Garner Mann Mack Moss Thornton Dennis Mcgee Farmer Delgado
Aguilar Vega Glover Manning Cohen Harmon Rodgers Robbins Newton Todd Blair Higgins Ingram Reese Cannon Strickland
Townsend Potter Goodwin Walton Rowe Hampton Ortega Patton Swanson Joseph Francis Goodman Maldonado Yates Becker
Erickson Hodges Rios Conner Adkins Webster Norman Malone Hammond Flowers Cobb Moody Quinn Blake Maxwell Pope
Floyd Osborne Paul Mccarthy Guerrero Lindsey Estrada Sandoval Gibbs Tyler Gross Fitzgerald Stokes Doyle Sherman
Saunders Wise Colon Gill Alvarado Greer Padilla Simon Waters Nunez Ballard Schwartz Mcbride Houston Christensen
Klein Pratt Briggs Parsons Mclaughlin Zimmerman French Buchanan Moran Copeland Roy Pittman Brady Mccormick
Holloway Brock Poole Frank Logan Owen Bass Marsh Drake Wong Jefferson Park Morton Abbott Sparks Patrick Norton
Huff Clayton Massey Lloyd Figueroa Carson Bowers Roberson Barton Tran Lamb Harrington Casey Boone Cortez Clarke
Mathis Singleton Wilkins Cain Bryan Underwood Hogan Mckenzie Collier Luna Phelps Mcguire Allison Bridges Wilkerson
Nash Summers Atkins Wilcox Pitts Conley Marquez Burnett Richard Cochran Chase Davenport Hood Gates Clay Ayala
Sawyer Roman Vazquez Dickerson Hodge Acosta Flynn Espinoza Nicholson Monroe Wolf Morrow Kirk Randall Anthony
Whitaker Oconnor Skinner Ware Molina Kirby Huffman Bradford Charles Gilmore Dominguez Oneal Bruce Lang Combs
Kramer Heath Hancock Gallagher Gaines Shaffer Short Wiggins Mathews Mcclain Fischer Wall Small Melton Hensley
Bond Dyer Cameron Grimes Contreras Christian Wyatt Baxter Snow Mosley Shepherd Larsen Hoover Beasley Glenn
Petersen Whitehead Meyers Keith Garrison Vincent Shields Horn Savage Olsen Schroeder Hartman Woodard Mueller""".split()
INTL_FIRST = "J. R. M. A. D. S. P. K. T. W. H. C. E. L. G. F. B. N.".split()

def person():
    return f"{rng.choice(FIRST)} {rng.choice(LAST)}"

def author():
    r = rng.random()
    if r < 0.45:
        a = f"{rng.choice(INTL_FIRST)} {rng.choice(INTL_AUTH)}"
    else:
        a = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    if rng.random() < 0.35:
        a2 = f"{rng.choice(INTL_FIRST)} {rng.choice(INTL_AUTH + LAST)}"
        a = f"{a}, {a2}"
    return a

# ----------------------------------------------------------------------------- titles
SUBJECTS = {
    "Computer Science": ["Algorithms", "Data Structures", "Operating Systems", "Computer Networks", "Database Systems",
        "Compiler Design", "Machine Learning", "Deep Learning", "Computer Architecture", "Distributed Systems",
        "Software Engineering", "Theory of Computation", "Cryptography", "Computer Vision", "Natural Language Processing",
        "Reinforcement Learning", "Information Retrieval", "Parallel Computing", "Computer Graphics", "Cloud Computing",
        "Python Programming", "C++ Programming", "Java Programming", "Web Development", "Discrete Mathematics"],
    "Mechanical Engineering": ["Thermodynamics", "Fluid Mechanics", "Heat and Mass Transfer", "Machine Design",
        "Strength of Materials", "Kinematics of Machinery", "Manufacturing Processes", "Metal Cutting", "CNC Machining",
        "Robotics", "Finite Element Analysis", "Vibrations", "Turbomachinery", "Internal Combustion Engines",
        "Refrigeration and Air Conditioning", "Engineering Mechanics", "Mechatronics", "Tribology",
        "Computational Fluid Dynamics", "Additive Manufacturing", "Metrology", "Industrial Engineering",
        "Composite Materials", "Control Engineering", "Product Design"],
    "Electrical Engineering": ["Circuit Theory", "Signals and Systems", "Digital Signal Processing", "Power Systems",
        "Electrical Machines", "Power Electronics", "Analog Electronics", "Digital Electronics", "VLSI Design",
        "Communication Systems", "Electromagnetic Theory", "Microprocessors", "Embedded Systems", "Control Systems",
        "RF and Microwave Engineering", "Antenna Theory", "Wireless Communication", "Information Theory"],
    "Civil Engineering": ["Structural Analysis", "Reinforced Concrete Design", "Soil Mechanics", "Geotechnical Engineering",
        "Transportation Engineering", "Hydraulics", "Surveying", "Environmental Engineering", "Steel Structures",
        "Construction Management", "Water Resources Engineering", "Earthquake Engineering"],
    "Chemical Engineering": ["Chemical Reaction Engineering", "Mass Transfer Operations", "Process Control",
        "Transport Phenomena", "Chemical Process Calculations", "Process Equipment Design", "Petroleum Refining",
        "Polymer Science", "Biochemical Engineering", "Catalysis"],
    "Mathematics": ["Linear Algebra", "Calculus", "Real Analysis", "Complex Analysis", "Probability",
        "Statistics", "Numerical Methods", "Differential Equations", "Optimization", "Abstract Algebra",
        "Graph Theory", "Stochastic Processes", "Topology", "Partial Differential Equations", "Number Theory"],
    "Physics": ["Classical Mechanics", "Quantum Mechanics", "Electrodynamics", "Statistical Mechanics", "Optics",
        "Solid State Physics", "Nuclear Physics", "Relativity", "Mathematical Physics", "Semiconductor Physics"],
    "Management & Economics": ["Microeconomics", "Macroeconomics", "Financial Accounting", "Corporate Finance",
        "Marketing Management", "Operations Management", "Organisational Behaviour", "Business Strategy",
        "Supply Chain Management", "Entrepreneurship", "Econometrics", "Project Management", "Game Theory"],
    "Humanities": ["Indian History", "World History", "Philosophy", "Psychology", "Sociology", "Linguistics",
        "Political Theory", "Ethics", "Indian Constitution", "Development Studies", "Technical Writing"],
}
TEMPLATES = ["Introduction to {t}", "Fundamentals of {t}", "Principles of {t}", "{t}", "Advanced {t}",
    "{t}: Theory and Practice", "Elements of {t}", "A First Course in {t}", "{t}: A Modern Approach",
    "Applied {t}", "{t} for Engineers", "Essentials of {t}", "Problems and Solutions in {t}",
    "Handbook of {t}", "{t}: Concepts and Applications", "Topics in {t}", "Understanding {t}",
    "{t} Made Simple", "Lectures on {t}", "Modern {t}"]

CLASSICS = [  # public-domain fiction & non-fiction
    ("Pride and Prejudice", "Jane Austen"), ("Emma", "Jane Austen"), ("Sense and Sensibility", "Jane Austen"),
    ("Great Expectations", "Charles Dickens"), ("A Tale of Two Cities", "Charles Dickens"), ("Oliver Twist", "Charles Dickens"),
    ("David Copperfield", "Charles Dickens"), ("War and Peace", "Leo Tolstoy"), ("Anna Karenina", "Leo Tolstoy"),
    ("Crime and Punishment", "Fyodor Dostoevsky"), ("The Brothers Karamazov", "Fyodor Dostoevsky"),
    ("Moby-Dick", "Herman Melville"), ("Frankenstein", "Mary Shelley"), ("Dracula", "Bram Stoker"),
    ("The Adventures of Sherlock Holmes", "Arthur Conan Doyle"), ("The Hound of the Baskervilles", "Arthur Conan Doyle"),
    ("Gitanjali", "Rabindranath Tagore"), ("The Home and the World", "Rabindranath Tagore"), ("Gora", "Rabindranath Tagore"),
    ("Jane Eyre", "Charlotte Bronte"), ("Wuthering Heights", "Emily Bronte"), ("Les Miserables", "Victor Hugo"),
    ("The Count of Monte Cristo", "Alexandre Dumas"), ("The Three Musketeers", "Alexandre Dumas"),
    ("Don Quixote", "Miguel de Cervantes"), ("The Odyssey", "Homer"), ("The Iliad", "Homer"),
    ("The Time Machine", "H. G. Wells"), ("The War of the Worlds", "H. G. Wells"), ("Treasure Island", "Robert Louis Stevenson"),
    ("Twenty Thousand Leagues Under the Seas", "Jules Verne"), ("Around the World in Eighty Days", "Jules Verne"),
    ("The Picture of Dorian Gray", "Oscar Wilde"), ("Heart of Darkness", "Joseph Conrad"), ("Ulysses", "James Joyce"),
    ("The Adventures of Tom Sawyer", "Mark Twain"), ("Adventures of Huckleberry Finn", "Mark Twain"),
    ("Middlemarch", "George Eliot"), ("Madame Bovary", "Gustave Flaubert"), ("The Metamorphosis", "Franz Kafka"),
    ("The Wealth of Nations", "Adam Smith"), ("On the Origin of Species", "Charles Darwin"), ("The Republic", "Plato"),
    ("Meditations", "Marcus Aurelius"), ("The Art of War", "Sun Tzu"), ("The Prince", "Niccolo Machiavelli"),
    ("Arthashastra", "Kautilya"), ("Hind Swaraj", "M. K. Gandhi"), ("Walden", "Henry David Thoreau"),
    ("Relativity: The Special and General Theory", "Albert Einstein"), ("Principia Mathematica", "Isaac Newton"),
    ("Siddhartha", "Hermann Hesse"), ("The Jungle Book", "Rudyard Kipling"), ("Kim", "Rudyard Kipling"),
    ("Little Women", "Louisa May Alcott"), ("The Scarlet Letter", "Nathaniel Hawthorne"), ("Dubliners", "James Joyce"),
]
REFERENCE = ["Oxford English Dictionary", "Encyclopaedia of Mechanical Engineering", "CRC Handbook of Chemistry and Physics",
    "Perry's Chemical Engineers' Handbook (Reference)", "Machinery's Handbook (Reference)", "IS 456: Code of Practice for Plain and Reinforced Concrete",
    "Indian Standard Steel Tables", "Atlas of the World", "Abramowitz and Stegun: Handbook of Mathematical Functions",
    "Encyclopaedia Britannica Vol. I", "Encyclopaedia Britannica Vol. II", "Encyclopaedia Britannica Vol. III",
    "IEEE Standard Dictionary of Electrical Terms", "ASM Handbook: Properties and Selection", "Steam Tables (SI Units)",
    "Design Data Book for Machine Elements", "Thesaurus of English Words", "Hindi-English Dictionary",
    "Yearbook of Indian Statistics 2025", "Who's Who in Indian Science", "Gazetteer of India", "Handbook of Fluid Dynamics",
    "Handbook of Statistical Tables", "Encyclopaedia of Computer Science", "Dictionary of Mathematics",
    "Handbook of Heat Transfer", "Manual of Surveying Instruments", "Dictionary of Economics", "Encyclopaedia of Philosophy",
    "Indian Electricity Rules Handbook", "Thermophysical Properties of Matter", "Materials Data Handbook",
    "National Building Code of India", "Handbook of Formulae and Physical Constants", "Directory of Indian Universities",
    "Oxford Dictionary of Quotations", "Chambers Biographical Dictionary", "Handbook of Industrial Robotics",
    "Gray's Anatomy (Reference)", "Encyclopaedia of Indian Literature"]

used_isbn = set()

def isbn13():
    while True:
        body = "97893" + "".join(str(rng.randint(0, 9)) for _ in range(7))
        s = sum((1 if i % 2 == 0 else 3) * int(c) for i, c in enumerate(body))
        code = body + str((10 - s % 10) % 10)
        if code not in used_isbn:
            used_isbn.add(code)
            return code

lib = Library()
meta = {}  # isbn -> {subject, year}
popularity = {}
titles_seen = set()

def add(book, subject, pop):
    lib.add_book(book)
    meta[book.isbn] = {"s": subject, "y": rng.randint(1985, 2025)}
    popularity[book.isbn] = pop

for subject, topics in SUBJECTS.items():
    n = {"Computer Science": 330, "Mechanical Engineering": 330, "Electrical Engineering": 230,
         "Civil Engineering": 150, "Chemical Engineering": 120, "Mathematics": 230, "Physics": 150,
         "Management & Economics": 160, "Humanities": 120}[subject]
    tries = 0
    while n and tries < 10000:
        tries += 1
        t = rng.choice(TEMPLATES).format(t=rng.choice(topics))
        if rng.random() < 0.25:
            t += f" ({rng.choice(['2nd', '3rd', '4th', '5th', '7th', '9th'])} ed.)"
        if t in titles_seen:
            continue
        titles_seen.add(t)
        pop = rng.paretovariate(1.3)
        copies = min(12, max(1, int(round(pop * rng.uniform(0.8, 2.2)))))
        add(Book(isbn13(), t, author(), copies=copies), subject, pop)
        n -= 1

for t, a in CLASSICS:
    pop = rng.paretovariate(1.6) * 0.8
    add(Book(isbn13(), t, a, copies=rng.randint(1, 4)), "Literature", pop)
for t in REFERENCE:
    add(ReferenceBook(isbn13(), t, rng.choice(["Oxford University Press", "CRC Press", "Bureau of Indian Standards",
        "McGraw-Hill", "Elsevier", "Publications Division, Govt. of India", "ASM International", "Wiley"])), "Reference", 0)

# ----------------------------------------------------------------------------- members
DEPTS = ["ME", "CS", "EE", "CE", "CH", "MM", "AE", "ED", "BT", "PH", "MA", "HS", "NA", "EP"]
member_meta = {}
activity = {}
def add_member(m, joined, act, dept=None):
    lib.add_member(m)
    member_meta[m.member_id] = {"j": joined.isoformat(), **({"d": dept} if dept else {})}
    activity[m.member_id] = act

for _ in range(1150):
    dept = rng.choice(DEPTS)
    batch = rng.choice([22, 23, 24, 25, 26])
    prog = rng.choices("BDMS", [70, 12, 10, 8])[0]
    while True:
        mid = f"{dept}{batch}{prog}{rng.randint(1, 120):03d}"
        if mid not in lib.members:
            break
    joined = date(2000 + batch, 7, 20) if batch <= 25 else date(2026, 7, 27)
    if joined < START:
        joined = START
    add_member(StudentMember(mid, person()), joined, rng.paretovariate(1.8), dept)
for i in range(1, 186):
    name = f"{rng.choice(['Dr.', 'Prof.', 'Prof.', 'Dr.'])} {person()}"
    add_member(FacultyMember(f"F{i:04d}", name), START, rng.paretovariate(2.0) * 1.2, rng.choice(DEPTS))
for i in range(1, 131):
    joined = START + timedelta(days=rng.randint(0, (TODAY - START).days - 10))
    add_member(GuestMember(f"G{i:04d}", person()), joined, rng.paretovariate(2.5) * 0.7)

# ----------------------------------------------------------------------------- fast loan index (sim only)
active_by_member = defaultdict(list)
_orig_issue, _orig_return = Library.issue_book, Library.return_book
def fast_active(self, member_id=None):
    if member_id is None:
        return [t for ts in active_by_member.values() for t in ts]
    return list(active_by_member[member_id])
lib.active_loans = fast_active.__get__(lib)

# ----------------------------------------------------------------------------- simulate circulation
isbns = [i for i, b in lib.books.items() if b.lendable]
ipop = [popularity[i] for i in isbns]
mids = list(lib.members)
returns_due = defaultdict(list)  # date -> [(isbn, member_id)]
fail = defaultdict(int)

def season(d):
    m = d.month
    f = {1: 1.0, 2: 1.1, 3: 1.25, 4: 1.3, 5: 0.55, 6: 0.35, 7: 0.7, 8: 1.05, 9: 1.15, 10: 1.25, 11: 1.35, 12: 0.5}[m]
    if d.weekday() == 6:
        f *= 0.25
    elif d.weekday() == 5:
        f *= 0.6
    return f

d = START
while d <= TODAY:
    # returns scheduled for today
    for isbn, mid in returns_due.pop(d, []):
        txn = lib.return_book(isbn, mid, on=d)
        active_by_member[mid].remove(txn)
    # fine payments: people settle up when they come in
    for mid in mids:
        m = lib.members[mid]
        if m.fines_due and rng.random() < 0.03:
            amt = m.fines_due if rng.random() < 0.8 else max(1, m.fines_due // 2)
            lib.pay_fine(mid, amt)
    # new loans
    eligible = [m for m in mids if member_meta[m]["j"] <= d.isoformat()]
    weights = [activity[m] for m in eligible]
    n = int(rng.gauss(78, 10) * season(d))
    for mid in rng.choices(eligible, weights, k=max(0, n)):
        isbn = rng.choices(isbns, ipop)[0]
        try:
            txn = lib.issue_book(isbn, mid, on=d)
        except LibraryError as e:
            fail[type(e).__name__] += 1
            continue
        active_by_member[mid].append(txn)
        m = lib.members[mid]
        r = rng.random()
        if r < 0.70:
            back = d + timedelta(days=rng.randint(2, m.loan_days))
        elif r < 0.90:
            back = txn.due_date + timedelta(days=rng.randint(1, 10))
        elif r < 0.98:
            back = txn.due_date + timedelta(days=rng.randint(11, 45))
        else:
            back = txn.due_date + timedelta(days=rng.randint(46, 160))
        if back <= TODAY:
            returns_due[back].append((isbn, mid))
    d += timedelta(days=1)

data = lib.to_dict()
data["meta"] = {
    "library": "Riverside Central Library",
    "generated_for": TODAY.isoformat(),
    "books": meta,
    "members": member_meta,
}
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    json.dump(data, fh, separators=(",", ":"), ensure_ascii=False)

act = sum(1 for t in lib.transactions if t.is_active)
print("books", len(lib.books), "copies", sum(b.total_copies for b in lib.books.values()))
print("members", len(lib.members), "txns", len(lib.transactions), "active", act,
      "overdue", len([1 for t in lib.transactions if t.is_active and t.days_overdue(TODAY) > 0]))
print("fines charged", sum(t.fine for t in lib.transactions), "outstanding", sum(m.fines_due for m in lib.members.values()))
print("rejected attempts", dict(fail))
