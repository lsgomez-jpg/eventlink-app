# controlador de usuarios

from flask import request, session, flash, redirect, url_for, render_template, jsonify
from models.usuario import Usuario
from models.evento import Evento
from models.servicio import Servicio
from database import db
from datetime import datetime
import re

class UsuarioController:
    
    @staticmethod
    def registro():
        # maneja el registro de usuarios organizadores y proveedores
        if request.method == 'GET':
            return render_template('registro.html')
        
        # obtener datos del formulario
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip().lower()
        contraseña = request.form.get('contraseña', '').strip()
        confirmar_contraseña = request.form.get('confirmar_contraseña', '').strip()
        rol = request.form.get('rol', '').strip()
        
        # validaciones de entrada
        errores = UsuarioController._validar_datos_registro(
            nombre, correo, contraseña, confirmar_contraseña, rol
        )
        
        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('registro.html')
        
        # Verificar si el usuario ya existe
        if UsuarioController._usuario_existe(correo):
            flash('Ya existe una cuenta con este correo electrónico', 'error')
            return render_template('registro.html')
        
        try:
            # Crear nuevo usuario
            nuevo_usuario = Usuario(
                nombre=nombre,
                correo=correo,
                contraseña=contraseña,
                rol=rol
            )
            
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            # Crear notificación de bienvenida
            UsuarioController._crear_notificacion_bienvenida(nuevo_usuario.id, rol)
            
            flash(f'¡Bienvenido a EventLink! Tu cuenta de {rol} ha sido creada exitosamente.', 'success')
            return redirect(url_for('usuario.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error interno del servidor. Intenta nuevamente.', 'error')
            return render_template('registro.html')
    
    @staticmethod
    def login():
        """Maneja el inicio de sesión de usuarios"""
        if request.method == 'GET':
            # Si ya está logueado, redirigir a su dashboard
            if 'user_id' in session:
                return UsuarioController._redirect_to_dashboard()
            return render_template('login.html')
        
        correo = request.form.get('correo', '').strip().lower()
        contraseña = request.form.get('contraseña', '').strip()
        
        # Validaciones básicas
        if not correo or not contraseña:
            flash('Correo y contraseña son obligatorios', 'error')
            return render_template('login.html')
        
        # Buscar usuario en la base de datos
        usuario = Usuario.query.filter_by(correo=correo, activo=True).first()
        
        if not usuario:
            flash('Correo no registrado', 'error')
            return render_template('login.html')
        
        if not usuario.check_password(contraseña):
            flash('Contraseña incorrecta', 'error')
            return render_template('login.html')
        
        # Crear sesión
        UsuarioController._crear_sesion(usuario)
        
        flash(f'¡Bienvenido de vuelta, {usuario.nombre}!', 'success')
        return UsuarioController._redirect_to_dashboard()
    
    @staticmethod
    def logout():
        """Cierra la sesión del usuario"""
        usuario_nombre = session.get('user_nombre', '')
        session.clear()
        flash(f'¡Hasta luego, {usuario_nombre}! Sesión cerrada exitosamente.', 'success')
        return redirect(url_for('index'))
    
    @staticmethod
    def perfil():
        """Muestra y actualiza el perfil del usuario"""
        if not UsuarioController._usuario_autenticado():
            return UsuarioController._acceso_no_autorizado()
        
        usuario = Usuario.query.get(session['user_id'])
        
        if request.method == 'GET':
            return render_template('perfil.html', usuario=usuario)
        
        # Actualizar perfil
        nombre = request.form.get('nombre', '').strip()
        
        if not nombre:
            flash('El nombre es obligatorio', 'error')
            return render_template('perfil.html', usuario=usuario)
        
        try:
            usuario.nombre = nombre
            db.session.commit()
            
            # Actualizar la sesión
            session['user_nombre'] = nombre
            
            flash('Perfil actualizado exitosamente', 'success')
            return render_template('perfil.html', usuario=usuario)
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el perfil', 'error')
            return render_template('perfil.html', usuario=usuario)
    
    @staticmethod
    def cambiar_contraseña():
        """Permite cambiar la contraseña del usuario"""
        if not UsuarioController._usuario_autenticado():
            return UsuarioController._acceso_no_autorizado()
        
        if request.method == 'GET':
            return render_template('cambiar_contraseña.html')
        
        contraseña_actual = request.form.get('contraseña_actual', '').strip()
        nueva_contraseña = request.form.get('nueva_contraseña', '').strip()
        confirmar_nueva = request.form.get('confirmar_nueva', '').strip()
        
        usuario = Usuario.query.get(session['user_id'])
        
        # Validaciones
        if not usuario.check_password(contraseña_actual):
            flash('La contraseña actual es incorrecta', 'error')
            return render_template('cambiar_contraseña.html')
        
        if len(nueva_contraseña) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('cambiar_contraseña.html')
        
        if nueva_contraseña != confirmar_nueva:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('cambiar_contraseña.html')
        
        try:
            usuario.set_password(nueva_contraseña)
            db.session.commit()
            
            flash('Contraseña cambiada exitosamente', 'success')
            return redirect(url_for('usuario.perfil'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al cambiar la contraseña', 'error')
            return render_template('cambiar_contraseña.html')
    
    @staticmethod
    def olvide_contraseña():
        """Maneja el proceso de recuperar contraseña"""
        if request.method == 'GET':
            return render_template('olvide_contraseña.html')
        
        correo = request.form.get('correo', '').strip().lower()
        nueva_contraseña = request.form.get('nueva_contraseña', '').strip()
        confirmar_contraseña = request.form.get('confirmar_contraseña', '').strip()
        
        # Validaciones básicas
        if not correo or not nueva_contraseña or not confirmar_contraseña:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('olvide_contraseña.html')
        
        if len(nueva_contraseña) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('olvide_contraseña.html')
        
        if nueva_contraseña != confirmar_contraseña:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('olvide_contraseña.html')
        
        # Buscar usuario en la base de datos
        usuario = Usuario.query.filter_by(correo=correo, activo=True).first()
        
        if not usuario:
            flash('No existe una cuenta registrada con este correo electrónico', 'error')
            return render_template('olvide_contraseña.html')
        
        try:
            # Actualizar contraseña
            usuario.set_password(nueva_contraseña)
            usuario.fecha_actualizacion = datetime.utcnow()
            db.session.commit()
            
            flash('Contraseña actualizada exitosamente. Ya puedes iniciar sesión con tu nueva contraseña.', 'success')
            return redirect(url_for('usuario.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la contraseña. Intenta nuevamente.', 'error')
            return render_template('olvide_contraseña.html')
    
    
    @staticmethod
    def estadisticas():
        """Muestra estadísticas del usuario según su rol"""
        if not UsuarioController._usuario_autenticado():
            return UsuarioController._acceso_no_autorizado()
        
        user_id = session['user_id']
        user_rol = session['user_rol']
        
        if user_rol == 'organizador':
            return UsuarioController._estadisticas_organizador(user_id)
        else:
            return UsuarioController._estadisticas_proveedor(user_id)
    
    @staticmethod
    def desactivar_cuenta():
        """Desactiva la cuenta del usuario"""
        if not UsuarioController._usuario_autenticado():
            return UsuarioController._acceso_no_autorizado()
        
        if request.method == 'POST':
            contraseña = request.form.get('contraseña', '').strip()
            
            usuario = Usuario.query.get(session['user_id'])
            
            if not usuario.check_password(contraseña):
                flash('Contraseña incorrecta', 'error')
                return render_template('desactivar_cuenta.html')
            
            try:
                usuario.activo = False
                db.session.commit()
                
                session.clear()
                flash('Tu cuenta ha sido desactivada. ¡Esperamos verte pronto!', 'success')
                return redirect(url_for('index'))
                
            except Exception as e:
                db.session.rollback()
                flash('Error al desactivar la cuenta', 'error')
                return render_template('desactivar_cuenta.html')
        
        return render_template('desactivar_cuenta.html')
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    @staticmethod
    def _validar_datos_registro(nombre, correo, contraseña, confirmar_contraseña, rol):
        """Valida los datos del formulario de registro"""
        errores = []
        
        # Validar nombre
        if not nombre or len(nombre) < 2:
            errores.append('El nombre debe tener al menos 2 caracteres')
        
        # Validar correo
        if not correo:
            errores.append('El correo es obligatorio')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', correo):
            errores.append('El formato del correo no es válido')
        
        # Validar contraseña
        if not contraseña:
            errores.append('La contraseña es obligatoria')
        elif len(contraseña) < 6:
            errores.append('La contraseña debe tener al menos 6 caracteres')
        
        # Validar confirmación de contraseña
        if contraseña != confirmar_contraseña:
            errores.append('Las contraseñas no coinciden')
        
        # Validar rol
        if rol not in ['organizador', 'proveedor']:
            errores.append('Debe seleccionar un rol válido')
        
        return errores
    
    @staticmethod
    def _usuario_existe(correo):
        """Verifica si ya existe un usuario con ese correo"""
        return Usuario.query.filter_by(correo=correo).first() is not None
    
    @staticmethod
    def _crear_sesion(usuario):
        """Crea la sesión del usuario"""
        session['user_id'] = usuario.id
        session['user_nombre'] = usuario.nombre
        session['user_correo'] = usuario.correo
        session['user_rol'] = usuario.rol.value  # Guardar el valor del enum, no el objeto
        session['login_time'] = datetime.now().isoformat()
    
    @staticmethod
    def _usuario_autenticado():
        """Verifica si el usuario está autenticado"""
        return 'user_id' in session
    
    @staticmethod
    def _acceso_no_autorizado():
        """Redirige cuando el acceso no está autorizado"""
        flash('Debes iniciar sesión para acceder a esta página', 'error')
        return redirect(url_for('usuario.login'))
    
    @staticmethod
    def _redirect_to_dashboard():
        """Redirige al dashboard apropiado según el rol"""
        if session['user_rol'] == 'organizador':
            return redirect(url_for('servicio.buscar_servicios'))
        elif session['user_rol'] == 'proveedor':
            return redirect(url_for('servicio.listar_servicios'))
        else:
            return redirect(url_for('index'))
    
    
        
        db.session.add(notificacion)
        db.session.commit()
    
    @staticmethod
    def _estadisticas_organizador(user_id):
        """Obtiene estadísticas para organizadores"""
        total_eventos = Evento.query.filter_by(organizador_id=user_id).count()
        eventos_activos = Evento.query.filter_by(
            organizador_id=user_id, 
            estado='activo'
        ).count()
        
        stats = {
            'total_eventos': total_eventos,
            'eventos_activos': eventos_activos,
            'eventos_completados': total_eventos - eventos_activos
        }
        
        return render_template('estadisticas_organizador.html', stats=stats)
    
    @staticmethod
    def _estadisticas_proveedor(user_id):
        """Obtiene estadísticas para proveedores"""
        total_servicios = Servicio.query.filter_by(proveedor_id=user_id).count()
        servicios_activos = Servicio.query.filter_by(
            proveedor_id=user_id, 
            estado='disponible'
        ).count()
        
        stats = {
            'total_servicios': total_servicios,
            'servicios_activos': servicios_activos,
            'servicios_inactivos': total_servicios - servicios_activos
        }
        
        return render_template('estadisticas_proveedor.html', stats=stats)