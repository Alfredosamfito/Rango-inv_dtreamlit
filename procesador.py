import streamlit as st
import pandas as pd
from io import StringIO

# Configurar título de la aplicación
st.title("_*Rendimiento* por :blue[RANGO]_")
st.subheader("Creado por :red[Alfredo Rubilar]", divider=True)
st.info(
    """
    Funcionamiento:\n
    1.- Cargue o arrastre INV FINAL que desee analizar.\n
    2.- Cuando cargue :green[*Vista previa del archivo*], presionar botón: "*Procesar Archivo*".\n
    3.- Seleccionar :blue[*Tag Inicial*] y :blue[*Tag Final*], presionar botón: :red[*"Filtrar Rango de Tag"*].\n
    4.- Opcional: presionar botón "Descargar Resultado" para bajar txt con datos.
    """
)
st.divider()
# Subir archivo
uploaded_file = st.file_uploader("*Cargar archivo INV FINAL (TXT):*", type=["txt"])

if uploaded_file is not None:
    # Leer el archivo y guardar en sesión para evitar reinicios
    if "archivo_cargado" not in st.session_state:
        st.session_state.archivo_cargado = uploaded_file.read().decode("utf-8")

    archivo_cargado = st.session_state.archivo_cargado

    st.success("Archivo cargado correctamente.")
    st.write("Vista previa del archivo:")
    st.text("\n".join(archivo_cargado.splitlines()[:10]))  # Muestra las primeras 10 líneas

    if st.button("Procesar archivo"):
        try:
            # Procesar archivo solo una vez y guardar en el estado
            if "df_procesado" not in st.session_state:
                filas = archivo_cargado.splitlines()
                filas_count = [fila for fila in filas if "Count" in fila]

                # Procesar filas y crear DataFrame
                data = []
                for fila in filas_count:
                    columnas = fila.split(",")
                    try:
                        unidades = int(columnas[5].lstrip("+-0") or 0)  # Limpia los signos y ceros iniciales
                        timestamp = pd.to_datetime(columnas[6], format="%m/%d/%Y %H:%M:%S")
                        operador = columnas[2]
                        tag = columnas[3]
                        data.append([operador, tag, unidades, timestamp])
                    except (IndexError, ValueError):
                        continue  # Ignorar filas mal formateadas

                df = pd.DataFrame(data, columns=["Operador", "TAG", "Unidades", "Timestamp"])

                if df.empty:
                    st.error("No se encontraron datos válidos en el archivo.")
                else:
                    st.session_state.df_procesado = df

            st.write("**Archivo procesado con éxito.**")
            st.write(st.session_state.df_procesado.head(10))  # Vista previa del DataFrame

        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

# Si ya se ha procesado el archivo
if "df_procesado" in st.session_state:
    df = st.session_state.df_procesado

    # Selección de TAG inicial y final
    tag_unicos = sorted(df["TAG"].unique())
    tag_inicial = st.selectbox("Selecciona TAG inicial:", tag_unicos, key="tag_inicial")
    tag_final = st.selectbox("Selecciona TAG final:", tag_unicos, index=len(tag_unicos) - 1, key="tag_final")

    if st.button("Filtrar rango de TAG"):
        rango_df = df[(df["TAG"] >= tag_inicial) & (df["TAG"] <= tag_final)]

        if rango_df.empty:
            st.warning("No se encontraron datos en el rango seleccionado.")
        else:
            # Mostrar rango filtrado
            st.write("**Rango filtrado:**")
            st.write(rango_df)

            # Cálculos
            operadores_unicos = rango_df["Operador"].nunique()
            tiempo_inicial = rango_df["Timestamp"].min()
            tiempo_final = rango_df["Timestamp"].max()
            horas = (tiempo_final - tiempo_inicial).total_seconds() / 3600
            total_unidades = rango_df["Unidades"].sum()
            ph = total_unidades / (horas * operadores_unicos) if horas > 0 and operadores_unicos > 0 else 0

            # Mostrar resultados
            with st.container(border=True):
                st.warning("**Resultados del análisis para el :blue[*rango seleccionado:*]**")
                st.write(f"Tiempo inicial: {tiempo_inicial}")
                st.write(f"Tiempo final: {tiempo_final}")
                st.write(f"Duración (horas): {horas:.2f}")
                st.write(f"Total de unidades: {total_unidades}")
                st.write(f"Operadores únicos: {operadores_unicos}")
                st.success(f"PH (Producción por hora): {ph:.2f}")

            # Crear archivo de resultados para descargar
            resultados = StringIO()
            resultados.write(f"TAG inicial: {tag_inicial}\n")
            resultados.write(f"TAG final: {tag_final}\n")
            resultados.write(f"Tiempo inicial: {tiempo_inicial}\n")
            resultados.write(f"Tiempo final: {tiempo_final}\n")
            resultados.write(f"Duración (horas): {horas:.2f}\n")
            resultados.write(f"Total de unidades: {total_unidades}\n")
            resultados.write(f"Operadores únicos: {operadores_unicos}\n")
            resultados.write(f"PH: {ph:.2f}\n")
            resultados.seek(0)

            # Convertir StringIO a bytes para permitir la descarga
            resultados_bytes = resultados.getvalue().encode("utf-8")

            st.download_button(
                label="Descargar resultados",
                data=resultados_bytes,
                file_name="resultados.txt",
                mime="text/plain"
            )
