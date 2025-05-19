from flask import jsonify, request, send_file
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import pymongo
from bson.objectid import ObjectId
import numpy as np
import base64
from database.mongodb import Mongodb


db = Mongodb().db()

from bson import ObjectId
from flask import jsonify
from datetime import datetime
import pymongo
from database.mongodb import Mongodb

db = Mongodb().db()

def generar_reporte_ventas():
    try:
        fecha_inicio = request.args.get('fechaInicio')
        fecha_fin = request.args.get('fechaFin')
        agrupacion = request.args.get('agrupacion', 'dia')

        # Validar fechas
        if not fecha_inicio or not fecha_fin:
            return jsonify({"success": False, "message": "Debe especificar ambas fechas"}), 400

        # Convertir las fechas a objetos datetime
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        except ValueError:
            return jsonify({"success": False, "message": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400

        # Consulta para obtener los productos más y menos vendidos (global)
        pipeline_totales = [
            {
                "$match": {
                    "estado": {"$in": ["finalizado", "en transcurso"]},
                    "fecha_confirmacion": {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}
                }
            },
            {"$unwind": "$productos"},
            {
                "$group": {
                    "_id": "$productos.id",
                    "nombre": {"$first": "$productos.name"},
                    "cantidad": {"$sum": "$productos.quantity"},
                    "monto_total": {"$sum": {"$multiply": ["$productos.quantity", "$productos.price"]}}
                }
            },
            {"$sort": {"cantidad": 1}}
        ]

        productos = list(db.pedidos.aggregate(pipeline_totales))

        if not productos:
            return jsonify({"success": False, "message": "No hay datos de ventas en el rango de fechas seleccionado"}), 404

        producto_mas_vendido = productos[-1] if productos else None
        producto_menos_vendido = productos[0] if productos else None

        # Consulta para productos más vendidos por período
        pipeline_mas_vendidos = [
            {
                "$match": {
                    "estado": {"$in": ["finalizado", "en transcurso"]},
                    "fecha_confirmacion": {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}
                }
            },
            {"$unwind": "$productos"},
            {
                "$group": {
                    "_id": {
                        "periodo": {
                            "$dateToString": {
                                "format": get_format_for_agrupacion(agrupacion),
                                "date": "$fecha_confirmacion"
                            }
                        },
                        "producto_id": "$productos.id",
                        "producto_nombre": "$productos.name"
                    },
                    "cantidad": {"$sum": "$productos.quantity"},
                    "monto_total": {"$sum": {"$multiply": ["$productos.quantity", "$productos.price"]}}
                }
            },
            {"$sort": {"_id.periodo": 1, "cantidad": -1}},
            {
                "$group": {
                    "_id": "$_id.periodo",
                    "productos": {
                        "$push": {
                            "nombre": "$_id.producto_nombre",
                            "cantidad": "$cantidad",
                            "monto_total": "$monto_total"
                        }
                    }
                }
            },
            {
                "$project": {
                    "producto_mas_vendido": {"$arrayElemAt": ["$productos", 0]},
                    "otros_productos": {"$slice": ["$productos", 1, 3]}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        productos_mas_vendidos_por_periodo = list(db.pedidos.aggregate(pipeline_mas_vendidos))

        # Consulta para agrupar las ventas por día, semana o mes
        pipeline_agrupacion = [
            {
                "$match": {
                    "estado": {"$in": ["finalizado", "en transcurso"]},
                    "fecha_confirmacion": {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}
                }
            },
            {"$unwind": "$productos"},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": get_format_for_agrupacion(agrupacion),
                            "date": "$fecha_confirmacion"
                        }
                    },
                    "total_ventas": {"$sum": "$productos.quantity"},
                    "monto_total": {"$sum": {"$multiply": ["$productos.quantity", "$productos.price"]}}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        ventas_agrupadas = list(db.pedidos.aggregate(pipeline_agrupacion))

        # Consulta para detalle diario de ventas
        pipeline_detalle_diario = [
            {
                "$match": {
                    "estado": {"$in": ["finalizado", "en transcurso"]},
                    "fecha_confirmacion": {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}
                }
            },
            {
                "$sort": {"fecha_confirmacion": 1}
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$fecha_confirmacion"
                        }
                    },
                    "pedidos": {
                        "$push": {
                            "pedido_id": "$_id",
                            "usuario": "$nombre",
                            "productos": "$productos",
                            "total": "$total"
                        }
                    },
                    "cantidad_total": {"$sum": {"$size": "$productos"}},
                    "monto_total": {"$sum": "$total"}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]

        detalle_ventas_diario = list(db.pedidos.aggregate(pipeline_detalle_diario))

        # Preparar datos para el gráfico
        labels = [venta["_id"] for venta in ventas_agrupadas]
        data = [venta["total_ventas"] for venta in ventas_agrupadas]
        montos = [venta["monto_total"] for venta in ventas_agrupadas]

        # Calcular métricas adicionales
        total_ventas = sum(montos) if montos else 0
        total_productos = sum(data) if data else 0
        
        # Contar clientes únicos
        pipeline_clientes = [
            {
                "$match": {
                    "estado": {"$in": ["finalizado", "en transcurso"]},
                    "fecha_confirmacion": {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}
                }
            },
            {"$group": {"_id": "$usuario_id"}},
            {"$count": "total_clientes"}
        ]
            
        resultado_clientes = list(db.pedidos.aggregate(pipeline_clientes))
        total_clientes = resultado_clientes[0]["total_clientes"] if resultado_clientes else 0
        
        # Calcular ticket promedio
        ticket_promedio = total_ventas / total_clientes if total_clientes > 0 else 0

        # Convertir ObjectId a strings para serialización JSON
        def convert_object_ids(data):
            if isinstance(data, dict):
                return {k: str(v) if isinstance(v, ObjectId) else convert_object_ids(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [convert_object_ids(item) for item in data]
            else:
                return str(data) if isinstance(data, ObjectId) else data

        # Preparar los datos para la respuesta
        response_data = {
            "success": True,
            "productoMasVendido": convert_object_ids(producto_mas_vendido) if producto_mas_vendido else None,
            "productoMenosVendido": convert_object_ids(producto_menos_vendido) if producto_menos_vendido else None,
            "productosMasVendidosPorPeriodo": convert_object_ids(productos_mas_vendidos_por_periodo),
            "detalleVentasDiario": convert_object_ids(detalle_ventas_diario),
            "graficoVentas": {
                "labels": labels,
                "data": data
            },
            "totalVentas": total_ventas,
            "totalProductos": total_productos,
            "totalClientes": total_clientes,
            "ticketPromedio": ticket_promedio
        }

        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error al generar reporte: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Error al generar el reporte: {str(e)}"}), 500

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

def generar_pdf_reporte():
    try:
        fecha_inicio = request.args.get('fechaInicio')
        fecha_fin = request.args.get('fechaFin')
        agrupacion = request.args.get('agrupacion', 'dia')

        # Obtener los datos del reporte
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d') if fecha_inicio else None
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d') if fecha_fin else None

        # Consulta para productos más/menos vendidos
        pipeline_totales = [
            {"$match": {"estado": {"$in": ["finalizado", "en transcurso"]}}},
            {"$unwind": "$productos"},
            {"$group": {
                "_id": "$productos.id",
                "nombre": {"$first": "$productos.name"},
                "cantidad": {"$sum": "$productos.quantity"},
                "monto_total": {"$sum": {"$multiply": ["$productos.quantity", "$productos.price"]}}
            }},
            {"$sort": {"cantidad": 1}}
        ]

        if fecha_inicio_dt and fecha_fin_dt:
            pipeline_totales[0]["$match"]["fecha_confirmacion"] = {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}

        productos = list(db.pedidos.aggregate(pipeline_totales))

        if not productos:
            return jsonify({"success": False, "message": "No hay datos de ventas"}), 404

        producto_mas_vendido = productos[-1]
        producto_menos_vendido = productos[0]

        # Consulta para productos más vendidos por período
        pipeline_mas_vendidos = [
            {"$match": {"estado": {"$in": ["finalizado", "en transcurso"]}}},
            {"$unwind": "$productos"},
            {"$group": {
                "_id": {
                    "periodo": {
                        "$dateToString": {
                            "format": get_format_for_agrupacion(agrupacion),
                            "date": "$fecha_confirmacion"
                        }
                    },
                    "producto_id": "$productos.id",
                    "producto_nombre": {"$first": "$productos.name"}
                },
                "cantidad": {"$sum": "$productos.quantity"},
                "monto_total": {"$sum": {"$multiply": ["$productos.quantity", "$productos.price"]}}
            }},
            {"$sort": {"_id.periodo": 1, "cantidad": -1}},
            {"$group": {
                "_id": "$_id.periodo",
                "producto_mas_vendido": {"$first": {
                    "nombre": "$_id.producto_nombre",
                    "cantidad": "$cantidad",
                    "monto_total": "$monto_total"
                }},
                "otros_productos": {"$push": {
                    "nombre": "$_id.producto_nombre",
                    "cantidad": "$cantidad",
                    "monto_total": "$monto_total"
                }}
            }},
            {"$sort": {"_id": 1}}
        ]

        if fecha_inicio_dt and fecha_fin_dt:
            pipeline_mas_vendidos[0]["$match"]["fecha_confirmacion"] = {"$gte": fecha_inicio_dt, "$lte": fecha_fin_dt}

        productos_mas_vendidos_por_periodo = list(db.pedidos.aggregate(pipeline_mas_vendidos))

        # Consulta para agrupar las ventas
        pipeline_agrupacion = [
            {"$match": {"estado": {"$in": ["finalizado", "en transcurso"]}}},
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

        if fecha_inicio_dt and fecha_fin_dt:
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
            {"$match": {"estado": {"$in": ["finalizado", "en transcurso"]}}},
            {"$group": {"_id": "$usuario_id"}},
            {"$count": "total_clientes"}
        ]
        
        if fecha_inicio_dt and fecha_fin_dt:
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
            ["Producto", "Cantidad", "Monto Total"],
            [f"Más vendido: {producto_mas_vendido['nombre']}", producto_mas_vendido['cantidad'], f"${producto_mas_vendido['monto_total']:,.2f}"],
            [f"Menos vendido: {producto_menos_vendido['nombre']}", producto_menos_vendido['cantidad'], f"${producto_menos_vendido['monto_total']:,.2f}"]
        ]
        
        table = Table(data_table, colWidths=[250, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DB1616')),  # Rojo del tema
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgreen),
            ('BACKGROUND', (0, 2), (-1, 2), colors.lightcoral),
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DB1616')),  # Rojo del tema
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table_resumen)
        elements.append(Spacer(1, 20))
        
        # Productos más vendidos por período
        elements.append(Paragraph("Productos Más Vendidos por Período", subtitle_style))
        elements.append(Spacer(1, 6))
        
        if productos_mas_vendidos_por_periodo:
            for periodo in productos_mas_vendidos_por_periodo:
                # Encabezado del período
                elements.append(Paragraph(f"Período: {periodo['_id']}", styles['Heading3']))
                elements.append(Spacer(1, 6))
                
                # Tabla con el producto más vendido y otros destacados
                periodo_data = [
                    ["Producto", "Cantidad", "Monto Total"],
                    [
                        periodo['producto_mas_vendido']['nombre'], 
                        periodo['producto_mas_vendido']['cantidad'], 
                        f"${periodo['producto_mas_vendido']['monto_total']:,.2f}"
                    ]
                ]
                
                # Agregar hasta 3 productos más destacados (sin incluir el primero que ya está)
                for producto in periodo['otros_productos'][1:4]:
                    periodo_data.append([
                        producto['nombre'], 
                        producto['cantidad'], 
                        f"${producto['monto_total']:,.2f}"
                    ])
                
                periodo_table = Table(periodo_data, colWidths=[250, 100, 100])
                periodo_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DB1616')),  # Rojo del tema
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, 1), colors.lightgreen),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(periodo_table)
                elements.append(Spacer(1, 12))
        else:
            elements.append(Paragraph("No hay datos de productos más vendidos por período", normal_style))
            elements.append(Spacer(1, 12))
        
        elements.append(PageBreak())
        
        # Generar gráfico de ventas
        plt.figure(figsize=(10, 6))
        plt.bar(labels, data, color='#DB1616')  # Usar el color rojo del tema
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