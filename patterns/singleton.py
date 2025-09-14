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
            print("✅ DatabaseManager inicializado (Singleton)")
    
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
        
        if mp_token and mp_token.strip():
            self._mercadopago_token = mp_token.strip()
            self._mercadopago_configurado = True
            
            # determinar si es token de prueba o produccion
            if mp_token.startswith('TEST-'):
                print("✅ MercadoPago configurado - MODO PRUEBA")
                print(f"   - Token: {mp_token[:20]}...")
                print("   - Modo: SANDBOX")
            else:
                print("✅ MercadoPago configurado - MODO PRODUCCIÓN")
                print(f"   - Token: {mp_token[:20]}...")
                print("   - Modo: PRODUCCIÓN")
        else:
            print("❌ MercadoPago NO configurado")
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
            
            # crear preferencia de pago para checkout api
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
                    "success": "http://localhost:5000/carrito/pago-exitoso",
                    "failure": "http://localhost:5000/carrito/pago-fallido",
                    "pending": "http://localhost:5000/carrito/pago-pendiente"
                },
                # configuracion especifica para checkout api
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
                
                print(f"✅ Preferencia creada exitosamente")
                print(f"   - ID: {resultado['response']['id']}")
                print(f"   - URL: {url_pago}")
                
                return {
                    'success': True,
                    'payment_id': resultado['response']['id'],
                    'id_preferencia': resultado['response']['id'],
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
                
                print(f"❌ Error: {error_msg}")
                
                return {
                    'success': False,
                    'message': f"Error de MercadoPago: {error_msg}",
                    'metodo': 'mercadopago'
                }
                
        except Exception as e:
            print(f"❌ Error interno: {e}")
            return {
                'success': False,
                'message': f"Error interno: {str(e)}",
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
