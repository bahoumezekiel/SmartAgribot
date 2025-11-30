import sqlite3
import pandas as pd
import os

# Configuration
DB_NAME = 'smartAgribot.db'
CSV_FOLDER = 'data_csv'  # Dossier contenant vos fichiers CSV

def check_database():
    """Vérifie que la base de données existe"""
    if not os.path.exists(DB_NAME):
        print("❌ Erreur: La base de données n'existe pas!")
        print("   Veuillez d'abord exécuter: python create_tables.py")
        return False
    return True

def import_regions(csv_path):
    """Importe les régions depuis le CSV"""
    conn = sqlite3.connect(DB_NAME)
    
    # Lire le CSV
    df = pd.read_csv(csv_path)
    
    # Colonnes attendues: Nom, Zone_climat, latitude, longitude
    # id_reg sera généré automatiquement
    df.to_sql('Region', conn, if_exists='append', index=False)
    
    conn.close()
    print(f"✅ {len(df)} régions importées")
    
    return len(df)

def import_cultures(csv_path):
    """Importe les cultures depuis le CSV"""
    conn = sqlite3.connect(DB_NAME)
    
    # Lire le CSV
    df = pd.read_csv(csv_path)
    
    # Supprimer id_culture si présent (sera généré auto)
    if 'id_culture' in df.columns:
        df = df.drop('id_culture', axis=1)
    
    # Colonnes: Nom, Type, Description
    df.to_sql('Cultures', conn, if_exists='append', index=False)
    
    conn.close()
    print(f"✅ {len(df)} cultures importées")
    
    return len(df)

def import_calendrier(csv_path):
    """Importe le calendrier cultural"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Lire le CSV
    df = pd.read_csv(csv_path)
    
    # Récupérer les IDs des cultures
    cursor.execute("SELECT id_culture, nom FROM Cultures")
    cultures_map = {nom.lower(): id_c for id_c, nom in cursor.fetchall()}
    
    # Récupérer les IDs des régions
    cursor.execute("SELECT id_reg FROM Region")
    region_ids = [row[0] for row in cursor.fetchall()]
    
    count = 0
    # Créer une entrée pour chaque culture × région
    for _, row in df.iterrows():
        culture_nom = row['Culture'].lower()
        
        if culture_nom in cultures_map:
            culture_id = cultures_map[culture_nom]
            
            # Créer une entrée pour chaque région
            for region_id in region_ids:
                cursor.execute('''
                INSERT INTO calendrier_cultural (id_culture, id_reg, periode_semis, periode_recolte)
                VALUES (?, ?, ?, ?)
                ''', (culture_id, region_id, row['Periode_semi'], row['Periode_recolte']))
                count += 1
    
    conn.commit()
    conn.close()
    print(f"✅ {count} entrées de calendrier importées")
    
    return count

def import_maladies(csv_path):
    """Importe les maladies et parasites"""
    conn = sqlite3.connect(DB_NAME)
    
    # Lire le CSV
    df = pd.read_csv(csv_path)
    
    # Supprimer id_parasite si présent
    if 'id_parasite' in df.columns:
        df = df.drop('id_parasite', axis=1)
    
    df.to_sql('maladies_parasites', conn, if_exists='append', index=False)
    
    conn.close()
    print(f"✅ {len(df)} maladies/parasites importés")
    
    return len(df)

def create_affecter_table():
    """Crée les relations culture-maladie"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Récupérer cultures et maladies
    cursor.execute("SELECT id_culture, nom FROM Cultures")
    cultures = cursor.fetchall()
    
    cursor.execute("SELECT id_parasite, nom FROM maladies_parasites")
    maladies = cursor.fetchall()
    
    count = 0
    # Associer chaque maladie à la culture correspondante
    # (Basé sur les mots-clés dans le nom de la maladie)
    for id_culture, culture_nom in cultures:
        for id_parasite, maladie_nom in maladies:
            # Si le nom de la culture apparaît dans le nom de la maladie
            if culture_nom.lower() in maladie_nom.lower():
                try:
                    cursor.execute('''
                    INSERT INTO affecter (id_culture, id_parasite)
                    VALUES (?, ?)
                    ''', (id_culture, id_parasite))
                    count += 1
                except sqlite3.IntegrityError:
                    pass  # Ignorer les doublons
    
    conn.commit()
    conn.close()
    print(f"✅ {count} relations culture-maladie créées")
    
    return count

