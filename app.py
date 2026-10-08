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
            pdf.add_page()
            pdf.set_font("Helvetica", size=10)

            # === ENCABEZADO / CLIENTE (Coordenadas milimétricas) ===
            pdf.set_xy(38, 40)
            pdf.cell(150, 8, text=str(cliente.get("nombre", "")), align='L')
            
            pdf.set_xy(31, 48)
            pdf.cell(160, 8, text=str(cliente.get("domicilio", "")), align='L')
            
            pdf.set_xy(5, 66)
            pdf.cell(55, 6, text=str(cliente.get("rif", "")), align='C')

            pdf.set_xy(63, 66)
            pdf.cell(60, 6, text=str(cliente.get("orden", "")), align='C')

            # === FECHA / FACTURA ===
            pdf.set_xy(32, 26)
            pdf.cell(12, 8, text=str(factura.get("fecha", "").get("dia", "")), align='C')

            pdf.set_xy(44, 26)
            pdf.cell(15, 8, text=str(factura.get("fecha", "").get("mes", "")), align='C')

            pdf.set_xy(59, 26)
            pdf.cell(15, 8, text=str(factura.get("fecha", "").get("anio", "")), align='C')
            
            # === RENGLONES DE LA TABLA ===
            y_inicial = 81  # Milímetros desde arriba donde inicia el primer renglón
            alto_fila = 7.65  # Espacio entre cada renglón

            for i, item in enumerate(items):
                y = y_inicial + (i * alto_fila)
                
                cant = float(item.get("cant", 0) or 0)
                descripcion = str(item.get("descripcion", ""))
                precio_base = float(item.get("precioBase", 0) or 0)
                tiene_iva = item.get("tieneIVA", False)
                total_renglon = float(item.get("subtotal", 0) or 0)

                if cant > 0:
                    pdf.set_xy(4, y)
                    # Mostrar entero si no tiene decimales (ej: 2 en vez de 2.0)
                    txt_cant = str(int(cant)) if cant.is_integer() else f"{cant:.2f}"
                    pdf.cell(12, 5, txt=txt_cant, align='C')

                pdf.set_xy(17, y)
                pdf.cell(110, 5, text=str(descripcion), align='L')

                if precio_base > 0:
                    pdf.set_xy(129, y)
                    pdf.cell(25, 5, txt=fmt_monto(precio_base), align='C')

                if cant > 0 and precio_base > 0:
                    pdf.set_xy(155, y)
                    alicuota = "16%" if tiene_iva else "E"
                    pdf.cell(9, 5, txt=alicuota, align='C')

                if total_renglon > 0:
                    pdf.set_xy(167, y)
                    pdf.cell(32, 5, txt=fmt_monto(total_renglon), align='C')

            pdf.set_xy(165, 234)
            pdf.cell(32, 5, text=str(fmt_monto(totales.get("baseImponible", 0))), align='C')

            pdf.set_xy(165, 240)
            pdf.cell(32, 5, text=str(fmt_monto(totales.get("exento", 0))), align='C')

            pdf.set_xy(165, 247)
            pdf.cell(32, 5, text=str(fmt_monto(totales.get("iva", 0))), align='C')

            pdf.set_xy(136, 248)
            pdf.cell(25, 4, text=str(fmt_monto(totales.get("baseImponible", 0))), align='C')
            pdf.set_xy(110, 248)
            pdf.cell(6, 4, text="16", align='C')

            pdf.set_xy(165, 254)
            pdf.cell(32, 5, text=str(fmt_monto(totales.get("totalGeneral", 0))), align='C')

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