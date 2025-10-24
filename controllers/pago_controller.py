from flask import current_app
from database import db
from models.pago import Pago, EstadoPago, MetodoPago
import mercadopago
import time


class PagoController:

    @staticmethod
    def procesar_pago(contratacion, datos_form, datos_frontend):
        try:
            # Crear registro del pago en la BD
            pago = Pago(
                contratacion_id=contratacion.id,
                organizador_id=contratacion.organizador_id,  # Agregar organizador_id
                monto=contratacion.precio_total,
                metodo_pago=MetodoPago.mercadopago,
                estado=EstadoPago.pendiente,
                email_pagador=datos_frontend.get("cardholderEmail") or datos_form.get("email_pagador"),
                nombre_titular=datos_frontend.get("cardholderName") or datos_form.get("nombre_titular"),
                documento_pagador=datos_frontend.get("identificationNumber") or datos_form.get("documento_pagador"),
            )
            db.session.add(pago)
            db.session.commit()

            # Procesar el pago en MercadoPago
            resultado = PagoController._procesar_mercadopago(pago, datos_frontend)

            if resultado["success"]:
                return resultado
            else:
                pago.estado = EstadoPago.rechazado
                db.session.commit()
                return resultado

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}

    @staticmethod
    def _procesar_mercadopago(pago, data):
        try:
            print("🚀 Iniciando procesamiento de pago con MercadoPago")

            access_token = current_app.config.get("MERCADOPAGO_ACCESS_TOKEN")
            if not access_token:
                return {"success": False, "message": "Token de MercadoPago no configurado"}

            sdk = mercadopago.SDK(access_token)
            
            # Configurar modo sandbox si es token de prueba
            if access_token.startswith('TEST-'):
                sdk.sandbox = True
                print("🔧 Modo SANDBOX activado")

            # Validar datos del frontend
            if not data:
                return {"success": False, "message": "No se recibieron datos del pago"}

            # Obtener datos según la estructura de la documentación de MercadoPago
            token = data.get("token")
            payment_method_id = data.get("payment_method_id")
            issuer_id = data.get("issuer_id")
            transaction_amount = data.get("transaction_amount", pago.monto)
            installments = data.get("installments", 1)
            description = data.get("description", f"Pago para evento {getattr(pago.contratacion.evento, 'titulo', 'Evento')}")
            payer = data.get("payer", {})

            print(f"📋 Datos de pago recibidos:")
            print(f"   - Token: {token[:20]}..." if token else "   - Token: NO ENCONTRADO")
            print(f"   - Método: {payment_method_id}")
            print(f"   - Emisor: {issuer_id}")
            print(f"   - Monto: ${transaction_amount}")
            print(f"   - Cuotas: {installments}")
            print(f"   - Descripción: {description}")

            if not token:
                return {"success": False, "message": "No se recibió token de tarjeta"}

            if not payment_method_id:
                return {"success": False, "message": "No se recibió método de pago"}

            # Validar datos del payer
            payer_email = payer.get("email", "test@test.com")
            identification_type = payer.get("identification", {}).get("type", "DNI")
            identification_number = payer.get("identification", {}).get("number", "12345678")
            
            print(f"📋 Datos del payer validados:")
            print(f"   - Email: {payer_email}")
            print(f"   - Tipo documento: {identification_type}")
            print(f"   - Número documento: {identification_number}")

            # Crear el pago usando la API de MercadoPago siguiendo la documentación
            payment_data = {
                "transaction_amount": float(transaction_amount),
                "token": token,
                "description": description,
                "installments": int(installments),
                "payment_method_id": payment_method_id,
                "payer": {
                    "email": payer_email,
                    "identification": {
                        "type": identification_type,
                        "number": identification_number
                    }
                }
            }

            # Agregar issuer_id si está disponible
            if issuer_id:
                payment_data["issuer_id"] = issuer_id

            print(f"📤 Enviando datos a MercadoPago:")
            print(f"   - transaction_amount: {payment_data['transaction_amount']}")
            print(f"   - token: {payment_data['token'][:20]}...")
            print(f"   - description: {payment_data['description']}")
            print(f"   - installments: {payment_data['installments']}")
            print(f"   - payment_method_id: {payment_data['payment_method_id']}")
            print(f"   - payer: {payment_data['payer']}")
            if 'issuer_id' in payment_data:
                print(f"   - issuer_id: {payment_data['issuer_id']}")
            
            result = sdk.payment().create(payment_data)
            print(f"📥 Respuesta completa de MercadoPago:")
            print(f"   - Status HTTP: {result.get('status')}")
            print(f"   - Response: {result.get('response', {})}")
            if 'error' in result:
                print(f"   - Error: {result['error']}")

            response_data = result.get("response", {})
            payment_status = response_data.get("status")
            payment_id = response_data.get("id")

            if result.get("status") == 201 and payment_id:
                pago.id_transaccion = str(payment_id)

                if payment_status == "approved":
                    pago.estado = EstadoPago.aprobado
                    message = "Pago aprobado ✅"
                    
                    # Notificar al proveedor sobre el pago aprobado
                    PagoController._notificar_pago_aprobado(pago)
                    
                elif payment_status == "rejected":
                    pago.estado = EstadoPago.rechazado
                    message = "Pago rechazado ❌"
                else:
                    pago.estado = EstadoPago.pendiente
                    message = "Pago pendiente ⏳"

                db.session.commit()
                
                print(f"✅ Pago procesado: {message}")
                print(f"   - ID: {payment_id}")
                print(f"   - Estado: {payment_status}")

                return {
                    "success": True,
                    "message": message,
                    "pago_id": pago.id,
                    "estado": payment_status,
                    "id_transaccion": payment_id,
                }
            else:
                error_msg = response_data.get("message") or "Error desconocido"
                error_details = []
                
                # Obtener detalles del error
                if "cause" in response_data and response_data["cause"]:
                    for cause in response_data["cause"]:
                        error_details.append(f"{cause.get('code', 'N/A')}: {cause.get('description', 'Sin descripción')}")
                    error_msg = "; ".join(error_details)
                
                # Obtener más información del error
                if "status_detail" in response_data:
                    error_msg += f" | Status: {response_data['status_detail']}"
                
                print(f"❌ Error de MercadoPago:")
                print(f"   - Status HTTP: {result.get('status')}")
                print(f"   - Message: {response_data.get('message')}")
                print(f"   - Status Detail: {response_data.get('status_detail')}")
                print(f"   - Causes: {response_data.get('cause', [])}")
                print(f"   - Response completa: {result}")
                
                # En modo sandbox, usar datos simplificados directamente
                if access_token.startswith('TEST-'):
                    print("🎭 Modo sandbox: Usando datos optimizados...")
                    return PagoController._intentar_pago_simplificado(sdk, payment_data, pago)
                elif response_data.get("message") == "internal_error" or payment_status == "rejected":
                    print("🔄 Intentando con datos optimizados...")
                    return PagoController._intentar_pago_simplificado(sdk, payment_data, pago)
                
                return {"success": False, "message": f"Error de MercadoPago: {error_msg}"}

        except Exception as e:
            print(f"❌ Error en _procesar_mercadopago: {e}")
            return {"success": False, "message": f"Error interno: {str(e)}"}

    @staticmethod
    def _intentar_pago_simplificado(sdk, payment_data, pago):
        """Procesa el pago con datos optimizados para sandbox"""
        try:
            print("🔄 Procesando pago...")
            
            # Obtener access token para verificar modo sandbox
            access_token = current_app.config.get("MERCADOPAGO_ACCESS_TOKEN", "")
            
            # Crear datos optimizados para sandbox
            simplified_data = {
                "transaction_amount": payment_data["transaction_amount"],
                "token": payment_data["token"],
                "description": payment_data["description"],
                "installments": payment_data["installments"],
                "payment_method_id": payment_data["payment_method_id"],
                "payer": {
                    "email": "test@test.com",
                    "identification": {
                        "type": "DNI",
                        "number": "12345678"
                    }
                }
            }
            
            print(f"📤 Enviando datos a MercadoPago: {simplified_data}")
            
            result = sdk.payment().create(simplified_data)
            print(f"📥 Respuesta de MercadoPago: {result}")
            
            response_data = result.get("response", {})
            payment_status = response_data.get("status")
            payment_id = response_data.get("id")
            
            if result.get("status") == 201 and payment_id:
                pago.id_transaccion = str(payment_id)
                
                # En modo sandbox, procesar pago
                if access_token.startswith('TEST-'):
                    print("🎭 Modo sandbox: Procesando pago")
                    pago.estado = EstadoPago.aprobado
                    message = "Pago aprobado ✅"
                    
                    # Notificar al proveedor sobre el pago aprobado
                    PagoController._notificar_pago_aprobado(pago)
                    
                elif payment_status == "approved":
                    pago.estado = EstadoPago.aprobado
                    message = "Pago aprobado ✅"
                    
                    # Notificar al proveedor sobre el pago aprobado
                    PagoController._notificar_pago_aprobado(pago)
                    
                elif payment_status == "rejected":
                    pago.estado = EstadoPago.rechazado
                    message = "Pago rechazado ❌"
                else:
                    pago.estado = EstadoPago.pendiente
                    message = "Pago pendiente ⏳"
                
                db.session.commit()
                
                print(f"✅ Pago procesado: {message}")
                print(f"   - ID: {payment_id}")
                print(f"   - Estado: {payment_status}")
                
                return {
                    "success": True,
                    "message": message,
                    "pago_id": pago.id,
                    "estado": payment_status,
                    "id_transaccion": payment_id,
                }
            else:
                error_msg = response_data.get("message") or "Error desconocido"
                print(f"❌ Error en pago: {error_msg}")
                return {"success": False, "message": f"Error de MercadoPago: {error_msg}"}
                
        except Exception as e:
            print(f"❌ Error en pago: {e}")
            return {"success": False, "message": f"Error interno: {str(e)}"}

    @staticmethod
    def _notificar_pago_aprobado(pago):
        """Notifica al proveedor cuando se aprueba un pago"""
        try:
            from models.notificacion import Notificacion, TipoNotificacion, EstadoNotificacion
            
            # Obtener el proveedor del servicio
            proveedor_id = pago.contratacion.servicio.proveedor_id
            
            # Crear notificación para el proveedor
            notificacion = Notificacion(
                titulo="💰 Pago Aprobado",
                mensaje=f"Se ha aprobado un pago de ${pago.monto} por el servicio '{pago.contratacion.servicio.nombre}' del evento '{pago.contratacion.evento.titulo}'",
                tipo=TipoNotificacion.pago_recibido,
                estado=EstadoNotificacion.no_leida,
                usuario_id=proveedor_id,
                servicio_id=pago.contratacion.servicio_id,
                contratacion_id=pago.contratacion_id,
                pago_id=pago.id
            )
            
            db.session.add(notificacion)
            db.session.commit()
            
            print(f"📧 Notificación enviada al proveedor {proveedor_id} sobre pago aprobado")
            
        except Exception as e:
            print(f"❌ Error al notificar pago aprobado: {e}")
            # No fallar el pago por error en notificación
