import streamlit as st
import pandas as pd
import plotly.express as px
from services.data_factory import load_scouting_data

# --- 1. CONFIGURATION (DOIT ETRE EN PREMIER ABSOLUMENT) ---
st.set_page_config(page_title="Market Analysis", page_icon="📊", layout="wide")

st.title("📊 Market Analysis & Arbitrage")
st.markdown("### Détection des actifs sous-évalués (Moneyball Approach)")

# --- 2. CHARGEMENT DES DONNÉES ---
df = load_scouting_data()

if df.empty:
    st.error("❌ Données introuvables. Vérifie ton chargement.")
    st.stop()

# --- 3. SIDEBAR INTELLIGENTE (FILTRES) ---
st.sidebar.header("🔍 Market Filters")

# Filtre A : Rôle
selected_role = st.sidebar.selectbox(
    "Filtrer par Rôle", 
    ["Tous"] + list(df['Role'].unique())
)

# Filtre B : Régions
all_regions = df['Region'].unique().tolist()
selected_regions = st.sidebar.multiselect(
    "Filtrer par Région", 
    all_regions, 
    default=all_regions, 
    placeholder="Choisis tes ligues..."
)

# Filtre C : Expérience
min_games = st.sidebar.slider("Minimum de games jouées", 5, 100, 10)

# --- 4. MOTEUR DE FILTRAGE ---
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

# --- 6. INTERFACE PRINCIPALE (COLONNES) ---
col_main, col_kpi = st.columns([3, 1])

# --- 6A. COLONNE DE DROITE : STRATÉGIE & CARTES ---
with col_kpi:
    st.subheader("🎯 Stratégie de Scouting")
    
    scouting_mode = st.radio(
        "Profil recherché :",
        [
            "💎 Vétérans Sous-cotés", 
            "🔥 Futures Pépites (Rookies)",
            "🎲 Reckless Bets (High Risk)"
        ],
        captions=[
            "Solides mais perdants (Moneyball)", 
            "Jeunes talents (Volume moyen)",
            "Échantillon faible, Stats divines"
        ]
    )
    
    st.divider()

    # --- MOTEUR DE DÉCISION ---
    
    # 1. MONEYBALL (Le choix rationnel)
    if "Vétérans" in scouting_mode:
        st.info("📉 **Logique :** On cherche l'anomalie de marché. Le joueur performe (KDA) mais l'équipe coule.")
        opportunities = df_market[
            (df_market['KDA'] > avg_kda) & 
            (df_market['Winrate'] < avg_winrate)
        ].copy()
        opportunities['Score'] = opportunities['KDA'] - avg_kda

    # 2. ROOKIES (L'investissement long terme)
    elif "Rookies" in scouting_mode:
        st.info("🔥 **Logique :** On cherche la consistence sur un début de carrière.")
        rookie_cap = 50
        opportunities = df_market[
            (df_market['Games'] <= rookie_cap) &
            (df_market['Games'] > 20) &       # Il faut un minimum de preuves
            (df_market['KDA'] > avg_kda * 1.1)
        ].copy()
        opportunities['Score'] = (opportunities['KDA'] * 2) + (opportunities['Winrate'] * 5)

    # 3. RECKLESS (Le coup de poker)
    else:
        st.warning("⚠️ **Logique :** Danger. Moins de 20 games. Ça peut être un smurf, un sub chanceux, ou un dieu.")
        opportunities = df_market[
            (df_market['Games'] <= 20) &      # Très peu de games
            (df_market['Winrate'] >= 0.6) &   # Il écrase tout
            (df_market['KDA'] > avg_kda * 1.2)# Il ne meurt pas
        ].copy()
        # Ici le score c'est l'impact pur
        opportunities['Score'] = opportunities['Winrate'] * 100

    # --- AFFICHAGE DES CARTES ---
    opportunities = opportunities.sort_values(by='Score', ascending=False)
    
    if not opportunities.empty:
        st.write(f"**{len(opportunities)} profils détectés**")
        for i, row in opportunities.head(4).iterrows():
            
            # Code couleur sémantique
            if "Reckless" in scouting_mode:
                border_color = "#ff2b2b" # ROUGE (Danger)
                icon = "🎲"
            elif "Rookies" in scouting_mode:
                border_color = "#00ff00" # VERT (Espoir)
                icon = "🌱"
            else:
                border_color = "#00aaff" # BLEU (Kale)
                icon = "💎"

            st.markdown(f"""
            <div style="
                padding: 12px; 
                border-radius: 8px; 
                border-left: 5px solid {border_color};
                background-color: #1e1e1e;
                margin-bottom: 12px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
                <div style="display:flex; justify-content:space-between;">
                    <strong>{icon} {row['Player']}</strong>
                    <span style="color:#888; font-size:0.8em;">{row['Region']}</span>
                </div>
                <div style="margin-top:5px; font-size:0.9em;">
                    <span style="color:#ddd;">KDA:</span> <span style="color:#fff; font-weight:bold;">{row['KDA']:.2f}</span> | 
                    <span style="color:#ddd;">WR:</span> <span style="color:#fff; font-weight:bold;">{row['Winrate']*100:.0f}%</span>
                </div>
                <div style="margin-top:5px; font-size:0.75em; color:#aaa; font-style:italic;">
                    Vol: {row['Games']} games
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("🚫 Le marché est sec. Aucun profil ne correspond.")

# --- 6B. COLONNE DE GAUCHE : GRAPHIQUE ---
with col_main:
    # Titre dynamique
    title_map = {
        "💎 Vétérans Sous-cotés": "Matrice d'Inefficacité (Veterans)",
        "🔥 Futures Pépites (Rookies)": "Radar de Croissance (Rookies)",
        "🎲 Reckless Bets (High Risk)": "Zone de Volatilité (Reckless)"
    }
    
    current_title = title_map.get(scouting_mode, "Analyse")
    st.subheader(f"📊 {current_title}")
    
    fig = px.scatter(
        df_market,
        x="KDA",
        y="Winrate",
        color="Region",
        size="Games",
        hover_name="Player",
        hover_data={"Role": True, "Games": True, "KDA": ":.2f", "Winrate": ":.1%"},
        title=f"Mapping : {len(df_market)} Joueurs",
        template="plotly_dark",
        opacity=0.7
    )

    # Quadrants de référence
    fig.add_hline(y=avg_winrate, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="Moy. Winrate")
    fig.add_vline(x=avg_kda, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="Moy. KDA")

    # Zone de Danger (Reckless)
    if "Reckless" in scouting_mode:
        fig.add_shape(type="rect",
            x0=avg_kda*1.2, y0=0.6, x1=df_market['KDA'].max()*1.1, y1=1.0,
            line=dict(color="Red", width=2, dash="dot"),
            fillcolor="rgba(255, 0, 0, 0.1)"
        )

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