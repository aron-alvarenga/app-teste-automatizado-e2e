import sys
import random
import json
import os
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, 
                             QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, 
                             QWidget, QFrame, QHeaderView, QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from faker import Faker

COLORS = {
    'primary': '#3B82F6',
    'primary_hover': '#2563EB',
    'secondary': '#6B7280',
    'success': '#10B981',
    'danger': '#EF4444',
    'warning': '#F59E0B',
    'light': '#F3F4F6',
    'dark': '#1F2937',
    'white': '#FFFFFF',
    'border': '#E5E7EB',
    'background': '#F9FAFB'
}

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('e2e_tester.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class StyledComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 5px 10px;
                background-color: {COLORS['white']};
                selection-background-color: {COLORS['primary']};
                min-height: 25px;
            }}
            QComboBox:hover {{
                border: 1px solid {COLORS['primary']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {COLORS['border']};
                border-left-style: solid;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }}
        """)

class StyledButton(QPushButton):
    def __init__(self, text, color='primary', parent=None):
        super().__init__(text, parent)
        self.color = color
        self.setStyleSheet(self._get_style())
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(30)
        font = self.font()
        font.setPointSize(9)
        self.setFont(font)
    
    def _get_style(self):
        colors = {
            'primary': (COLORS['primary'], COLORS['primary_hover'], COLORS['white']),
            'success': (COLORS['success'], '#0DA16E', COLORS['white']),
            'danger': (COLORS['danger'], '#DC2626', COLORS['white']),
            'secondary': (COLORS['secondary'], '#4B5563', COLORS['white']),
            'warning': (COLORS['warning'], '#D97706', COLORS['white']),
        }
        
        base_color, hover_color, text_color = colors.get(self.color, colors['primary'])
        
        return f"""
            QPushButton {{
                background-color: {base_color};
                color: {text_color};
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {base_color};
            }}
        """

class StyledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 5px 10px;
                background-color: {COLORS['white']};
                selection-background-color: {COLORS['primary']};
                min-height: 25px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['primary']};
            }}
        """)

class StyledTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                background-color: {COLORS['white']};
                gridline-color: {COLORS['border']};
                selection-background-color: {COLORS['primary']};
                selection-color: {COLORS['white']};
            }}
            QTableWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['light']};
                padding: 5px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                font-weight: bold;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {COLORS['light']};
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['secondary']};
                min-height: 20px;
                border-radius: 5px;
            }}
        """)

class StyledTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 5px;
                background-color: {COLORS['white']};
                selection-background-color: {COLORS['primary']};
            }}
            QScrollBar:vertical {{
                border: none;
                background: {COLORS['light']};
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['secondary']};
                min-height: 20px;
                border-radius: 5px;
            }}
        """)

