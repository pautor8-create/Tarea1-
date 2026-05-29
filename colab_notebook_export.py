import pandas as pd
import numpy as np

def cuestionario_wellness():
    print("--- CUESTIONARIO DIARIO DE WELLNESS (1-5) ---")
    print("(1 = Muy Mal / 5 = Excelente)")

    try:
        sueno = int(input("Calidad del sueño: "))
        dolor = int(input("Dolor muscular (1=Mucho dolor, 5=Nada): "))
        estres = int(input("Nivel de estrés (1=Muy estresado, 5=Relajado): "))
        fatiga = int(input("Fatiga general (1=Muy fatigado, 5=Fresco): "))

        score_subjetivo = (sueno + dolor + estres + fatiga) / 4
        return {"wellness_score": score_subjetivo, "raw": [sueno, dolor, estres, fatiga]}
    except ValueError:
        print("Por favor, introduce números del 1 al 5.")
        return None

# Simulación de respuesta
# wellness_hoy = cuestionario_wellness()


def calcular_readiness(rmssd_hoy, historial_rmssd, wellness_score):
    """
    Calcula el semáforo de readiness basado en rMSSD y Baseline (Media Móvil 7d).
    """
    baseline = np.mean(historial_rmssd[-7:]) if len(historial_rmssd) > 0 else rmssd_hoy
    std_dev = np.std(historial_rmssd[-7:]) if len(historial_rmssd) > 1 else 5

    # Lógica de Semáforo (Basada en Desviación Estándar de la Baseline)
    if rmssd_hoy >= (baseline - 0.5 * std_dev) and wellness_score >= 3.5:
        status = "🟢 VERDE: Entrenamiento de alta carga permitido."
        color = "green"
    elif rmssd_hoy >= (baseline - 1.5 * std_dev) or wellness_score >= 2.5:
        status = "🟡 AMARILLO: Carga moderada. Evitar records personales o fatiga extrema."
        color = "yellow"
    else:
        status = "🔴 ROJO: Recuperación prioritaria. Sesión de movilidad o descanso."
        color = "red"

    return {"status": status, "baseline": round(baseline, 2), "actual": rmssd_hoy, "color": color}

# Datos de ejemplo (Simulando un historial de Oura/Whoop)
historial_ejemplo = [60, 58, 60, 52, 68, 59, 61]
rmssd_hoy = 72  # Una caída significativa
wellness_hoy = 3.0

resultado = calcular_readiness(rmssd_hoy, historial_ejemplo, wellness_hoy)
print(f"RESULTADO: {resultado['status']}")
print(f"Baseline: {resultado['baseline']} ms | Hoy: {resultado['actual']} ms")


import matplotlib.pyplot as plt
import numpy as np
import requests
import base64

# --- CONFIGURACIÓN ---
API_KEY = "1gmr9ks369iy8p4yj0jtbzm40".strip()
ATHLETE_ID = "i454731".strip()

def verificar_conexion():
    user_pass = f"API_KEY:{API_KEY}"
    encoded_u = base64.b64encode(user_pass.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_u}"}

    print(f"--- PROBANDO CONEXIÓN PARA ATLETA {ATHLETE_ID} ---")
    url = f"https://intervals.icu/api/v1/athlete/{ATHLETE_ID}/wellness"

    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            print("✅ ¡CONEXIÓN ESTABLECIDA EXITOSAMENTE!")
            return True
        elif r.status_code == 403:
            print(f"❌ ERROR 403: Acceso Denegado.")
            print("CONSEJO: Asegúrate de que 'Allowed IP addresses' esté VACÍO en Intervals.icu -> Settings.")
            return False
        else:
            print(f"❌ ERROR {r.status_code}: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Error de red: {e}")
        return False

# Ejecutar test
conectado = verificar_conexion()

# Visualización de Estado
plt.figure(figsize=(10, 2))
color_bg = '#27ae60' if conectado else '#c0392b'
texto = "SISTEMA SINCRONIZADO" if conectado else "ERROR DE ACCESO (403)"
plt.text(0.5, 0.5, texto, ha='center', va='center', fontsize=15, color='white', weight='bold',
         bbox=dict(facecolor=color_bg, alpha=1, boxstyle='round,pad=1'))
plt.axis('off')
plt.show()


import requests
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

def descargar_datos_reales():
    oldest = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    newest = datetime.now().strftime('%Y-%m-%d')

    user_pass = f"API_KEY:{API_KEY}"
    encoded_u = base64.b64encode(user_pass.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_u}"}

    url = f"https://intervals.icu/api/v1/athlete/{ATHLETE_ID}/wellness?oldest={oldest}&newest={newest}"

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        if not data:
            return None
        df = pd.DataFrame(data)
        if 'rmssd' not in df.columns:
            df['rmssd'] = np.nan
        df = df.sort_values('id')
        return df
    return None

