import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from services.data_factory import load_scouting_data
from models.wilson_score import calculate_wilson_lower_bound

# --- CONFIGURATION (Doit être la première commande Streamlit) ---
st.set_page_config(page_title="Scouting Network", page_icon="🌍", layout="wide")

# --- FONCTIONS UTILITAIRES (Le moteur du graphique) ---
def create_radar_chart(row_a, row_b=None):
    """
    Crée un radar chart comparatif.
    On normalise les échelles pour que le graphique soit lisible.
    """
    categories = ['Winrate', 'KDA', 'Games']
    
    # Normalisation :
    # Winrate est déjà entre 0 et 1 (ex: 0.55)
    # KDA est divisé par 10 (ex: 5.0 devient 0.5)
    # Games est divisé par 100 (ex: 50 devient 0.5)
    
    fig = go.Figure()

    # Joueur A (Bleu KC)
    fig.add_trace(go.Scatterpolar(
        r=[row_a['Winrate'], row_a['KDA']/10, row_a['Games']/100], 
        theta=categories,
        fill='toself',
        name=row_a['Player'],
        line_color='#1E90FF'
    ))

    # Joueur B (Rouge Adversaire)
    if row_b is not None:
        fig.add_trace(go.Scatterpolar(
            r=[row_b['Winrate'], row_b['KDA']/10, row_b['Games']/100],
            theta=categories,
            fill='toself',
            name=row_b['Player'],
            line_color='#FF4500'
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1] # Echelle fixe de 0 à 1 pour comparer équitablement
            )),
        showlegend=True,
        margin=dict(t=20, b=20, l=20, r=20),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )
    return fig

# --- MAIN PAGE (L'interface) ---
st.title("🌍 Global Scouting Network")

# 1. Chargement & Calculs
df = load_scouting_data()

if df.empty:
    st.error("⚠️ Aucune donnée disponible. Vérifie que 'données 2025.csv' est bien dans le dossier 'data'.")
    st.stop()

# Calcul de la Fiabilité (Wilson Score)
# On crée la colonne 'Fiabilité' ici
df['Fiabilité'] = df.apply(calculate_wilson_lower_bound, axis=1)
# Tri par défaut par fiabilité
df = df.sort_values(by="Fiabilité", ascending=False)

# 2. Interface Onglets
tab1, tab2, tab3 = st.tabs(["📂 Base de données", "📊 Fiabilité", "⚔️ Duel & Comparateur"])

# --- ONGLET 1 : BASE DE DONNEES (FILTRABLE & CORRIGÉE) ---
with tab1:
    st.markdown("### 🌍 Global Scouting Network")
    
    # --- ZONE DE FILTRES ---
    # On crée des colonnes pour aligner les filtres proprement
    col_filter_1, col_filter_2 = st.columns(2)
    
    with col_filter_1:
        # Filtre Rôle (Multiselection)
        roles_list = df['Role'].unique().tolist()
        selected_roles = st.multiselect("Filtrer par Rôle", roles_list, default=roles_list, placeholder="Choisis les rôles...")

    with col_filter_2:
        # Filtre Région (Multiselection)
        regions_list = df['Region'].unique().tolist()
        selected_regions = st.multiselect("Filtrer par Région", regions_list, default=regions_list, placeholder="Choisis les régions...")

    # --- APPLICATION DES FILTRES ---
    # On garde uniquement les lignes qui correspondent aux choix
    filtered_df = df[
        (df['Role'].isin(selected_roles)) & 
        (df['Region'].isin(selected_regions))
    ].copy() # .copy() est important pour éviter les avertissements pandas

    # --- CORRECTION DES POURCENTAGES ---
    # On multiplie par 100 pour passer de 0.97 à 97.0
    # C'est plus simple pour l'affichage que de se battre avec les formats
    filtered_df['Winrate_Pct'] = filtered_df['Winrate'] * 100
    filtered_df['Fiabilite_Pct'] = filtered_df['Fiabilité'] * 100

    # --- AFFICHAGE DU TABLEAU ---
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_order=["Player", "Role", "Region", "Games", "Winrate_Pct", "KDA", "Fiabilite_Pct"], # Ordre forcé des colonnes
        column_config={
            "Player": st.column_config.TextColumn("Joueur", width="medium"),
            "Role": st.column_config.TextColumn("Rôle", width="small"),
            "Region": st.column_config.TextColumn("Région", width="small"),
            "Games": st.column_config.NumberColumn("Games 🕹️", format="%d"),
            
            # WINRATE (Échelle 0-100)
            "Winrate_Pct": st.column_config.ProgressColumn(
                "Winrate 🏆",
                help="Pourcentage de victoires",
                format="%d%%", # Affiche 97%
                min_value=0,
                max_value=100,
            ),
            
            "KDA": st.column_config.NumberColumn("KDA ⚔️", format="%.2f"),
            
            # FIABILITÉ (Échelle 0-100)
            "Fiabilite_Pct": st.column_config.ProgressColumn(
                "Indice Confiance 🔒",
                format="%d%%", 
                min_value=0,
                max_value=100,
            ),
        },
        hide_index=True
    )
    
    # Petit indicateur du nombre de joueurs trouvés
    st.caption(f"{len(filtered_df)} joueurs trouvés correspondant aux critères.")

