from flask import jsonify, request, send_file
import io
import matplotlib
matplotlib.use('Agg')  # Configurar matplotlib para usar sin interfaz gráfica
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import pymongo
from bson.objectid import ObjectId
import numpy as np
import base64
from database.mongodb import Mongodb

db = Mongodb().db()

def generar_reporte_ventas():
    try:
        fecha_inicio = request.args.get('fechaInicio')
        fecha_fin = request.args.get('fechaFin')
        agrupacion = request.args.get('agrupacion', 'dia')  # Por defecto, agrupar por día

        # Convertir las fechas a objetos datetime
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d') if fecha_inicio else None
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d') if fecha_fin else None

        # Consulta para obtener los productos más y menos vendidos
        pipeline = [
            {"$match": {"estado": {"$in": ["finalizado", "en transcurso"]}}},  # Incluir ambos estados
            {"$unwind": "$productos"},
            {"$group": {
                "_id": "$productos.id",
                "nombre": {"$first": "$productos.name"},
                "cantidad": {"$sum": "$productos.quantity"}
            }},
            {"$sort": {"cantidad": 1}}
        ]

        if fecha_inicio and fecha_fin:
            pipeline[0]["$match"]["fecha_confirmacion"] = {"$gte": fecha_inicio, "$lte": fecha_fin}

        productos = list(db.pedidos.aggregate(pipeline))

        if not productos:
            return jsonify({"success": False, "message": "No hay datos de ventas en el rango de fechas seleccionado"}), 404

        producto_mas_vendido = productos[-1]
        producto_menos_vendido = productos[0]

        # Consulta para agrupar las ventas por día, semana o mes
        pipeline_agrupacion = [
            {"$match": {"estado": {"$in": ["finalizado", "en transcurso"]}}},  # Incluir ambos estados
            {"$unwind": "$productos"},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": get_format_for_agrupacion(agrupacion),
                        "date": "$fecha_confirmacion"
                    }
                },
                "total_ventas": {"$sum": "$productos.quantity"},
                "monto_total": {"$sum": {"$multiply": ["$productos.quantity", "$productos.price"]}}
            }},
            {"$sort": {"_id": 1}}
        ]

        if fecha_inicio and fecha_fin:
            pipeline_agrupacion[0]["$match"]["fecha_confirmacion"] = {"$gte": fecha_inicio, "$lte": fecha_fin}

        ventas_agrupadas = list(db.pedidos.aggregate(pipeline_agrupacion))

        # Preparar datos para el gráfico
        labels = [venta["_id"] for venta in ventas_agrupadas]
        data = [venta["total_ventas"] for venta in ventas_agrupadas]
        montos = [venta["monto_total"] for venta in ventas_agrupadas]

        # Calcular métricas adicionales
        total_ventas = sum(montos) if montos else 0
        total_productos = sum(data) if data else 0
        
        # Contar clientes únicos
        pipeline_clientes = [
            {"$match": {"estado": {"$in": ["finalizado", "en transcurso"]}}},  # Incluir ambos estados
            {"$group": {"_id": "$usuario_id"}},
            {"$count": "total_clientes"}
        ]
        
        if fecha_inicio and fecha_fin:
            pipeline_clientes[0]["$match"]["fecha_confirmacion"] = {"$gte": fecha_inicio, "$lte": fecha_fin}
            
        resultado_clientes = list(db.pedidos.aggregate(pipeline_clientes))
        total_clientes = resultado_clientes[0]["total_clientes"] if resultado_clientes else 0
        
        # Calcular ticket promedio
        ticket_promedio = total_ventas / total_clientes if total_clientes > 0 else 0

        return jsonify({
            "success": True,
            "productoMasVendido": producto_mas_vendido,
            "productoMenosVendido": producto_menos_vendido,
            "graficoVentas": {
                "labels": labels,
                "data": data
            },
            "totalVentas": total_ventas,
            "totalProductos": total_productos,
            "totalClientes": total_clientes,
            "ticketPromedio": ticket_promedio
        }), 200

    except Exception as e:
        print(f"Error al generar reporte: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

def generar_pdf_reporte():
    try:
        fecha_inicio = request.args.get('fechaInicio')
        fecha_fin = request.args.get('fechaFin')
        agrupacion = request.args.get('agrupacion', 'dia')

        # Obtener los datos del reporte (reutilizando la lógica existente)
        # Aquí podrías llamar a una función que obtenga los mismos datos que generar_reporte_ventas
        # pero sin convertirlos a JSON
        
        # Consulta para obtener los productos más y menos vendidos
        pipeline = [
            {"$match": {"estado": {"$in": ["finalizado", "en transcurso"]}}},  # Incluir ambos estados
            {"$unwind": "$productos"},
            {"$group": {
                "_id": "$productos.id",
                "nombre": {"$first": "$productos.name"},
                "cantidad": {"$sum": "$productos.quantity"}
            }},
            {"$sort": {"cantidad": 1}}
        ]

        if fecha_inicio and fecha_fin:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
            pipeline[0]["$match"]["fecha_confirmacion"] = {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}

        productos = list(db.pedidos.aggregate(pipeline))

        if not productos:
            return jsonify({"success": False, "message": "No hay datos de ventas en el rango de fechas seleccionado"}), 404

        producto_mas_vendido = productos[-1]
        producto_menos_vendido = productos[0]

        # Consulta para agrupar las ventas
        pipeline_agrupacion = [
            {"$match": {"estado": {"$in": ["finalizado", "en transcurso"]}}},  # Incluir ambos estados
            {"$unwind": "$productos"},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": get_format_for_agrupacion(agrupacion),
                        "date": "$fecha_confirmacion"
                    }
                },
                "total_ventas": {"$sum": "$productos.quantity"},
                "monto_total": {"$sum": {"$multiply": ["$productos.quantity", "$productos.price"]}}
            }},
            {"$sort": {"_id": 1}}
        ]

        if fecha_inicio and fecha_fin:
            pipeline_agrupacion[0]["$match"]["fecha_confirmacion"] = {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}

        ventas_agrupadas = list(db.pedidos.aggregate(pipeline_agrupacion))
        
        # Preparar datos para el gráfico
        labels = [venta["_id"] for venta in ventas_agrupadas]
        data = [venta["total_ventas"] for venta in ventas_agrupadas]
        montos = [venta["monto_total"] for venta in ventas_agrupadas]
        
        # Calcular métricas adicionales
        total_ventas = sum(montos) if montos else 0
        total_productos = sum(data) if data else 0
        
        # Contar clientes únicos
        pipeline_clientes = [
            {"$match": {"estado": {"$in": ["finalizado", "en transcurso"]}}},  # Incluir ambos estados
            {"$group": {"_id": "$usuario_id"}},
            {"$count": "total_clientes"}
        ]
        
        if fecha_inicio and fecha_fin:
            pipeline_clientes[0]["$match"]["fecha_confirmacion"] = {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}
            
        resultado_clientes = list(db.pedidos.aggregate(pipeline_clientes))
        total_clientes = resultado_clientes[0]["total_clientes"] if resultado_clientes else 0
        ticket_promedio = total_ventas / total_clientes if total_clientes > 0 else 0
        
        # Crear un buffer para el PDF
        buffer = io.BytesIO()
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Estilos para el PDF
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Título del reporte
        elements.append(Paragraph(f"Reporte de Ventas", title_style))
        elements.append(Spacer(1, 12))
        
        # Período del reporte
        elements.append(Paragraph(f"Período: {fecha_inicio} a {fecha_fin}", subtitle_style))
        elements.append(Paragraph(f"Agrupado por: {agrupacion}", normal_style))
        elements.append(Spacer(1, 12))
        
        # Productos más y menos vendidos
        elements.append(Paragraph("Productos Destacados", subtitle_style))
        elements.append(Spacer(1, 6))
        
        # Tabla de productos destacados
        data_table = [
            ["Producto", "Cantidad"],
            [f"Más vendido: {producto_mas_vendido['nombre']}", producto_mas_vendido['cantidad']],
            [f"Menos vendido: {producto_menos_vendido['nombre']}", producto_menos_vendido['cantidad']]
        ]
        
        table = Table(data_table, colWidths=[300, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (1, 1), colors.lightgreen),
            ('BACKGROUND', (0, 2), (1, 2), colors.lightcoral),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Resumen de ventas
        elements.append(Paragraph("Resumen de Ventas", subtitle_style))
        elements.append(Spacer(1, 6))
        
        # Tabla de resumen
        data_resumen = [
            ["Métrica", "Valor"],
            ["Ventas Totales", f"${total_ventas:,.2f}"],
            ["Productos Vendidos", total_productos],
            ["Total Clientes", total_clientes],
            ["Ticket Promedio", f"${ticket_promedio:,.2f}"]
        ]
        
        table_resumen = Table(data_resumen, colWidths=[300, 100])
        table_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table_resumen)
        elements.append(Spacer(1, 20))
        
        # Generar gráfico de ventas
        plt.figure(figsize=(10, 6))
        plt.bar(labels, data)
        plt.title('Ventas por Período')
        plt.xlabel('Fecha')
        plt.ylabel('Cantidad Vendida')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Guardar el gráfico en un buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        # Añadir el gráfico al PDF
        elements.append(Paragraph("Gráfico de Ventas", subtitle_style))
        elements.append(Spacer(1, 6))
        
        img = Image(img_buffer, width=450, height=300)
        elements.append(img)
        
        # Crear el PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Enviar el PDF como respuesta
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"reporte_ventas_{fecha_inicio}_{fecha_fin}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error al generar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

def get_format_for_agrupacion(agrupacion):
    """Devuelve el formato de fecha según la agrupación seleccionada."""
    if agrupacion == "dia":
        return "%Y-%m-%d"  # Agrupar por día
    elif agrupacion == "semana":
        return "%Y-%U"  # Agrupar por semana (año y número de semana)
    elif agrupacion == "mes":
        return "%Y-%m"  # Agrupar por mes
    else:
        return "%Y-%m-%d"  # Por defecto, agrupar por día