# Ejecución
df_wellness = descargar_datos_reales()

# Verificar si hay datos válidos (distintos de cero o nulos)
tiene_datos = False
if df_wellness is not None:
    df_wellness['rmssd'] = pd.to_numeric(df_wellness['rmssd'], errors='coerce').fillna(0)
    if df_wellness['rmssd'].sum() > 0:
        tiene_datos = True

if tiene_datos:
    df_wellness['id'] = pd.to_datetime(df_wellness['id'])
    df_wellness['baseline'] = df_wellness['rmssd'].replace(0, np.nan).rolling(window=7, min_periods=1).mean()

    plt.figure(figsize=(12, 5))
    plt.plot(df_wellness['id'], df_wellness['rmssd'], marker='o', label='rMSSD Real', color='#3498db')
    plt.plot(df_wellness['id'], df_wellness['baseline'], label='Baseline (7d)', color='#e67e22', linestyle='--')
    plt.title("Tu variabilidad rMSSD (Datos Reales)")
    plt.legend()
    plt.show()
else:
    print("⚠️ CONEXIÓN OK, PERO NO HAY DATOS DE rMSSD.")
    print("Sincroniza tu app de salud con Intervals.icu o introduce un dato manual en la configuración.")
    plt.figure(figsize=(8, 2))
    plt.text(0.5, 0.5, "Esperando datos de HRV de Intervals.icu...", ha='center', va='center', style='italic')
    plt.axis('off')
    plt.show()


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

fechas = [datetime.now() - timedelta(days=i) for i in range(30)]
fechas.reverse()

np.random.seed(42)
rmssd_base = 60
ruido = np.random.normal(0, 5, 30)
fatiga = np.zeros(30)
fatiga[10:15] = -15

rmssd_simulado = rmssd_base + ruido + fatiga

df_sim = pd.DataFrame({'Fecha': fechas, 'rMSSD': rmssd_simulado})
df_sim['Baseline'] = df_sim['rMSSD'].rolling(window=7, min_periods=1).mean()

plt.figure(figsize=(14, 7))

std_sim = df_sim['rMSSD'].std()
plt.fill_between(df_sim['Fecha'],
                 df_sim['Baseline'] - 0.5 * std_sim,
                 df_sim['Baseline'] + 0.5 * std_sim,
                 color='green', alpha=0.1, label='Zona Óptima')

plt.plot(df_sim['Fecha'], df_sim['rMSSD'], marker='o', color='#2980b9',
         linewidth=2, markersize=8, label='rMSSD Diario (Simulado)')
plt.plot(df_sim['Fecha'], df_sim['Baseline'], color='#e67e22',
         linewidth=3, linestyle='--', label='Línea Base (7 días)')

plt.annotate('Pico de Fatiga',
             xy=(df_sim['Fecha'][12], df_sim['rMSSD'][12]),
             xytext=(df_sim['Fecha'][12], df_sim['rMSSD'][12]-15),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1),
             horizontalalignment='center')

plt.title("EJEMPLO VISUAL: Seguimiento de rMSSD y Recuperación", fontsize=16, fontweight='bold')
plt.ylabel("rMSSD (ms)", fontsize=12)
plt.xlabel("Últimos 30 días", fontsize=12)
plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.legend(loc='upper left')
plt.ylim(30, 80)
plt.tight_layout()
plt.show()


# Asegúrate de que df_sim (con datos simulados) se ha ejecutado en la celda anterior.
# Si no, ejecuta la celda que genera 'df_sim' primero (normalmente es la celda b8eb6b12).

# Extraer el rMSSD más reciente y el historial de rMSSD de los datos simulados
rmssd_hoy_simulado = df_sim['rMSSD'].iloc[-1] # Último valor simulado
historial_rmssd_simulado = df_sim['rMSSD'].iloc[:-1].tolist() # Todos los valores excepto el último

# Simulamos un wellness score, ya que no hemos ejecutado el cuestionario subjetivo
wellness_score_simulado = 4.0 # Asumimos un buen nivel de bienestar para la simulación

# Calcular el readiness usando los datos simulados
resultado_simulado = calcular_readiness(rmssd_hoy_simulado, historial_rmssd_simulado, wellness_score_simulado)

print("--- RESULTADO DE READINESS CON DATOS SIMULADOS ---")
print(f"RESULTADO: {resultado_simulado['status']}")
print(f"Baseline: {resultado_simulado['baseline']} ms | Hoy (simulado): {resultado_simulado['actual']} ms")
print(f"Color del semáforo: {resultado_simulado['color']}")


def determinar_color_semaforo(rmssd, baseline, std):
    if rmssd >= (baseline - 0.5 * std):
        return '#27ae60' # Verde
    elif rmssd >= (baseline - 1.5 * std):
        return '#f1c40f' # Amarillo
    else:
        return '#e74c3c' # Rojo

