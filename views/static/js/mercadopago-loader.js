/**
 * MercadoPago SDK Loader - Singleton Pattern
 * Garantiza que el SDK se carga UNA SOLA VEZ
 * Ubicación: static/js/mercadopago-loader.js
 */

window.loadMercadoPago = (() => {
    let mpPromise = null;
    let mpInstance = null;
    
    return function(publicKey, options = {}) {
        console.log('🔍 Verificando MercadoPago...');
        
        // Si ya tenemos una instancia, devolverla
        if (mpInstance) {
            console.log('♻️ Reutilizando instancia de MercadoPago existente');
            return Promise.resolve(mpInstance);
        }
        
        // Si ya hay una promesa en curso, devolverla
        if (mpPromise) {
            console.log('⏳ Esperando carga en progreso...');
            return mpPromise;
        }
        
        // Crear nueva promesa de carga
        mpPromise = new Promise((resolve, reject) => {
            // Si MercadoPago ya está cargado globalmente
            if (window.MercadoPago) {
                console.log('✅ MercadoPago SDK ya disponible globalmente');
                try {
                    mpInstance = new window.MercadoPago(publicKey, {
                        locale: options.locale || 'es-CO',
                        ...options
                    });
                    resolve(mpInstance);
                } catch (error) {
                    console.error('❌ Error al inicializar MercadoPago:', error);
                    mpPromise = null;
                    reject(error);
                }
                return;
            }
            
            // Verificar si ya existe el script
            const existingScript = document.querySelector('script[src*="mercadopago.com/js/v2"]');
            if (existingScript) {
                console.log('⏳ Script de MercadoPago ya en el DOM, esperando...');
                
                // Esperar a que se cargue
                const checkInterval = setInterval(() => {
                    if (window.MercadoPago) {
                        clearInterval(checkInterval);
                        try {
                            mpInstance = new window.MercadoPago(publicKey, {
                                locale: options.locale || 'es-CO',
                                ...options
                            });
                            console.log('✅ MercadoPago inicializado desde script existente');
                            resolve(mpInstance);
                        } catch (error) {
                            console.error('❌ Error al inicializar MercadoPago:', error);
                            mpPromise = null;
                            reject(error);
                        }
                    }
                }, 100);
                
                // Timeout después de 10 segundos
                setTimeout(() => {
                    clearInterval(checkInterval);
                    if (!window.MercadoPago) {
                        mpPromise = null;
                        reject(new Error('Timeout esperando MercadoPago SDK'));
                    }
                }, 10000);
                
                return;
            }
            
            // Cargar el script por primera vez
            console.log('📥 Cargando MercadoPago SDK...');
            const script = document.createElement('script');
            script.src = 'https://sdk.mercadopago.com/js/v2';
            script.async = true;
            
            script.onload = () => {
                console.log('✅ MercadoPago SDK cargado exitosamente');
                
                // Verificar que MercadoPago esté disponible
                if (!window.MercadoPago) {
                    mpPromise = null;
                    reject(new Error('MercadoPago no está disponible después de cargar el script'));
                    return;
                }
                
                try {
                    mpInstance = new window.MercadoPago(publicKey, {
                        locale: options.locale || 'es-CO',
                        ...options
                    });
                    console.log('✅ MercadoPago inicializado correctamente');
                    resolve(mpInstance);
                } catch (error) {
                    console.error('❌ Error al inicializar MercadoPago:', error);
                    mpPromise = null;
                    reject(error);
                }
            };
            
            script.onerror = (error) => {
                console.error('❌ Error al cargar MercadoPago SDK:', error);
                mpPromise = null;
                document.head.removeChild(script);
                reject(new Error('Error al cargar el script de MercadoPago'));
            };
            
            document.head.appendChild(script);
            console.log('📤 Script de MercadoPago agregado al DOM');
        });
        
        return mpPromise;
    };
})();

// Log de inicialización
console.log('✅ MercadoPago Loader inicializado');