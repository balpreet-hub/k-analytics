import pandas as pd
import os
import streamlit as st

def load_scouting_data():
    """
    Charge les données brutes matchs (CSV) et les agrège par joueur.
    Transforme les logs de matchs en statistiques de scouting.
    """
    csv_path = os.path.join("data", "données 2025.csv")

    if not os.path.exists(csv_path):
        st.error(f"⚠️ Fichier introuvable : {csv_path}")
        return pd.DataFrame()

    try:
        # 1. Chargement optimisé (on ne prend que les colonnes utiles)
        cols_needed = ['playername', 'position', 'league', 'result', 'kills', 'deaths', 'assists', 'datacompleteness']
        
        # Gestion des séparateurs (virgule ou point-virgule)
        try:
            df = pd.read_csv(csv_path, usecols=cols_needed)
        except:
            df = pd.read_csv(csv_path, sep=';', usecols=cols_needed)

        # 2. Filtrage
        # On garde uniquement les lignes complètes et on vire les lignes "team" (qui ne sont pas des joueurs)
        df = df[(df['datacompleteness'] == 'complete') & (df['position'] != 'team')]

        # 3. Agrégation Mathématique (Le coeur du moteur)
        # On regroupe toutes les games de chaque joueur
        stats = df.groupby(['playername', 'position', 'league']).agg(
            Games=('result', 'count'),          # Nombre de games jouées
            Wins=('result', 'sum'),             # Nombre de victoires
            Total_Kills=('kills', 'sum'),
            Total_Deaths=('deaths', 'sum'),
            Total_Assists=('assists', 'sum')
        ).reset_index()

        # 4. Création des Métriques Scouting
        # Winrate (ex: 0.65)
        stats['Winrate'] = round(stats['Wins'] / stats['Games'], 2)
        
        # KDA (Attention à la division par zéro si le joueur n'est jamais mort)
        stats['KDA'] = round((stats['Total_Kills'] + stats['Total_Assists']) / stats['Total_Deaths'].replace(0, 1), 2)

        # 5. Nettoyage Final pour l'Affichage
        # Mapping des rôles (jng -> Jungle, bot -> ADC...)
        role_map = {
            'top': 'Top', 
            'jng': 'Jungle', 
            'mid': 'Mid', 
            'bot': 'ADC', 
            'sup': 'Support'
        }
        stats['position'] = stats['position'].map(role_map).fillna(stats['position'])

        # Renommage des colonnes pour correspondre à ton application
        final_df = stats.rename(columns={
            'playername': 'Player',
            'position': 'Role',
            'league': 'Region'
        })

        # On retourne uniquement les colonnes propres
        return final_df[['Player', 'Role', 'Region', 'Games', 'Winrate', 'KDA']]

    except Exception as e:
        st.error(f"❌ Erreur critique lors de l'agrégation des données : {e}")
        return pd.DataFrame()