import os
import sys

import webview
from fpdf import FPDF


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

            # --- Encabezado Principal ---
            pdf.set_font("Helvetica", "B", 14)

            # --- Cuadro de Datos de Factura / Fecha ---
            #pdf.rect(140, 15, 60, 25)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_xy(140, 19)
            pdf.cell(60, 5, text="FECHA DE EMISIÓN", border=0, align="C")

            # Sub-tabla para Día / Mes / Año
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_xy(145, 23)
            pdf.cell(15, 5, text="DÍA", border=1, align="C")
            pdf.cell(18, 5, text="MES", border=1, align="C")
            pdf.cell(17, 5, text="AÑO", border=1, align="C")

            pdf.set_font("Helvetica", "", 10)
            pdf.set_xy(145, 28)
            pdf.cell(15, 5, text=str(factura.get("fecha", "").get("dia", "")), border=1, align="C")
            pdf.cell(18, 5, text=str(factura.get("fecha", "").get("mes", "")), border=1, align="C")
            pdf.cell(17, 5, text=str(factura.get("fecha", "").get("anio", "")), border=1, align="C")

            # --- Cuadro de Datos del Cliente ---
            pdf.rect(14, 35, 186, 23)

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(16, 36)
            pdf.cell(32, 6, text="Nombre / Razón:", border=0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(150, 6, text=str(cliente.get("nombre", "")), border="B")

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(16, 43)
            pdf.cell(32, 6, text="Domicilio Fiscal:", border=0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(150, 6, text=str(cliente.get("domicilio", "")), border="B")

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(16, 50)
            pdf.cell(20, 6, text="C.I / RIF:", border=0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(30, 6, text=str(cliente.get("rif", "")), border="B", align="C")

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(72, 50)
            pdf.cell(28, 6, text="N° Orden / Guía:", border=0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(30, 6, text=str(cliente.get("orden", "")), border="B", align="C")

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(137, 50)
            pdf.cell(28, 6, text="Metodo de Pago:", border=0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(30, 6, text="X DEFINIR", border="B", align="C")
            
            # === RENGLONES DE LA TABLA ===
            y_tabla_inicio = 60
            alto_fila = 6  # Espacio entre cada renglón

            pdf.set_font("Helvetica", "B", 8)
            pdf.set_xy(14, y_tabla_inicio)
            pdf.cell(13, 6, text="CANT.", border=1, align="C")
            pdf.cell(107, 6, text="DESCRIPCIÓN / CONCEPTO", border=1, align="C")
            pdf.cell(24, 6, text="P. UNITARIO", border=1, align="C")
            pdf.cell(11, 6, text="ALÍC.", border=1, align="C")
            pdf.cell(31, 6, text="SUBTOTAL", border=1, align="C")

            alto_cuerpo_tabla = 165 
            pdf.rect(14, y_tabla_inicio + 6, 186, alto_cuerpo_tabla)

            pdf.set_font("Helvetica", "", 9)
            y_inicial = y_tabla_inicio + 7
            alto_fila = 6

            for i, item in enumerate(items):
                y = y_inicial + (i * alto_fila)
                cant = float(item.get("cant", 0) or 0)
                descripcion = str(item.get("descripcion", ""))
                precio_base = float(item.get("precioBase", 0) or 0)
                tiene_iva = item.get("tieneIVA", False)
                total_renglon = float(item.get("subtotal", 0) or 0)

                if cant > 0:
                    pdf.set_xy(14, y)
                    txt_cant = str(int(cant)) if cant.is_integer() else f"{cant:.2f}"
                    pdf.cell(13, 5, text=txt_cant, align='C')

                pdf.set_xy(28, y)
                pdf.cell(105, 5, text=str(descripcion), align='L')

                if precio_base > 0:
                    pdf.set_xy(134, y)
                    pdf.cell(24, 5, text=fmt_monto(precio_base), align='C')

                if cant > 0 and precio_base > 0:
                    pdf.set_xy(158, y)
                    alicuota = "16%" if tiene_iva else "E"
                    pdf.cell(11, 5, text=alicuota, align='C')

                if total_renglon > 0:
                    pdf.set_xy(169, y)
                    pdf.cell(31, 5, text=fmt_monto(total_renglon), align='C')

            # --- RESUMEN DE TOTALES ---
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(135, 233)
            pdf.cell(32, 5, text="Base Imponible Bs.", border=1, align="L")
            pdf.cell(32, 5, text=str(fmt_monto(totales.get("baseImponible", 0))), border=1, align="R")

            pdf.set_xy(135, 238)
            pdf.cell(32, 5, text="Exento Bs.", border=1, align="L")
            pdf.cell(32, 5, text=str(fmt_monto(totales.get("exento", 0))), border=1, align="R")

            pdf.set_xy(135, 243)
            pdf.cell(32, 5, text="I.V.A. (16%)", border=1, align="L")
            pdf.cell(32, 5, text=str(fmt_monto(totales.get("iva", 0))), border=1, align="R")

            pdf.set_xy(135, 248)
            pdf.cell(32, 7, text="Total Bs.", border=1, align="L")
            pdf.cell(32, 7, text=str(fmt_monto(totales.get("totalGeneral", 0))), border=1, align="R")

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
    webview.start(debug=True)  # debug=True permite clic derecho -> inspeccionar elemento

if __name__ == "__main__":
    main()