# Calcular desviación estándar de la simulación para la lógica
std_dev = df_sim['rMSSD'].std()

# Aplicar lógica a cada día
df_sim['Color'] = [determinar_color_semaforo(row['rMSSD'], row['Baseline'], std_dev)
                   for _, row in df_sim.iterrows()]

# Visualización de Semáforos
plt.figure(figsize=(14, 6))

# Dibujar la línea base
plt.plot(df_sim['Fecha'], df_sim['Baseline'], color='gray', linestyle='--', alpha=0.5, label='Línea Base')

# Dibujar cada punto con su color de semáforo correspondiente
for i in range(len(df_sim)):
    plt.scatter(df_sim['Fecha'].iloc[i], df_sim['rMSSD'].iloc[i],
                color=df_sim['Color'].iloc[i], s=100, edgecolors='black', zorder=3)

# Crear leyenda personalizada
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='Listo (Verde)', markerfacecolor='#27ae60', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Precaución (Amarillo)', markerfacecolor='#f1c40f', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Descanso (Rojo)', markerfacecolor='#e74c3c', markersize=10)
]

plt.title("SISTEMA DE SEMÁFOROS: Estado de Readiness Diario", fontsize=15, fontweight='bold')
plt.ylabel("rMSSD (ms)")
plt.legend(handles=legend_elements, loc='upper left')
plt.grid(True, alpha=0.2)
plt.tight_layout()
plt.show()


import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# 1. Visualización Unificada
plt.figure(figsize=(15, 7))

# Sombreado de la zona de confort (Baseline +/- margen)
plt.fill_between(df_sim['Fecha'],
                 df_sim['Baseline'] - 0.5 * std_sim,
                 df_sim['Baseline'] + 0.5 * std_sim,
                 color='gray', alpha=0.1, label='Rango Normal')

# Línea de tendencia
plt.plot(df_sim['Fecha'], df_sim['Baseline'], color='#e67e22', linewidth=2,
         linestyle='--', label='Línea Base (7d)', zorder=1)

# Línea de conexión de datos
plt.plot(df_sim['Fecha'], df_sim['rMSSD'], color='#bdc3c7', alpha=0.5, zorder=2)

# Puntos coloreados por estado de Readiness
for i in range(len(df_sim)):
    plt.scatter(df_sim['Fecha'].iloc[i], df_sim['rMSSD'].iloc[i],
                color=df_sim['Color'].iloc[i], s=120, edgecolors='black',
                linewidth=1, zorder=3)

# Configuración de estética (sin emojis para evitar errores de fuente)
plt.title("DASHBOARD INTEGRADO: Evolución rMSSD y Readiness", fontsize=16, fontweight='bold', pad=20)
plt.ylabel("rMSSD (ms)", fontsize=12)
plt.grid(True, linestyle=':', alpha=0.6)

