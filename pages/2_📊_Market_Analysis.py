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

with col_kpi:
    st.subheader("🎯 Opportunités")
    st.caption("Joueurs 'Sous-cotés' (KDA > Avg mais Winrate < Avg)")
    
    # Logique d'Arbitrage Moneyball
    undervalued = df_market[
        (df_market['KDA'] > avg_kda) & 
        (df_market['Winrate'] < avg_winrate)
    ].copy()
    
    # Score d'arbitrage : Plus le KDA est haut par rapport à la moyenne, plus c'est intéressant
    undervalued['Gap'] = undervalued['KDA'] - avg_kda
    undervalued = undervalued.sort_values(by='Gap', ascending=False)
    
    if not undervalued.empty:
        for i, row in undervalued.head(4).iterrows():
            st.warning(
                f"💎 **{row['Player']}**\n\n"
                f"Region: {row['Region']}\n"
                f"KDA: {row['KDA']:.2f} (+{row['Gap']:.1f})\n"
                f"WR: {row['Winrate']*100:.0f}%"
            )
    else:
        st.success("Le marché est efficient. Pas d'anomalies détectées.")

    st.divider()
    st.metric("KDA Moyen", f"{avg_kda:.2f}")
    st.metric("Winrate Moyen", f"{avg_winrate*100:.1f}%")

# --- 7. DONNÉES BRUTES ---
with st.expander("📂 Voir les données du segment"):
    st.dataframe(
        df_market[['Player', 'Role', 'Region', 'Games', 'Winrate', 'KDA']], 
        use_container_width=True,
        hide_index=True
    )