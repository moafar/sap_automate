"""
Módulo para el procesamiento de archivos Excel de facturación.

Este script busca archivos .csv en una carpeta especificada, realiza cálculos
de descuentos e incrementos sobre los datos, cruza información con una tabla
de centros de coste (CECOS) y genera un nuevo archivo Excel con los resultados
detallados y un resumen por centro de coste.
"""

import pandas as pd
from pathlib import Path
import shutil
from tqdm import tqdm
import numpy as np

# Configuración de Tasas
# Periodo 1: Mes < 7
DESCUENTO1 = 0.0560
INCREMENTO1 = 0.0696

# Periodo 2: Mes >= 7
DESCUENTO2 = 0.0596 
INCREMENTO2 = 0.0696


def procesar_xlsx(ruta_carpeta: str):
    """
    Procesa todos los archivos CSV (.csv) encontrados en la carpeta especificada.

    Para cada archivo:
    1. Carga los datos de la hoja 'Sheet1'.
    2. Transforma y normaliza los códigos de unidad técnica (UT Fact.).
    3. Cruza los datos con la tabla de maestros de CECOS (dim_cecos.csv).
    4. Calcula descuentos, incrementos y diferencias.
    5. Genera un resumen por centro de coste.
    6. Guarda un nuevo archivo con prefijo 'r_' que incluye los datos procesados y el resumen.

    Args:
        ruta_carpeta (str): Ruta al directorio que contiene los archivos CSV a procesar.
    """
    carpeta = Path(ruta_carpeta)

    # ===== Cargar tabla CECOS =====
    dim_cecos = pd.read_csv("dim_cecos.csv")
    dim_cecos["Codi_str"] = (
        dim_cecos["Codi"]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )
    mapa_cecos = dim_cecos.set_index("Codi_str")["Centre de cost"]

    archivos = [f for f in carpeta.iterdir() if f.suffix.lower() == ".csv"]

    if not archivos:
        print("No se encontraron archivos CSV.")
        return

    # ===== Barra EXTERNA =====
    with tqdm(archivos, desc="Procesando archivos CSV", unit="archivo") as pbar:

        for archivo in pbar:

            # Mostrar archivo actual
            pbar.set_description(f"Archivo: {archivo.name}")

            # 1. Cargando CSV
            pbar.set_postfix(paso="Cargando CSV")
            
            # 1. Cargando CSV
            pbar.set_postfix(paso="Cargando CSV")
            
            # Pre-procesar CSV para manejar formato con filas completamente entrecomilladas
            import tempfile
            import csv
            
            temp_file = None
            try:
                # Intentar leer el archivo y limpiar formato especial
                with open(archivo, 'r', encoding='latin-1') as f_in:
                    lines = f_in.readlines()
                
                # Detectar si la primera línea está completamente entrecomillada
                if lines and lines[0].strip().startswith('ï»¿"') or lines[0].strip().startswith('"'):
                    pbar.set_postfix(paso="Limpiando formato CSV")
                    # Crear archivo temporal limpio
                    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.csv')
                    
                    for line in lines:
                        # Quitar BOM si existe
                        clean_line = line.replace('ï»¿', '')
                        # Si la línea empieza y termina con comillas, quitarlas
                        clean_line = clean_line.strip()
                        if clean_line.startswith('"') and clean_line.endswith('"'):
                            clean_line = clean_line[1:-1]
                        temp_file.write(clean_line + '\n')
                    
                    temp_file.close()
                    df = pd.read_csv(temp_file.name, sep=',', encoding='utf-8', low_memory=False)
                else:
                    # Formato estándar
                    df = pd.read_csv(archivo, sep=',', encoding='latin-1', low_memory=False)
            except Exception as e:
                try:
                    # Fallback: Ignorar comillas completamente
                    df = pd.read_csv(archivo, sep=",", encoding="latin-1", quoting=csv.QUOTE_NONE)
                except Exception as e2:
                    print(f"Error al leer {archivo.name}: {e}")
                    continue
            finally:
                # Limpiar archivo temporal
                if temp_file:
                    import os
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
            
            # Mostrar columnas disponibles para debug
            pbar.set_postfix(paso="Validando columnas")
            required_columns = ['UT Fact.', 'Preu unitari: Calculat per les taules de', 'Mes en que es factura']
            missing_cols = [col for col in required_columns if col not in df.columns]
            
            if missing_cols:
                print(f"\n❌ Error en {archivo.name}:")
                print(f"  Columnas requeridas NO encontradas: {missing_cols}")
                print(f"  Columnas disponibles en el archivo:")
                for i, col in enumerate(df.columns, 1):
                    print(f"    {i}. '{col}'")
                print()
                continue

            # 2. Transform UT Fact
            pbar.set_postfix(paso="Transformando UT Fact.")
            df["codigo_ceco"] = (
                df["UT Fact."].astype(str).str.strip().str.replace(r"\.0$", "", regex=True) + "00"
            )

            # 3. Cruce CECOS
            pbar.set_postfix(paso="Cruzando con CECOS")
            df["nombre_ceco"] = df["codigo_ceco"].map(mapa_cecos)

            # 4. Calcular Tasas según el mes
            pbar.set_postfix(paso="Calculando Tasas")
            base_col = "Preu unitari: Calculat per les taules de"
            
            # Condiciones
            cond_periodo1 = df['Mes en que es factura'] < 7
            cond_periodo2 = df['Mes en que es factura'] >= 7
            
            # Asignar tasas
            df['tasa_descuento'] = np.select(
                [cond_periodo1, cond_periodo2], 
                [DESCUENTO1, DESCUENTO2], 
                default=0.0
            )
            
            df['tasa_incremento'] = np.select(
                [cond_periodo1, cond_periodo2], 
                [INCREMENTO1, INCREMENTO2], 
                default=0.0
            )

            # 5. Calcular Importes
            pbar.set_postfix(paso="Calculando Importes")
            # Descuento: Precio / (1 + Tasa Descuento)
            df["DESCUENTO_CALCULADO"] = df[base_col].astype(float) / (1 + df['tasa_descuento'])
            
            # Incremento: Descuento * (1 + Tasa Incremento)
            df["INCREMENTO_CALCULADO"] = df["DESCUENTO_CALCULADO"] * (1 + df['tasa_incremento'])
            
            # 6. DIFF
            pbar.set_postfix(paso="Calculando DIFF")
            df["DIFF"] = df["INCREMENTO_CALCULADO"] - df[base_col]

            # 7. Resumen CECO
            pbar.set_postfix(paso="Generando resumen CECO")
            df_resumen = df.groupby(["nombre_ceco", "codigo_ceco"], as_index=False)["DIFF"].sum()

            # 8. Guardar archivo (lento)
            # Al ser CSV el origen, creamos un Excel nuevo desde cero
            output_path = archivo.with_name("r_" + archivo.stem + ".xlsx")

            pbar.set_postfix(paso="Escribiendo Excel...")
            with pd.ExcelWriter(
                output_path,
                engine="openpyxl",
                mode="w", # Write mode (crear nuevo)
            ) as writer:
                df_resumen.to_excel(writer, sheet_name="Resumen_CECO", index=False)
                df.to_excel(writer, sheet_name="Detalle_Procesado", index=False)

            # archivo terminado
            pbar.set_postfix(paso="OK")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Error: Debes especificar la ruta de la carpeta a procesar.")
        print("Uso: python main2.py <ruta_carpeta>")
        sys.exit(1)

    ruta_exports = sys.argv[1]
        
    print(f"Procesando carpeta: {ruta_exports}")
    procesar_xlsx(ruta_exports)
