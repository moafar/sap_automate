"""
Módulo para el procesamiento de archivos Excel de facturación.

Este script busca archivos .xlsx en una carpeta especificada, realiza cálculos
de descuentos e incrementos sobre los datos, cruza información con una tabla
de centros de coste (CECOS) y genera un nuevo archivo Excel con los resultados
detallados y un resumen por centro de coste.
"""

import pandas as pd
from pathlib import Path
import shutil
from tqdm import tqdm

DESCUENTO1 = 0.0560
INCREMENTO1 = 0.0696

DESCUENTO2 = 0.0596
INCREMENTO2 = 0.0696


def procesar_xlsx(ruta_carpeta: str):
    """
    Procesa todos los archivos Excel (.xlsx) encontrados en la carpeta especificada.

    Para cada archivo:
    1. Carga los datos de la hoja 'Sheet1'.
    2. Transforma y normaliza los códigos de unidad técnica (UT Fact.).
    3. Cruza los datos con la tabla de maestros de CECOS (dim_cecos.csv).
    4. Calcula descuentos, incrementos y diferencias.
    5. Genera un resumen por centro de coste.
    6. Guarda un nuevo archivo con prefijo 'r_' que incluye los datos procesados y el resumen.

    Args:
        ruta_carpeta (str): Ruta al directorio que contiene los archivos Excel a procesar.
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

    archivos = [f for f in carpeta.iterdir() if f.suffix.lower() == ".xlsx"]

    if not archivos:
        print("No se encontraron archivos XLSX.")
        return

    # ===== Barra EXTERNA =====
    with tqdm(archivos, desc="Procesando archivos XLSX", unit="archivo") as pbar:

        for archivo in pbar:

            # Mostrar archivo actual
            pbar.set_description(f"Archivo: {archivo.name}")

            # 1. Cargando hoja
            pbar.set_postfix(paso="Cargando Sheet1")
            df = pd.read_excel(archivo, engine="openpyxl", sheet_name="Sheet1")

            # 2. Transform UT Fact
            pbar.set_postfix(paso="Transformando UT Fact.")
            df["codigo_ceco"] = (
                df["UT Fact."].astype(str).str.strip().str.replace(r"\.0$", "", regex=True) + "00"
            )

            # 3. Cruce CECOS
            pbar.set_postfix(paso="Cruzando con CECOS")
            df["nombre_ceco"] = df["codigo_ceco"].map(mapa_cecos)

            # 4 DISPATCHER DESCUENTOS 
            pbar.set_postfix(paso="Calculando DESCUENTO")
            if (df["Mes en que es factura"] < 7):
                descuento = DESCUENTO1
                incremento = INCREMENTO1
            else:
                descuento = DESCUENTO2
                incremento = INCREMENTO2

            df["tasa_descuento"] = descuento
            df["tasa_incremento"] = incremento

            # 4.1 DESCUENTO

            base_col = "Preu unitari: Calculat per les taules de"
            df["DESCUENTO"] = df[base_col].astype(float) / (1 + DESCUENTO)

            # 5. INCREMENTO
            pbar.set_postfix(paso="Calculando INCREMENTO")
            df["INCREMENTO"] = df["DESCUENTO"] * (1 + INCREMENTO)

            # 6. DIFF
            pbar.set_postfix(paso="Calculando DIFF")
            df["DIFF"] = df["INCREMENTO"] - df[base_col]

            # 7. Resumen CECO
            pbar.set_postfix(paso="Generando resumen CECO")
            df_resumen = df.groupby(["nombre_ceco", "codigo_ceco"], as_index=False)["DIFF"].sum()

            # 8. Guardar archivo (lento)
            output_path = archivo.with_name("r_" + archivo.stem + ".xlsx")

            pbar.set_postfix(paso="Copiando archivo original")
            shutil.copy(archivo, output_path)

            pbar.set_postfix(paso="Escribiendo hojas nuevas...")
            with pd.ExcelWriter(
                output_path,
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace"
            ) as writer:
                df_resumen.to_excel(writer, sheet_name="Resumen_CECO", index=False)
                df.to_excel(writer, sheet_name="Detalle_Procesado", index=False)

            # archivo terminado
            pbar.set_postfix(paso="OK")


if __name__ == "__main__":
    procesar_xlsx("/home/rom/idi/regs")