# --- ONGLET 2 : ANALYSE FIABILITÉ ---
with tab2:
    st.markdown("### 📊 Indice de Fiabilité (Risk-Adjusted)")
    st.info("ℹ️ Le score de fiabilité pénalise les joueurs avec peu de matchs (incertitude), même s'ils ont un gros Winrate.")
    
    # Création des données pour l'affichage (0-100)
    rel_df = df.copy()
    rel_df['Winrate_Pct'] = rel_df['Winrate'] * 100
    rel_df['Fiabilite_Pct'] = rel_df['Fiabilité'] * 100

    st.dataframe(
        rel_df[['Player', 'Region', 'Games', 'Winrate_Pct', 'Fiabilite_Pct']],
        use_container_width=True,
        column_config={
            "Player": st.column_config.TextColumn("Joueur"),
            "Region": st.column_config.TextColumn("Région"),
            "Games": st.column_config.NumberColumn("Games", format="%d"),
            
            # WINRATE (Barre visuelle)
            "Winrate_Pct": st.column_config.ProgressColumn(
                "Winrate", 
                format="%d%%", 
                min_value=0, 
                max_value=100
            ),
            
            # FIABILITÉ (Barre visuelle)
            "Fiabilite_Pct": st.column_config.ProgressColumn(
                "Score Fiabilité 🔒", 
                help="Indice de confiance statistique (Wilson Score)",
                min_value=0, 
                max_value=100, 
                format="%d%%" 
            ),
        },
        hide_index=True
    )

# --- ONGLET 3 : COMPARATEUR (DUEL) ---
with tab3:
    st.markdown("### ⚔️ Comparateur Head-to-Head")
    
    col_search_1, col_search_2 = st.columns(2)
    
    # Création de la liste de recherche
    search_list = df['Player'] + " (" + df['Role'] + ")"
    
    with col_search_1:
        st.info("🔵 Joueur Principal (KC Focus)")
        choice_1 = st.selectbox("Rechercher Joueur 1", search_list, index=0)
        name_1 = choice_1.split(" (")[0]
        row_1 = df[df['Player'] == name_1].iloc[0]
        
        # KPI Cards
        c1, c2, c3 = st.columns(3)
        c1.metric("Winrate", f"{row_1['Winrate']*100:.0f}%")
        c2.metric("KDA", f"{row_1['KDA']:.2f}")
        c3.metric("Games", row_1['Games'])

    with col_search_2:
        st.warning("🔴 Adversaire (Cible)")
        # Sélection intelligente (prend le 2ème de la liste par défaut)
        idx_2 = 1 if len(search_list) > 1 else 0
        choice_2 = st.selectbox("Rechercher Joueur 2", search_list, index=idx_2)
        name_2 = choice_2.split(" (")[0]
        row_2 = df[df['Player'] == name_2].iloc[0]
        
        # KPI Cards avec Delta (Code couleur automatique vert/rouge)
        c1, c2, c3 = st.columns(3)
        c1.metric("Winrate", f"{row_2['Winrate']*100:.0f}%", delta=f"{(row_2['Winrate']-row_1['Winrate'])*100:.1f}%")
        c2.metric("KDA", f"{row_2['KDA']:.2f}", delta=f"{row_2['KDA']-row_1['KDA']:.2f}")
        c3.metric("Games", row_2['Games'], delta=f"{row_2['Games']-row_1['Games']}")

    st.divider()
    
    # Zone Graphique et Données
    col_graph, col_data = st.columns([2, 1])
    
    with col_graph:
        st.subheader("Visualisation Radar")
        # On suppose que ta fonction create_radar_chart existe toujours plus haut
        try:
            fig = create_radar_chart(row_1, row_2)
            st.plotly_chart(fig, use_container_width=True)
        except NameError:
            st.error("La fonction 'create_radar_chart' n'est pas définie.")
        st.caption("*Les échelles sont normalisées sur les maximums de la base de données.")

    with col_data:
        st.subheader("Détails Comparatifs")
        
        # Préparation propre des données pour l'affichage transposé
        # On formate les valeurs EN STRING ici car c'est dur de configurer un tableau transposé
        comp_data = [
            {
                "Métadonnée": "Winrate", 
                row_1['Player']: f"{row_1['Winrate']*100:.1f}%", 
                row_2['Player']: f"{row_2['Winrate']*100:.1f}%"
            },
            {
                "Métadonnée": "KDA", 
                row_1['Player']: f"{row_1['KDA']:.2f}", 
                row_2['Player']: f"{row_2['KDA']:.2f}"
            },
            {
                "Métadonnée": "Games", 
                row_1['Player']: row_1['Games'], 
                row_2['Player']: row_2['Games']
            },
            {
                "Métadonnée": "Fiabilité", 
                row_1['Player']: f"{row_1['Fiabilité']*100:.1f}%", 
                row_2['Player']: f"{row_2['Fiabilité']*100:.1f}%"
            }
        ]
        
        comp_df_clean = pd.DataFrame(comp_data)
        st.dataframe(comp_df_clean, hide_index=True, use_container_width=True)