class CardFrame(QFrame):
    def __init__(self, title=None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        if title:
            title_label = QLabel(title)
            font = title_label.font()
            font.setPointSize(11)
            font.setBold(True)
            title_label.setFont(font)
            self.layout.addWidget(title_label)
        
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {COLORS['white']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        
    def addWidget(self, widget):
        self.layout.addWidget(widget)
        
    def addLayout(self, layout):
        self.layout.addLayout(layout)

class TesteAutomatizadoE2E(QMainWindow):
    def __init__(self):
        super().__init__()
        self.faker = Faker()
        self.driver = None
        self.screenshot_dir = 'error_screenshots'
        
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
        
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Sistema de Testes Automatizados E2E')
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet(f"background-color: {COLORS['background']};")

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setCentralWidget(central_widget)

        url_card = CardFrame("URL do Teste")
        url_layout = QHBoxLayout()
        
        url_label = QLabel('URL:')
        url_label.setStyleSheet(f"color: {COLORS['dark']};")
        
        self.url_input = StyledLineEdit()
        self.url_input.setPlaceholderText("https://exemplo.com")
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input, 1)
        url_card.addLayout(url_layout)
        main_layout.addWidget(url_card)

        elementos_card = CardFrame("Elementos para Teste")
        
        self.tabela_elementos = StyledTableWidget()
        self.tabela_elementos.setColumnCount(5)
        self.tabela_elementos.setHorizontalHeaderLabels(['Elemento', 'Tipo de Seletor', 'Seletor', 'Ação', 'Valor'])
        self.tabela_elementos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_elementos.setAlternatingRowColors(True)
        
        elementos_card.addWidget(self.tabela_elementos)
        
        tabela_botoes_layout = QHBoxLayout()
        
        adicionar_btn = StyledButton('Adicionar Elemento', 'primary')
        adicionar_btn.clicked.connect(self.adicionar_elemento)
        
        remover_btn = StyledButton('Remover Elemento', 'danger')
        remover_btn.clicked.connect(self.remover_elemento)
        
        salvar_btn = StyledButton('Salvar Configuração', 'success')
        salvar_btn.clicked.connect(self.salvar_configuracao)
        
        carregar_btn = StyledButton('Carregar Configuração', 'warning')
        carregar_btn.clicked.connect(self.carregar_configuracao)
        
        tabela_botoes_layout.addWidget(adicionar_btn)
        tabela_botoes_layout.addWidget(remover_btn)
        tabela_botoes_layout.addSpacing(20)
        tabela_botoes_layout.addWidget(salvar_btn)
        tabela_botoes_layout.addWidget(carregar_btn)
        
        elementos_card.addLayout(tabela_botoes_layout)
        main_layout.addWidget(elementos_card)
        
        execucao_card = CardFrame("Execução de Testes")
        execucao_layout = QHBoxLayout()
        
        self.tipo_navegador = StyledComboBox()
        self.tipo_navegador.addItems(['Chrome', 'Firefox', 'Edge'])
        
        navegador_label = QLabel('Navegador:')
        navegador_label.setStyleSheet(f"color: {COLORS['dark']};")
        
        executar_btn = StyledButton('Executar Testes', 'success')
        executar_btn.clicked.connect(self.executar_testes)
        executar_btn.setMinimumWidth(150)
        
        execucao_layout.addWidget(navegador_label)
        execucao_layout.addWidget(self.tipo_navegador)
        execucao_layout.addStretch()
        execucao_layout.addWidget(executar_btn)
        
        execucao_card.addLayout(execucao_layout)
        main_layout.addWidget(execucao_card)
        
        log_card = CardFrame("Log de Execução")
        
        self.log_area = StyledTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(150)
        
        log_card.addWidget(self.log_area)
        main_layout.addWidget(log_card)

    def adicionar_elemento(self):
        linhas = self.tabela_elementos.rowCount()
        self.tabela_elementos.insertRow(linhas)
        
        self.tabela_elementos.setItem(linhas, 0, QTableWidgetItem(""))
        
        seletor_combo = StyledComboBox()
        seletor_combo.addItems(['ID', 'Name', 'XPath', 'CSS Selector', 'Class Name', 'Link Text'])
        self.tabela_elementos.setCellWidget(linhas, 1, seletor_combo)
        
        self.tabela_elementos.setItem(linhas, 2, QTableWidgetItem(""))
        
        acoes_combo = StyledComboBox()
        acoes_combo.addItems(['Inserir Texto', 'Clicar', 'Verificar Texto', 'Verificar Existência'])
        self.tabela_elementos.setCellWidget(linhas, 3, acoes_combo)
        
        self.tabela_elementos.setItem(linhas, 4, QTableWidgetItem(""))

    def remover_elemento(self):
        linha_atual = self.tabela_elementos.currentRow()
        if linha_atual >= 0:
            self.tabela_elementos.removeRow(linha_atual)

    def salvar_configuracao(self):
        configuracao = []
        for linha in range(self.tabela_elementos.rowCount()):
            elemento = {
                'elemento': self.tabela_elementos.item(linha, 0).text() if self.tabela_elementos.item(linha, 0) else '',
                'tipo_seletor': self.tabela_elementos.cellWidget(linha, 1).currentText(),
                'seletor': self.tabela_elementos.item(linha, 2).text() if self.tabela_elementos.item(linha, 2) else '',
                'acao': self.tabela_elementos.cellWidget(linha, 3).currentText(),
                'valor': self.tabela_elementos.item(linha, 4).text() if self.tabela_elementos.item(linha, 4) else ''
            }
            configuracao.append(elemento)

        nome_arquivo, _ = QFileDialog.getSaveFileName(self, 'Salvar Configuração', '', 'JSON (*.json)')
        if nome_arquivo:
            with open(nome_arquivo, 'w') as arquivo:
                json.dump(configuracao, arquivo, indent=4)
            
            self.log_area.append(f"✅ Configuração salva em: {nome_arquivo}")

    def carregar_configuracao(self):
        nome_arquivo, _ = QFileDialog.getOpenFileName(self, 'Carregar Configuração', '', 'JSON (*.json)')
        if nome_arquivo:
            with open(nome_arquivo, 'r') as arquivo:
                configuracao = json.load(arquivo)
            
            self.tabela_elementos.setRowCount(0)
            for elemento in configuracao:
                linha = self.tabela_elementos.rowCount()
                self.tabela_elementos.insertRow(linha)
                
                item_elemento = QTableWidgetItem(elemento['elemento'])
                self.tabela_elementos.setItem(linha, 0, item_elemento)

                seletor_combo = StyledComboBox()
                seletor_combo.addItems(['ID', 'Name', 'XPath', 'CSS Selector', 'Class Name', 'Link Text'])
                indice = seletor_combo.findText(elemento['tipo_seletor'])
                seletor_combo.setCurrentIndex(indice)
                self.tabela_elementos.setCellWidget(linha, 1, seletor_combo)

                item_seletor = QTableWidgetItem(elemento['seletor'])
                self.tabela_elementos.setItem(linha, 2, item_seletor)

                acoes_combo = StyledComboBox()
                acoes_combo.addItems(['Inserir Texto', 'Clicar', 'Verificar Texto', 'Verificar Existência'])
                indice = acoes_combo.findText(elemento['acao'])
                acoes_combo.setCurrentIndex(indice)
                self.tabela_elementos.setCellWidget(linha, 3, acoes_combo)

                item_valor = QTableWidgetItem(elemento['valor'])
                self.tabela_elementos.setItem(linha, 4, item_valor)
            
            self.log_area.append(f"📂 Configuração carregada de: {nome_arquivo}")

    def _gerar_valor_aleatorio(self, tipo):
        """Gera valores aleatórios baseados no tipo de campo"""
        if 'nome' in tipo.lower():
            return self.faker.name()
        elif 'email' in tipo.lower():
            return self.faker.email()
        elif 'telefone' in tipo.lower():
            return self.faker.phone_number()
        elif 'endereço' in tipo.lower():
            return self.faker.address()
        elif 'número' in tipo.lower():
            return str(self.faker.random_number(digits=5))
        return self.faker.text(max_nb_chars=20)

    def _configurar_driver(self, navegador):
        """Configuração robusta de WebDrivers"""
        try:
            if navegador == 'Chrome':
                service = ChromeService(ChromeDriverManager().install())
                options = webdriver.ChromeOptions()
                options.add_argument('--log-level=3')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                return webdriver.Chrome(service=service, options=options)
            
            elif navegador == 'Firefox':
                service = FirefoxService(GeckoDriverManager().install())
                options = webdriver.FirefoxOptions()
                options.add_argument('--log-level=fatal')
                return webdriver.Firefox(service=service, options=options)
            
            elif navegador == 'Edge':
                service = EdgeService(EdgeChromiumDriverManager().install())
                options = webdriver.EdgeOptions()
                options.add_argument('--log-level=3')
                return webdriver.Edge(service=service, options=options)
        
        except WebDriverException as e:
            logging.error(f"Erro ao configurar WebDriver: {e}")
            QMessageBox.critical(self, "Erro de Driver", 
                                 f"Não foi possível iniciar o navegador {navegador}. "
                                 "Verifique a instalação do driver.")
            return None

    def _salvar_screenshot(self, erro_msg):
        """Salva screenshot de erro com timestamp"""
        if not self.driver:
            return

        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"{self.screenshot_dir}/erro_{timestamp}.png"
            
            self.driver.save_screenshot(nome_arquivo)
            
            self.log_area.append(f"🖼️ Screenshot de erro salvo em: {nome_arquivo}")
            logging.info(f"Screenshot de erro salvo: {nome_arquivo}")
        
        except Exception as e:
            logging.error(f"Erro ao salvar screenshot: {e}")
            self.log_area.append(f"❌ Falha ao salvar screenshot: {e}")

    def executar_testes(self):
        try:
            self.log_area.clear()
            self.log_area.append("🚀 Iniciando execução dos testes...")
            
            navegador = self.tipo_navegador.currentText()
            
            self.log_area.append(f"🔧 Configurando navegador: {navegador}")
            self.driver = self._configurar_driver(navegador)
            
            if not self.driver:
                return

            url = self.url_input.text()
            self.driver.get(url)
            self.log_area.append(f"🌐 Navegando para: {url}")

            wait = WebDriverWait(self.driver, 20)
            actions = ActionChains(self.driver)

            for linha in range(self.tabela_elementos.rowCount()):
                elemento = self.tabela_elementos.item(linha, 0).text()
                tipo_seletor = self.tabela_elementos.cellWidget(linha, 1).currentText()
                seletor = self.tabela_elementos.item(linha, 2).text()
                acao = self.tabela_elementos.cellWidget(linha, 3).currentText()
                valor = self.tabela_elementos.item(linha, 4).text()

                self.log_area.append(f"⏳ Processando elemento: {elemento}")

                metodos_selecao = {
                    'ID': By.ID,
                    'Name': By.NAME,
                    'XPath': By.XPATH,
                    'CSS Selector': By.CSS_SELECTOR,
                    'Class Name': By.CLASS_NAME,
                    'Link Text': By.LINK_TEXT
                }

                try:
                    elemento_web = wait.until(
                        EC.presence_of_element_located((metodos_selecao[tipo_seletor], seletor))
                    )

                    self.driver.execute_script("arguments[0].scrollIntoView(true);", elemento_web)
                    wait.until(EC.visibility_of(elemento_web))

                    def safe_interaction():
                        valor_processado = valor
                        if valor.lower().startswith('random:'):
                            valor_processado = self._gerar_valor_aleatorio(valor.split(':')[1])

                        try:
                            if acao == 'Inserir Texto':
                                self.driver.execute_script("arguments[0].value = '';", elemento_web)
                                elemento_web.send_keys(valor_processado)
                                self.log_area.append(f"✏️ Inserindo texto em {elemento}: {valor_processado}")
                            
                            elif acao == 'Clicar':
                                self.driver.execute_script("arguments[0].click();", elemento_web)
                                self.log_area.append(f"👆 Clicando em {elemento}")
                            
                            elif acao == 'Verificar Texto':
                                texto_atual = elemento_web.text
                                if valor in texto_atual:
                                    self.log_area.append(f"✅ Verificação de texto OK para {elemento}")
                                else:
                                    erro_msg = f"❌ Falha na verificação de texto para {elemento}"
                                    self.log_area.append(erro_msg)
                                    self._salvar_screenshot(erro_msg)
                            
                            elif acao == 'Verificar Existência':
                                if elemento_web:
                                    self.log_area.append(f"✅ Elemento {elemento} existe")

                        except Exception as erro_interacao:
                            erro_msg = f"❌ Erro na interação com {elemento}: {erro_interacao}"
                            self.log_area.append(erro_msg)
                            logging.error(erro_msg)
                            self._salvar_screenshot(erro_msg)

                    safe_interaction()

                except Exception as e:
                    erro_msg = f"❌ Erro no elemento {elemento}: {str(e)}"
                    self.log_area.append(erro_msg)
                    logging.error(erro_msg)
                    self._salvar_screenshot(erro_msg)

            self.log_area.append("✅ Testes concluídos!")

        except Exception as erro:
            erro_msg = f"❌ Erro crítico durante execução dos testes: {erro}"
            logging.error(erro_msg)
            self.log_area.append(erro_msg)
            
            if self.driver:
                self._salvar_screenshot(erro_msg)
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    self.log_area.append("🔒 Navegador encerrado")
                except Exception as e:
                    logging.warning(f"Erro ao fechar navegador: {e}")

def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    try:
        teste_app = TesteAutomatizadoE2E()
        teste_app.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical(f"Erro fatal na aplicação: {e}")
        QMessageBox.critical(None, "Erro Crítico", str(e))

if __name__ == '__main__':
    main()