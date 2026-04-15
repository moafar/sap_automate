import logging
import time
import os
import yaml

logger = logging.getLogger("SAP_Automation")


class SegecGR55:
    """
    Seguimiento Económico: Automatización de la transacción GR55 en SAP.
    """

    def __init__(self, session, global_config):
        self.session = session
        self.global_config = global_config
        self.timeout = global_config.get('timeouts', {}).get('default_wait', 0.5)
        self.local_config = self._load_local_config()
        self.segec_cfg = self.local_config.get('segec_gr55', {})

    def _load_local_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def run(self) -> bool:
        """
        Ejecuta el flujo completo de la transacción GR55.
        """
        logger.info("Iniciando SEGEC GR55")
        logger.info(f"Config: {self.segec_cfg}")

        try:
            self._lanzar_transaccion()
            self._avanzar_a_seleccion()
            self._rellenar_filtros()
            self._ejecutar_busqueda()
            self._navegar_detalle_centres()
            logger.info("Detalle de centres de cost cargado correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error en SEGEC GR55: {e}")
            return False

    # ── Paso 1: Lanzar transacción y rellenar grupo de informes ──

    def _lanzar_transaccion(self):
        """Lanza /nGR55 y rellena el campo 'Grup d'informes' con Z002."""
        logger.debug("Ejecutando transacción /nGR55")
        self.session.findById("wnd[0]/tbar[0]/okcd").Text = "/nGR55"
        self.session.findById("wnd[0]").sendVKey(0)
        time.sleep(self.timeout)

        campo_grup = self.session.findById("wnd[0]/usr/ctxtRGRWJ-JOB")
        campo_grup.Text = "Z002"
        logger.info("Campo 'Grup d'informes' = Z002")

    # ── Paso 2: Avanzar a pantalla de selección (F8) ──

    def _avanzar_a_seleccion(self):
        """Pulsa F8 para avanzar a la pantalla de selección."""
        logger.debug("Pulsando F8 para avanzar a pantalla de selección")
        self.session.findById("wnd[0]").sendVKey(8)
        time.sleep(self.timeout)
        logger.info("F8 ejecutado — pantalla de selección cargada")

    # ── Paso 3: Rellenar filtros de la pantalla de selección ──

    def _rellenar_filtros(self):
        """Rellena los campos de filtro con valores del config.yaml."""
        cfg = self.segec_cfg

        # Societat CO
        campo = self.session.findById("wnd[0]/usr/ctxt$1KOKRE")
        campo.setFocus()
        campo.Text = str(cfg.get('sociedad_co', ''))
        logger.info(f"Societat CO = {campo.Text}")

        # Exercici
        campo = self.session.findById("wnd[0]/usr/txt$1GJAHLJ")
        campo.setFocus()
        campo.Text = str(cfg.get('ejercicio', ''))
        logger.info(f"Exercici = {campo.Text}")

        # Període de
        campo = self.session.findById("wnd[0]/usr/ctxt$0FRPMAF")
        campo.setFocus()
        campo.Text = str(cfg.get('periodo_de', ''))
        logger.info(f"Període de = {campo.Text}")

        # Període fins
        campo = self.session.findById("wnd[0]/usr/ctxt$0FRPMAT")
        campo.setFocus()
        campo.Text = str(cfg.get('periodo_fins', ''))
        logger.info(f"Període fins = {campo.Text}")

        # Grup de classes de cost
        campo = self.session.findById("wnd[0]/usr/ctxt$1KSTAR")
        campo.setFocus()
        campo.Text = str(cfg.get('grupo_clases_costo', ''))
        logger.info(f"Grup de classes de cost = {campo.Text}")

    # ── Paso 4: Ejecutar búsqueda (F8) ──

    def _ejecutar_busqueda(self):
        """Pulsa F8 para ejecutar la búsqueda con los filtros aplicados."""
        logger.debug("Pulsando F8 para ejecutar búsqueda")
        self.session.findById("wnd[0]").sendVKey(8)
        time.sleep(self.timeout * 4)
        logger.info("F8 ejecutado — resultados cargados")

    # ── Paso 5: Doble clic en '* Centres de cost' y esperar carga ──

    def _navegar_detalle_centres(self):
        """Hace doble clic en '* Centres de cost' (lbl[5,2]) y espera a que cargue el detalle."""
        logger.info("Navegando a detalle: '* Centres de cost' (lbl[5,2])")

        target = self.session.findById("wnd[0]/usr/lbl[5,2]")
        logger.debug(f"Elemento encontrado: Text='{getattr(target, 'Text', '')}'")

        target.setFocus()
        self.session.findById("wnd[0]").sendVKey(2)  # F2 = doble clic
        logger.info("Doble clic enviado. Esperando carga de detalle (hasta 10 min)...")

        # Esperar hasta 10 minutos, verificando cada 10 segundos
        max_wait = 600  # 10 minutos
        interval = 10   # cada 10 segundos
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(interval)
            elapsed += interval

            try:
                # Verificar si la pantalla cambió buscando un elemento
                # que solo existe en la pantalla de detalle
                wnd = self.session.findById("wnd[0]")
                status_bar = self.session.findById("wnd[0]/sbar")
                status_text = getattr(status_bar, 'Text', '')

                # Si la barra de estado no indica procesamiento, la pantalla cargó
                # Verificar que ya no estamos en la pantalla de resumen
                try:
                    self.session.findById("wnd[0]/usr/lbl[5,2]")
                    # Si lbl[5,2] todavía existe, seguimos en la misma pantalla
                    logger.debug(f"Esperando... ({elapsed}s / {max_wait}s) - Status: {status_text}")
                    continue
                except Exception:
                    # lbl[5,2] ya no existe → la pantalla cambió
                    logger.info(f"Pantalla de detalle cargada tras {elapsed}s")
                    return

            except Exception as e:
                logger.debug(f"Error verificando pantalla ({elapsed}s): {e}")
                continue

        raise TimeoutError(f"La pantalla de detalle no cargó en {max_wait}s (10 min)")
