import streamlit as st

st.title("2 📊 Market Analysis")

import streamlit as st
import pandas as pd
import plotly.express as px
from services.data_factory import load_scouting_data

st.set_page_config(page_title="Market Analysis", page_icon="📊", layout="wide")

st.title("📊 Market Analysis & Arbitrage")
st.markdown("### Détection des actifs sous-évalués (Moneyball Approach)")

# 1. Chargement des données
df = load_scouting_data()

if df.empty:
    st.error("Données introuvables.")
    st.stop()

# 2. Sidebar - Filtres de Marché
st.sidebar.header("🔍 Market Filters")
selected_role = st.sidebar.selectbox("Filtrer par Rôle", ["Tous"] + list(df['Role'].unique()))
min_games = st.sidebar.slider("Minimum de games jouées", 5, 50, 10)

# Filtrage
df_market = df[df['Games'] >= min_games].copy()
if selected_role != "Tous":
    df_market = df_market[df_market['Role'] == selected_role]

# 3. Calcul des Moyennes (Le "Benchmark" du marché)
avg_winrate = df_market['Winrate'].mean()
avg_kda = df_market['KDA'].mean()

# 4. Interface
col_main, col_kpi = st.columns([3, 1])

with col_main:
    st.subheader(f"Matrice de Performance - {selected_role}")
    
    # Création du Scatter Plot (Nuage de points)
    fig = px.scatter(
        df_market,
        x="KDA",
        y="Winrate",
        color="Region",        # Code couleur par ligue
        size="Games",          # La taille du point dépend de l'expérience
        hover_name="Player",   # Affiche le nom au survol
        hover_data=["Role", "Games"],
        text="Player",         # Affiche le nom sur le graph
        title=f"Efficiency Matrix ({selected_role})",
        template="plotly_dark"
    )

    # Ajout des lignes moyennes (Quadrants)
    fig.add_hline(y=avg_winrate, line_dash="dash", line_color="white", annotation_text="Avg Winrate")
    fig.add_vline(x=avg_kda, line_dash="dash", line_color="white", annotation_text="Avg KDA")

    # Personnalisation visuelle
    fig.update_traces(textposition='top center')
    fig.update_layout(
        height=600,
        xaxis_title="Performance Individuelle (KDA)",
        yaxis_title="Performance d'Équipe (Winrate)",
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col_kpi:
    st.subheader("🎯 Cibles Prioritaires")
    st.info("Joueurs 'Sous-cotés' (Haut KDA, Bas Winrate)")
    
    # Logique d'Arbitrage : KDA > Moyenne MAIS Winrate < Moyenne
    # On cherche l'écart (Spread) le plus grand
    undervalued = df_market[
        (df_market['KDA'] > avg_kda) & 
        (df_market['Winrate'] < avg_winrate)
    ].copy()
    
    # On calcule un score d'injustice : (KDA - Avg) + (Avg - Winrate)
    # C'est purement heuristique pour le tri
    undervalued['Arbitrage_Score'] = (undervalued['KDA'] - avg_kda)
    undervalued = undervalued.sort_values(by='Arbitrage_Score', ascending=False)
    
    if not undervalued.empty:
        for i, row in undervalued.head(5).iterrows():
            st.warning(f"💎 **{row['Player']}** ({row['Region']})\n\nKDA: {row['KDA']} | WR: {row['Winrate']*100:.0f}%")
    else:
        st.write("Aucun joueur sous-évalué détecté dans ce segment.")

    st.divider()
    st.metric("Prix Moyen du Marché (KDA)", f"{avg_kda:.2f}")
    st.metric("Winrate Moyen", f"{avg_winrate*100:.1f}%")

# 5. Tableau Détaillé
with st.expander("Voir les données brutes du marché"):
    st.dataframe(df_market.sort_values(by="KDA", ascending=False), use_container_width=True)