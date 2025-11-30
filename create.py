import sqlite3

# Configuration
DB_NAME = 'smartAgribot.db'

def create_database():
    """Crée la base de données avec toutes les tables"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("🔧 Création des tables...\n")
    
    # Table Region
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Region (
        id_reg INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        zone_climat TEXT,
        latitude REAL,
        longitude REAL
    )
    ''')
    print("✅ Table Region créée")
    
    # Table meteo_cache
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS meteo_cache (
        id_meteo INTEGER PRIMARY KEY AUTOINCREMENT,
        region_id INTEGER NOT NULL,
        data_json TEXT,
        timestamp_ DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (region_id) REFERENCES Region(id_reg)
    )
    ''')
    print("✅ Table meteo_cache créée")
    
    # Table Cultures
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Cultures (
        id_culture INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        type TEXT,
        description TEXT
    )
    ''')
    print("✅ Table Cultures créée")
    
    # Table calendrier_cultural
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS calendrier_cultural (
        id_calendar INTEGER PRIMARY KEY AUTOINCREMENT,
        id_culture INTEGER NOT NULL,
        id_reg INTEGER NOT NULL,
        periode_semis TEXT,
        periode_recolte TEXT,
        FOREIGN KEY (id_culture) REFERENCES Cultures(id_culture),
        FOREIGN KEY (id_reg) REFERENCES Region(id_reg)
    )
    ''')
    print("✅ Table calendrier_cultural créée")
    
    # Table maladies_parasites
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maladies_parasites (
        id_parasite INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        traitement TEXT
    )
    ''')
    print("✅ Table maladies_parasites créée")
    
    # Table affecter (liaison Culture-Maladie)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS affecter (
        id_culture INTEGER NOT NULL,
        id_parasite INTEGER NOT NULL,
        PRIMARY KEY (id_culture, id_parasite),
        FOREIGN KEY (id_culture) REFERENCES Cultures(id_culture),
        FOREIGN KEY (id_parasite) REFERENCES maladies_parasites(id_parasite)
    )
    ''')
    print("✅ Table affecter créée")
    
    # Table conseils_pratiques
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conseils_pratiques (
        id_cons INTEGER PRIMARY KEY AUTOINCREMENT,
        id_culture INTEGER NOT NULL,
        nom TEXT,
        bonnes_pratique TEXT,
        FOREIGN KEY (id_culture) REFERENCES Cultures(id_culture)
    )
    ''')
    print("✅ Table conseils_pratiques créée")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Base de données '{DB_NAME}' créée avec succès!")
    print("📋 7 tables créées: Region, meteo_cache, Cultures, calendrier_cultural,")
    print("   maladies_parasites, affecter, conseils_pratiques")

def verify_tables():
    """Vérifie que toutes les tables ont été créées"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("\n📊 Tables présentes dans la base:")
    for table in tables:
        print(f"   • {table[0]}")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  SCRIPT 1 - CRÉATION DE LA BASE DE DONNÉES")
    print("=" * 60)
    print()
    
    create_database()
    verify_tables()
    
    