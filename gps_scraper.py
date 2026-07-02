import time
import json
import csv
import os
import mysql.connector
from mysql.connector import Error
from datetime import datetime, time as dt_time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import subprocess
import pytz

class LatitudM2MScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.session_active = False
        self.cookies_file = "session_cookies.json"
        
        # Configuración MySQL (desde variables de entorno)
        self.mysql_config = {
            'host': os.environ.get('MYSQL_HOST', 'host.docker.internal'),
            'database': os.environ.get('MYSQL_DATABASE', 'gps_data'),
            'user': os.environ.get('MYSQL_USER', 'root'),
            'password': os.environ.get('MYSQL_PASSWORD', '')
        }
        
        print(f"📊 Configuración MySQL:")
        print(f"   Host: {self.mysql_config['host']}")
        print(f"   Database: {self.mysql_config['database']}")
        print(f"   User: {self.mysql_config['user']}")
        
        # 👇 LISTA DE UNIDADES (CÁMBIALA POR LA TUYA)
        self.vehiculos = [
            "FRONTAL #02 - Maxxforce",
            "FRONTAL #04 - NARANJA",
            "FRONTAL BLANCO #03 - Héctor Noriega",
            "ROLL OFF #01 - CHATO",
            "ROLL OFF #02  RAYADO - Diógenes Rojas",
            "ROLL OFF #03 NUEVO",
            "Roll off #4"
        ]
    
    def find_chromedriver(self):
        """Busca chromedriver en el sistema automáticamente"""
        rutas_posibles = [
            "/usr/bin/chromedriver",
            "/usr/lib/chromium-browser/chromedriver",
            "/usr/local/bin/chromedriver",
            "/snap/bin/chromedriver"
        ]
        
        try:
            result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                ruta = result.stdout.strip()
                if os.path.exists(ruta):
                    print(f"✅ Chromedriver encontrado: {ruta}")
                    return ruta
        except:
            pass
        
        for ruta in rutas_posibles:
            if os.path.exists(ruta):
                print(f"✅ Chromedriver encontrado: {ruta}")
                return ruta
        
        print("❌ No se encontró chromedriver.")
        return None
    
    def setup_driver(self):
        """Configura el driver para Chromium en modo HEADLESS"""
        options = Options()
        options.binary_location = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
        
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-site-isolation-trials')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-crash-reporter')
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        chromedriver_path = self.find_chromedriver()
        
        if chromedriver_path is None:
            print("❌ No se encontró chromedriver")
            raise Exception("Chromedriver no encontrado")
        
        print(f"🌐 Iniciando Chromium en modo HEADLESS...")
        
        try:
            service = Service(chromedriver_path)
            service.start()
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chromium listo (modo invisible)")
        except Exception as e:
            print(f"❌ Error al iniciar Chromium: {e}")
            raise e
    
    def login(self):
        """Inicia sesión en la plataforma"""
        print("🔐 Iniciando sesión...")
        
        self.driver.get("https://gps.latitudm2m.com/?lang=es")
        time.sleep(5)
        
        try:
            print("🔍 Buscando campos de login...")
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "user"))
            )
            
            username_field = self.driver.find_element(By.ID, "user")
            password_field = self.driver.find_element(By.ID, "passw")
            login_button = self.driver.find_element(By.ID, "submit")
            
            print("✅ Campos encontrados, ingresando datos...")
            
            username_field.clear()
            username_field.send_keys(self.username)
            time.sleep(1)
            
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)
            
            login_button.click()
            print("✅ Clic en Iniciar sesión")
            
            time.sleep(8)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "user_name_target"))
                )
                print("✅ Sesión iniciada correctamente")
                self.save_cookies()
                self.session_active = True
                return True
            except:
                print("⚠️ No se detectó el panel de usuario, pero continuamos...")
                self.session_active = True
                return True
            
        except Exception as e:
            print(f"❌ Error en el proceso de login: {e}")
            self.session_active = True
            return True
    
    def save_cookies(self):
        """Guarda las cookies en un archivo"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            print(f"🍪 Cookies guardadas en {self.cookies_file}")
        except Exception as e:
            print(f"⚠️ No se pudieron guardar las cookies: {e}")
    
    def load_cookies(self):
        """Carga cookies guardadas"""
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        self.driver.add_cookie(cookie)
                print("🍪 Cookies cargadas")
                return True
            except Exception as e:
                print(f"⚠️ Error al cargar cookies: {e}")
                return False
        return False
    
    def ensure_logged_in(self):
        """Asegura que estamos logueados"""
        self.setup_driver()
        self.driver.get("https://gps.latitudm2m.com/?lang=es")
        time.sleep(3)
        
        if self.load_cookies():
            self.driver.refresh()
            time.sleep(3)
            
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "user_name_target"))
                )
                print("✅ Sesión restaurada con cookies")
                self.session_active = True
                return True
            except:
                print("🔄 Cookies expiradas, iniciando sesión...")
                return self.login()
        else:
            return self.login()
    
    def close_dropdown_force(self):
        """CIERRA FORZADAMENTE la lista desplegable"""
        try:
            self.driver.execute_script("""
                var dropdowns = document.querySelectorAll('.vtblist');
                dropdowns.forEach(function(d) {
                    d.style.display = 'none';
                });
                document.body.click();
            """)
            time.sleep(0.5)
            return True
        except:
            return False
    
    def select_plantilla(self, nombre_plantilla):
        """Selecciona una plantilla de informe específica"""
        try:
            print(f"   📋 Seleccionando plantilla: {nombre_plantilla}")
            
            self.close_dropdown_force()
            time.sleep(1)
            
            campo = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "report_templates_filter_reports"))
            )
            
            campo.click()
            campo.send_keys(Keys.CONTROL + 'a')
            campo.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            campo.send_keys(nombre_plantilla)
            print(f"   📌 Escribiendo: {nombre_plantilla}")
            time.sleep(2)
            
            resultado = self.driver.execute_script(f"""
                var items = document.querySelectorAll('.vtblist .itm');
                for (var i = 0; i < items.length; i++) {{
                    var texto = items[i].textContent.trim();
                    if (texto.includes('{nombre_plantilla}') || texto === '{nombre_plantilla}') {{
                        items[i].click();
                        return true;
                    }}
                }}
                return false;
            """)
            
            if resultado:
                print(f"   ✅ Plantilla seleccionada: {nombre_plantilla}")
                time.sleep(1)
                self.close_dropdown_force()
                time.sleep(1)
                return True
            else:
                print(f"   ❌ No se encontró la plantilla: {nombre_plantilla}")
                return False
            
        except Exception as e:
            print(f"   ❌ Error al seleccionar plantilla: {e}")
            return False
    
    def select_vehiculo(self, nombre_vehiculo):
        """Selecciona un vehículo específico de la lista con limpieza forzada"""
        try:
            print(f"   🔍 Seleccionando: {nombre_vehiculo}")
            
            self.close_dropdown_force()
            time.sleep(1)
            
            campo = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "report_templates_filter_units"))
            )
            
            campo.click()
            time.sleep(0.3)
            campo.send_keys(Keys.CONTROL + 'a')
            time.sleep(0.3)
            campo.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            self.driver.execute_script("arguments[0].value = '';", campo)
            time.sleep(0.3)
            
            self.driver.execute_script("""
                var campo = arguments[0];
                campo.value = '';
                campo.dispatchEvent(new Event('input', { bubbles: true }));
                campo.dispatchEvent(new Event('change', { bubbles: true }));
                campo.dispatchEvent(new Event('blur', { bubbles: true }));
            """, campo)
            time.sleep(0.5)
            
            campo.send_keys(nombre_vehiculo)
            print(f"   📌 Escribiendo: {nombre_vehiculo}")
            time.sleep(2)
            
            resultado = self.driver.execute_script(f"""
                var items = document.querySelectorAll('.vtblist .itm');
                for (var i = 0; i < items.length; i++) {{
                    var texto = items[i].textContent.trim();
                    if (texto === '{nombre_vehiculo}') {{
                        items[i].click();
                        return true;
                    }}
                }}
                return false;
            """)
            
            if resultado:
                print(f"   ✅ Seleccionado: {nombre_vehiculo}")
                time.sleep(1)
                
                try:
                    campo.send_keys(Keys.ENTER)
                    print("   📌 Confirmando selección con ENTER")
                    time.sleep(1)
                except:
                    pass
                
                self.close_dropdown_force()
                time.sleep(2)
                
                valor_actual = campo.get_attribute('value')
                if valor_actual == nombre_vehiculo:
                    print(f"   ✅ Confirmado: {valor_actual}")
                    return True
                else:
                    print(f"   ⚠️ El campo muestra: '{valor_actual}', esperado: '{nombre_vehiculo}'")
                    return self.select_vehiculo_alternativo(nombre_vehiculo)
            else:
                print(f"   ❌ No se encontró: {nombre_vehiculo}")
                return False
            
        except Exception as e:
            print(f"   ❌ Error al seleccionar vehículo: {e}")
            return False
    
    def select_vehiculo_alternativo(self, nombre_vehiculo):
        """Método alternativo para seleccionar vehículo"""
        try:
            print(f"   🔍 Intentando método alternativo: {nombre_vehiculo}")
            
            self.close_dropdown_force()
            time.sleep(1)
            
            resultado = self.driver.execute_script(f"""
                var campo = document.getElementById('report_templates_filter_units');
                if (!campo) return false;
                
                campo.value = '';
                campo.dispatchEvent(new Event('input', {{ bubbles: true }}));
                campo.dispatchEvent(new Event('change', {{ bubbles: true }}));
                
                campo.value = '{nombre_vehiculo}';
                campo.dispatchEvent(new Event('input', {{ bubbles: true }}));
                
                var items = document.querySelectorAll('.vtblist .itm');
                for (var i = 0; i < items.length; i++) {{
                    if (items[i].textContent.trim() === '{nombre_vehiculo}') {{
                        items[i].click();
                        return true;
                    }}
                }}
                return false;
            """)
            
            if resultado:
                print(f"   ✅ Seleccionado (JS): {nombre_vehiculo}")
                time.sleep(2)
                
                campo = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "report_templates_filter_units"))
                )
                valor_actual = campo.get_attribute('value')
                if valor_actual == nombre_vehiculo:
                    print(f"   ✅ Confirmado: {valor_actual}")
                    return True
                else:
                    print(f"   ⚠️ El campo muestra: '{valor_actual}'")
                    return False
            else:
                print(f"   ❌ No se encontró: {nombre_vehiculo}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error en método alternativo: {e}")
            return False
    
    def execute_report(self):
        """Ejecuta el informe"""
        print("   📊 Ejecutando informe...")
        
        try:
            self.close_dropdown_force()
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, 30)
            
            execute_btn = wait.until(
                EC.element_to_be_clickable((By.ID, "report_templates_filter_params_execute"))
            )
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", execute_btn)
            time.sleep(1)
            
            actions = ActionChains(self.driver)
            actions.move_to_element(execute_btn).pause(0.5).click().perform()
            print("   ✅ Clic en Ejecutar")
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"   ❌ Error al ejecutar el informe: {e}")
            return False
    
    def wait_for_report_results(self):
        """Espera a que los resultados del informe carguen"""
        print("   ⏳ Esperando que los datos carguen...")
        
        try:
            WebDriverWait(self.driver, 45).until(
                EC.presence_of_element_located((By.ID, "report_result_body_target"))
            )
            print("   ✅ Tabla de resultados cargada")
            time.sleep(3)
            return True
        except:
            print("   ⚠️ No se detectó la tabla de resultados")
            return False
    
    def get_report_title(self):
        """Obtiene el título del informe actual"""
        try:
            titulo = self.driver.find_element(By.CSS_SELECTOR, ".ui-accordion-header-active span").text
            return titulo.strip()
        except:
            return "Desconocido"
    
    def scrape_table_data(self):
        """Extrae los datos de la tabla de resultados"""
        print("   📋 Extrayendo datos de la tabla...")
        
        try:
            time.sleep(2)
            
            titulo = self.get_report_title()
            print(f"   📊 Tipo de informe: {titulo}")
            
            try:
                table_body = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "report_result_body_target"))
                )
            except:
                print("   ⚠️ No se encontró la tabla de resultados")
                return []
            
            rows = table_body.find_elements(By.XPATH, ".//table/tbody/tr")
            print(f"   🔍 Encontradas {len(rows)} filas")
            
            data = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    row_data = {'tipo_informe': titulo}
                    num_columnas = len(cells)
                    
                    if num_columnas == 6:  # Estacionamientos
                        row_data.update({
                            'comienzo': cells[0].text.strip(),
                            'fin': cells[1].text.strip(),
                            'duracion': cells[2].text.strip(),
                            'tiempo_total': cells[3].text.strip(),
                            'tiempo_entre': cells[4].text.strip(),
                            'ubicacion': cells[5].text.strip()
                        })
                        data.append(row_data)
                    
                    elif num_columnas >= 11:  # Viajes
                        row_data.update({
                            'numero': cells[1].text.strip() if len(cells) > 1 else '',
                            'comienzo': cells[2].text.strip() if len(cells) > 2 else '',
                            'ubicacion_inicial': cells[3].text.strip() if len(cells) > 3 else '',
                            'coordenadas': cells[4].text.strip() if len(cells) > 4 else '',
                            'kilometros': cells[5].text.strip() if len(cells) > 5 else '',
                            'duracion': cells[6].text.strip() if len(cells) > 6 else '',
                            'horas_motor': cells[7].text.strip() if len(cells) > 7 else '',
                            'velocidad_maxima': cells[8].text.strip() if len(cells) > 8 else '',
                            'cantidad_viajes': cells[9].text.strip() if len(cells) > 9 else '',
                            'consumido': cells[10].text.strip() if len(cells) > 10 else ''
                        })
                        data.append(row_data)
                    else:
                        row_data['datos'] = [cell.text.strip() for cell in cells]
                        data.append(row_data)
            
            print(f"   ✅ Datos extraídos: {len(data)} filas")
            return data
            
        except Exception as e:
            print(f"   ❌ Error al extraer datos: {e}")
            return []
    
    def limpiar_procesos(self):
        """Limpia procesos residuales"""
        try:
            print("🧹 Limpiando procesos residuales...")
            os.system("pkill -f chromedriver 2>/dev/null")
            os.system("pkill -f chromium 2>/dev/null")
            print("✅ Limpieza completada")
        except:
            pass
    
    def guardar_en_mysql(self, data):
        """Guarda los datos en MySQL con INSERT ... ON DUPLICATE KEY UPDATE"""
        if not data:
            print("⚠️ No hay datos para guardar en MySQL")
            return False
        
        try:
            print("📤 Guardando datos en MySQL...")
            print(f"   Host: {self.mysql_config['host']}")
            print(f"   Database: {self.mysql_config['database']}")
            
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor()
            
            # Verificar que la tabla existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS viajes_gps (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    vehiculo VARCHAR(100) NOT NULL,
                    numero VARCHAR(10),
                    comienzo DATETIME,
                    ubicacion_inicial VARCHAR(500),
                    coordenadas VARCHAR(100),
                    kilometros VARCHAR(20),
                    duracion VARCHAR(20),
                    horas_motor VARCHAR(20),
                    velocidad_maxima VARCHAR(20),
                    cantidad_viajes VARCHAR(10),
                    consumido VARCHAR(20),
                    tipo_informe VARCHAR(50),
                    fecha_registro DATE,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_viaje (vehiculo, comienzo)
                )
            """)
            
            # Preparar los datos
            fecha_hoy = datetime.now().date()
            insertados = 0
            actualizados = 0
            
            for row in data:
                # Extraer valores
                vehiculo = row.get('vehiculo', '')
                numero = row.get('numero', '')
                comienzo = row.get('comienzo', None)
                ubicacion_inicial = row.get('ubicacion_inicial', '')
                coordenadas = row.get('coordenadas', '')
                kilometros = row.get('kilometros', '')
                duracion = row.get('duracion', '')
                horas_motor = row.get('horas_motor', '')
                velocidad_maxima = row.get('velocidad_maxima', '')
                cantidad_viajes = row.get('cantidad_viajes', '')
                consumido = row.get('consumido', '')
                tipo_informe = row.get('tipo_informe', '')
                
                # Convertir comienzo a formato DATETIME si es posible
                if comienzo:
                    try:
                        from datetime import datetime as dt
                        comienzo_dt = dt.strptime(comienzo, "%d.%m.%Y %H:%M:%S")
                        comienzo = comienzo_dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        # Si falla, dejarlo como está
                        pass
                else:
                    comienzo = None
                
                # Query con UPSERT
                query = """
                    INSERT INTO viajes_gps (
                        vehiculo, numero, comienzo, ubicacion_inicial, coordenadas,
                        kilometros, duracion, horas_motor, velocidad_maxima,
                        cantidad_viajes, consumido, tipo_informe, fecha_registro
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON DUPLICATE KEY UPDATE
                        ubicacion_inicial = VALUES(ubicacion_inicial),
                        coordenadas = VALUES(coordenadas),
                        kilometros = VALUES(kilometros),
                        duracion = VALUES(duracion),
                        horas_motor = VALUES(horas_motor),
                        velocidad_maxima = VALUES(velocidad_maxima),
                        cantidad_viajes = VALUES(cantidad_viajes),
                        consumido = VALUES(consumido),
                        tipo_informe = VALUES(tipo_informe),
                        fecha_actualizacion = CURRENT_TIMESTAMP
                """
                
                cursor.execute(query, (
                    vehiculo, numero, comienzo, ubicacion_inicial, coordenadas,
                    kilometros, duracion, horas_motor, velocidad_maxima,
                    cantidad_viajes, consumido, tipo_informe, fecha_hoy
                ))
                
                if cursor.rowcount == 1:
                    insertados += 1
                elif cursor.rowcount == 2:
                    actualizados += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"   ✅ MySQL: {insertados} registros insertados, {actualizados} actualizados")
            return True
            
        except Error as e:
            print(f"   ❌ Error en MySQL: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Error general: {e}")
            return False
    
    def save_to_csv(self, data, filename=None):
        """Guarda los datos en CSV"""
        if not data:
            print("   ⚠️ No hay datos para guardar")
            return None
            
        if filename is None:
            fecha_actual = datetime.now().strftime('%Y%m%d')
            filename = f"resultados/datos_gps_{fecha_actual}.csv"
        
        try:
            all_keys = set()
            for row in data:
                all_keys.update(row.keys())
            
            os.makedirs('resultados', exist_ok=True)
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                writer.writeheader()
                writer.writerows(data)
            print(f"   💾 CSV guardado en {filename}")
            return filename
        except Exception as e:
            print(f"   ❌ Error al guardar CSV: {e}")
            return None
    
    def process_all_vehiculos(self):
        """Procesa todos los vehículos, guarda CSV y envía a MySQL"""
        print("\n" + "="*50)
        print("🚀 INICIANDO PROCESAMIENTO DE VEHÍCULOS")
        print("="*50)
        
        vehiculos = self.vehiculos
        
        if not vehiculos:
            print("❌ No hay vehículos en la lista")
            return False
        
        print(f"\n📋 Procesando {len(vehiculos)} vehículos:")
        for v in vehiculos:
            print(f"   - {v}")
        
        todos_los_datos = []
        procesados = 0
        fallidos = 0
        
        for i, vehiculo in enumerate(vehiculos, 1):
            print(f"\n{'='*50}")
            print(f"[{i}/{len(vehiculos)}] Procesando: {vehiculo}")
            print("="*50")
            
            if not self.select_plantilla("Viajes"):
                print("   ⚠️ No se pudo seleccionar la plantilla 'Viajes'")
                fallidos += 1
                continue
            
            if not self.select_vehiculo(vehiculo):
                fallidos += 1
                print(f"   ⚠️ Vehículo no encontrado, continuando...")
                continue
            
            if not self.execute_report():
                fallidos += 1
                print(f"   ❌ No se pudo ejecutar el informe")
                continue
            
            if not self.wait_for_report_results():
                fallidos += 1
                continue
            
            data = self.scrape_table_data()
            
            if data:
                for row in data:
                    row['vehiculo'] = vehiculo
                todos_los_datos.extend(data)
                procesados += 1
                print(f"   ✅ {len(data)} filas agregadas")
            else:
                fallidos += 1
                print(f"   ⚠️ Sin datos para este vehículo")
            
            print(f"   ⏳ Esperando 3 segundos antes del siguiente...")
            time.sleep(3)
        
        print("\n" + "="*50)
        print("📊 RESUMEN FINAL")
        print("="*50)
        print(f"✅ Vehículos procesados: {procesados}")
        print(f"❌ Fallidos: {fallidos}")
        
        if todos_los_datos:
            print(f"📊 Total de filas: {len(todos_los_datos)}")
            
            # 1. Guardar CSV
            self.save_to_csv(todos_los_datos)
            
            # 2. Guardar en MySQL
            self.guardar_en_mysql(todos_los_datos)
            
            return True
        else:
            print("⚠️ No hay datos para guardar")
            return False
    
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            try:
                self.driver.quit()
                print("🔒 Navegador cerrado")
            except:
                pass

    def esta_en_horario(self):
        """Verifica si la hora actual está entre 6:00 AM y 7:00 PM (hora Tijuana)"""
        try:
            tijuana_tz = pytz.timezone('America/Tijuana')
            now = datetime.now(tijuana_tz)
            hora_actual = now.time()
            
            hora_inicio = dt_time(6, 0, 0)
            hora_fin = dt_time(19, 0, 0)
            
            return hora_inicio <= hora_actual <= hora_fin
        except:
            hora_actual = datetime.now().time()
            hora_inicio = dt_time(6, 0, 0)
            hora_fin = dt_time(19, 0, 0)
            return hora_inicio <= hora_actual <= hora_fin

# ============================================
# 🚀 EJECUCIÓN PRINCIPAL CON PROGRAMACIÓN
# ============================================

if __name__ == "__main__":
    USERNAME = os.environ.get('USERNAME', 'LuisDiaZ')
    PASSWORD = os.environ.get('PASSWORD', 'Supervision/25')
    
    scraper = LatitudM2MScraper(USERNAME, PASSWORD)
    
    try:
        print("\n" + "="*50)
        print("🚀 INICIANDO SCRAPER DE LATITUD M2M (PROGRAMADO)")
        print(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("⏰ Horario: 6:00 AM - 7:00 PM (cada 10 minutos)")
        print("📊 Datos: CSV + MySQL")
        print("="*50 + "\n")
        
        ejecuciones = 0
        while True:
            try:
                if scraper.esta_en_horario():
                    ejecuciones += 1
                    print(f"\n{'='*50}")
                    print(f"✅ EJECUCIÓN #{ejecuciones} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print("="*50)
                    
                    scraper.ensure_logged_in()
                    time.sleep(3)
                    
                    exito = scraper.process_all_vehiculos()
                    
                    if exito:
                        print(f"✅ Ejecución #{ejecuciones} completada con éxito")
                    else:
                        print("❌ Falló la ejecución")
                    
                    scraper.close()
                    scraper.limpiar_procesos()
                    
                    print(f"\n⏳ Esperando 10 minutos hasta la próxima ejecución...")
                    time.sleep(600)
                    
                else:
                    print(f"⏰ Fuera de horario ({datetime.now().strftime('%H:%M')}). Esperando 5 minutos...")
                    time.sleep(300)
                    
            except KeyboardInterrupt:
                print("\n🛑 Detenido por el usuario")
                break
            except Exception as e:
                print(f"❌ Error en ejecución programada: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)
                
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()
        scraper.limpiar_procesos()
        print("\n🔒 Programa finalizado")
