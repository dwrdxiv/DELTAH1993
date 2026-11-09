import os
import sys

import webview
from fpdf import FPDF

# Medidas del contenido en mm (la hoja se mantiene tamaño carta: 216 x 279)
MARGEN_IZQ = 14
ANCHO_CONTENIDO = 178

# Alturas de los bloques (mm)
Y_CLIENTE = 50        # borde superior del recuadro del cliente (antes 35)
ALTO_CLIENTE = 23
Y_TABLA = 75          # inicio del encabezado de la tabla (antes 60)
ALTO_ENCABEZADO = 6
ALTO_FILA = 6          # separación vertical entre renglones
ALTO_CUERPO = 152      # antes 140 (capacidad: 25 renglones)
Y_TOTALES = 235       # inicio del resumen de totales (antes 223)


# Función para resolver rutas tanto en desarrollo como empaquetado
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def fmt_monto(valor):
    try:
        # Formato inicial: 1,000,000.00 -> convierte a 1.000.000,00
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"

class FacturaAPI:
    def generar_pdf(self, payload):
        try:
            cliente = payload.get("cliente", {})
            factura = payload.get("factura", {})
            items = payload.get("items", [])
            totales = payload.get("totales", {})
            nombre_archivo = payload.get("nombre_archivo", "factura_salida").strip()

            if not nombre_archivo:
                nombre_archivo = "factura"

            # Formato en mm: (ancho, alto). Ajusta con las medidas que tomaste
            ancho_mm = float(payload.get("ancho_mm", 216))
            alto_mm = float(payload.get("alto_mm", 279))

            pdf = FPDF(orientation='P', unit='mm', format=(ancho_mm, alto_mm))
            pdf.set_auto_page_break(auto=False)  # Desactivar salto automático de página
            pdf.add_page()


            pdf.set_font("Helvetica", size=10)

            # =========================================================
            # DIBUJO DE ESTRUCTURA Y ENCABEZADOS (Hoja en Blanco)
            # =========================================================

            # --- Cuadro de Datos de Factura / Fecha (lado izquierdo) ---
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_xy(MARGEN_IZQ, 32)
            pdf.cell(45, 5, text="FECHA DE EMISIÓN", border=0, align="C")

            # Sub-tabla para Día / Mes / Año
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_xy(MARGEN_IZQ, 37)
            pdf.cell(14, 5, text="DÍA", border=0, align="C")
            pdf.cell(16, 5, text="MES", border=0, align="C")
            pdf.cell(15, 5, text="AÑO", border=0, align="C")

            pdf.set_font("Helvetica", "", 10)
            pdf.set_xy(MARGEN_IZQ, 42)
            pdf.cell(14, 5, text=str(factura.get("fecha", "").get("dia", "")), border=0, align="C")
            pdf.cell(16, 5, text=str(factura.get("fecha", "").get("mes", "")), border=0, align="C")
            pdf.cell(15, 5, text=str(factura.get("fecha", "").get("anio", "")), border=0, align="C")

            # --- Cuadro de Datos del Cliente (sin recuadro ni líneas) ---
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(16, Y_CLIENTE + 1)
            pdf.cell(32, 6, text="Nombre / Razón:", border=0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(ANCHO_CONTENIDO - 36, 6, text=str(cliente.get("nombre", "")), border=0)

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(16, Y_CLIENTE + 8)
            pdf.cell(32, 6, text="Domicilio Fiscal:", border=0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(ANCHO_CONTENIDO - 36, 6, text=str(cliente.get("domicilio", "")), border=0)

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(16, Y_CLIENTE + 15)
            pdf.cell(20, 6, text="C.I / RIF:", border=0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(30, 6, text=str(cliente.get("rif", "")), border=0, align="C")

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(70, Y_CLIENTE + 15)
            pdf.cell(28, 6, text="N° Orden / Guía:", border=0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(30, 6, text=str(cliente.get("orden", "")), border=0, align="C")

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(132, Y_CLIENTE + 15)
            pdf.cell(28, 6, text="Metodo de Pago:", border=0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(30, 6, text=str(factura.get("metodo", "")), border=0, align="C")
            
            # === RENGLONES DE LA TABLA ===
            # Anchos: 13 + 101 + 23 + 11 + 30 = 178 mm
            y_tabla_inicio = Y_TABLA

            pdf.set_font("Helvetica", "B", 8)
            pdf.set_xy(MARGEN_IZQ, y_tabla_inicio)
            pdf.cell(13, ALTO_ENCABEZADO, text="CANT.", border=1, align="C")
            pdf.cell(101, ALTO_ENCABEZADO, text="DESCRIPCIÓN / CONCEPTO", border=1, align="C")
            pdf.cell(23, ALTO_ENCABEZADO, text="P. UNITARIO", border=1, align="C")
            pdf.cell(11, ALTO_ENCABEZADO, text="ALÍC.", border=1, align="C")
            pdf.cell(30, ALTO_ENCABEZADO, text="SUBTOTAL", border=1, align="C")

            pdf.rect(MARGEN_IZQ, y_tabla_inicio + ALTO_ENCABEZADO, ANCHO_CONTENIDO, ALTO_CUERPO)

            pdf.set_font("Helvetica", "", 9)
            y_inicial = y_tabla_inicio + ALTO_ENCABEZADO + 1

            for i, item in enumerate(items):
                y = y_inicial + (i * ALTO_FILA)
                cant = float(item.get("cant", 0) or 0)
                descripcion = str(item.get("descripcion", ""))
                precio_base = float(item.get("precioBase", 0) or 0)
                tiene_iva = item.get("tieneIVA", False)
                total_renglon = float(item.get("subtotal", 0) or 0)

                if cant > 0:
                    pdf.set_xy(MARGEN_IZQ, y)
                    txt_cant = str(int(cant)) if cant.is_integer() else f"{cant:.2f}"
                    pdf.cell(13, 5, text=txt_cant, align='C')

                pdf.set_xy(28, y)
                pdf.cell(100, 5, text=str(descripcion), align='L')

                if precio_base > 0:
                    pdf.set_xy(128, y)
                    pdf.cell(23, 5, text=fmt_monto(precio_base), align='C')

                if cant > 0 and precio_base > 0:
                    pdf.set_xy(151, y)
                    alicuota = "16%" if tiene_iva else "E"
                    pdf.cell(11, 5, text=alicuota, align='C')

                if total_renglon > 0:
                    pdf.set_xy(162, y)
                    pdf.cell(30, 5, text=fmt_monto(total_renglon), align='C')

            # --- RESUMEN DE TOTALES (sin bordes) ---
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(128, Y_TOTALES)
            pdf.cell(32, 5, text="Base Imponible Bs.", border=0, align="L")
            pdf.cell(32, 5, text=str(fmt_monto(totales.get("baseImponible", 0))), border=0, align="R")

            pdf.set_xy(128, Y_TOTALES + 5)
            pdf.cell(32, 5, text="Exento Bs.", border=0, align="L")
            pdf.cell(32, 5, text=str(fmt_monto(totales.get("exento", 0))), border=0, align="R")

            pdf.set_xy(128, Y_TOTALES + 10)
            pdf.cell(32, 5, text="I.V.A. (16%) Bs.", border=0, align="L")
            pdf.cell(32, 5, text=str(fmt_monto(totales.get("iva", 0))), border=0, align="R")

            pdf.set_xy(128, Y_TOTALES + 15)
            pdf.cell(32, 7, text="Total Bs.", border=0, align="L")
            pdf.cell(32, 7, text=str(fmt_monto(totales.get("totalGeneral", 0))), border=0, align="R")

            ruta_salida = f"{nombre_archivo}.pdf"
            pdf.output(ruta_salida)

            return {"exito": True, "mensaje": f"Archivo guardado como: {ruta_salida}"}
        except Exception as e:  # noqa: BLE001
            return {"exito": False, "mensaje": f"Error: {str(e)}"}  # noqa: RUF010

def main():
    api = FacturaAPI()
    html_path = get_resource_path(os.path.join("ui", "index.html"))

    # Crear ventana nativa con motor WebKit
    window = webview.create_window(  # noqa: F841
        title="Generador de Facturas",
        url=html_path,
        js_api=api,
        width=800,
        height=665,
        min_size=(900, 665)
    )
    webview.start()  # debug=True permite clic derecho -> inspeccionar elemento

if __name__ == "__main__":
    main()
