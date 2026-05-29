import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Configuración de la página
st.set_page_config(page_title='Dashboard de Readiness & rMSSD', layout='wide')

st.title('📈 Dashboard de Rendimiento: Evolución rMSSD y Readiness')

# 1. Función para generar datos (usando tu lógica de simulación)
def generar_datos():
    fechas = pd.date_range(end=pd.Timestamp.now(), periods=30)
    np.random.seed(42)
    rmssd = np.random.normal(loc=60, scale=8, size=30).round(1)
    
    df = pd.DataFrame({'Fecha': fechas, 'rMSSD': rmssd})
    df['Baseline'] = df['rMSSD'].rolling(window=7, min_periods=1).mean().round(1)
    std_sim = df['rMSSD'].std()
    
    colores = []
    for idx, row in df.iterrows():
        desvio = row['rMSSD'] - row['Baseline']
        if desvio > -0.5 * std_sim:
            colores.append('#27ae60') # Verde
        elif desvio > -1.5 * std_sim:
            colores.append('#f1c40f') # Amarillo
        else:
            colores.append('#e74c3c') # Rojo
    df['Color'] = colores
    return df, std_sim

df_sim, std_sim = generar_datos()

# 2. Sidebar para filtros
st.sidebar.header('Filtros')
estados = st.sidebar.multiselect('Filtrar Estado:', ['Verde (Ready)', 'Amarillo (Precaución)', 'Rojo (Descanso)'], default=['Verde (Ready)', 'Amarillo (Precaución)', 'Rojo (Descanso)'])

# Mapear la selección a los colores hexadecimales
mapa_colores = {
    'Verde (Ready)': '#27ae60',
    'Amarillo (Precaución)': '#f1c40f',
    'Rojo (Descanso)': '#e74c3c'
}
colores_filtrados = [mapa_colores[e] for e in estados]

# Filtrar el dataframe según la selección del usuario
df_filtrado = df_sim[df_sim['Color'].isin(colores_filtrados)]

# 3. Métricas principales mejoradas con los colores del semáforo (Emojis y lógica clara)
if not df_filtrado.empty:
    last = df_filtrado.iloc[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric('rMSSD Hoy', f"{last['rMSSD']} ms")
    col2.metric('Baseline (7d)', f"{last['Baseline']} ms")
    
    # Lógica del semáforo exacta para el estado actual
    if last['Color'] == '#27ae60':
        estado_texto = "🟢 Verde (Ready)"
    elif last['Color'] == '#f1c40f':
        estado_texto = "🟡 Amarillo (Precaución)"
    else:
        estado_texto = "🔴 Rojo (Descanso)"
        
    col3.metric('Estado Actual', estado_texto)

st.divider()

# 4. Gráfico Matplotlib optimizado (Como tu primera aplicación)
if not df_filtrado.empty:
    fig, ax = plt.subplots(figsize=(15, 6)) # Un poco más ancho para mejorar visualización
    
    # Sombreado de la zona de confort
    ax.fill_between(df_filtrado['Fecha'], df_filtrado['Baseline'] - 0.5*std_sim, df_filtrado['Baseline'] + 0.5*std_sim, color='gray', alpha=0.1, label='Rango Normal')
    
    # Línea base intermitente
    ax.plot(df_filtrado['Fecha'], df_filtrado['Baseline'], color='#e67e22', linestyle='--', linewidth=2, label='Línea Base (7d)')
    
    # Línea continua gris suave que une los puntos
    ax.plot(df_filtrado['Fecha'], df_filtrado['rMSSD'], color='#bdc3c7', alpha=0.6, zorder=2)
    
    # Puntos con los colores del semáforo exactos
    ax.scatter(df_filtrado['Fecha'], df_filtrado['rMSSD'], color=df_filtrado['Color'], s=120, edgecolors='black', linewidth=1, zorder=3)
    
    # Configuración de estética y rejilla limpia
    ax.set_title("DASHBOARD INTEGRADO: Evolución rMSSD y Readiness", fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel("rMSSD (ms)", fontsize=12)
    ax.grid(True, linestyle=':', alpha=0.6)

    # Leyenda personalizada idéntica a la otra app
    legend_elements = [
        Line2D([0], [0], color='#e67e22', linestyle='--', label='Línea Base'),
        Line2D([0], [0], marker='o', color='w', label='Verde (Ready)', markerfacecolor='#27ae60', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Amarillo (Precaución)', markerfacecolor='#f1c40f', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Rojo (Descanso)', markerfacecolor='#e74c3c', markersize=10)
    ]
    ax.legend(handles=legend_elements, loc='upper left', frameon=True)
    
    plt.tight_layout()
    st.pyplot(fig)
else:
    st.warning("Selecciona al menos un estado en los filtros laterales para mostrar los datos.")

# 5. Tabla de datos
st.subheader('Datos del periodo')
st.dataframe(df_filtrado.sort_values('Fecha', ascending=False), use_container_width=True)
