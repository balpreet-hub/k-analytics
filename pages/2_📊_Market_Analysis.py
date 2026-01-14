# --- 6. INTERFACE PRINCIPALE (CORRIGÉE & ÉTENDUE) ---
col_main, col_kpi = st.columns([3, 1])

with col_kpi:
    st.subheader("🎯 Stratégie de Scouting")
    
    scouting_mode = st.radio(
        "Profil recherché :",
        [
            "💎 Vétérans Sous-cotés", 
            "🔥 Futures Pépites (Rookies)",
            "🎲 Reckless Bets (High Risk)"  # <--- NOUVEAU
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

# --- LA PARTIE GRAPHIQUE ---
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
    fig.add_hline(y=avg_winrate, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=avg_kda, line_dash="dash", line_color="gray", opacity=0.5)

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