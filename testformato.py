"""Pruebas de generación de PDF usando la lógica real de app.py.

Cada caso llama a FacturaAPI.generar_pdf() con datos de ejemplo, de modo
que el PDF resultante se pueda abrir o imprimir y comparar contra el
formato físico de la factura. Los archivos se guardan en salida_pruebas/.

La hoja se mantiene tamaño carta (216 x 279 mm); el contenido va reducido
a 178 mm de ancho y alineado a la izquierda. El módulo del cliente empieza
en y = 50 mm y el resto del formato (tabla y totales) se desplaza con él.

Ejecutar con el entorno del proyecto:
    .\\venv\\Scripts\\python.exe testformato.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from app import (
    ALTO_CLIENTE,
    ALTO_CUERPO,
    ALTO_ENCABEZADO,
    ALTO_FILA,
    ANCHO_CONTENIDO,
    FacturaAPI,
    MARGEN_IZQ,
    Y_CLIENTE,
    Y_TABLA,
    Y_TOTALES,
    fmt_monto,
)

CARPETA_SALIDA = Path(__file__).resolve().parent / "salida_pruebas"

ANCHO_ESPERADO_MM = 216
ALTO_ESPERADO_MM = 279
TOLERANCIA_MM = 0.5


# =========================================================
# DATOS DE EJEMPLO
# =========================================================

def caso_factura_completa():
    """Factura típica: ítems con IVA, exentos, cantidad decimal y línea de
    continuación (sin cantidad ni precio) como las que se imprimen a mano."""
    return {
        "nombre_archivo": "01_factura_completa",
        "cliente": {
            "nombre": "DISTRIBUIDORA EJEMPLO, C.A.",
            "domicilio": "AV. PRINCIPAL, EDIF. CENTRO, PISO 2, OFICINA 4, ZONA INDUSTRIAL",
            "rif": "J-12345678-9",
            "orden": "ORD-2026-0089",
        },
        "factura": {
            "fecha": {"dia": "21", "mes": "10", "anio": "2026"},
            "metodo": "Transferencia",
        },
        "items": [
            {"cant": 2, "descripcion": "PRODUCTO DE PRUEBA A", "precioBase": 150.00, "tieneIVA": True, "subtotal": 300.00},
            {"cant": 0, "descripcion": "LINEA ADICIONAL DE DESCRIPCION EXTENDIDA", "precioBase": 0, "tieneIVA": False, "subtotal": 0},
            {"cant": 5, "descripcion": "PRODUCTO EXENTO B", "precioBase": 40.00, "tieneIVA": False, "subtotal": 200.00},
            {"cant": 1.5, "descripcion": "SERVICIO TECNICO POR HORA (CANTIDAD DECIMAL)", "precioBase": 320.50, "tieneIVA": True, "subtotal": 480.75},
            {"cant": 12, "descripcion": "CAÑERIA GALVANIZADA 1/2\" x 6M", "precioBase": 18.99, "tieneIVA": True, "subtotal": 227.88},
            {"cant": 3, "descripcion": "MANO DE OBRA INSTALACION", "precioBase": 450.00, "tieneIVA": True, "subtotal": 1350.00},
        ],
        "totales": {
            "baseImponible": 2358.63,
            "exento": 200.00,
            "iva": 377.38,
            "totalGeneral": 2936.01,
        },
    }


def caso_solo_exentos():
    """Factura sin base imponible: el IVA debe salir en 0,00."""
    return {
        "nombre_archivo": "02_solo_exentos",
        "cliente": {
            "nombre": "CLIENTE EXENTO SIN RIF",
            "domicilio": "CALLE 5, CASA 12, BARRIO CENTRO",
            "rif": "V-00000000",
            "orden": "ORD-2026-0090",
        },
        "factura": {
            "fecha": {"dia": "01", "mes": "11", "anio": "2026"},
            "metodo": "Efectivo",
        },
        "items": [
            {"cant": 1, "descripcion": "LIBRO DE TEXTO", "precioBase": 120.00, "tieneIVA": False, "subtotal": 120.00},
            {"cant": 4, "descripcion": "CUADERNO UNIVERSITARIO", "precioBase": 25.50, "tieneIVA": False, "subtotal": 102.00},
            {"cant": 2, "descripcion": "BOLIGRAFO NEGRO", "precioBase": 3.75, "tieneIVA": False, "subtotal": 7.50},
        ],
        "totales": {
            "baseImponible": 0.00,
            "exento": 229.50,
            "iva": 0.00,
            "totalGeneral": 229.50,
        },
    }


def caso_sin_items():
    """Caso límite: sin renglones, solo los datos del cliente y totales en cero."""
    return {
        "nombre_archivo": "03_sin_items",
        "cliente": {
            "nombre": "",
            "domicilio": "",
            "rif": "",
            "orden": "",
        },
        "factura": {
            "fecha": {"dia": "", "mes": "", "anio": ""},
            "metodo": "",
        },
        "items": [],
        "totales": {
            "baseImponible": 0,
            "exento": 0,
            "iva": 0,
            "totalGeneral": 0,
        },
    }


def caso_muchos_items():
    """Estrés del cuerpo de la tabla: 25 renglones, el máximo que entra en el
    rect de productos del formato actual."""
    items = []
    for i in range(1, 26):
        con_iva = i % 3 != 0
        precio = 10.00 + i
        items.append({
            "cant": i,
            "descripcion": f"RENGLON DE PRUEBA N° {i:02d} - PRODUCTO DE DEMOSTRACION",
            "precioBase": precio,
            "tieneIVA": con_iva,
            "subtotal": round(i * precio, 2),
        })
    base = round(sum(it["subtotal"] for it in items if it["tieneIVA"]), 2)
    exento = round(sum(it["subtotal"] for it in items if not it["tieneIVA"]), 2)
    iva = round(base * 0.16, 2)
    return {
        "nombre_archivo": "04_muchos_items",
        "cliente": {
            "nombre": "CONSTRUCTORA LOS ANDES, C.A.",
            "domicilio": "CARRERA 12 CON CALLE 8, GALPON 3, SECTOR NORTE",
            "rif": "J-98765432-1",
            "orden": "ORD-2026-0091",
        },
        "factura": {
            "fecha": {"dia": "31", "mes": "10", "anio": "2026"},
            "metodo": "Credito 30 dias",
        },
        "items": items,
        "totales": {
            "baseImponible": base,
            "exento": exento,
            "iva": iva,
            "totalGeneral": round(base + exento + iva, 2),
        },
    }


def caso_montos_altos():
    """Montos con separador de miles y decimales para revisar el ancho de las
    columnas P. UNITARIO / SUBTOTAL y del resumen de totales."""
    return {
        "nombre_archivo": "05_montos_altos",
        "cliente": {
            "nombre": "PETROLEOS DEL SUR, S.A.",
            "domicilio": "AV. LIBERTADOR, TORRE EMPRESARIAL, PISO 18, CARACAS",
            "rif": "J-30456789-0",
            "orden": "ORD-2026-0092",
        },
        "factura": {
            "fecha": {"dia": "15", "mes": "09", "anio": "2026"},
            "metodo": "Transferencia",
        },
        "items": [
            {"cant": 1250, "descripcion": "VALVULA INDUSTRIAL DE ALTA PRESION", "precioBase": 1250000.50, "tieneIVA": True, "subtotal": 1562500625.00},
            {"cant": 80, "descripcion": "TUBERIA DE ACERO AL CARBONO", "precioBase": 987654.32, "tieneIVA": True, "subtotal": 79012345.60},
            {"cant": 2, "descripcion": "SERVICIO DE INSPECCION EXENTO", "precioBase": 4500000.00, "tieneIVA": False, "subtotal": 9000000.00},
        ],
        "totales": {
            "baseImponible": 1641512970.60,
            "exento": 9000000.00,
            "iva": 262642075.30,
            "totalGeneral": 1913155045.90,
        },
    }


def caso_valores_por_defecto():
    """Sin nombre_archivo ni medidas: usar los valores por defecto
    (factura_salida.pdf y hoja 216 x 279 mm)."""
    return {
        "cliente": {
            "nombre": "PRUEBA DE VALORES POR DEFECTO",
            "domicilio": "SIN DOMICILIO REGISTRADO",
            "rif": "V-11111111",
            "orden": "ORD-2026-0093",
        },
        "factura": {
            "fecha": {"dia": "31", "mes": "10", "anio": "2026"},
            "metodo": "Contado",
        },
        "items": [
            {"cant": 1, "descripcion": "ITEM UNICO DE PRUEBA", "precioBase": 100.00, "tieneIVA": True, "subtotal": 100.00},
        ],
        "totales": {
            "baseImponible": 100.00,
            "exento": 0.00,
            "iva": 16.00,
            "totalGeneral": 116.00,
        },
    }


CASOS = [
    ("Factura completa (IVA + exento + decimal)", caso_factura_completa, "01_factura_completa.pdf"),
    ("Solo productos exentos", caso_solo_exentos, "02_solo_exentos.pdf"),
    ("Sin ítems (caso límite)", caso_sin_items, "03_sin_items.pdf"),
    ("25 renglones (máximo del formato)", caso_muchos_items, "04_muchos_items.pdf"),
    ("Montos altos (miles/millones)", caso_montos_altos, "05_montos_altos.pdf"),
    ("Valores por defecto", caso_valores_por_defecto, "factura_salida.pdf"),
]


# =========================================================
# EJECUCIÓN DE LAS PRUEBAS
# =========================================================

def medir_pagina_mm(datos: bytes) -> tuple[float, float] | None:
    """Lee el /MediaBox del PDF y lo devuelve en milímetros."""
    coincidencia = re.search(
        rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\]",
        datos,
    )
    if not coincidencia:
        return None
    _, _, ancho_pt, alto_pt = map(float, coincidencia.groups())
    return round(ancho_pt * 25.4 / 72, 1), round(alto_pt * 25.4 / 72, 1)


def validar_geometria() -> list[str]:
    """Comprueba que los bloques del formato no se solapen ni se salgan de la hoja."""
    errores = []
    fin_cliente = Y_CLIENTE + ALTO_CLIENTE
    fin_encabezado = Y_TABLA + ALTO_ENCABEZADO
    fin_cuerpo = fin_encabezado + ALTO_CUERPO
    fin_totales = Y_TOTALES + 15 + 7

    if fin_cliente > Y_TABLA:
        errores.append(
            f"el recuadro del cliente termina en {fin_cliente} mm, "
            f"pero el encabezado empieza antes ({Y_TABLA} mm)"
        )
    if fin_cuerpo > Y_TOTALES:
        errores.append(
            f"el cuerpo de la tabla termina en {fin_cuerpo} mm, "
            f"pero los totales empiezan antes ({Y_TOTALES} mm)"
        )
    if fin_totales > ALTO_ESPERADO_MM:
        errores.append(
            f"los totales terminan en {fin_totales} mm y se salen de la hoja "
            f"({ALTO_ESPERADO_MM} mm)"
        )
    if MARGEN_IZQ + ANCHO_CONTENIDO > ANCHO_ESPERADO_MM:
        errores.append("el contenido se sale del ancho de la hoja")
    return errores


def validar_pdf(ruta: Path) -> list[str]:
    """Revisa que el archivo exista, sea un PDF válido y tenga hoja carta."""
    errores = []
    if not ruta.exists():
        return [f"no se generó el archivo {ruta.name}"]
    datos = ruta.read_bytes()
    if len(datos) < 1000:
        errores.append(f"archivo demasiado pequeño ({len(datos)} bytes)")
    if not datos.startswith(b"%PDF"):
        errores.append("el archivo no comienza con la firma %PDF")
    if b"%%EOF" not in datos[-2048:]:
        errores.append("el archivo no termina con %%EOF (puede estar truncado)")

    medidas = medir_pagina_mm(datos)
    if medidas is None:
        errores.append("no se pudo leer el tamaño de página (/MediaBox)")
    else:
        ancho, alto = medidas
        if (abs(ancho - ANCHO_ESPERADO_MM) > TOLERANCIA_MM
                or abs(alto - ALTO_ESPERADO_MM) > TOLERANCIA_MM):
            errores.append(
                f"tamaño de hoja inesperado: {ancho} x {alto} mm "
                f"(se esperaba {ANCHO_ESPERADO_MM} x {ALTO_ESPERADO_MM} mm)"
            )
    return errores


def ejecutar_pruebas() -> int:
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    api = FacturaAPI()
    correctas = 0
    fallidas = 0

    print("Distribución vertical (mm):")
    print(
        f"  cliente y={Y_CLIENTE}..{Y_CLIENTE + ALTO_CLIENTE} | "
        f"encabezado y={Y_TABLA}..{Y_TABLA + ALTO_ENCABEZADO} | "
        f"cuerpo hasta {Y_TABLA + ALTO_ENCABEZADO + ALTO_CUERPO} | "
        f"totales y={Y_TOTALES}..{Y_TOTALES + 22}"
    )
    print(f"  renglones máximos: {ALTO_CUERPO // ALTO_FILA}")
    errores_geometria = validar_geometria()
    if errores_geometria:
        fallidas += 1
        print("[FALLO] Geometría del formato")
        for error in errores_geometria:
            print(f"         - {error}")
    else:
        correctas += 1
        print("[ OK  ] Geometría del formato (sin solapes)")
    print()

    # generar_pdf escribe en el directorio de trabajo, así que nos ubicamos
    # en salida_pruebas/ para que todos los PDF queden juntos.
    directorio_original = os.getcwd()
    os.chdir(CARPETA_SALIDA)
    try:
        print(f"Carpeta de salida: {CARPETA_SALIDA}\n")
        for titulo, constructor, archivo_esperado in CASOS:
            payload = constructor()
            resultado = api.generar_pdf(payload)
            ruta = CARPETA_SALIDA / archivo_esperado

            errores = []
            if not resultado.get("exito"):
                errores.append(resultado.get("mensaje", "error desconocido"))
            errores.extend(validar_pdf(ruta))

            if errores:
                fallidas += 1
                print(f"[FALLO] {titulo}")
                for error in errores:
                    print(f"         - {error}")
            else:
                correctas += 1
                tamano_kb = ruta.stat().st_size / 1024
                medidas = medir_pagina_mm(ruta.read_bytes())
                detalle_medidas = (
                    f" - hoja {medidas[0]} x {medidas[1]} mm" if medidas else ""
                )
                print(f"[ OK  ] {titulo} -> {archivo_esperado} ({tamano_kb:.1f} KB){detalle_medidas}")
    finally:
        os.chdir(directorio_original)

    print("\nFormato de montos (fmt_monto):")
    for valor in (0, 1234.5, 1250000.5, None):
        print(f"  {valor!r:>12} -> {fmt_monto(valor)}")

    total = correctas + fallidas
    print(f"\nResultado: {correctas}/{total} pruebas correctas")
    if fallidas:
        print("Revisa los errores anteriores antes de imprimir.")
        return 1

    print(f"Listo. Abre o imprime los PDF de: {CARPETA_SALIDA}")
    print("Imprime al 100% / tamaño real (sin 'ajustar a página').")
    return 0


if __name__ == "__main__":
    sys.exit(ejecutar_pruebas())
