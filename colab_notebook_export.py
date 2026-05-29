import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Configuración de la página
st.set_page_config(page_title='Dashboard de Carga Interna', layout='wide')

st.title('⚽ Dashboard de Rendimiento: Monitorización de Carga Interna')

# 1. Función de datos simulados optimizada para los 3 atletas
@st.cache_data
def generar_datos_atletas():
    np.random.seed(44)
    fechas = pd.date_range(end=pd.Timestamp.now(), periods=30)
    atletas = ["Pau", "Rafa", "Nordin"]
    lista_df = []
    
    for atleta in atletas:
        if atleta == "Pau":
            media, desviacion = 65, 6  # Pau hoy estará recuperado (Verde)
        elif atleta == "Rafa":
            media, desviacion = 70, 8  # Rafa hoy estará en el límite (Amarillo)
        else:
            media, desviacion = 64, 7  # Nordin hoy tendrá una caída fuerte (Rojo)
            
        rmssd = np.random.normal(loc=media, scale=desviacion, size=30).round(1)
        
        # Forzamos los datos del último día (Hoy) para clavar el ejemplo analítico
        if atleta == "Pau": rmssd[-1] = 71.0       
        elif atleta == "Rafa": rmssd[-1] = 62.0     
        elif atleta == "Nordin": rmssd[-1] = 46.0   
            
        df = pd.DataFrame({'Fecha': fechas, 'Atleta': atleta, 'rMSSD': rmssd})
        df['Baseline'] = df['rMSSD'].rolling(window=7, min_periods=1).mean().round(1)
        std_atleta = df['rMSSD'].std()
        
        colores = []
        desvios_pct = []
        for idx, row in df.iterrows():
            desvio_absoluto = row['rMSSD'] - row['Baseline']
            pct = (desvio_absoluto / row['Baseline']) * 100
            desvios_pct.append(round(pct, 1))
            
            if desvio_absoluto > -0.5 * std_atleta:
                colores.append('#27ae60') # Verde
            elif desvio_absoluto > -1.5 * std_atleta:
                colores.append('#f1c40f') # Amarillo
            else:
                colores.append('#e74c3c') # Rojo
                
        df['Color'] = colores
        df['Desvio_Pct'] = desvios_pct
        lista_df.append(df)
        
    return pd.concat(lista_df)

df_todos = generar_datos_atletas()

# CREACIÓN DE PESTAÑAS
tab1, tab2 = st.tabs(["👤 Análisis Individual", "👥 Vista de Equipo (Comparador)"])

# ==========================================
# PESTAÑA 1: ANÁLISIS INDIVIDUAL
# ==========================================
with tab1:
    st.sidebar.header('🎛️ Filtros Individuales')
    atleta_seleccionado = st.sidebar.selectbox('Selecciona el Atleta:', options=df_todos['Atleta'].unique(), key='sb_atleta')
    
    df_atleta = df_todos[df_todos['Atleta'] == atleta_seleccionado]
    std_sim = df_atleta['rMSSD'].std()
    last = df_atleta.iloc[-1]
    
    # Métricas superiores
    col1, col2, col3 = st.columns(3)
    col1.metric(f"rMSSD Hoy ({atleta_seleccionado})", f"{last['rMSSD']} ms")
    col2.metric("Línea Base (7d)", f"{last['Baseline']} ms")
    
    if last['Color'] == '#27ae60': estado_texto = "🟢 Verde (Ready)"
    elif last['Color'] == '#f1c40f': estado_texto = "🟡 Amarillo (Precaución)"
    else: estado_texto = "🔴 Rojo (Descanso)"
    col3.metric("Disposición Diaria", estado_texto)
    
    st.divider()
    
    # Gráfica temporal limpia sin bucles antiguos
    fig, ax = plt.subplots(figsize=(15, 5))
    ax.fill_between(df_atleta['Fecha'], df_atleta['Baseline'] - 0.5*std_sim, df_atleta['Baseline'] + 0.5*std_sim, color='gray', alpha=0.1, label='Rango Normal')
    ax.plot(df_atleta['Fecha'], df_atleta['Baseline'], color='#e67e22', linestyle='--', linewidth=2, label='Línea Base (7d)')
    ax.plot(df_atleta['Fecha'], df_atleta['rMSSD'], color='#bdc3c7', alpha=0.6, zorder=2)
    ax.scatter(df_atleta['Fecha'], df_atleta['rMSSD'], color=df_atleta['Color'], s=120, edgecolors='black', zorder=3)
    ax.set_title(f"EVOLUCIÓN TEMPORAL: {atleta_seleccionado.upper()}", fontsize=12, fontweight='bold')
    ax.set_ylabel("rMSSD (ms)")
    ax.grid(True, linestyle=':', alpha=0.6)
    
    legend_elements = [
        Line2D([0], [0], color='#e67e22', linestyle='--', label='Línea Base'),
        Line2D([0], [0], marker='o', color='w', label='Verde (Ready)', markerfacecolor='#27ae60', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Amarillo', markerfacecolor='#f1c40f', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Rojo (Descanso)', markerfacecolor='#e74c3c', markersize=10)
    ]
    ax.legend(handles=legend_elements, loc='upper left')
    st.pyplot(fig)

# ==========================================
# PESTAÑA 2: VISTA DE EQUIPO (EL COMPARADOR)
# ==========================================
with tab2:
    st.subheader("📊 Análisis Comparativo: Desviación de Carga Interna (Hoy)")
    st.markdown("Este gráfico muestra cuánto se desvía el rMSSD de hoy respecto a la media de cada jugador.")
    
    hoy_atletas = df_todos.groupby('Atleta').last().reset_index()
    
    fig_comp, ax_comp = plt.subplots(figsize=(12, 4))
    barras = ax_comp.barh(hoy_atletas['Atleta'], hoy_atletas['Desvio_Pct'], color=hoy_atletas['Color'], edgecolor='black', height=0.5)
    ax_comp.axvline(0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    
    for barra in barras:
        ancho = barra.get_width()
        pos_x = ancho + 0.5 if ancho >= 0 else ancho - 3.5
        ax_comp.text(pos_x, barra.get_y() + barra.get_height()/2, f"{ancho:+.1f}%", 
                     va='center', ha='left' if ancho >= 0 else 'right', fontweight='bold', fontsize=11)
    
    ax_comp.set_xlim(-40, 20)
    ax_comp.set_xlabel("Porcentaje de Desviación respecto a la Línea Base (%)")
    ax_comp.set_title("ESTADO DEL VESTUARIO: % VARIACIÓN rMSSD DIARIO", fontsize=12, fontweight='bold', pad=10)
    ax_comp.grid(True, axis='x', linestyle=':', alpha=0.5)
    ax_comp.invert_yaxis()
    st.pyplot(fig_comp)
    
    st.markdown("### 📋 Recomendación de Estado de Carga")
    c1, c2, c3 = st.columns(3)
    with c1: st.info("**Pau**\n\n🟢 **Ready** (+9.2%)\n\nApto para tareas de alta intensidad.")
    with c2: st.warning("**Rafa**\n\n🟡 **Precaución** (-11.4%)\n\nFatiga moderada. Regular volumen.")
    with c3: st.error("**Nordin**\n\n🔴 **Descanso** (-28.1%)\n\nCaída crítica. Riesgo alto. Sesión de recuperación.")
