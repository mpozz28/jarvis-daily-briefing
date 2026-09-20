import json
import os
import random
from datetime import datetime, timedelta

def generate_dataset():
    dataset = []
    
    # 1. HIGH RELEVANCE (Score 90-100) - AI, Macroeconomics, Major Tech
    high_impact_templates = [
        ("OpenAI announces breakthrough in Q* reasoning capabilities", "TECH", 98),
        ("Federal Reserve cuts interest rates by 50 basis points", "FINANZA", 95),
        ("NVIDIA unveils next-gen Blackwell GPU architecture", "TECH", 92),
        ("European Union passes comprehensive AI Act", "POLITICS", 90),
        ("US GDP growth exceeds expectations in Q3", "FINANZA", 91),
        ("Major breakthrough in solid-state battery tech by Toyota", "TECH", 88)
    ]
    
    # 2. MEDIUM RELEVANCE (Score 50-85) - Standard updates, funding, standard politics
    medium_impact_templates = [
        ("Anthropic releases minor Claude 3.5 update", "TECH", 75),
        ("Bitcoin stabilizes around 65k after brief dip", "FINANZA", 70),
        ("Local startup raises $5M in seed funding", "TECH", 60),
        ("Senate debates new tech antitrust bill", "POLITICS", 65),
        ("Apple announces new color options for iPhone 16", "TECH", 55)
    ]
    
    # 3. LOW RELEVANCE / HARD NEGATIVES (Score 0-40) - Outdated, Gossip, Irrelevant
    low_impact_templates = [
        ("Top 10 vacation spots for this summer", "LIFESTYLE", 10),
        ("Celebrity spotted at local coffee shop", "GOSSIP", 5),
        ("How to bake the perfect chocolate chip cookie", "FOOD", 15),
        ("Review: The new ergonomic office chair", "LIFESTYLE", 20),
        ("Local sports team wins regional championship", "SPORTS", 25)
    ]
    
    # HARD NEGATIVES (Sembrano tech/finanza ma sono vecchi o inutili)
    hard_negatives = [
        ("Windows 7 support officially ends today", "TECH", 0), # Troppo vecchio
        ("CEO buys a new yacht", "FINANZA", 5), # Irrilevante
        ("Rumor: Apple might remove headphone jack", "TECH", 0) # Vecchio/Fake
    ]

    base_time = datetime.now()
    item_id = 1

    # Funzione helper per aggiungere articoli
    def add_items(templates, count, time_offset_days, variance=5):
        nonlocal item_id
        for _ in range(count):
            template = random.choice(templates)
            # Aggiungiamo un po' di variazione al titolo per simulare fonti diverse
            title = f"{template[0]} {random.choice(['- Report', 'says expert', '| Analysis', ''])}".strip()
            score = max(0, min(100, template[2] + random.randint(-variance, variance)))
            
            # Se la notizia è vecchia di anni, il vero sistema dovrebbe penalizzarla
            pub_date = (base_time - timedelta(days=time_offset_days)).isoformat() + "Z"
            if time_offset_days > 365:
                score = min(score, 20)
                
            dataset.append({
                "id": str(item_id),
                "title": title,
                "summary": f"This is an automated summary for the article regarding {template[0].lower()}.",
                "area": template[1],
                "source": random.choice(["Reuters", "Bloomberg", "ArXiv", "TechCrunch", "Unknown Blog"]),
                "published": pub_date,
                "expected_relevance": score
            })
            item_id += 1

    # Popoliamo il dataset (120 articoli in totale)
    add_items(high_impact_templates, 20, time_offset_days=0)     # 20 Notizie bomba di oggi
    add_items(medium_impact_templates, 40, time_offset_days=1)    # 40 Notizie medie di ieri
    add_items(low_impact_templates, 40, time_offset_days=0)       # 40 Notizie inutili
    add_items(hard_negatives, 20, time_offset_days=1000)          # 20 Hard negatives (vecchie/ingannevoli)

    # Creiamo la cartella se non esiste
    os.makedirs('eval', exist_ok=True)
    
    # Salviamo il file
    file_path = os.path.join('eval', 'ranking_dataset.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=4)
        
    print(f"✅ Golden Dataset generato con successo in: {file_path}")
    print(f"📊 Totale articoli: {len(dataset)}")

if __name__ == "__main__":
    generate_dataset()