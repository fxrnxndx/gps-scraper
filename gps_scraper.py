import time
import json
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import subprocess

class LatitudM2MScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.session_active = False
        self.cookies_file = "session_cookies.json"
        
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
        """Configura el driver para Chromium en modo HEADLESS (para Docker)"""
        options = Options()
        
        # Usar Chromium en lugar de Brave (más común en Docker)
        options.binary_location = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
        
        # MODO HEADLESS
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
    
    def process_all_vehiculos(self, max_vehiculos=None):
        """Procesa todos los vehículos y guarda en un solo archivo por día"""
        print("\n" + "="*50)
        print("🚀 INICIANDO PROCESAMIENTO DE VEHÍCULOS")
        print("="*50)
        
        vehiculos = self.vehiculos
        
        if not vehiculos:
            print("❌ No hay vehículos en la lista")
            return
        
        if max_vehiculos:
            vehiculos = vehiculos[:max_vehiculos]
        
        print(f"\n📋 Procesando {len(vehiculos)} vehículos:")
        for v in vehiculos:
            print(f"   - {v}")
        
        todos_los_datos = []
        
        procesados = 0
        fallidos = 0
        
        for i, vehiculo in enumerate(vehiculos, 1):
            print(f"\n{'='*50}")
            print(f"[{i}/{len(vehiculos)}] Procesando: {vehiculo}")
            print("="*50)
            
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
        
        # GUARDAR TODOS LOS DATOS EN UN SOLO ARCHIVO POR DÍA
        if todos_los_datos:
            fecha_actual = datetime.now().strftime('%Y%m%d')
            nombre_archivo = f"resultados/datos_gps_{fecha_actual}.csv"
            
            try:
                all_keys = set()
                for row in todos_los_datos:
                    all_keys.update(row.keys())
                
                with open(nombre_archivo, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                    writer.writeheader()
                    writer.writerows(todos_los_datos)
                print(f"\n💾 TODOS los datos guardados en: {nombre_archivo}")
                print(f"📊 Total de filas: {len(todos_los_datos)}")
            except Exception as e:
                print(f"❌ Error al guardar CSV: {e}")
        else:
            print("⚠️ No hay datos para guardar")
        
        print("\n" + "="*50)
        print("📊 RESUMEN FINAL")
        print("="*50)
        print(f"✅ Vehículos procesados: {procesados}")
        print(f"❌ Fallidos: {fallidos}")
        print(f"📁 Datos guardados en: resultados/datos_gps_{datetime.now().strftime('%Y%m%d')}.csv")
        print("="*50)
    
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            try:
                self.driver.quit()
                print("🔒 Navegador cerrado")
            except:
                pass

# ============================================
# 🚀 EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == "__main__":
    # Leer credenciales de variables de entorno (para Docker)
    USERNAME = os.environ.get('USERNAME', 'LuisDiaZ')
    PASSWORD = os.environ.get('PASSWORD', 'Supervision/25')
    
    scraper = LatitudM2MScraper(USERNAME, PASSWORD)
    
    try:
        print("\n" + "="*50)
        print("🚀 INICIANDO SCRAPER DE LATITUD M2M (DOCKER)")
        print("="*50 + "\n")
        
        scraper.ensure_logged_in()
        print("⏳ Esperando 5 segundos para que la página se estabilice...")
        time.sleep(5)
        
        scraper.process_all_vehiculos()
        
    except KeyboardInterrupt:
        print("\n🛑 Detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()
        scraper.limpiar_procesos()