def import_conseils(csv_path):
    """Importe les conseils pratiques"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Lire le CSV
    df = pd.read_csv(csv_path)
    
    # Récupérer toutes les cultures dans l'ordre
    cursor.execute("SELECT id_culture, nom FROM Cultures ORDER BY id_culture")
    cultures = cursor.fetchall()
    
    count = 0
    # Associer chaque ligne du CSV à une culture (ligne 1 -> culture 1, ligne 2 -> culture 2, etc.)
    for idx, row in df.iterrows():
        if idx < len(cultures):
            culture_id = cultures[idx][0]  # Prendre l'ID de la culture correspondante
            
            cursor.execute('''
            INSERT INTO conseils_pratiques (id_culture, bonnes_pratique)
            VALUES (?, ?)
            ''', (culture_id, row['bonnes_pratiques']))
            count += 1
        else:
            print(f"⚠️  Ligne {idx+1} du CSV conseils ignorée (pas de culture correspondante)")
    
    conn.commit()
    conn.close()
    print(f"✅ {count} conseils pratiques importés")
    
    return count

def display_stats():
    """Affiche les statistiques de la base de données"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("  STATISTIQUES DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    tables = ['Region', 'Cultures', 'calendrier_cultural', 
              'maladies_parasites', 'affecter', 'conseils_pratiques']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  • {table:.<40} {count:>5} enregistrements")
    
    conn.close()

def main():
    """Fonction principale d'insertion"""
    print("=" * 60)
    print("  SCRIPT 2 - INSERTION DES DONNÉES")
    print("=" * 60)
    print()
    
    # Vérifier que la base existe
    if not check_database():
        return
    
    print("🚀 Début de l'import des données...\n")
    
    try:
        # 1. Régions (pas de dépendances)
        csv_file = f'{CSV_FOLDER}/region.csv'
        if os.path.exists(csv_file):
            import_regions(csv_file)
        else:
            print(f"⚠️  Fichier non trouvé: {csv_file}")
        
        # 2. Cultures (pas de dépendances)
        csv_file = f'{CSV_FOLDER}/cultures.csv'
        if os.path.exists(csv_file):
            import_cultures(csv_file)
        else:
            print(f"⚠️  Fichier non trouvé: {csv_file}")
        
        # 3. Maladies (pas de dépendances)
        csv_file = f'{CSV_FOLDER}/maladies.csv'
        if os.path.exists(csv_file):
            import_maladies(csv_file)
        else:
            print(f"⚠️  Fichier non trouvé: {csv_file}")
        
        # 4. Calendrier (dépend de Cultures et Region)
        csv_file = f'{CSV_FOLDER}/calendrier.csv'
        if os.path.exists(csv_file):
            import_calendrier(csv_file)
        else:
            print(f"⚠️  Fichier non trouvé: {csv_file}")
        
        # 5. Table de liaison culture-maladie
        create_affecter_table()
        
        # 6. Conseils (dépend de Cultures)
        csv_file = f'{CSV_FOLDER}/conseils.csv'
        if os.path.exists(csv_file):
            import_conseils(csv_file)
        else:
            print(f"⚠️  Fichier non trouvé: {csv_file}")
        
        # Afficher les statistiques
        display_stats()
        
        print("\n🎉 Import terminé avec succès!")
        print(f"📁 Base de données: {DB_NAME}")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'import: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()