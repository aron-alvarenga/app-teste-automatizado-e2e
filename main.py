import sys
import random
import json
import os
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, 
                             QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, 
                             QWidget)
from PyQt5.QtCore import Qt
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

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('e2e_tester.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

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
        self.setGeometry(100, 100, 800, 600)

        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        layout_principal = QVBoxLayout()

        url_layout = QHBoxLayout()
        url_label = QLabel('URL do Teste:')
        self.url_input = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout_principal.addLayout(url_layout)

        self.tabela_elementos = QTableWidget()
        self.tabela_elementos.setColumnCount(5)
        self.tabela_elementos.setHorizontalHeaderLabels(['Elemento', 'Tipo de Seletor', 'Seletor', 'Ação', 'Valor'])
        layout_principal.addWidget(self.tabela_elementos)

        botoes_layout = QHBoxLayout()
        
        adicionar_btn = QPushButton('Adicionar Elemento')
        adicionar_btn.clicked.connect(self.adicionar_elemento)
        botoes_layout.addWidget(adicionar_btn)

        remover_btn = QPushButton('Remover Elemento')
        remover_btn.clicked.connect(self.remover_elemento)
        botoes_layout.addWidget(remover_btn)

        salvar_btn = QPushButton('Salvar Configuração')
        salvar_btn.clicked.connect(self.salvar_configuracao)
        botoes_layout.addWidget(salvar_btn)

        carregar_btn = QPushButton('Carregar Configuração')
        carregar_btn.clicked.connect(self.carregar_configuracao)
        botoes_layout.addWidget(carregar_btn)

        layout_principal.addLayout(botoes_layout)

        execucao_layout = QHBoxLayout()
        
        executar_btn = QPushButton('Executar Testes')
        executar_btn.clicked.connect(self.executar_testes)
        execucao_layout.addWidget(executar_btn)

        self.tipo_navegador = QComboBox()
        self.tipo_navegador.addItems(['Chrome', 'Firefox', 'Edge'])
        execucao_layout.addWidget(self.tipo_navegador)

        layout_principal.addLayout(execucao_layout)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout_principal.addWidget(self.log_area)

        container = QWidget()
        container.setLayout(layout_principal)
        self.setCentralWidget(container)

    def adicionar_elemento(self):
        linhas = self.tabela_elementos.rowCount()
        self.tabela_elementos.insertRow(linhas)
        
        seletor_combo = QComboBox()
        seletor_combo.addItems(['ID', 'Name', 'XPath', 'CSS Selector', 'Class Name', 'Link Text'])
        self.tabela_elementos.setCellWidget(linhas, 1, seletor_combo)

        acoes_combo = QComboBox()
        acoes_combo.addItems(['Inserir Texto', 'Clicar', 'Verificar Texto', 'Verificar Existência'])
        self.tabela_elementos.setCellWidget(linhas, 3, acoes_combo)

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

                seletor_combo = QComboBox()
                seletor_combo.addItems(['ID', 'Name', 'XPath', 'CSS Selector', 'Class Name', 'Link Text'])
                indice = seletor_combo.findText(elemento['tipo_seletor'])
                seletor_combo.setCurrentIndex(indice)
                self.tabela_elementos.setCellWidget(linha, 1, seletor_combo)

                item_seletor = QTableWidgetItem(elemento['seletor'])
                self.tabela_elementos.setItem(linha, 2, item_seletor)

                acoes_combo = QComboBox()
                acoes_combo.addItems(['Inserir Texto', 'Clicar', 'Verificar Texto', 'Verificar Existência'])
                indice = acoes_combo.findText(elemento['acao'])
                acoes_combo.setCurrentIndex(indice)
                self.tabela_elementos.setCellWidget(linha, 3, acoes_combo)

                item_valor = QTableWidgetItem(elemento['valor'])
                self.tabela_elementos.setItem(linha, 4, item_valor)

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
            
            self.log_area.append(f"Screenshot de erro salvo em: {nome_arquivo}")
            logging.info(f"Screenshot de erro salvo: {nome_arquivo}")
        
        except Exception as e:
            logging.error(f"Erro ao salvar screenshot: {e}")
            self.log_area.append(f"Falha ao salvar screenshot: {e}")

    def executar_testes(self):
        try:
            self.log_area.clear()
            
            navegador = self.tipo_navegador.currentText()
            
            self.driver = self._configurar_driver(navegador)
            
            if not self.driver:
                return

            url = self.url_input.text()
            self.driver.get(url)
            self.log_area.append(f"Navegando para: {url}")

            wait = WebDriverWait(self.driver, 20)
            actions = ActionChains(self.driver)

            for linha in range(self.tabela_elementos.rowCount()):
                elemento = self.tabela_elementos.item(linha, 0).text()
                tipo_seletor = self.tabela_elementos.cellWidget(linha, 1).currentText()
                seletor = self.tabela_elementos.item(linha, 2).text()
                acao = self.tabela_elementos.cellWidget(linha, 3).currentText()
                valor = self.tabela_elementos.item(linha, 4).text()

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
                                self.log_area.append(f"Inserindo texto em {elemento}: {valor_processado}")
                            
                            elif acao == 'Clicar':
                                self.driver.execute_script("arguments[0].click();", elemento_web)
                                self.log_area.append(f"Clicando em {elemento}")
                            
                            elif acao == 'Verificar Texto':
                                texto_atual = elemento_web.text
                                if valor in texto_atual:
                                    self.log_area.append(f"Verificação de texto OK para {elemento}")
                                else:
                                    erro_msg = f"Falha na verificação de texto para {elemento}"
                                    self.log_area.append(erro_msg)
                                    self._salvar_screenshot(erro_msg)
                            
                            elif acao == 'Verificar Existência':
                                if elemento_web:
                                    self.log_area.append(f"Elemento {elemento} existe")

                        except Exception as erro_interacao:
                            erro_msg = f"Erro na interação com {elemento}: {erro_interacao}"
                            self.log_area.append(erro_msg)
                            logging.error(erro_msg)
                            self._salvar_screenshot(erro_msg)

                    safe_interaction()

                except Exception as e:
                    erro_msg = f"Erro no elemento {elemento}: {str(e)}"
                    self.log_area.append(erro_msg)
                    logging.error(erro_msg)
                    self._salvar_screenshot(erro_msg)

        except Exception as erro:
            erro_msg = f"Erro crítico durante execução dos testes: {erro}"
            logging.error(erro_msg)
            self.log_area.append(erro_msg)
            
            if self.driver:
                self._salvar_screenshot(erro_msg)
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logging.warning(f"Erro ao fechar navegador: {e}")

def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    try:
        teste_app = TesteAutomatizadoE2E()
        teste_app.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical(f"Erro fatal na aplicação: {e}")
        QMessageBox.critical(None, "Erro Crítico", str(e))

if __name__ == '__main__':
    main()