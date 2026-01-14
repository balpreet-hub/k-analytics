import streamlit as st
import pandas as pd
import plotly.express as px
from services.data_factory import load_scouting_data

# --- 1. CONFIGURATION (DOIT ETRE EN PREMIER) ---
st.set_page_config(page_title="Market Analysis", page_icon="📊", layout="wide")

st.title("📊 Market Analysis & Arbitrage")
st.markdown("### Détection des actifs sous-évalués (Moneyball Approach)")

# --- 2. CHARGEMENT DES DONNÉES ---
df = load_scouting_data()

if df.empty:
    st.error("❌ Données introuvables. Vérifie ton chargement.")
    st.stop()

# --- 3. SIDEBAR INTELLIGENTE ---
st.sidebar.header("🔍 Market Filters")

# Filtre A : Rôle
selected_role = st.sidebar.selectbox(
    "Filtrer par Rôle", 
    ["Tous"] + list(df['Role'].unique())
)

# Filtre B : Régions (Nouveau)
all_regions = df['Region'].unique().tolist()
selected_regions = st.sidebar.multiselect(
    "Filtrer par Région", 
    all_regions, 
    default=all_regions, # Tout sélectionné par défaut
    placeholder="Choisis tes ligues..."
)

# Filtre C : Expérience
min_games = st.sidebar.slider("Minimum de games jouées", 5, 100, 20)

# --- 4. MOTEUR DE FILTRAGE ---
# On filtre d'abord par Games, puis par Rôle, puis par Région
df_market = df[
    (df['Games'] >= min_games) & 
    (df['Region'].isin(selected_regions))
].copy()

if selected_role != "Tous":
    df_market = df_market[df_market['Role'] == selected_role]

if df_market.empty:
    st.warning("⚠️ Aucun joueur ne correspond à ces critères.")
    st.stop()

# --- 5. CALCUL DU BENCHMARK (MOYENNES) ---
avg_winrate = df_market['Winrate'].mean()
avg_kda = df_market['KDA'].mean()

# --- 6. INTERFACE PRINCIPALE ---
col_main, col_kpi = st.columns([3, 1])

