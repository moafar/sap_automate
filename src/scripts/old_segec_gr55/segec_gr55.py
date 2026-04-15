
import logging
import time

logger = logging.getLogger("SAP_Automation")

class SegecGR55:
    """
    Seguimiento Económico: Lanza la transacción GR55 en SAP.
    """
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.timeout = config.get('timeouts', {}).get('default_wait', 0.5)

    def run(self, segec_cfg: dict) -> bool:
        """
        Ejecuta la transacción GR55 y avanza a la siguiente pantalla tras diligenciar Z002.
        """
        try:
            # Paso 1: Lanzar transacción
            self.session.findById("wnd[0]/tbar[0]/okcd").Text = "/nGR55"
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(self.timeout)
            input("Transacción GR55 lanzada. Verifica la pantalla y presiona Enter para continuar...")

            # Paso 2: Diligenciar campo 'Grup d'informes' con 'Z002'
            campo_grup = self.session.findById("wnd[0]/usr/ctxtRGRWJ-JOB")
            campo_grup.Text = "Z002"
            logger.info("Campo 'Grup d'informes' diligenciado con Z002")
            input("Campo Z002 diligenciado. Verifica la pantalla y presiona Enter para continuar...")

            # Paso 3: Avanzar a la siguiente pantalla (F8)
            self.session.findById("wnd[0]").sendVKey(8)
            time.sleep(self.timeout)
            input("Pantalla de selección cargada. Verifica la pantalla y presiona Enter para mostrar los elementos visibles...")

            # Paso 4: Barrido recursivo de elementos visibles en la segunda pantalla
            def print_element_tree(element, prefix=""):
                try:
                    desc = f"{prefix}{element.Id} [{element.Type}]"
                    # Si el elemento tiene texto visible, lo mostramos
                    if hasattr(element, 'Text') and element.Text:
                        desc += f" -> '{element.Text}'"
                    print(desc)
                    # Recorrer hijos si existen
                    if hasattr(element, 'Children'):
                        for child in element.Children:
                            print_element_tree(child, prefix + "  ")
                except Exception as e:
                    print(f"[ERROR] No se pudo inspeccionar un elemento: {e}")

            print("\n--- Barrido recursivo de elementos visibles en la segunda pantalla ---")
            wnd = self.session.findById("wnd[0]")
            print_element_tree(wnd)
            print("--- Fin del barrido ---\n")

            # Paso 5: Ubicar foco y modificar campo 'Societat CO'
            societad_label = self.session.findById("wnd[0]/usr/txt%_$1KOKRE_%_APP_%-TEXT")
            societad_field = self.session.findById("wnd[0]/usr/ctxt$1KOKRE")
            societad_field.setFocus()
            societad_field.Text = ""
            societad_field.Text = "IDI"
            logger.info("Campo 'Societat CO' actualizado a 'IDI'")

            # Paso 6: Borrar y reemplazar campo 'Exercici' con valor de configuración
            exercici_label = self.session.findById("wnd[0]/usr/txt%_$1GJAHLJ_%_APP_%-TEXT")
            exercici_field = self.session.findById("wnd[0]/usr/txt$1GJAHLJ")
            exercici_field.setFocus()
            ejercicio_valor = segec_cfg.get('ejercicio', '')
            exercici_field.Text = ""
            exercici_field.Text = str(ejercicio_valor)
            logger.info(f"Campo 'Exercici' actualizado a '{ejercicio_valor}'")

            # Paso 7: Borrar y reemplazar campo 'Període de' con valor de configuración
            periode_label = self.session.findById("wnd[0]/usr/txt%_$0FRPMAF_%_APP_%-TEXT")
            periode_field = self.session.findById("wnd[0]/usr/ctxt$0FRPMAF")
            periode_field.setFocus()
            periodo_de_valor = segec_cfg.get('periodo_de', '')
            periode_field.Text = ""
            periode_field.Text = str(periodo_de_valor)
            logger.info(f"Campo 'Període de' actualizado a '{periodo_de_valor}'")

            # Paso 8: Borrar y reemplazar campo 'Període fins' con valor de configuración
            periode_fins_label = self.session.findById("wnd[0]/usr/txt%_$0FRPMAT_%_APP_%-TEXT")
            periode_fins_field = self.session.findById("wnd[0]/usr/ctxt$0FRPMAT")
            periode_fins_field.setFocus()
            periodo_fins_valor = segec_cfg.get('periodo_fins', '')
            periode_fins_field.Text = ""
            periode_fins_field.Text = str(periodo_fins_valor)
            logger.info(f"Campo 'Període fins' actualizado a '{periodo_fins_valor}'")

            # Paso 9: Borrar y reemplazar campo 'Grup de classes de cost' con valor de configuración
            grup_classes_label = self.session.findById("wnd[0]/usr/txt%_$1KSTAR_%_APP_%-TEXT")
            grup_classes_field = self.session.findById("wnd[0]/usr/ctxt$1KSTAR")
            grup_classes_field.setFocus()
            grupo_clases_valor = segec_cfg.get('grupo_clases_costo', '')
            grup_classes_field.Text = ""
            grup_classes_field.Text = str(grupo_clases_valor)
            logger.info(f"Campo 'Grup de classes de cost' actualizado a '{grupo_clases_valor}'")

            # Paso 10: Ejecutar (F8)
            self.session.findById("wnd[0]").sendVKey(8)
            logger.info("Ejecutado F8 para continuar el proceso.")

            # Paso 11: Barrido recursivo de elementos visibles en la tercera pantalla
            def print_element_tree(element, prefix=""):
                try:
                    desc = f"{prefix}{element.Id} [{element.Type}]"
                    if hasattr(element, 'Text') and element.Text:
                        desc += f" -> '{element.Text}'"
                    print(desc)
                    if hasattr(element, 'Children'):
                        for child in element.Children:
                            print_element_tree(child, prefix + "  ")
                except Exception as e:
                    print(f"[ERROR] No se pudo inspeccionar un elemento: {e}")

            print("\n--- Barrido recursivo de elementos visibles en la tercera pantalla ---")
            wnd = self.session.findById("wnd[0]")
            print_element_tree(wnd)
            print("--- Fin del barrido ---\n")

            # Paso 12: Hacer doble clic en el elemento lbl[66,2] ('26.305.397,36-')
            # Paso 12: Verificar existencia del elemento lbl[5,2] y mostrar sus propiedades
            try:
                target_label = self.session.findById("wnd[0]/usr/lbl[5,2]")
                print("Elemento encontrado: ")
                print(f"  Id: {target_label.Id}")
                print(f"  Type: {target_label.Type}")
                print(f"  Name: {getattr(target_label, 'Name', '')}")
                print(f"  Text: {getattr(target_label, 'Text', '')}")
                logger.info("Elemento lbl[5,2] encontrado y mostrado en pantalla.")
                try:
                    target_label.setFocus()
                    logger.info("setFocus() realizado en lbl[5,2].")
                    # Intentar doble clic (puede fallar)
                    # Intentar activar el elemento con Enter
                    try:
                        wnd = self.session.findById("wnd[0]")
                        wnd.sendVKey(2)
                        logger.info("sendVKey(2) (Enter) enviado tras setFocus() en lbl[5,2].")
                        print("sendVKey(2) (Enter) enviado tras setFocus() en lbl[5,2]")
                    except Exception as e:
                        logger.error(f"No se pudo enviar sendVKey(2) tras setFocus en lbl[5,2]: {e}")
                        print("No se pudo enviar sendVKey(2) tras setFocus en lbl[5,2]")
                except Exception as e:
                    logger.error(f"No se pudo hacer setFocus en lbl[5,2]: {e}")
                    print("No se pudo hacer setFocus en lbl[5,2]")
            except Exception as e:
                logger.error(f"No se encontró el elemento lbl[5,2]: {e}")
                print("No se encontró el elemento lbl[5,2]")

            logger.info("Fin del script tras intento de doble clic en lbl[5,2].")
            import sys
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error en GR55: {e}")
            return False
