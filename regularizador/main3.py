"""
Procesador de facturación (versión con 3 descuentos + 1 incremento)

Reglas:
- DESCUENTO1 = 0.0560 -> aplica si 'Mes en que es factura' < 7
- DESCUENTO2 = 0.0596 -> aplica si 7 <= 'Mes en que es factura' < 11
- DESCUENTO3 = 0.0696 -> aplica si 'Mes en que es factura' >= 11

Incremento único:
- INCREMENTO = 0.0951 (aplica a todos)

Este script se basa en `main2.py` y mantiene la misma estrategia de lectura
robusta de CSV y salida a Excel.
"""

import pandas as pd
from pathlib import Path
from tqdm import tqdm
import numpy as np
import tempfile
import csv
import os

# Tasas
DESCUENTO1 = 0.0560
DESCUENTO2 = 0.0596
DESCUENTO3 = 0.0696
INCREMENTO = 0.0951


def procesar_xlsx(ruta_carpeta: str):
    carpeta = Path(ruta_carpeta)

    # Cargar tabla CECOS (espera dim_cecos.csv en cwd)
    dim_cecos = pd.read_csv("dim_cecos.csv")
    dim_cecos["Codi_str"] = (
        dim_cecos["Codi"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    )
    mapa_cecos = dim_cecos.set_index("Codi_str")["Centre de cost"]

    archivos = [f for f in carpeta.iterdir() if f.suffix.lower() == ".csv"]
    if not archivos:
        print("No se encontraron archivos CSV.")
        return

    required_columns = ['UT Fact.', 'Preu unitari: Calculat per les taules de', 'Mes en que es factura']

    with tqdm(archivos, desc="Procesando archivos CSV", unit="archivo") as pbar:
        for archivo in pbar:
            pbar.set_description(f"Archivo: {archivo.name}")

            # Lectura robusta similar a main2.py
            temp_file = None
            try:
                with open(archivo, 'r', encoding='latin-1') as f_in:
                    lines = f_in.readlines()

                needs_clean = False
                if lines:
                    first = lines[0].strip()
                    if first.startswith('ï»¿"') or first.startswith('"'):
                        needs_clean = True

                if needs_clean:
                    pbar.set_postfix(paso="Limpiando formato CSV")
                    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.csv')
                    for line in lines:
                        clean_line = line.replace('ï»¿', '')
                        clean_line = clean_line.strip()
                        if clean_line.startswith('"') and clean_line.endswith('"'):
                            clean_line = clean_line[1:-1]
                        temp_file.write(clean_line + '\n')
                    temp_file.close()
                    df = pd.read_csv(temp_file.name, sep=',', encoding='utf-8', low_memory=False)
                else:
                    df = pd.read_csv(archivo, sep=',', encoding='latin-1', low_memory=False)
            except Exception as e:
                try:
                    df = pd.read_csv(archivo, sep=",", encoding="latin-1", quoting=csv.QUOTE_NONE, low_memory=False)
                except Exception as e2:
                    print(f"Error al leer {archivo.name}: {e}")
                    if temp_file:
                        try:
                            os.unlink(temp_file.name)
                        except Exception:
                            pass
                    continue
            finally:
                if temp_file:
                    try:
                        os.unlink(temp_file.name)
                    except Exception:
                        pass

            # Validar columnas
            pbar.set_postfix(paso="Validando columnas")
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                print(f"\n❌ Error en {archivo.name}: columnas requeridas NO encontradas: {missing_cols}\n")
                continue

            # Transform UT Fact
            pbar.set_postfix(paso="Transformando UT Fact.")
            df["codigo_ceco"] = (
                df["UT Fact."].astype(str).str.strip().str.replace(r"\.0$", "", regex=True) + "00"
            )

            # Cruce CECOS
            pbar.set_postfix(paso="Cruzando con CECOS")
            df["nombre_ceco"] = df["codigo_ceco"].map(mapa_cecos)

            # Calcular tasas según el mes con 3 tramos
            pbar.set_postfix(paso="Calculando Tasas")
            base_col = "Preu unitari: Calculat per les taules de"

            # Convertir columna de mes si necesario
            try:
                mes_series = df['Mes en que es factura'].astype(int)
            except Exception:
                mes_series = pd.to_numeric(df['Mes en que es factura'], errors='coerce').fillna(0).astype(int)

            cond1 = mes_series < 7
            cond2 = (mes_series >= 7) & (mes_series < 11)
            cond3 = mes_series >= 11

            df['tasa_descuento'] = np.select([cond1, cond2, cond3], [DESCUENTO1, DESCUENTO2, DESCUENTO3], default=0.0)
            df['tasa_incremento'] = INCREMENTO

            # Calcular importes
            pbar.set_postfix(paso="Calculando Importes")
            df[base_col] = pd.to_numeric(df[base_col], errors='coerce').fillna(0.0)

            # Descuento: Precio / (1 + tasa_descuento)
            df["DESCUENTO_CALCULADO"] = df[base_col] / (1 + df['tasa_descuento'])

            # Incremento: Descuento * (1 + INCREMENTO)
            df["INCREMENTO_CALCULADO"] = df["DESCUENTO_CALCULADO"] * (1 + df['tasa_incremento'])

            # DIFF
            df["DIFF"] = df["INCREMENTO_CALCULADO"] - df[base_col]

            # Resumen por CECO
            pbar.set_postfix(paso="Generando resumen CECO")
            df_resumen = df.groupby(["nombre_ceco", "codigo_ceco"], as_index=False)["DIFF"].sum()

            # Guardar Excel
            output_path = archivo.with_name("r_" + archivo.stem + ".xlsx")
            pbar.set_postfix(paso="Escribiendo Excel...")
            with pd.ExcelWriter(output_path, engine="openpyxl", mode="w") as writer:
                df_resumen.to_excel(writer, sheet_name="Resumen_CECO", index=False)
                df.to_excel(writer, sheet_name="Detalle_Procesado", index=False)

            pbar.set_postfix(paso="OK")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Error: Debes especificar la ruta de la carpeta a procesar.")
        print("Uso: python main3.py <ruta_carpeta>")
        sys.exit(1)
    ruta_exports = sys.argv[1]
    print(f"Procesando carpeta: {ruta_exports}")
    procesar_xlsx(ruta_exports)