with col_main:
    st.subheader(f"Matrice de Performance - {selected_role}")
    
    # Création du Graphique Avancé
    fig = px.scatter(
        df_market,
        x="KDA",
        y="Winrate",
        color="Region",                # Code couleur par ligue
        size="Games",                  # Taille = Expérience
        hover_name="Player",           # Nom en gras au survol
        hover_data={
            "Role": True, 
            "Games": True, 
            "KDA": ":.2f", 
            "Winrate": ":.1%"
        },
        title=f"Efficiency Matrix ({len(df_market)} joueurs)",
        template="plotly_dark",
        opacity=0.8
    )

    # Ajout des lignes moyennes (Quadrants)
    fig.add_hline(y=avg_winrate, line_dash="dash", line_color="white", opacity=0.5, annotation_text="Avg Winrate")
    fig.add_vline(x=avg_kda, line_dash="dash", line_color="white", opacity=0.5, annotation_text="Avg KDA")

    # CUSTOMISATION UX (Ce que tu as demandé)
    fig.update_traces(
        marker=dict(line=dict(width=1, color='White')), # Bordure blanche pour lisibilité
        selector=dict(mode='markers')
    )
    
    fig.update_layout(
        height=650,
        xaxis_title="Performance Individuelle (KDA)",
        yaxis_title="Performance d'Équipe (Winrate)",
        dragmode='pan', # <--- PERMET DE BOUGER AVEC LE CLIC GAUCHE (Standard Map)
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Activation du Scroll pour Zoomer
    st.plotly_chart(
        fig, 
        use_container_width=True, 
        config={'scrollZoom': True, 'displayModeBar': True} # <--- LA CLE DU ZOOM
    )

# --- 6. INTERFACE PRINCIPALE ---
col_main, col_kpi = st.columns([3, 1])

with col_kpi:
    st.subheader("🎯 Stratégie de Scouting")
    
    # SÉLECTEUR DE MODE : C'est ici que tout change
    scouting_mode = st.radio(
        "Quel type de joueur cherches-tu ?",
        ["💎 Vétérans Sous-cotés", "🔥 Futures Pépites (Rookies)"],
        captions=["Bonnes stats, mauvaise équipe", "Peu d'expérience, stats explosives"]
    )
    
    st.divider()

    # LOGIQUE 1 : MONEYBALL (Vétérans solides dans mauvaises équipes)
    if scouting_mode == "💎 Vétérans Sous-cotés":
        st.markdown("##### 📉 Cibles : 'Unfair Loss'")
        st.caption("Joueurs avec un KDA supérieur à la moyenne, mais un Winrate inférieur.")
        
        opportunities = df_market[
            (df_market['KDA'] > avg_kda) & 
            (df_market['Winrate'] < avg_winrate)
        ].copy()
        
        # On trie par l'écart de KDA (le plus injustement traité)
        opportunities['Score'] = opportunities['KDA'] - avg_kda

    # LOGIQUE 2 : ROOKIE RADAR (Haut potentiel, faible volume)
    else:
        st.markdown("##### 🚀 Cibles : 'High Potential'")
        st.caption("Joueurs avec moins de 50 games (Rookies) mais des stats dominantes.")
        
        # On définit un "Rookie" comme quelqu'un qui a PEU de games dans le dataset filtré
        # On prend les joueurs qui ont moins de 60 games (ajustable)
        rookie_cap = 60
        
        opportunities = df_market[
            (df_market['Games'] <= rookie_cap) &    # C'est un nouveau
            (df_market['KDA'] > avg_kda * 1.1) &    # 10% meilleur que la moyenne mécanique
            (df_market['Winrate'] > 0.5)            # Il gagne quand même (mentalité winner)
        ].copy()
        
        # Pour les rookies, on veut un mix de KDA explosif et de Winrate
        opportunities['Score'] = (opportunities['KDA'] * 2) + (opportunities['Winrate'] * 10)

    # --- AFFICHAGE DES CARTES JOUEURS ---
    opportunities = opportunities.sort_values(by='Score', ascending=False)
    
    if not opportunities.empty:
        for i, row in opportunities.head(5).iterrows():
            # Couleur dynamique selon le mode
            card_color = "orange" if scouting_mode == "🔥 Futures Pépites (Rookies)" else "blue"
            
            with st.container():
                st.markdown(f"""
                <div style="
                    padding: 10px; 
                    border-radius: 8px; 
                    border-left: 5px solid {card_color};
                    background-color: #262730;
                    margin-bottom: 10px;">
                    <strong>{row['Player']}</strong> <span style="color:gray; font-size:0.8em;">({row['Region']})</span><br>
                    <span style="font-size:0.9em;">🗡️ KDA: {row['KDA']:.2f} | 🏆 WR: {row['Winrate']*100:.0f}%</span><br>
                    <span style="font-size:0.8em; color: #aaa;">🕹️ {row['Games']} games</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Aucun profil ne correspond à cette recherche.")

# --- LA PARTIE GRAPHIQUE (COLONNE GAUCHE) ---
with col_main:
    st.subheader(f"Analyse de Marché : {scouting_mode}")
    
    # On adapte le titre du graph selon le mode
    graph_title = "Matrice d'Inefficacité" if "Vétérans" in scouting_mode else "Radar à Rookies"
    
    fig = px.scatter(
        df_market,
        x="KDA",
        y="Winrate",
        color="Region",
        size="Games",
        hover_name="Player",
        hover_data={"Role": True, "Games": True, "KDA": ":.2f", "Winrate": ":.1%"},
        title=graph_title,
        template="plotly_dark",
        opacity=0.7
    )

    # Quadrants
    fig.add_hline(y=avg_winrate, line_dash="dash", line_color="white", opacity=0.3)
    fig.add_vline(x=avg_kda, line_dash="dash", line_color="white", opacity=0.3)
    
    # Si on est en mode "Pépites", on met en évidence la zone "High KDA / Low Games"
    # C'est visuel seulement, mais ça aide à comprendre
    
    fig.update_traces(marker=dict(line=dict(width=1, color='White')))
    fig.update_layout(
        height=650,
        xaxis_title="KDA (Mécanique)",
        yaxis_title="Winrate (Impact)",
        dragmode='pan',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

# --- 7. DONNÉES BRUTES ---
with st.expander("📂 Voir les données du segment"):
    st.dataframe(
        df_market[['Player', 'Role', 'Region', 'Games', 'Winrate', 'KDA']], 
        use_container_width=True,
        hide_index=True
    )