# Leyenda personalizada
legend_elements = [
    Line2D([0], [0], color='#e67e22', linestyle='--', label='Línea Base'),
    Line2D([0], [0], marker='o', color='w', label='Verde (Ready)', markerfacecolor='#27ae60', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Amarillo (Precaución)', markerfacecolor='#f1c40f', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Rojo (Descanso)', markerfacecolor='#e74c3c', markersize=10)
]
plt.legend(handles=legend_elements, loc='upper left', frameon=True)

plt.tight_layout()
plt.show()


import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# 2. Cálculo de promedios por color de semáforo
color_map = {
    '#27ae60': 'Verde (Ready)',
    '#f1c40f': 'Amarillo (Precaución)',
    '#e74c3c': 'Rojo (Descanso)'
}

# Agregamos el nombre del estado al dataframe
df_sim['Estado'] = df_sim['Color'].map(color_map)

# Calculamos el promedio y cantidad de días
resumen_stats = df_sim.groupby('Estado')['rMSSD'].agg(['mean', 'count']).rename(columns={'mean': 'Promedio rMSSD', 'count': 'Días'})

print("--- ANÁLISIS DE RENDIMIENTO POR ESTADO ---")
display(resumen_stats.sort_values(by='Promedio rMSSD', ascending=False))


import os
from google.colab import files

# Definimos el contenido del archivo .py basado en tu dashboard
streamlit_code = """
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
            colores.append('#27ae60')
        elif desvio > -1.5 * std_sim:
            colores.append('#f1c40f')
        else:
            colores.append('#e74c3c')
    df['Color'] = colores
    return df, std_sim

df_sim, std_sim = generar_datos()

# 2. Sidebar para filtros
st.sidebar.header('Filtros')
estados = st.sidebar.multiselect('Filtrar Estado:', ['Verde (Ready)', 'Amarillo (Precaución)', 'Rojo (Descanso)'], default=['Verde (Ready)', 'Amarillo (Precaución)', 'Rojo (Descanso)'])

# 3. Métricas principales
last = df_sim.iloc[-1]
col1, col2, col3 = st.columns(3)
col1.metric('rMSSD Hoy', f"{last['rMSSD']} ms")
col2.metric('Baseline', f"{last['Baseline']} ms")
col3.metric('Estado', 'Ready' if last['Color'] == '#27ae60' else 'Atención')

# 4. Gráfico Matplotlib
fig, ax = plt.subplots(figsize=(12, 5))
ax.fill_between(df_sim['Fecha'], df_sim['Baseline'] - 0.5*std_sim, df_sim['Baseline'] + 0.5*std_sim, color='gray', alpha=0.1)
ax.plot(df_sim['Fecha'], df_sim['Baseline'], color='#e67e22', linestyle='--')
ax.plot(df_sim['Fecha'], df_sim['rMSSD'], color='#bdc3c7', alpha=0.5)
ax.scatter(df_sim['Fecha'], df_sim['rMSSD'], color=df_sim['Color'], s=100, edgecolors='black', zorder=3)

st.pyplot(fig)

# 5. Tabla de datos
st.subheader('Datos del periodo')
st.dataframe(df_sim.sort_values('Fecha', ascending=False))
"""

# Escribir el archivo
filename = "dashboard_readiness.py"
with open(filename, "w") as f:
    f.write(streamlit_code)

print(f"✅ Archivo {filename} generado.")

# Descargar automáticamente
files.download(filename)


import sys

# Instalamos Streamlit y pyngrok

print("¡Streamlit y pyngrok instalados!")


from pyngrok import ngrok
import subprocess
import os

# Solicitar el token de ngrok al usuario
print("Consigue tu token en: https://dashboard.ngrok.com/get-started/your-authtoken")
NGROK_AUTH_TOKEN = input("Pega aquí tu Authtoken de ngrok: ").strip()

# Configurar el token
ngrok.set_auth_token(NGROK_AUTH_TOKEN)

# Matar procesos previos
ngrok.kill()

try:
    # Iniciar túnel
    ngrok_tunnel = ngrok.connect(8501)
    print("\n✅ URL pública del Dashboard:", ngrok_tunnel.public_url)

    # Ejecutar Streamlit en segundo plano
    command = ["streamlit", "run", "dashboard_readiness.py", "--server.port", "8501", "--server.headless", "true"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("🚀 Streamlit dashboard iniciado con éxito.")
    print("Haz clic en el enlace de arriba para ver tu archivo .py en funcionamiento.")
except Exception as e:
    print(f"❌ Error al iniciar el túnel: {e}")


# Para detener el túnel ngrok y el proceso Streamlit si los iniciaste previamente en esta sesión.
# Descomenta las siguientes líneas y ejecuta esta celda si necesitas detenerlos explícitamente.

# from pyngrok import ngrok
# import subprocess

# ngrok.kill() # Mata todos los procesos de ngrok
# print("Todos los túneles ngrok han sido cerrados.")

# Si tienes una referencia al proceso de Streamlit, puedes terminarlo
# Por ejemplo, si lo guardaste en una variable 'process' como en la celda anterior
# if 'process' in locals() and process.poll() is None:
# #     process.terminate()
# #     print("Proceso de Streamlit terminado.")


import google.generativeai as genai
from google.colab import userdata
import PIL.Image
import os

# Intentar obtener la API KEY de los secretos de Colab
try:
    GOOGLE_API_KEY = userdata.get('GOOGLE_API_KEY')
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Usar la captura más reciente proporcionada
    img_path = '/content/Captura de pantalla 2026-05-16 122413.png'

    if os.path.exists(img_path):
        img = PIL.Image.open(img_path)
        prompt = """
        Analiza esta imagen de la configuración de Intervals.icu.
        Dime específicamente:
        1. ¿El campo 'Allowed IP addresses' tiene algún texto o está vacío? (Si tiene texto, esa es la causa del error 403).
        2. ¿Están marcados los permisos de 'Wellness' y 'Athlete:Read'?
        """
        response = model.generate_content([prompt, img])
        print("--- ANÁLISIS AUTOMÁTICO DE CONFIGURACIÓN ---")
        print(response.text)
    else:
        print("Archivo de imagen no encontrado. Por favor, asegúrate de que el nombre coincida.")

except Exception as e:
    print(f"⚠️ No se pudo realizar el análisis automático: {e}")
    print("\nPASOS MANUALES PARA SOLUCIONAR EL ERROR 403:")
    print("1. Entra en Intervals.icu -> Settings -> API Access.")
    print("2. BORRA cualquier IP que aparezca en 'Allowed IP addresses' (debe estar en blanco).")
    print("3. Verifica que la casilla 'Wellness' esté activa.")
