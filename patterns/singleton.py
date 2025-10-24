import os
import time
import mercadopago
from flask import current_app

class DatabaseManager:
    # singleton para gestion de conexiones a bd
    
    _instancia = None
    _inicializado = False
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(DatabaseManager, cls).__new__(cls)
        return cls._instancia
    
    def __init__(self):
        if not self._inicializado:
            self._inicializado = True
            print("[OK] DatabaseManager inicializado (Singleton)")
    
    def get_connection(self):
        # obtiene una conexion a la base de datos
        return current_app.db

class PaymentGateway:
    # singleton para gestion de pagos con mercadopago
    
    _instancia = None
    _inicializado = False
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(PaymentGateway, cls).__new__(cls)
        return cls._instancia
    
    def __init__(self):
        if not self._inicializado:
            self._mercadopago_configurado = False
            self._mercadopago_token = None
            self._estadisticas = {
                'pagos_mercadopago': 0,
                'pagos_exitosos': 0,
                'pagos_fallidos': 0
            }
            self._configurar_pasarelas()
            self._inicializado = True
    
    def _configurar_pasarelas(self):
        # configura mercadopago desde cero
        mp_token = os.environ.get('MERCADOPAGO_ACCESS_TOKEN')
        
        # si no hay token en variables de entorno, usar token fijo para pruebas
        if not mp_token or not mp_token.strip():
            mp_token = "TEST-4157849620035829-091318-914e52c84a25ee69d717188c213520c2-812982447"
            print("[WARN] Usando token de prueba fijo ")
        
        if mp_token and mp_token.strip():
            self._mercadopago_token = mp_token.strip()
            self._mercadopago_configurado = True
            
            # determinar si es token de prueba o produccion
            if mp_token.startswith('TEST-'):
                print("[OK] MercadoPago configurado - MODO PRUEBA")
                print(f"   - Token: {mp_token[:20]}...")
                print("   - Modo: SANDBOX")
            else:
                print("[OK] MercadoPago configurado - MODO PRODUCCION")
                print(f"   - Token: {mp_token[:20]}...")
                print("   - Modo: PRODUCCIÓN")
        else:
            print("[ERROR] MercadoPago NO configurado")
            print("   - Configura la variable de entorno MERCADOPAGO_ACCESS_TOKEN")
            print("   - Obtén tu token en: https://www.mercadopago.com.co/developers")
            self._mercadopago_configurado = False
    
    def procesar_pago_mercadopago(self, monto, descripcion, email_pagador, datos_tarjeta=None):
        # procesa un pago usando mercadopago
        if not self._mercadopago_configurado:
            return {
                'success': False, 
                'message': 'MercadoPago no configurado. Configura MERCADOPAGO_ACCESS_TOKEN', 
                'metodo': 'mercadopago'
            }
        
        # validaciones basicas
        if not email_pagador or '@' not in email_pagador:
            return {
                'success': False, 
                'message': 'Email de pagador inválido', 
                'metodo': 'mercadopago'
            }
        
        if float(monto) <= 0:
            return {
                'success': False, 
                'message': 'Monto inválido', 
                'metodo': 'mercadopago'
            }
        
        try:
            print(f"🔄 Procesando pago con MercadoPago:")
            print(f"   - Monto: ${monto}")
            print(f"   - Descripción: {descripcion}")
            print(f"   - Email: {email_pagador}")
            
            # inicializar sdk de mercadopago
            sdk = mercadopago.SDK(self._mercadopago_token)
            
            # configurar modo sandbox si es token de prueba
            if self._mercadopago_token.startswith('TEST-'):
                sdk.sandbox = True
                print("   - Modo: SANDBOX")
            else:
                print("   - Modo: PRODUCCIÓN")
            
            # crear preferencia para checkout pro (permite seleccionar metodo de pago)
            preferencia = {
                "items": [
                    {
                        "title": descripcion,
                        "quantity": 1,
                        "unit_price": float(monto),
                        "currency_id": "COP"
                    }
                ],
                "payer": {
                    "email": email_pagador
                },
                "external_reference": f"eventlink_{int(time.time())}",
                "notification_url": "https://webhook.site/mercadopago-eventlink",
                "back_urls": {
                    "success": "https://webhook.site/mercadopago-success",
                    "failure": "https://webhook.site/mercadopago-failure", 
                    "pending": "https://webhook.site/mercadopago-pending"
                },
                # configuracion para checkout pro
                "payment_methods": {
                    "excluded_payment_methods": [],
                    "excluded_payment_types": [],
                    "installments": 12
                }
            }
            
            # crear preferencia
            resultado = sdk.preference().create(preferencia)
            
            if resultado["status"] == 201:
                # actualizar estadisticas
                self._estadisticas['pagos_mercadopago'] += 1
                self._estadisticas['pagos_exitosos'] += 1
                
                # obtener url de pago
                url_pago = resultado['response'].get('sandbox_init_point', resultado['response']['init_point'])
                payment_id = resultado['response']['id']
                
                print(f"[OK] Preferencia creada exitosamente")
                print(f"   - ID: {payment_id}")
                print(f"   - URL: {url_pago}")
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'id_preferencia': payment_id,
                    'url_pago': url_pago,
                    'monto': monto,
                    'metodo': 'mercadopago',
                    'estado': 'pending',
                    'modo': 'sandbox' if 'sandbox' in url_pago else 'produccion'
                }
            else:
                # error en la creacion
                error_msg = resultado.get("message", "Error desconocido")
                if "response" in resultado and "message" in resultado["response"]:
                    error_msg = resultado["response"]["message"]
                
                print(f"[ERROR] Error: {error_msg}")
                
                return {
                    'success': False,
                    'message': f"Error de MercadoPago: {error_msg}",
                    'metodo': 'mercadopago'
                }
                
        except Exception as e:
            print(f"[ERROR] Error interno: {e}")
            return {
                'success': False,
                'message': f"Error interno: {str(e)}",
                'metodo': 'mercadopago'
            }
    
    def procesar_pago_checkout_api(self, monto, descripcion, token, payment_method_id, installments=1, issuer_id=None, payer=None):
        """
        Procesa un pago usando Checkout API (pago directo con token de tarjeta)
        
        Args:
            monto (float): Monto del pago
            descripcion (str): Descripcion del pago
            token (str): Token de la tarjeta generado por MercadoPago.js
            payment_method_id (str): ID del metodo de pago (visa, mastercard, etc.)
            installments (int): Numero de cuotas
            issuer_id (str): ID del emisor de la tarjeta
            payer (dict): Datos del pagador
            
        Returns:
            dict: Resultado del pago
        """
        # verificar que mercadopago este configurado
        if not self._mercadopago_configurado:
            return {
                'success': False, 
                'message': 'MercadoPago no configurado. Configura MERCADOPAGO_ACCESS_TOKEN', 
                'metodo': 'mercadopago'
            }
        
        # validaciones basicas
        if not token or not token.strip():
            return {
                'success': False, 
                'message': 'Token de tarjeta requerido', 
                'metodo': 'mercadopago'
            }
        
        if not payment_method_id:
            return {
                'success': False, 
                'message': 'Método de pago requerido', 
                'metodo': 'mercadopago'
            }
        
        if float(monto) <= 0:
            return {
                'success': False, 
                'message': 'Monto inválido', 
                'metodo': 'mercadopago'
            }
        
        try:
            print(f"🔄 Procesando pago con Checkout API:")
            print(f"   - Monto: ${monto}")
            print(f"   - Descripción: {descripcion}")
            print(f"   - Método: {payment_method_id}")
            print(f"   - Cuotas: {installments}")
            
            # inicializar sdk de mercadopago
            sdk = mercadopago.SDK(self._mercadopago_token)
            
            # configurar modo sandbox si es token de prueba
            if self._mercadopago_token.startswith('TEST-'):
                sdk.sandbox = True
                print("   - Modo: SANDBOX")
            else:
                print("   - Modo: PRODUCCIÓN")
            
            # crear pago directo con checkout api
            payment_data = {
                "transaction_amount": float(monto),
                "token": token,
                "description": descripcion,
                "installments": int(installments),
                "payment_method_id": payment_method_id,
                "payer": payer or {
                    "email": "test@test.com"
                }
            }
            
            # agregar issuer_id si esta disponible
            if issuer_id:
                payment_data["issuer_id"] = issuer_id
            
            # crear pago directo
            print(f"📤 Enviando datos a MercadoPago: {payment_data}")
            resultado = sdk.payment().create(payment_data)
            print(f"📥 Respuesta de MercadoPago: {resultado}")
            
            if resultado["status"] == 201:
                # actualizar estadisticas
                self._estadisticas['pagos_mercadopago'] += 1
                self._estadisticas['pagos_exitosos'] += 1
                
                # obtener estado del pago
                payment_status = resultado['response'].get('status', 'pending')
                payment_id = resultado['response']['id']
                
                print(f"[OK] Pago procesado exitosamente")
                print(f"   - ID: {payment_id}")
                print(f"   - Estado: {payment_status}")
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'monto': monto,
                    'metodo': 'mercadopago',
                    'estado': payment_status,
                    'modo': 'sandbox' if self._mercadopago_token.startswith('TEST-') else 'produccion',
                    'response': resultado['response']
                }
            else:
                # error en la creacion
                error_msg = resultado.get("message", "Error desconocido")
                if "response" in resultado and "message" in resultado["response"]:
                    error_msg = resultado["response"]["message"]
                elif "response" in resultado and "cause" in resultado["response"]:
                    error_msg = resultado["response"]["cause"][0].get("description", error_msg)
                
                print(f"[ERROR] Error al crear el pago: {error_msg}")
                print(f"[ERROR] Resultado completo: {resultado}")
                
                return {
                    'success': False,
                    'message': f'Error de MercadoPago: {error_msg}',
                    'metodo': 'mercadopago'
                }
                
        except Exception as e:
            print(f"[ERROR] Error en procesar_pago_checkout_api: {e}")
            return {
                'success': False,
                'message': f'Error interno: {str(e)}',
                'metodo': 'mercadopago'
            }
    
    def get_estadisticas(self):
        # retorna estadisticas de pagos
        return self._estadisticas.copy()
    
    def reset_estadisticas(self):
        # reinicia las estadisticas
        self._estadisticas = {
            'pagos_mercadopago': 0,
            'pagos_exitosos': 0,
            'pagos_fallidos': 0
        }

# instancias globales de singletons
db_manager = DatabaseManager()
payment_gateway = PaymentGateway()
